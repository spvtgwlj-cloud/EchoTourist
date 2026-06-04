from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from app.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, AuthResponse, UserResponse
from app.core.security import decode_token
from app.services.auth_service import auth_service
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import requests
from jose import jwk, jwt as jose_jwt

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


@router.post("/register", response_model=AuthResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.register(
        db, email=req.email, password=req.password, name=req.name
    )


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.login(db, email=req.email, password=req.password)


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return await auth_service.get_me(user)


# ── Google OAuth ──────────────────────────────────────────────────────────

# 开发模式 Mock 谷歌登录
class DevGoogleAuthRequest(BaseModel):
    email: str = ""
    name: str = ""


@router.post("/google/dev", response_model=AuthResponse)
async def google_auth_dev(
    body: DevGoogleAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    """开发模式：模拟 Google OAuth 登录（仅 development 环境可用）。"""
    if settings.environment != "development":
        raise HTTPException(status_code=403, detail="Only available in development mode")

    import uuid as uuid_mod

    email = body.email or f"devuser_{uuid_mod.uuid4().hex[:8]}@example.com"
    name = body.name or "Dev User"

    # 查找或创建用户
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            id=uuid_mod.uuid4(),
            email=email,
            name=name,
            is_active=True,
            is_admin="admin" in email,
            google_id=f"dev_{uuid_mod.uuid4().hex[:12]}",
        )
        db.add(user)
        await db.flush()

    return auth_service._build_auth_response(user)

GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"
_certs_cache: tuple[list, float] | None = None  # (keys, fetch_time)


async def _get_google_public_key(kid: str):
    """获取 Google 公钥并缓存（每 1 小时刷新一次）。"""
    import time
    global _certs_cache
    now = time.time()
    keys = None
    if _certs_cache and now - _certs_cache[1] < 3600:
        keys = _certs_cache[0]
    else:
        try:
            resp = requests.get(GOOGLE_CERTS_URL, timeout=5)
            resp.raise_for_status()
            keys = resp.json().get("keys", [])
            _certs_cache = (keys, now)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Failed to fetch Google certs: {e}")

    for key in keys:
        if key.get("kid") == kid:
            return jwk.construct(key)
    return None


class GoogleAuthRequest(BaseModel):
    credential: str


@router.post("/google", response_model=AuthResponse)
async def google_auth(
    body: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    """使用 Google ID Token 登录或注册。"""
    if not settings.google_client_id:
        raise HTTPException(status_code=501, detail="Google OAuth not configured")

    # 解码 token header 获取 kid
    try:
        unverified_headers = jose_jwt.get_unverified_header(body.credential)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid token format")

    kid = unverified_headers.get("kid")
    if not kid:
        raise HTTPException(status_code=400, detail="Missing token key ID")

    # 获取 Google 公钥并验证
    public_key = await _get_google_public_key(kid)
    if not public_key:
        raise HTTPException(status_code=400, detail="Unable to verify token signature")

    try:
        payload = jose_jwt.decode(
            body.credential,
            public_key,
            algorithms=["RS256"],
            audience=settings.google_client_id,
            options={"verify_at_hash": False},
        )
    except jose_jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jose_jwt.JWTError as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {e}")

    # 提取用户信息
    google_id = payload.get("sub")
    email = payload.get("email", "")
    name = payload.get("name", email.split("@")[0] if email else "User")
    avatar_url = payload.get("picture")

    if not google_id or not email:
        raise HTTPException(status_code=400, detail="Missing required user info from Google")

    # 查找或创建用户
    result = await db.execute(
        select(User).where(
            (User.email == email) | (User.google_id == google_id)
        )
    )
    user = result.scalar_one_or_none()

    if user:
        # 更新 google_id（如果之前是通过邮箱注册的）
        if not user.google_id:
            user.google_id = google_id
        if avatar_url and not user.avatar_url:
            user.avatar_url = avatar_url
        await db.flush()
    else:
        # 创建新用户
        from app.core.security import hash_password
        import uuid
        user = User(
            id=uuid.uuid4(),
            email=email,
            name=name,
            google_id=google_id,
            avatar_url=avatar_url,
            is_active=True,
            is_admin=False,
        )
        db.add(user)
        await db.flush()

    return auth_service._build_auth_response(user)
