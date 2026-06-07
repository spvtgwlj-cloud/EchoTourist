"""搜索 API 路由。"""

from fastapi import APIRouter, Query
from typing import Optional

from app.search.client import get_es
from app.search.query import search_tours
from app.schemas.search import SearchResponse

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResponse)
async def search(
    q: Optional[str] = Query(None, description="搜索关键词"),
    locale: str = Query("en"),
    difficulty: Optional[str] = Query(None),
    theme: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    min_duration: Optional[int] = Query(None),
    max_duration: Optional[int] = Query(None),
    sort_by: str = Query("rating", description="rating | price_asc | price_desc | duration | newest"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
):
    es = await get_es()
    return await search_tours(
        es,
        query=q,
        locale=locale,
        difficulty=difficulty,
        theme=theme,
        min_price=min_price,
        max_price=max_price,
        min_duration=min_duration,
        max_duration=max_duration,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )
