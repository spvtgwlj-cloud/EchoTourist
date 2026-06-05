# Echo Tours — 旅游平台产品设计文档 (PRD)

> **版本**: v2.7.0  
> **最后更新**: 2026-06-05  
> **文档状态**: ✅ 已定稿  
> **产品名称**: Echo Tours（回声旅行）  
> **产品定位**: 面向全球旅行者的多语言旅游预订平台

---

## 目录

1. [产品概述](#1-产品概述)
2. [目标用户与角色](#2-目标用户与角色)
3. [功能模块总览](#3-功能模块总览)
4. [公共功能模块](#4-公共功能模块)
5. [用户功能模块](#5-用户功能模块)
6. [管理员功能模块](#6-管理员功能模块)
7. [订单与支付系统](#7-订单与支付系统)
8. [搜索系统](#8-搜索系统)
9. [内容管理系统](#9-内容管理系统)
10. [国际化与多语言](#10-国际化与多语言)
11. [缓存与性能优化](#11-缓存与性能优化)
12. [后台任务系统](#12-后台任务系统)
13. [安全体系](#13-安全体系)
14. [数据模型总览](#14-数据模型总览)
15. [API 端点完整列表](#15-api-接口完整列表)
16. [前端路由与页面映射](#16-前端路由与页面映射)
17. [技术架构](#17-技术架构)
18. [部署与运维](#18-部署与运维)
19. [非功能性需求](#19-非功能性需求)
20. [附录](#20-附录)

---

## 1. 产品概述

### 1.1 产品愿景

Echo Tours 是一个面向全球旅行者的全栈旅游预订平台，旨在为用户提供从目的地探索、旅游产品浏览、景点发现到在线预订支付的一站式体验。平台支持多语言（英语、简体中文、西班牙语），覆盖旅游产品（跟团游/私人定制游）和景点门票两条核心业务线。

### 1.2 核心价值主张

| 价值 | 说明 |
|------|------|
| **一站式预订** | 从浏览、收藏、下单到支付，全流程在线完成 |
| **多语言支持** | 前端 UI + 后端业务内容三层国际化架构 |
| **灵活订单** | 支持旅游产品预订和景点门票购买双业务线 |
| **安全支付** | 集成 Stripe 支付网关，支持沙箱测试模式 |
| **智能搜索** | Elasticsearch 全文搜索，多维度筛选与排序 |
| **管理员工台** | 完整的后台管理系统，涵盖产品、订单、评价审核 |

### 1.3 产品技术栈

| 层次 | 技术 | 备注 |
|------|------|------|
| **前端框架** | Next.js 15 (React 19) | SSR + 客户端交互 |
| **前端语言** | TypeScript 5.7 | 全类型安全 |
| **样式方案** | Tailwind CSS 4 + Shadcn/ui | 原子化 CSS |
| **后端框架** | FastAPI (Python 3.12+) | 异步高性能 |
| **数据库** | PostgreSQL 16 | 关系型主存储 |
| **ORM** | SQLAlchemy 2.0 (async) | 异步 ORM |
| **缓存** | Redis 7 | 数据缓存 + Celery 消息代理 |
| **搜索引擎** | Elasticsearch 8 | 全文搜索 |
| **支付网关** | Stripe | Checkout Sessions |
| **任务队列** | Celery 5.4 | 异步/定时任务 |
| **容器化** | Docker | 微服务部署 |
| **CI/CD** | GitHub Actions | 自动化测试与部署 |

---

## 2. 目标用户与角色

### 2.1 用户角色定义

| 角色 | 权限级别 | 描述 |
|------|----------|------|
| **访客 (Guest)** | 公开访问 | 未登录用户，可浏览所有公开内容 |
| **注册用户 (User)** | 基本权限 | 登录后可预订、收藏、评价、查看订单 |
| **管理员 (Admin)** | 最高权限 | 管理产品、订单、用户、评价审核、系统维护 |

### 2.2 用户画像

| 画像 | 需求场景 |
|------|----------|
| **自由行游客** | 浏览目的地和景点，购买景点门票 |
| **跟团游旅客** | 搜索旅游产品，对比行程和价格，预订支付 |
| **旅行社/导游** | 管理员后台创建和管理旅游产品 |
| **平台运营者** | 审核用户评价，查看平台统计数据，管理订单 |

---

## 3. 功能模块总览

```
Echo Tours 功能地图
├── 🌐 公共功能
│   ├── 首页
│   ├── 旅游产品列表
│   ├── 旅游产品详情
│   ├── 目的地列表
│   ├── 目的地详情
│   ├── 景点浏览
│   ├── 全文搜索
│   ├── 用户认证（登录/注册/Google SSO）
│   └── 国际化和多语言切换
│
├── 👤 用户功能
│   ├── 旅游产品收藏（心愿单）
│   ├── 景点收藏
│   ├── 订单创建（旅游/门票）
│   ├── Stripe 支付
│   ├── 订单历史查询
│   ├── 旅游产品评价
│   └── 个人资料管理
│
└── 🔧 管理员功能
    ├── 仪表盘（统计数据）
    ├── 旅游产品管理（CRUD + 多语言）
    ├── 出发日期管理
    ├── 图片/视频上传管理
    ├── 订单管理
    ├── 用户管理
    ├── 评价审核（批准/拒绝）
    └── 搜索索引重建
```

---

## 4. 公共功能模块

### 4.1 首页 (Homepage)

**路由**: `/:locale/`  
**页面类型**: 服务端渲染 (SSR)  
**缓存**: ISR revalidate=300s

#### 功能点

| 区域 | 内容 | 数据来源 |
|------|------|----------|
| **Hero 横幅** | 渐变背景 + 主标题/副标题 + 2 个 CTA 按钮（"查看旅游" / "查看全部"） | 静态翻译文案 |
| **精选旅游** | 评分最高的 6 个旅游产品，3 列网格展示 TourCard | `GET /api/v1/tours?sort=rating&page_size=6` |
| **为什么选择我们** | 4 个特色卡片（专家导游、定制旅游、最优价格、24/7 支持） | 静态翻译文案 |
| **热门目的地** | 3 个静态目的地卡片（北京、南京、西安），链接到目的地详情 | 硬编码翻译键 |
| **行动号召 CTA** | 全宽主色区域 + CTA 按钮 | 静态翻译文案 |

#### 异常状态

- **加载中**: 完整骨架屏（HeroSkeleton + FeaturedSkeleton + FeaturesSkeleton + DestinationsPreviewSkeleton + CTASkeleton）
- **数据为空**: 精选旅游区域隐藏（不显示空 Section）
- **网络错误**: 数据获取失败时该区域静默隐藏

### 4.2 旅游产品列表 (Tours List)

**路由**: `/:locale/tours`  
**页面类型**: SSR  
**缓存**: ISR revalidate=120s

#### 功能点

| 功能 | 详情 |
|------|------|
| **列表展示** | 分页网格展示，每页 12 个 TourCard |
| **按目的地筛选** | 可选 URL 查询参数 `?destination=slug` |
| **结果计数** | 顶部显示匹配产品数量 |
| **导航** | 点击卡片进入旅游详情页 |

#### 异常状态

- **加载中**: 6 个 TourCardSkeleton 骨架占位
- **数据为空**: 显示空状态提示 "没有找到旅游产品"
- **错误**: 静默失败（ISR 在构建时获取数据）

### 4.3 旅游产品详情 (Tour Detail)

**路由**: `/:locale/tours/[slug]`  
**页面类型**: SSR + 客户端交互 (TourDetailClient)  
**缓存**: SSR revalidate=300s

#### 功能点

| 区域 | 详情 |
|------|------|
| **面包屑导航** | 旅游列表 > 当前旅游名称 |
| **图片画廊** | 可切换的大图展示（支持图片/视频），带指示器点导航 |
| **评分徽章** | 星级 + 平均评分 + 评价数量 |
| **元信息** | 难度徽章（简单/中等/挑战性）、产品类型、名称、副标题 |
| **基本信息** | 行程天数/晚数、最大人数、目的地名称 |
| **产品描述** | 概述文本 |
| **行程亮点** | 带绿色复选标记的要点列表 |
| **每日行程** | 编号卡片，含日标题、描述、餐食徽章 |
| **包含/不包含** | 两个并列列表（勾选/叉选） |
| **固定侧边栏** | 日期选择器（可用日期列表，售罄/已过时禁用）、人数计数器（+/-）、价格计算、"立即预订" 按钮 |
| **收藏按钮** | WishlistButton 一键收藏切换 |
| **评价区域** | 评价列表 + 评价表单（已登录用户） |

#### 日期选择器逻辑

- 仅显示 `status="available"` 且 `start_date >= today` 的团期
- 已售罄日期显示 "已售罄" 标签并禁用选择
- 人数计数器范围 1 ~ `min(max_pax, availability)`
- 价格实时计算：`price_per_pax × pax_count`

#### 异常状态

- **加载中**: TourDetailSkeleton 完整骨架
- **产品不存在**: 调用 `notFound()` 显示自定义 404 页面
- **无可用日期**: 日期选择器显示 "暂无可用日期"
- **无效 slug**: 404 页面

### 4.4 目的地列表 (Destinations)

**路由**: `/:locale/destinations`  
**页面类型**: SSR

#### 功能点

| 功能 | 详情 |
|------|------|
| **目的地展示** | 所有活跃目的地列表，每个含名称、描述、旅游/景点数量 |
| **关联景点** | 每个目的地展示前 5 个景点，含图片、评分、价格 |
| **收藏景点** | 每个景点卡片上的 WishlistButton |
| **查看全部** | 链接到目的地详情页 |

#### 异常状态

- **加载中**: DestinationCardSkeleton 骨架占位
- **数据为空**: MapPin 图标 + "暂无目的地" 提示

### 4.5 目的地详情 (Destination Detail)

**路由**: `/:locale/destinations/[slug]`  
**页面类型**: SSR

#### 功能点

| 区域 | 详情 |
|------|------|
| **头部信息** | 返回链接、目的地名称、描述、旅游产品数量 |
| **景点网格** | 景点卡片列表（图片、名称、评分、价格），悬停显示 "立即预订" 按钮 |
| **景点直达下单** | 点击 "立即预订" 携带 `attraction_id`、`ticket_id`、`price` 等参数跳转结账页 |
| **旅游产品网格** | 使用 TourCard 展示该目的地的旅游产品 |

#### 异常状态

- **加载中**: DestinationDetailSkeleton
- **目的地不存在**: `notFound()` → 404
- **无景点/旅游**: 显示 "暂无" 提示

### 4.6 景点浏览 (Attractions)

景点数据嵌套在目的地模块中，通过以下端点获取：

- `GET /api/v1/destinations/{slug}/attractions` — 获取目的地下的所有活跃景点（按 sort_order 排序）

景点卡片包含：
- 景点图片
- 景点名称（多语言）
- 评分（1-5 星）
- 起价
- 快捷收藏按钮
- 快捷预订按钮（直达结账）

### 4.7 全文搜索 (Search)

**路由**: `/:locale/search`  
**页面类型**: 完全客户端渲染

详见 [第 8 节 — 搜索系统](#8-搜索系统)

### 4.8 用户认证 (Auth)

**路由**: `/:locale/auth`  
**页面类型**: 客户端渲染

#### 功能点

| 功能 | 详情 |
|------|------|
| **邮箱密码登录** | email + password → `POST /api/v1/auth/login` |
| **邮箱密码注册** | name + email + password → `POST /api/v1/auth/register` |
| **Google 一键登录** | Google Identity Services (GIS) → `POST /api/v1/auth/google` |
| **开发模式登录** | 开发环境下的模拟 Google 登录 → `POST /api/v1/auth/google/dev` |
| **模式切换** | URL 参数 `?mode=signup` 控制登录/注册切换 |
| **已登录重定向** | 已认证用户自动跳转首页 |

#### 认证流程

1. 登录/注册成功后返回 JWT (`access_token`)
2. Token 存入 `localStorage` 的 `auth_token` 键
3. Zustand Store (`useAuthStore`) 存储用户信息和认证状态
4. 后续请求自动附加 `Authorization: Bearer {token}` 请求头

#### 异常状态

- **表单验证错误**: 红色文字提示
- **认证失败**: 红色错误横幅显示错误详情
- **Google 登录未配置**: 自动降级为 DevGoogleLogin 组件

### 4.9 国际化与多语言切换

- **支持语言**: 英语 (en)、简体中文 (zh)、西班牙语 (es)
- **默认语言**: 英语
- **URL 模式**: `/:locale/...`（前缀模式）
- **语言切换**: Header 中的 Globe 下拉菜单
- **自动检测**: 基于 Accept-Language 请求头

详见 [第 10 节 — 国际化与多语言](#10-国际化与多语言)

---

## 5. 用户功能模块

### 5.1 旅游产品收藏 (Tour Wishlist)

**路由**: `/:locale/user/wishlist`  
**API**: `GET /api/v1/wishlist` / `POST /api/v1/wishlist/{tour_id}` / `DELETE /api/v1/wishlist/{tour_id}`

#### 功能点

| 功能 | 详情 |
|------|------|
| **添加收藏** | 点击 WishlistButton 的心形图标，调用 POST 添加 |
| **取消收藏** | 再次点击已收藏的心形图标，调用 DELETE 移除 |
| **收藏列表** | 页面展示所有收藏的旅游产品，使用 TourCard 渲染 |
| **未登录处理** | 点击收藏按钮时跳转到登录页 |
| **UI 反馈** | 红色实心 = 已收藏，灰色轮廓 = 未收藏，动画过渡 |

#### 异常状态

- **加载中**: TourGridSkeleton (3 卡片)
- **收藏为空**: 心形图标 + "暂无收藏" + "浏览旅游" 按钮
- **未登录**: 静默不加载，或跳转登录页

### 5.2 景点收藏 (Attraction Wishlist)

**API**: `GET /api/v1/wishlist/attractions` / `POST /api/v1/wishlist/attractions/{attraction_id}` / `DELETE /api/v1/wishlist/attractions/{attraction_id}`

与旅游产品收藏共用 WishlistButton 组件，通过 `itemType="attraction"` 区分。

### 5.3 订单创建 (Booking/Order)

**路由**: `/:locale/checkout`  
**API**: `POST /api/v1/orders`

#### 双业务线

| 业务线 | 需要参数 | 执行逻辑 |
|--------|----------|----------|
| **旅游产品预订** | `tour_id` + `tour_date_id` + `pax_count` | 递减团期库存，按团期价格计算总额 |
| **景点门票购买** | `attraction_id` + `attraction_ticket_id` + `pax_count` | 递减门票库存，按票价计算总额 |

#### 结账页面流程

1. 检查用户认证状态（未登录 → 跳转 `/auth`）
2. 从 URL 查询参数读取预订信息：
   - 旅游：`?tour=slug&date=id&pax=N`
   - 景点：`?attraction_id=xxx&ticket_id=xxx&price=yyy&name=zzz`
3. 加载详情展示预订摘要卡片
4. 用户填写联系信息（姓名、邮箱、电话）
5. 点击支付 → 创建订单 → 获取 Stripe Session ID
6. 重定向到 Stripe Checkout 页面
7. 支付完成 → 跳转成功页

#### 异常状态

- **未登录**: 自动跳转登录页
- **认证加载中**: Loading 旋转器
- **Stripe 配置缺失**: 自动切换到模拟支付（mock session）
- **订单创建失败**: 错误提示 + 重试
- **库存不足**: 系统返回错误，前端展示提示

### 5.4 Stripe 支付

**API**: `POST /api/v1/payments/create-intent` + `POST /api/v1/payments/stripe-webhook`

#### 支付流程

1. 前端调用 `POST /api/v1/payments/create-intent` 传入 `order_id`
2. 后端检查订单状态（已支付则拒绝），创建 Stripe Checkout Session
3. 返回 `session_id` → 前端重定向到 Stripe 托管支付页
4. 支付完成后 Stripe 回调 Webhook：`checkout.session.completed`
5. Webhook 处理：更新订单状态为 `confirmed`、支付状态为 `paid`
6. 异步发送预订确认邮件

#### 支付沙箱

- Stripe 未配置时自动返回 `mock_` 前缀的 Session ID
- 前端检测到 mock session 时跳转到模拟成功页

#### 支付成功页

**路由**: `/:locale/checkout/success`

- 绿色复选确认图标
- 显示订单号
- 按钮："查看订单" / "返回首页"

### 5.5 订单历史 (My Orders)

**路由**: `/:locale/user/orders`  
**API**: `GET /api/v1/orders`

#### 功能点

- 加载用户所有订单列表
- 每个订单卡片包含：订单号、旅游/景点名称、出发日期、人数、总价
- 状态徽章（颜色编码）：
  - `pending` = 黄色（待付款）
  - `confirmed` = 绿色（已确认）
  - `completed` = 蓝色（已完成）
  - `cancelled` = 红色（已取消）
  - `refunded` = 灰色（已退款）
- 支付状态徽章：`paid` = 绿色

#### 异常状态

- **加载中**: 3 个 Skeleton 占位
- **订单为空**: 空状态提示 "暂无订单"
- **国际化**: 订单状态通过翻译映射显示对应语言

### 5.6 旅游产品评价 (Reviews)

**API**: `POST /api/v1/reviews` / `GET /api/v1/reviews/tour/{tour_id}`

#### 功能点

| 功能 | 详情 |
|------|------|
| **创建评价** | 已登录用户可提交，含评分（1-5 星）、标题、评论内容 |
| **评价展示** | 旅游详情页展示评价列表（分页），含平均评分 |
| **审核流程** | 新评价默认 `status="pending"`，管理员审核后可见 |
| **邮件通知** | 新评价提交后异步通知管理员 |

#### 异常状态

- **未登录**: 评论表单提示用户登录
- **提交中**: 按钮加载状态 + 旋转器
- **提交错误**: 表单内显示红色错误提示

### 5.7 个人资料管理 (Profile)

**路由**: `/:locale/user/profile`  
**API**: `GET /api/v1/users/me/profile` / `PATCH /api/v1/users/me/profile`

#### 功能点

- 只读邮箱字段
- 可编辑姓名
- 语言区域选择器（en/zh/es）
- 统计卡片：评价数量、订单数量
- 保存按钮（带加载/成功/错误状态）

#### 异常状态

- **未认证**: 页面不渲染
- **加载中**: Skeleton 占位
- **保存失败**: 错误提示

---

## 6. 管理员功能模块

> 所有管理接口需要管理员 JWT 认证（`is_admin=True`）

### 6.1 仪表盘 (Dashboard)

**路由**: `/:locale/admin`  
**API**: `GET /api/v1/admin/stats`

#### 统计指标

| 指标 | 说明 |
|------|------|
| 总旅游产品数 | 含已发布数量 |
| 总订单数 | 全部订单 |
| 总用户数 | 注册用户 |
| 总收入 | 已完成订单的总金额 |
| 待审核评价 | `status="pending"` 的评价数量 |

#### 异常状态

- **非管理员**: 重定向到 `/auth`
- **加载中**: AdminDashboardSkeleton / 旋转器

### 6.2 旅游产品管理

#### 产品列表

**路由**: `/:locale/admin/tours`  
**API**: `GET /api/v1/admin/tours`

- 表格展示：名称、状态、价格、天数、难度、操作按钮
- 状态徽章：已发布（绿色）、草稿（灰色）、其他（黄色）
- 操作：编辑、日期管理、查看预览
- "添加旅游" 按钮链接到创建页面

#### 创建旅游产品

**路由**: `/:locale/admin/tours/create`  
**API**: `POST /api/v1/admin/tours`

表单包含：
- 基本信息：slug、状态、类型（跟团游/私人游）、难度（简单/中等/挑战性）
- 行程天数、晚数、起价、货币（USD/CNY/EUR）
- 最大/最小人数
- 三种语言的名称、副标题、描述
- 多种语言的亮点、包含、不包含动态列表

#### 编辑旅游产品

**路由**: `/:locale/admin/tours/[id]/edit`  
**API**: `GET /api/v1/admin/tours/{tour_id}` + `PATCH /api/v1/admin/tours/{tour_id}`

编辑页面包含三个语言选项卡（英语、中文、西班牙语）：

| 选项卡区域 | 字段 |
|------------|------|
| 基本信息 | slug（只读）、状态、类型、难度、天数、晚数、起价、货币、人数 |
| 名称与描述 | 名称、副标题、描述（各语言独立） |
| 高亮与详情 | 亮点、包含、不包含（各语言独立动态列表） |
| 行程 | 每日行程 JSON 编辑（各语言独立） |
| 照片与视频 | 图片/视频上传、预览、删除、排序 |

图片上传：
- 支持格式：常见图片格式 + MP4/WebM/MOV
- 最大文件：60MB
- 拖放上传区域 + 删除按钮
- `POST /api/v1/admin/upload` → 返回可访问 URL

#### 出发日期管理

**路由**: `/:locale/admin/tours/[id]/dates`  
**API**: 完整 CRUD

- 添加日期：日期选择器 + 价格 + 可用名额
- 日期表格：开始日期、结束日期、价格、可用名额、状态
- 内联编辑：点击行可直接修改价格和名额
- 删除：带确认弹窗
- 状态徽章：可用（绿色）、已售罄（红色）、已取消（灰色）
- 统计：总日期数、可用数、已售罄数

#### 产品删除

- 软删除：设置 `deleted_at` 字段
- API：`DELETE /api/v1/admin/tours/{tour_id}`

### 6.3 订单管理

**路由**: `/:locale/admin/orders`  
**API**: `GET /api/v1/admin/orders` + `PATCH /api/v1/admin/orders/{order_id}/status`

#### 功能点

- 表格展示：订单号、客户名、状态、支付状态、总价、人数、日期
- 状态徽章：待处理（黄）、已确认（绿）、已完成（蓝）、已取消（红）
- 支付状态徽章：已支付（绿）、其他（灰）
- 管理员可更新订单状态和支付状态

### 6.4 用户管理

**API**: `GET /api/v1/admin/users`

- 列出所有注册用户（分页）
- 用于平台运营的用户概览

### 6.5 评价审核

**路由**: `/:locale/admin/reviews`  
**API**: `GET /api/v1/admin/reviews` + `PATCH /api/v1/admin/reviews/{review_id}`

#### 功能点

| 功能 | 详情 |
|------|------|
| **评价列表** | 默认显示待审核评价，支持按状态筛选 |
| **筛选切换** | 待处理 / 已批准 / 已拒绝 三个标签切换 |
| **评价卡片** | 星级评分、标题、评论文本、日期 |
| **审核操作** | 批准（绿色按钮）、拒绝（红色按钮） |
| **自动刷新** | 操作后自动重新加载列表 |

#### 异常状态

- **加载中**: Skeleton + TableSkeleton
- **评论为空**: "未找到评论" 居中提示

### 6.6 搜索索引管理

**API**: `POST /api/v1/admin/reindex`

手动触发 Elasticsearch 全文搜索索引重建。

---

## 7. 订单与支付系统

### 7.1 订单状态机

```
pending → confirmed → completed
    ↓                      ↓
cancelled              cancelled
    ↓
refunded
```

| 状态 | 含义 | 可操作 |
|------|------|--------|
| `pending` | 待付款/待处理 | 管理员可确认或取消 |
| `confirmed` | 已确认（支付成功） | 管理员可标记完成或取消 |
| `completed` | 已完成（出游结束） | 只读终态 |
| `cancelled` | 已取消 | 只读终态 |
| `refunded` | 已退款 | 只读终态 |

### 7.2 支付状态

| 状态 | 含义 |
|------|------|
| `pending` | 未支付 |
| `paid` | 已支付 |

### 7.3 订单号生成规则

格式：`ECHO-YYYYMMDD-XXXXXXXX`

- 前缀：`ECHO`
- 日期：当前日期
- 后缀：UUID 前 8 位大写

示例：`ECHO-20260605-A3F2C1B0`

### 7.4 库存管理策略

- **旅游产品**: 团期级别库存管理，下单时原子递减 `tour_dates.availability`
- **景点门票**: 门票类型级别库存管理，下单时原子递减 `attraction_tickets.availability`
- **并发控制**: Redis 缓存 + 数据库级别原子操作
- **库存不足**: 抛出 `InsufficientStockException`，订单创建失败

### 7.5 价格计算

- **旅游产品**: `total = tour_date.price_per_pax × pax_count`
- **景点门票**: `total = ticket.price × pax_count`
- **费用构成**: subtotal + discount（优惠） + tax（税费） = total

---

## 8. 搜索系统

### 8.1 技术架构

使用 Elasticsearch 8，独立索引 `tours`，每日自动重建。

### 8.2 索引映射

```json
{
  "settings": {
    "analysis": {
      "analyzer": {
        "tours_combined": {
          "tokenizer": "standard",
          "filter": ["lowercase", "asciifolding"]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "id": { "type": "keyword" },
      "slug": { "type": "keyword" },
      "status": { "type": "keyword" },
      "type": { "type": "keyword" },
      "duration_days": { "type": "integer" },
      "start_price": { "type": "float" },
      "currency": { "type": "keyword" },
      "avg_rating": { "type": "float" },
      "review_count": { "type": "integer" },
      "difficulty": { "type": "keyword" },
      "max_pax": { "type": "integer" },
      "destination_ids": { "type": "keyword" },
      "name": { "type": "text", "fields": { "keyword": { "type": "keyword" } } },
      "description": { "type": "text" },
      "subtitle": { "type": "text" },
      "highlights": { "type": "text" },
      "locale": { "type": "keyword" },
      "published_at": { "type": "date" },
      "created_at": { "type": "date" }
    }
  }
}
```

### 8.3 搜索能力

#### 搜索字段权重

| 字段 | 权重 |
|------|------|
| `name` | ×3 |
| `subtitle` | ×2 |
| `description` | ×1.5 |
| `highlights` | ×1 |

#### 筛选条件

| 维度 | 类型 | 示例值 |
|------|------|--------|
| 关键词 (`q`) | 全文搜索 | "Great Wall" |
| 难度 (`difficulty`) | 精确匹配 | easy / moderate / challenging |
| 最低价格 (`min_price`) | 范围过滤 | 100 |
| 最高价格 (`max_price`) | 范围过滤 | 2000 |
| 最短天数 (`min_duration`) | 范围过滤 | 3 |
| 最长天数 (`max_duration`) | 范围过滤 | 14 |
| 语言 (`locale`) | 精确匹配 | en / zh / es |

#### 排序选项

| 排序方式 | 说明 |
|----------|------|
| `rating` | 按评分降序（默认） |
| `price_asc` | 价格升序 |
| `price_desc` | 价格降序 |
| `duration` | 天数升序 |
| `newest` | 最新发布排序 |

#### 聚合统计 (Facets)

| 聚合 | 说明 |
|------|------|
| `difficulties` | 各难度层级的产品数量 |
| `price_ranges` | 价格区间分布（0-100, 100-500, 500-1000, 1000-2000, 2000+） |

### 8.4 前端搜索页面

**路由**: `/:locale/search`

- **实时搜索**: 输入防抖 300ms
- **搜索输入**: SearchInput 组件
- **筛选控件**: SearchFilters 组件（难度、排序）
- **结果展示**: 结果计数 + TourCard 网格
- **空结果**: 空状态提示
- **初始状态**: 从 URL 参数 `?q=&difficulty=&sort_by=` 读取

#### 异常状态

- **加载中**: 旋转器 + TourGridSkeleton
- **错误**: 红色错误横幅 + 错误信息

### 8.5 索引维护

| 任务 | 触发器 | 方式 |
|------|--------|------|
| 启动自动索引 | 应用启动 | `lifespan` 事件中执行 |
| 每日重建 | Celery Beat | 每日一次 `reindex_all_tours` 任务 |
| 手动重建 | 管理员 API | `POST /api/v1/admin/reindex` |

---

## 9. 内容管理系统

### 9.1 旅游产品 (Tour)

| 字段 | 多语言 | 说明 |
|------|--------|------|
| slug | × | URL 标识符 |
| status | × | draft / published |
| type | × | group_tour / private_tour |
| duration_days / nights | × | 行程天数和晚数 |
| max_pax / min_pax | × | 团组人数限制 |
| start_price | × | 起价 |
| currency | × | USD / CNY / EUR |
| difficulty | × | easy / moderate / challenging |
| destination_ids | × | 关联目的地 UUID 数组 |
| avg_rating / review_count | × | 系统自动计算 |
| highlights | × | 产品级亮点（回退用） |
| includes / excludes | × | 产品级包含/不包含（回退用） |
| ✅ name / subtitle / description | ✓ | 核心文案 |
| ✅ itinerary (JSON) | ✓ | 每日行程 |
| ✅ highlights / includes / excludes | ✓ | 翻译级详情 |

### 9.2 目的地 (Destination)

- slug（唯一标识）
- image_url
- status（active / inactive）
- 多语言：name、description、meta_title、meta_description

### 9.3 景点 (Attraction)

- slug（唯一标识，按目的地索引）
- destination_id（关联目的地）
- image_url、rating、sort_order、status
- ticket_price、ticket_currency
- 多语言：name、description、ticket_info、opening_hours

### 9.4 景点门票 (AttractionTicket)

- 关联景点
- ticket_type（standard / vip / child）— 同一景点下类型唯一
- price、currency
- availability（库存数量）
- status（available / sold_out / discontinued）

### 9.5 图片/视频管理

- 上传 API：`POST /api/v1/admin/upload`（最大 60MB）
- 多图管理：`DELETE /api/v1/admin/tours/{tour_id}/images/{image_id}`
- 支持类型：图片 + 视频（MP4 / WebM / MOV）
- 排序字段：`sort_order`

---

## 10. 国际化与多语言

### 10.1 三层国际化架构

| 层次 | 范围 | 实现方式 |
|------|------|----------|
| **L1: UI 文案** | 导航、按钮、标签、提示 | `next-intl` JSON 文件 |
| **L2: 业务内容** | 产品名称、描述、目的地 | 数据库翻译表 |
| **L3: SEO 内容** | 元标题、元描述 | 数据库翻译表 |

### 10.2 前端国际化

- **框架**: next-intl v3
- **文件结构**: `messages/{locale}/common.json`
- **支持语言**: en (英语)、zh (简体中文)、es (西班牙语)
- **URL 模式**: `/{locale}/...` 前缀模式，所有路由带语言前缀
- **语言检测**: 基于 `Accept-Language` 请求头，默认英语
- **切换方式**: Header 下拉菜单，切换后替换 URL 语言前缀

### 10.3 后端内容国际化

- 每个多语言实体对应一个翻译表，使用 `locale` 列区分
- 翻译表使用外键关联主表，CASCADE 删除
- 主表字段存储语言无关数据（slug、价格、状态等）
- 读取策略：优先请求的语言 → 英语 → 第一个可用翻译

### 10.4 翻译表清单

| 主表 | 翻译表 | 多语言字段 |
|------|--------|------------|
| `tours` | `tour_translations` | name, subtitle, description, itinerary, highlights, includes, excludes, meta_title, meta_description |
| `destinations` | `destination_translations` | name, description, meta_title, meta_description |
| `attractions` | `attraction_translations` | name, description, ticket_info, opening_hours, meta_title, meta_description |

---

## 11. 缓存与性能优化

### 11.1 Redis 缓存策略

#### 缓存配置

| 数据 | 缓存键模式 | TTL | 失效时机 |
|------|-----------|-----|----------|
| 旅游产品列表 | `cache:TourService.list_tours:*` | 120s | — |
| 旅游产品详情 | `cache:TourService.get_tour:*` | 300s | — |
| 旅游产品日期 | `cache:TourService.get_tour_dates:*` | 60s | 订单创建时清除 |

#### 缓存装饰器

使用 `@cache_result(ttl=N)` 装饰器：
1. 计算缓存键：MD5(函数名 + 序列化参数)
2. 命中：反序列化 JSON → Pydantic 模型验证
3. 未命中：执行函数 → 序列化结果 → Redis SETEX
4. 缓存键自动排除 `AsyncSession` 参数

#### 缓存清理

使用 `@invalidate_cache("pattern")` 装饰器：
- 修改操作后扫描 Redis 中匹配 `cache:{pattern}:*` 的键并删除
- 订单创建后自动清理对应旅游产品的日期缓存

### 11.2 前端性能优化

| 策略 | 实现 |
|------|------|
| SSR/ISR | 服务端渲染 + 增量静态再生成 |
| 图片优化 | `next/image` 远程图片模式 |
| JS 分包 | Next.js 自动代码分割 |
| 骨架屏 | 每个页面对应专门的 Skeleton 组件 |
| 客户端状态 | Zustand 轻量状态管理 |

### 11.3 后端性能优化

| 策略 | 实现 |
|------|------|
| 异步处理 | FastAPI + asyncpg + async SQLAlchemy |
| 数据库连接池 | pool_size=10, max_overflow=20 |
| 懒加载优化 | 使用 `selectin` 加载策略 |
| 速率限制 | slowapi 120 req/min |
| 连接健康检查 | `pool_pre_ping=True` |

---

## 12. 后台任务系统

### 12.1 Celery 配置

- **Broker**: Redis（默认 localhost:6379/0）
- **序列化**: JSON
- **确认模式**: `task_acks_late=True` — 任务完成后才确认
- **预取**: `worker_prefetch_multiplier=1` — 公平分发
- **结果过期**: 3600 秒自动清理

### 12.2 异步任务清单

| 任务名称 | 功能 | 重试策略 | 触发时机 |
|----------|------|----------|----------|
| `send_welcome_email` | 发送欢迎邮件 | 3 次, 30s 间隔 | 用户注册 |
| `send_booking_confirmation` | 发送预订确认邮件 | 3 次, 30s 间隔 | 支付成功 |
| `send_review_notification` | 通知管理员新评价 | 3 次, 30s 间隔 | 提交评价 |
| `reindex_all_tours` | 重建 ES 搜索索引 | 2 次, 60s 间隔 | 每日 + 手动 |
| `cleanup_expired_sessions` | 清理过期缓存键 | 无 | 每日 |

### 12.3 定时任务 (Celery Beat)

| 任务 | 频率 |
|------|------|
| `cleanup-expired-sessions` | 每天 1 次 |
| `reindex-all-tours` | 每天 1 次 |

---

## 13. 安全体系

### 13.1 认证与授权

| 机制 | 实现 |
|------|------|
| **密码哈希** | bcrypt (passlib) |
| **JWT Token** | HS256 算法，24 小时过期 |
| **Bearer 认证** | `Authorization: Bearer {token}` |
| **管理员鉴权** | 中间件检查 `user.is_admin` |
| **Google OAuth** | Google Identity Services + ID 令牌验证 |

### 13.2 数据安全

| 措施 | 实现 |
|------|------|
| **CORS** | 白名单配置来源 |
| **Cascade 删除** | 外键级联防止孤立数据 |
| **软删除** | `deleted_at` 字段标记，不物理删除 |
| **SQL 注入防护** | SQLAlchemy ORM 参数化查询 |

### 13.3 API 安全

| 措施 | 实现 |
|------|------|
| **速率限制** | slowapi 120 次/分钟 |
| **输入验证** | Pydantic 模型严格校验 |
| **错误信息** | 不泄漏堆栈细节 |
| **UUID 验证** | 路径参数 UUID 格式校验 |

### 13.4 异常处理层次

```
AppException (基类)
├── NotFoundException (404)
├── ValidationException (422)
├── AuthenticationException (401)
├── PermissionDeniedException (403)
├── ConflictException (409)
├── InsufficientStockException (400)
└── ServiceUnavailableException (503)
```

所有异常统一通过 `register_error_handlers` 注册的处理器转换为 `{ "detail": "...", "error_code": "..." }` JSON 响应。

---

## 14. 数据模型总览

### 14.1 ER 关系概要

```
User (1) ──── (N) Order (N) ──── (N) OrderPassenger
User (1) ──── (N) Review (N) ──── (1) Tour
User (1) ──── (N) Wishlist (N) ──── (1) Tour
User (1) ──── (N) AttractionWishlist (N) ──── (1) Attraction

Destination (1) ──── (N) Tour (通过 destination_ids 数组关联)
Destination (1) ──── (N) Attraction (1) ──── (N) AttractionTicket

Tour (1) ──── (N) TourTranslation
Tour (1) ──── (N) TourDate
Tour (1) ──── (N) TourImage
Tour (1) ──── (N) Review

Destination (1) ──── (N) DestinationTranslation
Attraction (1) ──── (N) AttractionTranslation
```

### 14.2 核心模型字段清单

#### User (users)
| 字段 | 类型 | 约束 |
|------|------|------|
| id | UUID | PK |
| email | String(255) | UNIQUE, NOT NULL, INDEX |
| name | String(100) | NOT NULL |
| hashed_password | String(255) | NULLABLE |
| avatar_url | String(500) | NULLABLE |
| google_id | String(255) | UNIQUE, NULLABLE |
| is_active | Boolean | DEFAULT true |
| is_admin | Boolean | DEFAULT false |
| locale | String(10) | DEFAULT 'en' |
| created_at / updated_at | DateTime(tz) | 自动 |

#### Tour (tours)
| 字段 | 类型 | 约束 |
|------|------|------|
| id | UUID | PK |
| slug | String(200) | INDEX |
| status | String(20) | DEFAULT 'draft' |
| type | String(30) | DEFAULT 'group_tour' |
| duration_days | SmallInteger | NOT NULL |
| duration_nights | SmallInteger | DEFAULT 0 |
| max_pax / min_pax | SmallInteger | NULLABLE / DEFAULT 1 |
| start_price | Float | DEFAULT 0 |
| currency | String(3) | DEFAULT 'USD' |
| difficulty | String(20) | DEFAULT 'easy' |
| highlights / includes / excludes | ARRAY(Text) | PG 数组 |
| destination_ids | ARRAY(UUID) | PG 数组 |
| avg_rating | Float | DEFAULT 0 |
| review_count | Integer | DEFAULT 0 |
| deleted_at | DateTime(tz) | NULLABLE (软删除) |

#### Order (orders)
| 字段 | 类型 | 约束 |
|------|------|------|
| id | UUID | PK |
| order_no | String(30) | UNIQUE, NOT NULL, INDEX |
| user_id | UUID | FK → users.id, NULLABLE |
| tour_id | UUID | FK → tours.id, NULLABLE |
| tour_date_id | UUID | FK → tour_dates.id, NULLABLE |
| attraction_id | UUID | FK → attractions.id, NULLABLE |
| attraction_ticket_id | UUID | FK → attraction_tickets.id, NULLABLE |
| status | String(30) | DEFAULT 'pending' |
| pax_count | SmallInteger | NOT NULL |
| subtotal / discount / tax / total | Float | — |
| currency | String(3) | DEFAULT 'USD' |
| contact_name / contact_email / contact_phone | 各类 | NULLABLE |
| special_requests | Text | NULLABLE |
| stripe_session_id | String(255) | NULLABLE |
| payment_status | String(30) | DEFAULT 'pending' |

#### Review (reviews)
| 字段 | 类型 | 约束 |
|------|------|------|
| id | UUID | PK |
| tour_id | UUID | FK, NOT NULL, INDEX |
| user_id | UUID | FK, NOT NULL |
| rating | SmallInteger | 1-5 |
| title | String(200) | NULLABLE |
| comment | Text | NULLABLE |
| status | String(20) | DEFAULT 'pending' |

完整字段清单详见 [数据模型定义文件](src/backend/app/models/)。

### 14.3 唯一约束清单

| 表 | 约束名 | 字段 |
|----|--------|------|
| users | uq_users_email | email |
| users | uq_users_google_id | google_id |
| destinations | uq_destinations_slug | slug |
| attractions | uq_attractions_slug | slug |
| attraction_tickets | uq_attraction_ticket_type | (attraction_id, ticket_type) |
| orders | uq_orders_order_no | order_no |
| wishlists | uq_user_tour_wishlist | (user_id, tour_id) |
| attraction_wishlists | uq_user_attraction_wishlist | (user_id, attraction_id) |

---

## 15. API 接口完整列表

### 15.1 公开接口（无需认证）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查（版本、ES 状态、Stripe/OAuth 配置） |
| POST | `/api/v1/auth/register` | 用户注册 |
| POST | `/api/v1/auth/login` | 用户登录 |
| POST | `/api/v1/auth/google` | Google OAuth 登录 |
| POST | `/api/v1/auth/google/dev` | 开发环境模拟 Google 登录 |
| GET | `/api/v1/tours` | 旅游产品列表（分页、按难度筛选） |
| GET | `/api/v1/tours/{slug_or_id}` | 旅游产品详情 |
| GET | `/api/v1/tours/{tour_id}/dates` | 旅游产品可用日期 |
| GET | `/api/v1/destinations` | 目的地列表 |
| GET | `/api/v1/destinations/{slug}` | 目的地详情 |
| GET | `/api/v1/destinations/{slug}/tours` | 目的地下的旅游产品 |
| GET | `/api/v1/destinations/{slug}/attractions` | 目的地下的景点列表 |
| GET | `/api/v1/reviews/tour/{tour_id}` | 旅游产品评价（分页，含平均评分） |
| GET | `/api/v1/search` | 全文搜索（含筛选、排序、聚合） |
| POST | `/api/v1/payments/create-intent` | 创建 Stripe Checkout Session |
| POST | `/api/v1/payments/stripe-webhook` | Stripe Webhook 回调 |

### 15.2 用户接口（需 JWT 认证）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/auth/me` | 获取当前用户信息 |
| POST | `/api/v1/orders` | 创建订单 |
| GET | `/api/v1/orders` | 获取用户订单列表 |
| GET | `/api/v1/orders/{order_id}` | 获取订单详情 |
| POST | `/api/v1/reviews` | 创建评价 |
| GET | `/api/v1/users/me/profile` | 获取个人资料 |
| PATCH | `/api/v1/users/me/profile` | 更新个人资料 |
| GET | `/api/v1/wishlist` | 旅游产品收藏列表 |
| POST | `/api/v1/wishlist/{tour_id}` | 添加旅游产品收藏 |
| DELETE | `/api/v1/wishlist/{tour_id}` | 移除旅游产品收藏 |
| GET | `/api/v1/wishlist/attractions` | 景点收藏列表 |
| POST | `/api/v1/wishlist/attractions/{attraction_id}` | 添加景点收藏 |
| DELETE | `/api/v1/wishlist/attractions/{attraction_id}` | 移除景点收藏 |

### 15.3 管理接口（需管理员 JWT 认证）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/admin/stats` | 仪表盘统计数据 |
| GET | `/api/v1/admin/tours` | 旅游产品管理列表（含草稿） |
| POST | `/api/v1/admin/tours` | 创建旅游产品 |
| GET | `/api/v1/admin/tours/{tour_id}` | 获取完整产品详情（含翻译、图片、团期） |
| PATCH | `/api/v1/admin/tours/{tour_id}` | 部分更新产品 |
| PUT | `/api/v1/admin/tours/{tour_id}` | 完整替换更新产品 |
| DELETE | `/api/v1/admin/tours/{tour_id}` | 软删除产品 |
| POST | `/api/v1/admin/upload` | 上传图片/视频（≤60MB） |
| DELETE | `/api/v1/admin/tours/{tour_id}/images/{image_id}` | 删除图片/视频 |
| GET | `/api/v1/admin/tours/{tour_id}/dates` | 获取所有团期 |
| POST | `/api/v1/admin/tours/{tour_id}/dates` | 新增团期 |
| PATCH | `/api/v1/admin/tours/{tour_id}/dates/{date_id}` | 更新团期 |
| DELETE | `/api/v1/admin/tours/{tour_id}/dates/{date_id}` | 删除团期 |
| GET | `/api/v1/admin/orders` | 订单管理列表 |
| PATCH | `/api/v1/admin/orders/{order_id}/status` | 更新订单状态 |
| GET | `/api/v1/admin/users` | 用户管理列表 |
| GET | `/api/v1/admin/reviews` | 评价管理列表 |
| PATCH | `/api/v1/admin/reviews/{review_id}` | 审核评价（批准/拒绝） |
| POST | `/api/v1/admin/reindex` | 重建搜索索引 |

> **总计**: 36 个唯一 API 端点（不含 /health）
> - 公开: 16 个
> - 需用户认证: 13 个
> - 需管理员认证: 19 个
> - 其中支付: 2 个

### 15.4 API 统一响应格式

所有 API 响应遵循统一格式：

```json
// 成功响应
{
  "code": 200,
  "data": { ... },
  "message": "ok"
}

// 分页响应
{
  "code": 200,
  "data": [ ... ],
  "message": "ok",
  "meta": {
    "total": 100,
    "page": 1,
    "page_size": 12
  }
}

// 错误响应
{
  "detail": "Resource not found",
  "error_code": "NOT_FOUND"
}
```

---

## 16. 前端路由与页面映射

### 16.1 完整路由表

| 路由 | 页面文件 | 类型 | 功能 | 认证 |
|------|----------|------|------|------|
| `/` | `app/layout.tsx` | SSR | 根布局 | — |
| `/:locale` | `app/[locale]/layout.tsx` | SSR | 全局布局（Header/Footer/i18n） | — |
| `/:locale` | `app/[locale]/page.tsx` | SSR | 首页 | — |
| `/:locale/tours` | `app/[locale]/tours/page.tsx` | SSR | 旅游列表 | — |
| `/:locale/tours/[slug]` | `app/[locale]/tours/[slug]/page.tsx` | SSR+C | 旅游详情 | — |
| `/:locale/destinations` | `app/[locale]/destinations/page.tsx` | SSR | 目的地列表 | — |
| `/:locale/destinations/[slug]` | `app/[locale]/destinations/[slug]/page.tsx` | SSR | 目的地详情 | — |
| `/:locale/search` | `app/[locale]/search/page.tsx` | CSR | 实时搜索 | — |
| `/:locale/auth` | `app/[locale]/auth/page.tsx` | CSR | 登录/注册 | — |
| `/:locale/checkout` | `app/[locale]/checkout/page.tsx` | CSR | 结账（旅游/门票） | 需登录 |
| `/:locale/checkout/success` | `app/[locale]/checkout/success/page.tsx` | CSR | 支付成功确认 | — |
| `/:locale/user/orders` | `app/[locale]/user/orders/page.tsx` | CSR | 我的订单 | 需登录 |
| `/:locale/user/profile` | `app/[locale]/user/profile/page.tsx` | CSR | 个人资料 | 需登录 |
| `/:locale/user/wishlist` | `app/[locale]/user/wishlist/page.tsx` | CSR | 我的收藏 | 需登录 |
| `/:locale/admin` | `app/[locale]/admin/page.tsx` | CSR | 管理仪表盘 | 需管理员 |
| `/:locale/admin/tours` | `app/[locale]/admin/tours/page.tsx` | CSR | 管理旅游列表 | 需管理员 |
| `/:locale/admin/tours/create` | `app/[locale]/admin/tours/create/page.tsx` | CSR | 创建旅游 | 需管理员 |
| `/:locale/admin/tours/[id]/edit` | `app/[locale]/admin/tours/[id]/edit/page.tsx` | CSR | 编辑旅游 | 需管理员 |
| `/:locale/admin/tours/[id]/dates` | `app/[locale]/admin/tours/[id]/dates/page.tsx` | CSR | 管理团期 | 需管理员 |
| `/:locale/admin/orders` | `app/[locale]/admin/orders/page.tsx` | CSR | 管理订单 | 需管理员 |
| `/:locale/admin/reviews` | `app/[locale]/admin/reviews/page.tsx` | CSR | 评价审核 | 需管理员 |
| `/:locale/not-found` | `app/[locale]/not-found.tsx` | CSR | 404 页面 | — |

> SSR = 服务端渲染, CSR = 客户端渲染, SSR+C = 服务端 + 客户端混合

### 16.2 核心组件树

```
Layout (app/[locale]/layout.tsx)
├── Header
│   ├── Logo (Echo Tours)
│   ├── NavLinks (首页 / 旅游 / 目的地 / 搜索)
│   ├── LanguageSwitcher (en / zh / es)
│   └── AuthSection (登录/注册 或 用户菜单)
├── <page content>
└── Footer
    ├── About / Contact / FAQ
    ├── Social Links
    └── Newsletter Subscription

TourCard (复用组件)
├── Image (next/image)
├── RatingBadge
├── DifficultyBadge
├── PriceDisplay
└── WishlistButton

TourDetailClient
├── Breadcrumb
├── ImageGallery
├── TourInfo (rating / meta / description)
├── HighlightsList
├── ItineraryTimeline
├── IncludesExcludesGrid
├── ReviewsSection (ReviewCard + ReviewForm)
├── StickyBookingSidebar
│   ├── DateSelector
│   ├── PaxCounter
│   ├── PriceCalculator
│   └── BookNowButton
└── WishlistButton
```

### 16.3 骨架屏组件清单

| 组件 | 对应页面 |
|------|----------|
| HomeHeroSkeleton / HomeFeaturedSkeleton / ... | 首页 |
| TourCardSkeleton / TourGridSkeleton | 旅游列表、搜索结果 |
| TourDetailSkeleton | 旅游详情 |
| DestinationCardSkeleton / DestinationGridSkeleton | 目的地列表 |
| DestinationDetailSkeleton | 目的地详情 |
| SearchPageSkeleton | 搜索页 |
| TableSkeleton | 管理表格页面 |
| AdminDashboardSkeleton | 管理仪表盘 |

---

## 17. 技术架构

### 17.1 系统架构图

```
┌──────────────────────────────────────────────┐
│                CDN / Nginx                    │
└──────────┬───────────────────────┬────────────┘
           │                       │
    ┌──────▼──────┐        ┌──────▼──────┐
    │  Next.js 15  │        │  FastAPI    │
    │  Frontend    │◄──────►│  Backend    │
    │  (3000)      │  API   │  (8000)     │
    └──────────────┘        └──────┬──────┘
                                   │
    ┌──────────────────────────────┼──────────────────┐
    │                    ┌────────▼────────┐          │
    │                    │   PostgreSQL    │          │
    │                    │      16         │          │
    │                    └─────────────────┘          │
    │                                                  │
    │  ┌─────────────┐  ┌─────────────┐               │
    │  │   Redis 7   │  │Elasticsearch│               │
    │  │  Cache/BR   │  │     8       │               │
    │  └─────────────┘  └─────────────┘               │
    │                                                  │
    │  ┌─────────────┐  ┌─────────────┐               │
    │  │  Celery     │  │  Celery     │               │
    │  │  Worker     │  │  Beat       │               │
    │  └─────────────┘  └─────────────┘               │
    └──────────────────────────────────────────────────┘
```

### 17.2 请求流程

```
浏览器 → Next.js (SSR) → FastAPI → Service Layer → CRUD → DB
                           ↑               ↓
                        Redis Cache    Elasticsearch
                           ↑               ↓
                      Cache Decorator  Search Index
```

### 17.3 依赖清单

#### 前端 (Next.js 15)
- next, react, react-dom — 核心框架
- next-intl — 国际化
- zustand — 状态管理
- tailwindcss — CSS 框架
- shadcn/ui (radix-ui) — UI 组件
- lucide-react — 图标库
- stripe-js — 支付前端 SDK
- sonner — 通知组件
- react-hook-form + zod — 表单验证

#### 后端 (Python 3.12+)
- fastapi, uvicorn — Web 框架
- sqlalchemy[asyncio], asyncpg, alembic — 数据库 ORM + 迁移
- pydantic, pydantic-settings — 数据验证
- python-jose, passlib, bcrypt — 认证安全
- redis[hiredis] — 缓存
- elasticsearch[async] — 搜索引擎
- stripe — 支付网关
- celery[redis] — 异步任务
- sendgrid — 邮件服务
- slowapi — 速率限制
- httpx — HTTP 客户端
- tenacity — 重试逻辑

---

## 18. 部署与运维

### 18.1 容器化部署

- **Docker**: 微服务容器化
- **编排**: Docker Compose（本地开发）/ 阿里云 ECS（生产）
- **反向代理**: Nginx

### 18.2 CI/CD 流水线 (GitHub Actions)

| 阶段 | 操作 |
|------|------|
| **触发** | push / 合并到 main / develop |
| **测试** | pytest 单元测试 + 集成测试 |
| **构建** | Docker 镜像构建 |
| **部署** | 阿里云 ECS 自动部署 |

### 18.3 环境变量配置

通过 Pydantic `Settings` 加载的配置：

| 配置项 | 说明 |
|--------|------|
| `database_url` | PostgreSQL 异步连接串 |
| `redis_url` | Redis 连接串 |
| `elasticsearch_url` | ES 连接串 |
| `secret_key` | JWT 签名密钥 |
| `stripe_secret_key / stripe_public_key` | Stripe API 密钥 |
| `stripe_webhook_secret` | Stripe Webhook 签名密钥 |
| `sendgrid_api_key` | SendGrid 邮件 API 密钥 |
| `google_client_id / google_client_secret` | Google OAuth 凭证 |
| `cors_origins` | CORS 白名单 |
| `frontend_url` | 前端 URL（重定向用） |
| `static_dir` | 静态文件目录 |
| `debug / environment` | 运行环境标识 |

### 18.4 种子数据

启动时通过 `scripts/seed_data.py` 填充示例数据：

- **3 个目的地**: 北京、南京、西安（中英双语）
- **10 个旅游产品**: 覆盖北京主要景点，含中英双语翻译、行程、图片、价格日历
- **4 个用户**: 1 个管理员 + 3 个普通用户
- **12 条评价**: 跨多个旅游产品的混合语言评价
- **45 个景点**: 每个城市 15 个景点（中英双语）

默认测试账号：
- 管理员: admin@echotours.com / Admin123!
- 用户: 张三 / Test1234!, 李四 / Test1234!, John Smith / Test1234!

---

## 19. 非功能性需求

### 19.1 性能指标

| 指标 | 目标 |
|------|------|
| 页面加载时间 | 首页 < 1.5s（75 分位） |
| API 响应时间 | < 200ms（75 分位） |
| 搜索响应时间 | < 300ms |
| 并发用户数 | 支持 1000+ 并发 |
| 数据库连接池 | pool_size=10, max_overflow=20 |

### 19.2 可用性

| 指标 | 目标 |
|------|------|
| API 可用性 | 99.9% |
| 计划内停机 | 每月不超过 1 小时 |
| 错误率 | < 0.1% 的请求返回 5xx |

### 19.3 安全性

- 密码使用 bcrypt 加密存储
- JWT 24 小时过期
- API 速率限制 120 次/分钟
- CORS 白名单限制
- 输入严格校验（Pydantic）
- 统一错误处理，不泄漏内部细节

### 19.4 可维护性

- 类型注解全覆盖（Python Type Hints + TypeScript）
- 统一的 API 响应格式 `{code, data, message}`
- 统一的异常处理体系
- Docstring 注释规范
- Conventional Commits 提交规范
- ESLint + Prettier + Black 代码格式化

### 19.5 可扩展性

- 模块化单体架构，支持逐步演进为微服务
- 服务层与 API 层分离，业务逻辑可独立测试
- 缓存层可插拔设计
- 翻译表设计支持未来新增语言
- 订单模型支持扩展业务线（旅游 + 门票双模式）

---

## 20. 附录

### 20.1 术语表

| 术语 | 英文 | 说明 |
|------|------|------|
| 旅游产品 | Tour | 打包的旅游行程产品 |
| 景点 | Attraction | 目的地下的具体景点/景区 |
| 目的地 | Destination | 城市或旅游区域 |
| 团期 | TourDate | 旅游产品的具体出发日期 |
| 景点门票 | AttractionTicket | 景点的门票类型（标准/VIP/儿童） |
| 订单 | Order | 用户提交的预订订单 |
| 评价 | Review | 用户对旅游产品的评价 |
| 收藏 | Wishlist | 用户的收藏列表 |
| 翻译 | Translation | 多语言内容翻译记录 |

### 20.2 参考文档

| 文档 | 路径 |
|------|------|
| 架构设计文档 | `/docs/architecture-design.md` |
| 实施计划 | `/docs/implementation-plan.md` |
| 使用手册 | `/docs/使用手册.md` |
| 测试用例 | `/docs/测试用例-全业务流程.md` |
| 部署运维文档 | `/docs/部署和运维文档.md` |
| 市场分析报告 | `/docs/market-analysis-report.md` |
| 测试覆盖计划 | `/docs/全功能自动化测试覆盖计划.md` |

### 20.3 版本演进

| 版本 | 主要功能 | 状态 |
|------|----------|------|
| v1.0 | 基础架构、旅游产品浏览、用户认证 | ✅ 已上线 |
| v2.0 | 目的地模块、Stripe 支付 | ✅ 已上线 |
| v2.1 | Elasticsearch 全文搜索 | ✅ 已上线 |
| v2.2 | 用户评论系统 + 管理员审核 | ✅ 已上线 |
| v2.3 | 多语言国际化（en/zh/es） | ✅ 已上线 |
| v2.4 | 景点模块 + 景点收藏 | ✅ 已上线 |
| v2.5 | 景点门票购买 + 直达下单 | ✅ 已上线 |
| v2.6 | 管理员工台完善（日期管理、评价审核） | ✅ 已上线 |
| v2.7 | 全量回归测试 + 稳定性优化 | ✅ 已发布就绪 |

---

> **文档结束** — Echo Tours v2.7.0  
> 本文档覆盖了平台的全部 36 个 API 端点、21 个前端页面、15 个数据库模型、6 个服务模块、2 条业务线（旅游 + 景点门票）、3 种语言支持（en/zh/es）、2 种角色（用户 + 管理员）的完整产品功能。
