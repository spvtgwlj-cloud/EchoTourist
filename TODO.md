# Echo Tours 全栈旅游平台 — 项目状态

> 生成时间：2026-06-04 16:45 UTC+8
> 目的：在开启新对话前完整传递上下文

---

## 一、项目整体完成情况

### Phase 1 — 项目骨架 ✅ 已完成

交付 ~65 个文件，建立基本项目结构和功能雏形：

- **后端 (FastAPI 28 个文件)**：数据模型（Tour/User/Order 等 8 个表）、4 个 API 路由（auth/tours/orders/payments）、数据库配置、JWT 认证、Dockerfile
- **前端 (Next.js 15 31 个文件)**：首页/产品列表/详情/结账/登录/订单/404 共 7 个页面、Header/Footer/TourCard 组件、3 语言 i18n、Shadcn/ui 基座
- **基础设施**：Docker Compose（postgres/redis/es/backend/frontend 5 服务）、CI Pipeline、部署脚本

### Phase 2 — 扩展功能 ✅ 全部完成 + 迭代补充

交付 ~100+ 个新增文件，完成 9 个 Batch 迭代：

| Batch | 内容 | 核心交付 |
|-------|------|---------|
| Batch 1 | 架构分层 | 异常体系、CRUD 基类、4 个 Service、错误中间件、统一响应格式 |
| Batch 2 | Redis + ES | 异步 Redis 缓存装饰器、ES 索引映射+搜索查询+批量索引 |
| Batch 3 | 领域模型 | Review/Destination/Wishlist 模型+CRUD+API + User Profile API |
| Batch 4 | Celery 异步 | Celery 实例、邮件任务(欢迎/预订确认)、搜索重建、维护任务 |
| Batch 5 | 前端页面 | 目的地/搜索/Profile/心愿单 5 新页面、修复 auth/checkout/Header 3 个 bug |
| Batch 6 | 管理后台 | Admin API(统计/CRUD/审核)、前端仪表盘/产品/订单/评论管理 |
| Batch 7 | 收尾 | Alembic 初始迁移、slowapi 限流(120/min)、psycopg2 依赖 |
| Batch 8 | 种子数据 + SSR 修复 + E2E 测试 | `scripts/seed_data.py`、Next.js API Rewrite、Playwright 26 项测试 |
| **Batch 9** | **景点功能 + 图片修复 + 弃用清理** | **45 景点（含 Unsplash 图片）、SVG 占位图、`datetime.utcnow()` 修复** |

---

## 二、当前交付概览

### 文件统计

| 类别 | 文件数 |
|------|--------|
| **后端模型** | 13 个（Tour/TourTranslation/TourDate/TourImage/User/Order/OrderPassenger/Review/Destination/DestinationTranslation/Wishlist/**Attraction**/**AttractionTranslation**） |
| **API 端点** | 30+（auth/tours/orders/payments/search/reviews/destinations/**attractions**/wishlist/users/admin） |
| **前端页面** | 15 个路由（含 3 个管理后台子页） |
| **Docker 服务** | 8 个（postgres/redis/es/backend/frontend/celery_worker/celery_beat） |
| **多语言** | 3 个（en/zh/es） |

### 服务状态

| 服务 | 镜像 | 端口 | 运行状态 |
|------|------|------|---------|
| PostgreSQL 16 | postgres:16-alpine | 5432 | ✅ Healthy |
| Redis 7 | redis:7-alpine | 6379 | ✅ Healthy |
| Elasticsearch 8.17 | elasticsearch:8.17.0 | 9200 | ✅ Healthy |
| Backend (FastAPI) | echo-website-backend | 8000 | ✅ Up |
| Frontend (Next.js 15) | echo-website-frontend | 3000 | ✅ Up |
| Celery Worker | echo-website-celery_worker | — | ✅ Connected to Redis |
| Celery Beat | echo-website-celery_beat | — | ✅ Beat running |

### API 端点

| 前缀 | 端点 | 认证 | 说明 |
|------|------|------|------|
| `/api/v1/auth` | POST register / login / GET me | 部分 | 注册/登录/当前用户 |
| `/api/v1/tours` | GET list / detail / dates | 否 | 产品浏览 |
| `/api/v1/orders` | POST / GET list / detail | JWT | 预订管理 |
| `/api/v1/payments` | POST create-intent / POST webhook | 否 | Stripe 支付 |
| `/api/v1/search` | GET search | 否 | ES 全文搜索 |
| `/api/v1/reviews` | POST create / GET tour reviews | 部分 | 评价 |
| `/api/v1/destinations` | GET list / detail / tours | 否 | 目的地 |
| `/api/v1/destinations/{slug}/attractions` | GET list | 否 | **景点列表（按 sort_order 排序）** |
| `/api/v1/wishlist` | GET / POST / DELETE | JWT | 收藏 |
| `/api/v1/users` | GET profile / PATCH profile | JWT | 用户资料 |
| `/api/v1/admin` | stats / tours / orders / users / reviews | Admin | 管理后台 |
| `/health` | GET | 否 | 健康检查 |

### 前端页面 (15 个路由)

| 路由 | 类型 | 说明 |
|------|------|------|
| `/[locale]` | SSR | 首页（Hero + 特色产品 + 目的地预览 + CTA） |
| `/[locale]/tours` | SSR | 旅游产品列表（分页 + 难度筛选） |
| `/[locale]/tours/[slug]` | SSR+CSR | 详情（图片画廊/行程/预订边栏/日期选择/星级评分） |
| `/[locale]/search` | CSR | 全文搜索（300ms 防抖 + 分面筛选 + 排序） |
| `/[locale]/destinations` | SSR | 目的地列表 |
| `/[locale]/destinations/[slug]` | SSR | 目的地详情 + 景点网格（Top 15）+ 关联 tours |
| `/[locale]/auth` | CSR | 登录/注册（完整 API 连接） |
| `/[locale]/checkout` | CSR | 结账（先创建订单再支付 + 联系人表单） |
| `/[locale]/checkout/success` | CSR | 支付成功确认 |
| `/[locale]/user/orders` | CSR | 订单列表 |
| `/[locale]/user/profile` | CSR | 个人资料编辑 |
| `/[locale]/user/wishlist` | CSR | 心愿单 |
| `/[locale]/admin` | CSR | 管理仪表盘 |
| `/[locale]/admin/tours` | CSR | 产品管理表格 |
| `/[locale]/admin/orders` | CSR | 订单管理表格 |
| `/[locale]/admin/reviews` | CSR | 评论审核 |

### 种子数据

| 类别 | 数量 | 说明 |
|------|------|------|
| 🏙️ **目的地** | 3 个 | 北京、南京、西安，中英双语 |
| 🏛️ **旅游产品** | 12 个 | 覆盖北京 9 个 5A 景区 + 北京3日游 + 南京2日游 + 西安2日游 |
| 🏛️ **景点** | **45 个** | **每城市 Top 15，本地 SVG 占位图 + 中英描述 + 评分（支持管理后台替换为真实图片）** |
| 👤 **用户** | 4 个 | 管理员 1 + 演示用户 3 |
| 💬 **评论** | 12 条 | 中英各半，3-5 星，已审核 |
| 📅 **团期** | 55 个 | 覆盖未来 2-3 个月 |
| 🖼️ **产品图片** | 22 张 | SVG 渐变占位图 + 加载失败回退组件 |

### 测试

| 测试组 | 用例数 | 类型 |
|--------|--------|------|
| 后端单元/集成测试 | **307 项** | pytest（异常/CRUD/Service/API/Cache/Search/Celery + 全量模型/业务流程/边缘数据） |
| E2E 测试 | **26 项** | Playwright Chromium（首页/产品/搜索/认证/管理后台） |
| Python E2E 自动化 | **16 步** | Playwright Python sync_api 有头模式（全业务流程：浏览→注册→下单→支付→评价→后台） |
| **合计** | **333 项 + 16 步 E2E** | 全部通过 ✅ |

---

## 三、已知问题 / 待改进

### 优先级: 高 — 影响用户体验

1. ~~**管理后台 Tour/User 创建功能缺失**~~ ✅ **已解决**
   - `POST /api/v1/admin/tours` + 前端创建表单 + 图片上传已实现

2. ~~**Alembic 迁移落后于模型**~~ ✅ **已解决**
   - 完整 schema 迁移 `5bf1e9edbde4` 已编写，覆盖全部 13 个表

### 优先级: 中 — 功能完善

3. ~~**前端 loading skeleton**~~ ✅ **已解决**
   - 已为 7 个页面创建专用骨架屏
   - 覆盖：首页、产品列表/详情、目的地列表/详情、搜索、管理后台

4. ~~**OAuth 登录 stub**~~ ✅ **已解决**
   - 后端添加 `POST /api/v1/auth/google/dev` 开发模式 Mock 端点
   - 前端增加 🛠️ **Dev Google 登录**按钮（无 Google Client ID 时自动显示）
   - 支持自定义邮箱登录或自动生成随机邮箱
   - 生产环境配置真实 GOOGLE_CLIENT_ID 后自动切换为正式 OAuth

5. **Stripe 支付生产就绪**
   - 需配置真实 Stripe secret key + webhook secret
   - 当前在开发模式使用 mock

### 优先级: 低 — 优化/远期

6. **搜索页面 useSearchParams 兼容性**
   - next-intl 导出方式需确认兼容性

7. **按领域拆分微服务** — Booking/Payment/Search/User/CMS/AI/Notification
8. **AI 旅行规划** — LLM 驱动的行程推荐
9. **更多语言** — ja/ko/fr/de/ar
10. **Kubernetes 迁移** — 从 Docker Compose 到 K8s
11. **原生移动 App** — React Native

---

## 四、关键文件路径速查

### 后端

| 路径 | 说明 |
|------|------|
| `docker-compose.yml` | 8 个服务编排 |
| `src/backend/main.py` | FastAPI 入口 + 路由注册 + 限流 |
| `src/backend/app/database.py` | DB 引擎 + init_db + Alembic 迁移 |
| `src/backend/app/config.py` | pydantic-settings 配置 |
| `src/backend/app/api/v1/` | 11 个 API 路由文件（含 attractions） |
| `src/backend/app/models/` | 13 个 SQLAlchemy 模型 |
| `src/backend/app/crud/` | 8 个 CRUD 文件（含 attraction） |
| `src/backend/app/services/` | 5 个 Service 文件 |
| `src/backend/app/cache/` | Redis 缓存层 |
| `src/backend/app/search/` | ES 搜索层 |
| `src/backend/app/tasks/` | Celery 任务层 |
| `src/backend/alembic/versions/` | 数据库迁移文件 |
| `src/backend/tests/` | 23 个测试文件，260 项测试 |

### 前端

| 路径 | 说明 |
|------|------|
| `src/frontend/app/[locale]/` | 15 个页面路由 |
| `src/frontend/components/` | ~18 个组件（含 ImageWithFallback） |
| `src/frontend/lib/` | API 客户端 + Types + Store + Utils |
| `src/frontend/messages/` | en/zh/es 3 语言翻译 |
| `src/frontend/public/images/tours/` | 22 个 SVG 占位图 |
| `src/frontend/public/images/destinations/` | 3 个 SVG 占位图 |

### 其他

| 路径 | 说明 |
|------|------|
| `scripts/seed_data.py` | 种子数据脚本（运行: `docker compose exec backend python /app/scripts/seed_data.py`） |
| `scripts/e2e_test.py` | **Python Playwright 全业务流程自动化脚本（16 步，有头模式）** |
| `scripts/generate_placeholders.py` | SVG 占位图生成脚本 |
| `tests/e2e/` | Playwright E2E 测试（4 个文件，26 项） |
| `docs/应用程序开发进展.md` | 完整开发进展文档 |

---

## 五、启动方式

```bash
# 启动全部服务
cd /Users/wulianjun/.claude/Echo-Website
docker compose up --build -d

# 初始化新表（新增 Attraction 模型后需要）
docker compose exec backend python3 -c "
import asyncio
from app.database import engine, Base
async def create():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
asyncio.run(create())
"

# 运行种子数据
docker compose exec backend python /app/scripts/seed_data.py

# 运行全部后端测试
docker compose exec backend bash -c "cd /app && pytest tests/ -v"

# 运行 E2E 测试（从宿主机）
npx playwright test --config=tests/e2e/playwright.config.ts

# 访问
open http://localhost:3000          # 前端
open http://localhost:3000/en/destinations/beijing  # 北京景点
open http://localhost:8000/docs     # API 文档
```

---

> **项目根目录**: `/Users/wulianjun/.claude/Echo-Website`
> **登录凭据**: `admin@echotours.com` / `Admin123!`
> **当前版本**: v1.7（Python Playwright 全业务流程自动化脚本 + 16 步 E2E 通过 + API 兜底容错 + 有头模式截图验证）
> **下一步建议**: 继续中/低优先级项或进入新功能开发
