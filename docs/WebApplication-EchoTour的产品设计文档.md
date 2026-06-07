# Echo Tours — 旅游平台产品设计文档 (PRD)

> **版本**: v4.1  
> **最后更新**: 2026-06-07  
> **文档状态**: ✅ 已定稿  
> **产品名称**: Echo Tours（回声旅行）  
> **产品定位**: 面向全球旅行者的多语言旅游预订平台

---

## 目录

1. [产品概述](#1-产品概述)
2. [用户角色与场景](#2-用户角色与场景)
3. [功能总览](#3-功能总览)
4. [公共功能（访客）](#4-公共功能访客)
5. [用户功能（已登录）](#5-用户功能已登录)
6. [管理功能（管理员）](#6-管理功能管理员)
7. [订单与支付系统](#7-订单与支付系统)
8. [搜索系统](#8-搜索系统)
9. [内容管理系统（CMS）](#9-内容管理系统cms)
10. [国际化与多语言](#10-国际化与多语言)
11. [技术架构](#11-技术架构)
12. [数据模型总览](#12-数据模型总览)
13. [API 端点完整列表](#13-api-端点完整列表)
14. [前端路由与组件](#14-前端路由与组件)
15. [部署与运维](#15-部署与运维)
16. [非功能性需求](#16-非功能性需求)
17. [附录](#17-附录)

---

## 1. 产品概述

### 1.1 产品愿景

Echo Tours 是一个面向全球旅行者的全栈旅游预订平台。用户可以从目的地探索开始，浏览旅游产品和景点，通过在线预订支付完成整个旅程规划。平台同时支持自定制旅程功能，让游客自由组合多段行程、目的地和基础服务。

产品覆盖两条核心业务线：

| 业务线 | 说明 | 目标用户 |
|--------|------|----------|
| **标准化旅游产品** | 固定行程的跟团游/私家团，含价格日历与团期管理 | 追求便捷的跟团游客 |
| **自定制旅程** | 自由组合多段行程、目的地、景点、旅游产品和基础服务 | 追求个性化的自由行游客 |
| **景点门票** | 独立于旅游产品的景点门票购买 | 自助游散客 |

### 1.2 核心价值主张

| 价值 | 说明 |
|------|------|
| **一站式预订** | 从浏览、收藏、下单到支付，全流程在线完成 |
| **多语言支持** | 前端 UI + 后端业务内容三层国际化（英/中/西） |
| **灵活预订** | 支持标准化旅游产品、自定制旅程、景点门票三种预订模式 |
| **安全支付** | 集成 Stripe 支付网关，支持开发沙箱模式 |
| **智能搜索** | Elasticsearch 全文搜索，多维度筛选与排序 |
| **管理后台** | 完整的后台管理系统，覆盖产品/订单/评价/目的地/景点/基础服务 |

### 1.3 产品技术栈

| 层次 | 技术 | 备注 |
|------|------|------|
| **前端框架** | Next.js 15 (React 19) | SSR + CSR 混合渲染 |
| **前端语言** | TypeScript 5.7 | 全类型安全 |
| **样式方案** | Tailwind CSS 4 + Shadcn/ui | 原子化 CSS |
| **后端框架** | FastAPI (Python 3.12+) | 异步高性能 |
| **数据库** | PostgreSQL 16 | 关系型主存储 |
| **ORM** | SQLAlchemy 2.0 (async) | 异步 ORM + Alembic 迁移 |
| **缓存** | Redis 7 | 数据缓存 + Celery 消息代理 |
| **搜索引擎** | Elasticsearch 8 | 全文搜索 |
| **支付网关** | Stripe | Checkout Sessions + Webhook |
| **任务队列** | Celery 5.4 | 异步/定时任务 |
| **邮件服务** | SendGrid | 模板邮件（支持 Mock 模式） |
| **容器化** | Docker + Docker Compose | 微服务编排 |
| **CI/CD** | GitHub Actions | 自动化测试与部署 |
| **反向代理** | Nginx | 生产环境前端代理 |

### 1.4 产品规模统计

| 类别 | 数量 |
|------|------|
| **后端代码文件** | ~85 个 |
| **前端代码文件** | ~48 个 |
| **Docker 服务数** | 10 个（含 Nginx、2×Celery、MailHog） |
| **API 端点总数** | 70+ 个 |
| **前端页面路由** | >25 个 |
| **前端组件** | ~35 个 |
| **后端测试数** | 467 项通过（含核心/CRUD/API/搜索/缓存/任务/逆向/边界/回归/安全/并发） |
| **E2E 测试数** | 20 个 Playwright spec 文件（核心功能/用户中心/管理后台/多语言/异常/回归/后置清理） |
| **支持语言** | 3 种（en / zh / es），400+ 翻译键 |
| **种子数据** | 3 目的地 / 30 产品（北京28+南京1+西安1）/ 45 景点 / 9 基础服务 / 4 用户 / 12 评论 / 202 团期 / 60 ES 文档 |

---

## 2. 用户角色与场景

### 2.1 用户角色定义

| 角色 | 权限级别 | 访问范围 | 认证要求 |
|------|----------|----------|----------|
| **访客 (Guest)** | 公开 | 浏览所有公开内容（产品/目的地/景点/搜索） | 无 |
| **注册用户 (User)** | 基本 | 预订、收藏、评价、订单管理、个人资料 | JWT 认证 |
| **管理员 (Admin)** | 最高 | 管理后台所有功能 + 系统维护 | JWT + `is_admin` 检查 |

### 2.2 用户场景与旅程

#### 场景 A：跟团游旅客

```
发现 → 浏览旅游列表 → 查看详情（行程/日期/评价）→ 收藏 → 下单 → 支付 → 出行 → 评价
```

典型用户流程：
1. 首页浏览推荐产品 → 旅游列表（按目的地筛选）
2. 查看产品详情（行程亮点、每日安排、价格日历）
3. 收藏感兴趣的产品（方便后续查找）
4. 下单（选择出发日期、人数）→ Stripe 支付
5. 在订单中心查看订单状态
6. 出行后在详情页提交评价

#### 场景 B：自由行游客

```
探索目的地 → 查看景点 → 自定制旅程 → 提交报价请求 → 确认支付
```

典型用户流程：
1. 浏览目的地列表 → 进入目的地详情（景点+产品）
2. 查看景点详情（评分、图片轮播、门票价格）
3. 收藏景点或直达下单门票
4. 使用自定制旅程功能：添加多段行程（目的地+景点+旅游产品）
5. 选择基础服务（接送机/导游/车辆/住宿/餐饮）
6. 使用预设导语快速生成定制请求
7. 提交报价请求 → 等待管理员确认
8. 收到报价后确认并支付

#### 场景 C：平台运营者（管理员）

```
仪表盘监控 → 产品管理 → 订单处理 → 评价审核 → 内容管理
```

典型管理流程：
1. 仪表盘查看统计数据（产品数/订单数/用户数/收入）
2. 创建/编辑/删除旅游产品（多语言同步）
3. 管理出发团期（增删改查）
4. 处理用户订单（状态更新）
5. 审核用户评价（批准/拒绝）
6. 管理目的地/景点/基础服务内容
7. 处理自定制旅程报价请求

---

## 3. 功能总览

```
Echo Tours 功能地图
├── 🌐 公共功能（访客可访问）
│   ├── 首页（推荐产品 + 热门目的地 + 咨询表单浮窗）
│   ├── 旅游产品列表（分页 + 目的地/主题/难度筛选）
│   ├── 旅游产品详情（行程/日期/评价/收藏/主题标签）
│   ├── 目的地列表 + 详情（景点 + 产品）
│   ├── 景点浏览 + 门票查询
│   ├── 景点详情弹窗（媒体轮播 + 介绍）
│   ├── 自定制旅程（多段行程 + 基础服务 + 导语）
│   ├── 全文搜索（ES + 筛选 + 排序）
│   ├── 24/7 电话展示（全局 Header + Footer）
│   ├── 在线咨询表单（浮动按钮 + 弹窗）
│   └── 用户认证（邮箱登录/注册 + Google SSO）
│
├── 👤 用户功能（需登录）
│   ├── 旅游产品收藏（心愿单）
│   ├── 景点收藏
│   ├── 下单（旅游产品 / 景点门票）
│   ├── Stripe 支付（含沙箱模式）
│   ├── 订单历史（状态跟踪）
│   ├── 旅游产品评价
│   ├── 个人资料管理
│   └── 自定制旅程请求状态查看
│
└── 🔧 管理功能（需管理员）
    ├── 仪表盘（关键指标统计）
    ├── 旅游产品管理（列表/创建/编辑/删除 + 多语言）
    │   ├── 产品基本字段 + 序列号
    │   ├── 多语言编辑（三语标签页切换）
    │   ├── 出发团期管理（CRUD）
    │   └── 图片/视频上传管理
    ├── 目的地管理（CRUD + 多语言）
    ├── 景点管理（编辑 + 媒体管理）
    ├── 基础服务管理（CRUD + 多语言）
    ├── 自定制旅程管理（查看 + 报价确认）
    ├── 订单管理（状态更新）
    ├── 用户管理（列表浏览）
    ├── 评价审核（批准/拒绝）
    ├── 搜索索引管理（手动重建）
    └── 咨询管理（列表查看 / 状态更新 / 备注）
```

---

## 4. 公共功能（访客）

### 4.1 首页 (Homepage)

**路由**: `/:locale/`  
**页面类型**: SSR  
**缓存**: ISR revalidate=300s

#### 功能点

| 区域 | 内容 | 数据来源 |
|------|------|----------|
| **Hero 横幅** | 渐变背景 + 主标题/副标题 + 2 个 CTA 按钮 | 静态翻译文案 |
| **精选旅游** | 评分最高的 6 个产品，3 列 TourCard 网格 | `GET /api/v1/tours?sort=rating&page_size=6` |
| **为什么选择我们** | 4 个特色卡片（专家导游/定制旅游/最优价格/支持） | 静态翻译文案 |
| **热门目的地** | 3 个静态目的地卡片（北京/南京/西安） | 硬编码翻译键 |
| **行动号召 CTA** | 全宽主色区域 + CTA 按钮 | 静态翻译文案 |
| **咨询表单浮窗** | 全站右下角浮动按钮（全局所有页面均可见），展开后为弹窗表单（姓名/邮箱/电话/目的地/人数/需求描述），含 24/7 电话展示 | `InquiryForm` 组件（Client Component，挂载于全局 Layout） |

#### 异常状态

- **加载中**: 完整骨架屏（Hero + Featured + Features + DestinationsPreview + CTA）
- **数据为空**: 精选旅游区域静默隐藏
- **网络错误**: 数据获取失败时该区域静默隐藏
- **表单错误**: 提交失败时弹窗内显示错误提示
- **提交成功**: 显示成功动画 + 24h 内联系提示 + 可重新提交

### 4.2 旅游产品列表 (Tours List)

**路由**: `/:locale/tours`  
**页面类型**: SSR  
**缓存**: ISR revalidate=120s

#### 功能点

| 功能 | 详情 |
|------|------|
| **列表展示** | 分页网格展示，每页 12 个 TourCard（含图片/评分/名称/价格/难度） |
| **按目的地筛选** | URL 查询参数 `?destination=slug` |
| **结果计数** | 顶部显示匹配产品数量 |
| **收藏按钮** | 每张卡片右上角 WishlistButton |

#### 异常状态

- **加载中**: 6 个 TourCardSkeleton 骨架占位
- **数据为空**: "没有找到旅游产品" 空状态提示
- **错误**: 静默失败（ISR 构建时获取数据）

### 4.3 旅游产品详情 (Tour Detail)

**路由**: `/:locale/tours/[slug]`  
**页面类型**: SSR + 客户端交互 (TourDetailClient)  
**缓存**: SSR revalidate=300s

#### 功能点

| 区域 | 详情 |
|------|------|
| **面包屑导航** | 旅游列表 > 当前产品名称 |
| **图片画廊** | 可切换大图展示（图片/视频混合），指示器点导航 |
| **评分徽章** | 星级 + 平均评分 + 评价数量 |
| **元信息** | 难度徽章、产品类型、名称、副标题 |
| **基本信息** | 天数/晚数、最大人数、目的地名称 |
| **产品描述** | 多语言概述文本 |
| **行程亮点** | 带绿色复选标记的要点列表（各语言独立） |
| **每日行程** | 编号卡片，含日标题、描述、餐食徽章 |
| **包含/不包含** | 两个并列列表（勾选/叉选） |
| **收藏按钮** | WishlistButton 一键收藏切换 |
| **评价区域** | 评价列表（分页）+ 已登录用户可提交评价表单 |
| **固定侧边栏** | 日期选择器（可用日期/售罄禁用）、人数计数器、价格计算、立即预订按钮 |

#### 日期选择器逻辑

- 仅显示 `status="available"` 且 `start_date >= today` 的团期
- 已售罄日期显示 "已售罄" 标签并禁用选择
- 人数计数器范围 1 ~ `min(max_pax, availability)`
- 价格实时计算：`price_per_pax × pax_count`

#### 异常状态

- **加载中**: TourDetailSkeleton 完整骨架
- **产品不存在**: `notFound()` → 自定义 404
- **无可用日期**: "暂无可用日期" 提示
- **无效 slug**: 404 页面

### 4.4 目的地列表 (Destinations)

**路由**: `/:locale/destinations`  
**页面类型**: SSR

#### 功能点

| 功能 | 详情 |
|------|------|
| **目的地展示** | 所有活跃目的地，每个含名称/描述/旅游产品数/景点数 |
| **关联景点** | 每个目的地展示前 5 个景点（图片/评分/收藏/直达预订按钮） |
| **收藏景点** | 景点卡片上的 WishlistButton |
| **查看全部** | 链接到目的地详情页 |

#### 异常状态

- **加载中**: DestinationCardSkeleton 骨架占位
- **数据为空**: MapPin 图标 + "暂无目的地"

### 4.5 目的地详情 (Destination Detail)

**路由**: `/:locale/destinations/[slug]`  
**页面类型**: SSR

#### 功能点

| 区域 | 详情 |
|------|------|
| **头部信息** | 返回链接、目的地名称、描述、旅游产品数量 |
| **景点网格** | 景点卡片（图片/名称/评分/收藏/直达预订），悬停显示 "立即预订" |
| **景点直达下单** | 点击 "立即预订" 携带参数跳转结账页（attraction_id/ticket_id/price） |
| **旅游产品网格** | TourCard 展示该目的地下的旅游产品 |

#### 异常状态

- **加载中**: DestinationDetailSkeleton
- **目的地不存在**: `notFound()` → 404
- **无景点/旅游**: "暂无" 提示

### 4.6 景点浏览 (Attractions)

景点数据嵌套在目的地模块中，核心端点：
- `GET /api/v1/destinations/{slug}/attractions` — 按 sort_order 排序

#### 景点卡片

每张景点卡片包含：
- 景点图片（本地 SVG 占位图，后台可替换）
- 景点名称（多语言）
- 评分（1-5 星）
- 起价
- 快捷收藏按钮（WishlistButton）
- 快捷预订按钮（直达结账）

#### 景点详情弹窗 (AttractionInfoModal)

**触发**: 点击景点卡片上的 "More Information" 按钮  
**组件**: `AttractionInfoModal`

| 区域 | 内容 |
|------|------|
| **媒体轮播** | 景点图片轮播（最多 8 张媒体），缩略图导航 |
| **基本信息** | 名称、评分（星级）、描述介绍 |
| **门票信息** | 门票类型列表（含价格、库存、状态） |
| **直达操作** | 门票选择 + 购买按钮直达结账页 |

### 4.7 自定制旅程 (Custom Tour)

**路由**: `/:locale/custom-tour`  
**页面类型**: CSR  
**API**: `POST /api/v1/custom-tours/quote` / `POST /api/v1/custom-tours/requests`

自定制旅程允许用户自由组合多段行程，生成个性化旅行方案。是整个平台差异化的核心能力。

#### 核心概念

| 概念 | 说明 |
|------|------|
| **定制请求 (CustomTourRequest)** | 一次完整的定制旅程申请，包含多段行程 |
| **行程段 (CustomTourSegment)** | 一个目的地+时间段内的游览安排 |
| **系统目的地 (segment.destination_id)** | 关联平台已有目的地（北京/南京/西安） |
| **自定义目的地 (segment.custom_destination)** | 用户自由输入的目的地名称（不限于平台已有） |
| **旅游产品 (CustomTourSegmentTour)** | 行程段内选择的标准化旅游产品 |
| **基础服务 (CustomTourService)** | 行程段附加的增值服务（接送/导游/住宿/餐饮等） |

#### 功能点

| 模块 | 功能 | 详情 |
|------|------|------|
| **多段行程** | 添加/删除行程段 | 每段独立设置目的地、日期、天数等 |
| **系统目的地** | 从平台已有目的地中选择 | 支持自定义输入目的地名称 |
| **景点选择** | 选择行程段内的游览景点 | 基于目的地加载可选景点列表 |
| **产品选择** | 选择行程段内的旅游产品 | — |
| **基础服务** | 附加增值服务（多选） | 接送机/导游/车辆/住宿/餐饮等 |
| **预设导语** | 快速填写旅行偏好 | 三段预设模板（浪漫/家庭/文化） |
| **报价计算** | 实时估算总价 | 服务费按单位价格计算 |
| **提交请求** | 提交定制请求给管理员 | 管理员确认后回复报价 |

#### 预设导语模板

| 模板 | 标题 | 内容方向 |
|------|------|----------|
| 🌹 浪漫之旅 | "我和伴侣正要计划一次难忘的蜜月旅行..." | 浪漫体验、美食、特色住宿 |
| 👨‍👩‍👧‍👦 家庭出游 | "我们准备带父母和孩子一起出行..." | 轻松节奏、亲子活动、安全舒适 |
| 🎒 冒险探索 | "我想要一次与众不同的深度旅行..." | 独特体验、小众景点、极限运动 |

#### UI 组件结构

```
CustomTourPage
├── SegmentList
│   └── SegmentCard (×N)
│       ├── DestinationPicker（系统目的地 + 自定义输入）
│       ├── DateRangePicker
│       ├── AttractionSelector
│       └── TourSelector
├── BaseServicePanel（全局服务选择）
├── PromptPresets（预设导语）
├── PromptInput（自定义需求描述）
├── PriceSummary（报价概览）
└── SubmitButton
```

#### 异常状态

- **加载中**: 页面级别 Skeleton 加载提示
- **目的地加载失败**: 错误提示 + 重试按钮
- **多段行程支持**: 至少 1 段，最多 10 段
- **提交失败**: 服务器错误提示

### 4.8 全文搜索 (Search)

**路由**: `/:locale/search`  
**页面类型**: CSR  
**API**: `GET /api/v1/search`

详见 [第 8 节 — 搜索系统](#8-搜索系统)

### 4.9 用户认证 (Auth)

**路由**: `/:locale/auth`  
**页面类型**: CSR

#### 功能点

| 功能 | 详情 |
|------|------|
| **邮箱密码登录** | email + password → `POST /api/v1/auth/login` |
| **邮箱密码注册** | name + email + password → `POST /api/v1/auth/register` |
| **Google 一键登录** | Google Identity Services → `POST /api/v1/auth/google` |
| **开发模式登录** | 未配置 Google OAuth 时自动降级 |
| **模式切换** | URL 参数 `?mode=signup` 切换登录/注册 |
| **已登录重定向** | 已认证用户自动跳转首页 |

#### 认证流程

1. 登录/注册成功 → 返回 JWT (`access_token`)
2. Token 存入 `localStorage` 的 `auth_token` 键
3. Zustand Store (`useAuthStore`) 管理认证状态
4. 后续请求自动附加 `Authorization: Bearer {token}` 头
5. 页面加载时 `loadFromStorage()` 恢复认证状态

#### 异常状态

- **表单验证错误**: 红色文字提示
- **认证失败**: 红色错误横幅
- **Google 登录未配置**: 自动降级为 DevGoogleLogin

### 4.10 国际化与多语言切换

- **支持语言**: 英语 (en) / 简体中文 (zh) / 西班牙语 (es)
- **默认语言**: 英语（基于 Accept-Language）
- **URL 模式**: `/:locale/...` 前缀模式
- **切换方式**: Header 中的 Globe 下拉菜单

详见 [第 10 节 — 国际化与多语言](#10-国际化与多语言)

---

## 5. 用户功能（已登录）

### 5.1 旅游产品收藏 (Tour Wishlist)

**路由**: `/:locale/user/wishlist`  
**API**: `GET /api/v1/wishlist` / `POST /api/v1/wishlist/{tour_id}` / `DELETE /api/v1/wishlist/{tour_id}`

#### 功能点

| 功能 | 详情 |
|------|------|
| **添加收藏** | 点击 WishlistButton 心形图标 → POST 添加 |
| **取消收藏** | 再次点击已收藏的心形图标 → DELETE 移除 |
| **收藏列表页** | 展示所有收藏产品（TourCard 渲染） |
| **未登录处理** | 点击收藏按钮时跳转登录页 |
| **UI 反馈** | 红色实心 = 已收藏，灰色空心 = 未收藏，渐变动画 |

#### 异常状态

- **加载中**: TourGridSkeleton (3 卡片)
- **收藏为空**: 心形图标 + "暂无收藏" + "浏览旅游" 按钮
- **未登录**: 跳转登录页

### 5.2 景点收藏 (Attraction Wishlist)

**API**: `GET /api/v1/wishlist/attractions` / `POST /api/v1/wishlist/attractions/{attraction_id}` / `DELETE /api/v1/wishlist/attractions/{attraction_id}`

与旅游产品收藏共用 `WishlistButton` 组件，通过 `itemType="attraction"` 区分业务线。

### 5.3 下单 (Booking)

**路由**: `/:locale/checkout`  
**页面类型**: CSR

#### 三条业务线

| 业务线 | 核心参数 | 库存逻辑 |
|--------|----------|----------|
| **旅游产品预订** | `tour_id` + `tour_date_id` + `pax_count` | 递减团期 `availability` |
| **景点门票购买** | `attraction_id` + `ticket_id` + `pax_count` | 递减门票 `availability` |

#### 结账页面流程

1. 检查用户认证态（未登录 → 跳转 `/auth`）
2. 从 URL 参数读取预订信息：旅游 `?tour=slug&date=id&pax=N` / 景点 `?attraction_id=xxx&ticket_id=xxx`
3. 加载详情展示预订摘要卡片
4. 用户填写联系信息（姓名、邮箱、电话）
5. 点击支付 → `POST /api/v1/orders` 创建订单 → `POST /api/v1/payments/create-intent`
6. 重定向到 Stripe Checkout 或沙箱成功页
7. 支付完成 → 跳转成功页（`:locale/checkout/success`）

#### 异常状态

- **未登录**: 自动跳转登录页
- **认证加载中**: Loading 旋转器
- **Stripe 未配置**: 自动切换到模拟支付
- **订单创建失败**: 错误提示 + 重试
- **库存不足**: 前端展示库存不足提示

### 5.4 Stripe 支付

**API**: `POST /api/v1/payments/create-intent` + `POST /api/v1/payments/stripe-webhook`

#### 支付流程

1. 前端 `POST /api/v1/payments/create-intent`（传入 `order_id`）
2. 后端检查订单状态（已支付则拒绝），创建 Stripe Checkout Session
3. 返回 `session_id` → 前端重定向到 Stripe 托管支付页
4. 支付完成 → Stripe 回调 Webhook `checkout.session.completed`
5. Webhook 更新订单状态 `confirmed`、支付状态 `paid`
6. 异步发送预订确认邮件（Celery）

#### 沙箱模式

- Stripe 未配置时自动返回 `mock_` 前缀 Session ID
- 前端检测到 mock session 时跳转到模拟成功页

#### 支付成功页

**路由**: `/:locale/checkout/success`
- 绿色复选确认图标
- 显示订单号
- 操作按钮："查看订单" / "返回首页"

### 5.5 订单历史 (My Orders)

**路由**: `/:locale/user/orders`  
**API**: `GET /api/v1/orders`

#### 功能点

- 加载用户所有订单列表（分页）
- 订单卡片：订单号、产品名称、出发日期、人数、总价
- 状态徽章颜色编码：
  - `pending` = 黄色（待付款）
  - `confirmed` = 绿色（已确认）
  - `completed` = 蓝色（已完成）
  - `cancelled` = 红色（已取消）
  - `refunded` = 灰色（已退款）
- 支付状态：`paid` = 绿色

#### 异常状态

- **加载中**: 3 个 Skeleton 占位
- **订单为空**: "暂无订单" 空状态
- **国际化**: 状态通过翻译映射显示

### 5.6 旅游产品评价 (Reviews)

**API**: `POST /api/v1/reviews` / `GET /api/v1/reviews/tour/{tour_id}`

#### 功能点

| 功能 | 详情 |
|------|------|
| **创建评价** | 已登录用户提交（评分 1-5 星 + 标题 + 评论） |
| **评价展示** | 旅游详情页评价列表（分页）+ 平均评分 |
| **审核流程** | 新评价默认 `pending`，管理员审核后可见 |
| **去重保护** | 同一用户同一产品只能评价一次（409 Conflict） |
| **邮件通知** | 新评价提交后异步通知所有管理员 |
| **评分重算** | 评价创建/修改时自动更新 Tour 的 `avg_rating` 和 `review_count` |

#### 异常状态

- **未登录**: 评论表单提示登录
- **重复评价**: "您已评价过此产品" 提示
- **提交错误**: 表单内红色错误提示

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

## 6. 管理功能（管理员）

> 所有管理接口需 `is_admin=True` 的 JWT 认证，非管理员重定向到 `/auth`

### 6.1 仪表盘 (Dashboard)

**路由**: `/:locale/admin`  
**API**: `GET /api/v1/admin/stats`

#### 统计指标

| 指标 | 数据来源 | 说明 |
|------|----------|------|
| 总旅游产品数 | `SELECT COUNT(*) FROM tours WHERE deleted_at IS NULL` | 含已发布/草稿 |
| 已发布产品数 | `WHERE status='published'` | 子统计 |
| 总订单数 | `SELECT COUNT(*) FROM orders` | 全部订单 |
| 总用户数 | `SELECT COUNT(*) FROM users` | 注册用户 |
| 总收入 | `SUM(total) WHERE payment_status='paid'` | 已完成支付总金额 |
| 待审核评价 | `WHERE status='pending'` | 未审核评价 |

#### 异常状态

- **非管理员**: 重定向到 `/auth`
- **加载中**: AdminDashboardSkeleton

### 6.2 旅游产品管理 (Tours)

#### 产品列表

**路由**: `/:locale/admin/tours`  
**API**: `GET /api/v1/admin/tours`

| 列 | 内容 |
|----|------|
| **Serial No.** | 格式 `{area_code}-{serial_number}`（如 010-0001） |
| **Name** | 产品名称（回退到 slug） |
| **Sort** | 排序字段 (`sort_order`) |
| **Status** | 状态徽章（已发布=绿 / 草稿=灰 / 其他=黄） |
| **Price** | 起价 |
| **Days** | 行程天数 |
| **Difficulty** | 难度（easy/moderate/challenging） |
| **Actions** | Edit / Dates / Preview / Delete |

#### 产品序列号 (Serial Number)

每个旅游产品分配一个唯一的序列号，用于产品标识和管理：
- **格式**: `{城市区号}-{4位数字}`，如 `010-0001`
- **城市区号**: 取自第一个目的地的 `area_code` 字段
- **序列号**: 按城市独立编号（4 位补零）
- **自动生成**: 新建产品未指定时自动生成（同城市最大号 +1）
- **管理用途**: 方便运营团队识别和管理产品

**区号映射（种子数据）:**

| 城市 | 区号 | 序列号示例 |
|------|------|-----------|
| 北京 | 010 | 010-0001 ~ 010-0010 |
| 南京 | 025 | 025-0001 |
| 西安 | 029 | 029-0001 |

#### 创建旅游产品

**路由**: `/:locale/admin/tours/create`  
**API**: `POST /api/v1/admin/tours`

表单包含：
- **基本信息**: slug、状态、类型（group_tour/private_tour）、难度（easy/moderate/challenging）
- **序列号**: 可选，未填时自动生成
- **行程**: 天数、晚数、起价、货币（USD/CNY/EUR）
- **人数**: 最大/最小人数
- **多语言**: 三种语言的名称、副标题、描述
- **特色**: 多种语言的亮点/包含/不包含动态列表

#### 编辑旅游产品

**路由**: `/:locale/admin/tours/[id]/edit`  
**API**: `GET /api/v1/admin/tours/{tour_id}` + `PATCH /api/v1/admin/tours/{tour_id}`

| 选项卡区域 | 字段 |
|------------|------|
| 基本信息 | slug（只读）、状态、类型、难度、天数、晚数、起价、货币、人数 |
| 名称与描述 | 名称、副标题、描述（各语言独立） |
| 亮点与详情 | 亮点、包含、不包含（各语言独立动态列表） |
| 行程 | 每日行程 JSON 编辑（各语言独立） |
| 照片与视频 | 图片/视频上传、预览、删除、排序 |

**图片上传:**
- 常见图片格式（JPG/PNG/WebP/GIF/SVG）+ 视频（MP4/WebM/MOV）
- 最大文件 60MB
- 拖放上传 + 删除按钮
- `POST /api/v1/admin/upload` → 返回可访问 URL

#### 出发日期管理

**路由**: `/:locale/admin/tours/[id]/dates`  
**API**: 团期完整 CRUD

| 操作 | 说明 |
|------|------|
| **列表** | 表格展示所有团期（日期/价格/库存/状态） |
| **新增** | 日期选择器 + 价格 + 可用名额 |
| **编辑** | 内联编辑直接修改价格和名额 |
| **删除** | 带确认弹窗永久删除 |
| **状态徽章** | 可用=绿 / 已售罄=红 / 已取消=灰 |
| **统计** | 总日期数 / 可用数 / 已售罄数 |

#### 产品删除

- **方式**: 软删除（设置 `deleted_at` 时间戳）
- **API**: `DELETE /api/v1/admin/tours/{tour_id}`
- **前端**: 列表行 Delete 按钮 → 确认弹窗 → 调用 API → 从列表移除
- **效果**: 已删除产品不再出现于管理列表，历史订单保留

### 6.3 目的地管理 (Destinations)

**路由**: `/:locale/admin/destinations`  
**API**: 完整 CRUD（列表/创建/详情/更新/删除）

| 操作 | 说明 |
|------|------|
| **列表** | 分页表格（slug/名称/状态/图片/操作） |
| **创建** | slug + 图片 URL + 状态 + 多语言翻译（name/description/meta） |
| **详情** | 完整信息含 translations 数组 |
| **更新** | 支持增量式翻译更新 |
| **删除** | 无关联景点时允许删除；有关联景点时返回 422 |
| **唯一性** | slug 重复返回 409 |

#### 异常状态

- **删除有关联景点**: 422 ValidationException
- **slug 重复**: 409 Conflict
- **不存在**: 404 NotFound

### 6.4 景点管理 (Attractions)

**路由**: `/:locale/admin/attractions`  
**API**: `GET /api/v1/admin/attractions` + `GET /api/v1/admin/attractions/{id}` + `PATCH /api/v1/admin/attractions/{id}`

#### 功能点

| 功能 | 说明 |
|------|------|
| **景点列表** | 分页列表，含名称、目的地、评分、状态 |
| **景点详情** | 完整信息（含 translations、media、tickets） |
| **基础信息编辑** | 更新 image_url、rating、sort_order、status |
| **多语言编辑** | 更新 name、description、ticket_info、opening_hours |
| **媒体管理** | 媒体（图片）上传/删除/排序，上限 8 个 |

### 6.5 基础服务管理 (Base Services)

**API**: `GET /api/v1/admin/base-services` + `POST` + `PUT` + `DELETE`

| 操作 | 说明 |
|------|------|
| **列表** | 所有基础服务（名称/类型/价格/状态） |
| **创建** | 名称 + 多语言 + 计价单位 + 单价 + 分类 |
| **更新** | 全字段编辑 |
| **删除** | 存在关联定制旅程时返回 422 |
| **404 处理** | 删除不存在的服务返回 404 |

**基础服务清单（种子数据）:**

| 名称 | 计价类型 | 价格 |
|------|----------|------|
| One-way Airport Transfer | per_trip | $60.0 |
| One-way Train Station Transfer | per_trip | $40.0 |
| English Guide Service | per_day | $120.0 |
| Spanish Guide Service | per_day | $140.0 |
| French Guide Service | per_day | $140.0 |
| Vehicle Service | per_pax | $35.0 |
| Hotel Service | per_pax | $65.0 |
| Lunch Service | per_pax | $15.0 |
| Dinner Service | per_pax | $25.0 |

### 6.6 自定制旅程管理 (Custom Tour Admin)

**路由**: `/:locale/admin/custom-tours`  
**API**: `GET /api/v1/admin/custom-tours` + `PATCH /api/v1/admin/custom-tours/{id}`

| 功能 | 说明 |
|------|------|
| **请求列表** | 所有用户提交的定制请求 |
| **详情查看** | 行程段、景点、产品、服务、用户需求描述 |
| **价格确认** | 管理员回复确认价格（更新 `admin_notes`/`status`/`estimated_price`） |
| **状态标记** | pending / confirmed / approved / rejected |

### 6.7 订单管理

**路由**: `/:locale/admin/orders`  
**API**: `GET /api/v1/admin/orders` + `PATCH /api/v1/admin/orders/{order_id}/status`

| 功能 | 说明 |
|------|------|
| **订单列表** | 表格展示（订单号/客户名/状态/支付状态/总价/人数/日期） |
| **状态更新** | 管理员可更新订单状态和支付状态 |
| **状态徽章** | 待处理=黄 / 已确认=绿 / 已完成=蓝 / 已取消=红 |
| **支付徽章** | 已支付=绿 / 其他=灰 |

### 6.8 用户管理

**API**: `GET /api/v1/admin/users`
- 分页列出所有注册用户
- 查看用户概览信息

### 6.9 评价审核

**路由**: `/:locale/admin/reviews`  
**API**: `GET /api/v1/admin/reviews` + `PATCH /api/v1/admin/reviews/{review_id}`

| 功能 | 说明 |
|------|------|
| **评价列表** | 默认显示待审核评价，支持状态筛选 |
| **筛选切换** | 待处理 / 已批准 / 已拒绝 三个标签 |
| **评价卡片** | 星级、标题、评论文本、日期 |
| **审核操作** | 批准（绿色按钮）、拒绝（红色按钮） |
| **自动刷新** | 操作后自动重载 |

#### 异常状态

- **加载中**: Skeleton + TableSkeleton
- **评论为空**: "未找到评论"

### 6.10 搜索索引管理

**API**: `POST /api/v1/admin/reindex`
- 手动触发 Elasticsearch 索引重建
- 从数据库重新构建所有产品的搜索索引

### 6.11 咨询管理 (Enquiries)

**路由**: `/:locale/admin/enquiries`  
**API**: `GET /api/v1/admin/enquiries` + `GET /api/v1/admin/enquiries/{id}` + `PATCH /api/v1/admin/enquiries/{id}` + `DELETE /api/v1/admin/enquiries/{id}`

#### 功能点

| 功能 | 说明 |
|------|------|
| **咨询列表** | 分页表格（名称/邮箱/电话/目的地/人数/状态/提交时间），支持 status 筛选 |
| **详情查看** | 展开查看完整咨询内容（含需求描述和用户留言） |
| **状态更新** | pending → contacted / resolved / closed |
| **备注填写** | 管理员内部备注字段 |
| **删除** | 手动清理无效咨询记录 |

#### 状态流程

```
pending → contacted → resolved
                     → closed
```

#### 异常状态

- **无咨询**: "暂无咨询" 空状态
- **列表加载中**: Skeleton 占位

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
- 示例：`ECHO-20260605-A3F2C1B0`

### 7.4 库存管理策略

| 业务线 | 库存单元 | 扣减方式 | 并发控制 |
|--------|----------|----------|----------|
| 旅游产品 | `tour_dates.availability` | 原子递减 | SQL UPDATE SET availability = availability - N |
| 景点门票 | `attraction_tickets.availability` | 原子递减 | 同上 |
| 唯一约束 | `(user_id, tour_id)` wishtlist | 数据库唯一约束 | IntegrityError → 409 |

**超卖防护**: 下单前检查 `availability >= pax_count`，不足时抛出 `InsufficientStockException`。

### 7.5 价格计算

| 场景 | 公式 |
|------|------|
| 旅游产品 | `total = tour_date.price_per_pax × pax_count` |
| 景点门票 | `total = ticket.price × pax_count` |
| 费用结构 | `subtotal - discount + tax = total` |

### 7.6 邮件通知

| 触发时机 | 邮件类型 | 发送方式 |
|----------|----------|----------|
| 用户注册 | 欢迎邮件 | Celery 异步 + SendGrid |
| 支付成功 | 预订确认邮件 | Celery 异步 + SendGrid |
| 提交评价 | 评价通知（管理员） | Celery 异步 + SendGrid |

---

## 8. 搜索系统

### 8.1 技术架构

使用 Elasticsearch 8，独立索引 `tours`。每条文档按 `(tour_id, locale)` 分拆，一个旅游产品对应 2-3 条文档覆盖多语言。

### 8.2 索引映射

```json
{
  "settings": { "analysis": { "analyzer": { "tours_combined": { ... } } } },
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
      "theme": { "type": "keyword" },
      "max_pax": { "type": "integer" },
      "destination_ids": { "type": "keyword" },
      "name": { "type": "text", "fields": { "keyword": { "type": "keyword" } } },
      "description": { "type": "text" },
      "subtitle": { "type": "text" },
      "highlights": { "type": "text" },
      "images": { "type": "nested", "properties": { "url": { "type": "keyword" }, "alt": { "type": "text" } } },
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
| 关键词 `q` | 全文搜索 | "Great Wall" |
| 难度 `difficulty` | 精确匹配 | easy/moderate/challenging |
| 主题 `theme` | 精确匹配 | citywalk / culture_history / nature / food / ... |
| 最低价格 `min_price` | 范围过滤 | 100 |
| 最高价格 `max_price` | 范围过滤 | 2000 |
| 最短天数 `min_duration` | 范围过滤 | 3 |
| 最长天数 `max_duration` | 范围过滤 | 14 |
| 语言 `locale` | 精确匹配 | en/zh/es |

#### 排序选项

| 方式 | 说明 |
|------|------|
| `rating` | 按评分降序（默认） |
| `price_asc` | 价格升序 |
| `price_desc` | 价格降序 |
| `duration` | 天数升序 |
| `newest` | 最新发布排序 |

#### 聚合统计 (Facets)

| 聚合 | 说明 |
|------|------|
| `difficulties` | 各难度层级的产品数量 |
| `themes` | 各主题标签的产品数量 |
| `price_ranges` | 价格区间分布（0-100 / 100-500 / 500-1000 / 1000-2000 / 2000+） |

### 8.4 前端搜索页面

**路由**: `/:locale/search`

- **实时搜索**: 输入防抖 300ms
- **搜索输入**: SearchInput 组件（带清空按钮）
- **筛选控件**: SearchFilters（主题、难度、排序）
- **结果展示**: 结果计数 + TourCard 网格
- **空结果**: 空状态提示
- **初始状态**: 从 URL 参数 `?q=&difficulty=&sort_by=` 读取

#### 异常状态

- **加载中**: 旋转器 + TourGridSkeleton
- **错误**: 红色错误横幅 + 错误信息

### 8.5 索引维护

| 任务 | 触发器 | 方式 |
|------|--------|------|
| 启动自动索引 | 应用启动 | `lifespan` 事件中执行 `bulk_index_tours()` |
| 每日重建 | Celery Beat | 每日一次 `reindex_all_tours` 任务 |
| 手动重建 | 管理员 API | `POST /api/v1/admin/reindex` |

---

## 9. 内容管理系统（CMS）

### 9.1 旅游产品 (Tour)

| 字段 | 多语言 | 说明 |
|------|--------|------|
| slug | × | URL 标识符，唯一索引 |
| serial_number | × | 序列号（如 0001），按城市独立编号 |
| status | × | draft / published |
| type | × | group_tour / private_tour |
| duration_days / nights | × | 行程天数和晚数 |
| max_pax / min_pax | × | 团组人数限制 |
| start_price | × | 起价 |
| currency | × | USD / CNY / EUR |
| difficulty | × | easy / moderate / challenging |
| sort_order | × | 排序权重 |
| theme | × | 旅行主题标签：citywalk / culture_history / nature / food / honeymoon / family / luxury / adventure / photography / wellness / hidden_gems / festival |
| destination_ids | × | 关联目的地 UUID 数组（PG Array） |
| avg_rating / review_count | × | 系统自动计算 |
| highlights / includes / excludes | × | 产品级（回退用，优先使用翻译级） |
| ✅ name / subtitle / description | ✓ | 核心文案 |
| ✅ itinerary (JSON) | ✓ | 每日行程（含 day/title/description/meals） |
| ✅ highlights / includes / excludes | ✓ | 翻译级详情（JSON 数组） |
| ✅ meta_title / meta_description | ✓ | SEO 元数据 |
| **deleted_at** | × | 软删除时间戳 |

### 9.2 目的地 (Destination)

| 字段 | 多语言 | 说明 |
|------|--------|------|
| slug | × | 唯一标识，UNIQUE INDEX |
| area_code | × | 城市电话区号（如 010/025/029） |
| image_url | × | 图片 URL |
| status | × | active / inactive |
| ✅ name / description | ✓ | 核心文案 |
| ✅ meta_title / meta_description | ✓ | SEO 元数据 |

### 9.3 景点 (Attraction)

| 字段 | 多语言 | 说明 |
|------|--------|------|
| slug | × | 唯一标识（按目的地索引） |
| destination_id | × | 关联目的地 FK |
| image_url | × | 封面图片 |
| rating | × | 评分 1-5 |
| sort_order | × | 排序权重 |
| status | × | active / inactive |
| ✅ name / description | ✓ | 核心文案 |
| ✅ ticket_info / opening_hours | ✓ | 门票信息/开放时间 |

#### 景点媒体 (AttractionMedia)

| 字段 | 说明 |
|------|------|
| url | 媒体 URL |
| type | image / video |
| sort_order | 排序权重 |
| **上限**: 每个景点最多 8 个媒体文件 |

### 9.4 景点门票 (AttractionTicket)

| 字段 | 说明 |
|------|------|
| ticket_type | standard / vip / child（同一景点下唯一） |
| price | 价格 |
| currency | 货币 |
| availability | 库存数量 |
| status | available / sold_out / discontinued |

### 9.5 基础服务 (BaseService)

| 字段 | 多语言 | 说明 |
|------|--------|------|
| name | ✓ | 服务名称 |
| unit_type | × | per_day / per_pax / per_trip |
| unit_price | × | 单价 |
| currency | × | 货币 |
| category | × | 分类标签 |
| sort_order | × | 排序 |
| status | × | active / inactive |

### 9.6 自定制旅程模型

#### CustomTourRequest（定制请求）
| 字段 | 说明 |
|------|------|
| user_id | 用户 FK |
| start_date / end_date | 行程日期范围 |
| pax_count | 人数 |
| prompt | 旅行需求描述 |
| status | draft / submitted / quoted / approved / rejected |
| estimated_price | 管理员报价 |
| admin_notes | 管理员备注 |

#### CustomTourSegment（行程段）
| 字段 | 说明 |
|------|------|
| request_id | 关联请求 FK |
| destination_id | 系统目的地 FK（可为空） |
| custom_destination | 自定义目的地名称（可为空） |
| attraction_ids | 景点 UUID 数组 |
| start_date / end_date | 段内日期范围 |
| sort_order | 段排序 |
| **约束**: destination_id 和 custom_destination 至少一个非空 |

#### CustomTourService（关联服务）
| 字段 | 说明 |
|------|------|
| segment_id | 关联行程段 FK |
| service_id | 基础服务 FK |
| quantity | 数量 |
| unit_price | 锁定单价（创建时记录） |

### 9.7 图片/视频管理

- 上传 API: `POST /api/v1/admin/upload`（最大 60MB）
- 产品图片管理: `DELETE /api/v1/admin/tours/{id}/images/{image_id}`
- 景点媒体管理: POST/DELETE media + PUT reorder（上限 8 个）
- 支持格式: 图片（JPG/PNG/WebP/GIF/SVG）+ 视频（MP4/WebM/MOV）
- 排序字段: `sort_order`

### 9.8 咨询表单 (Enquiry)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | PK |
| name | String(100) | 联系人姓名 |
| email | String(255) | 联系邮箱 |
| phone | String(50) | NULLABLE 联系电话 |
| destination | String(200) | NULLABLE 感兴趣的目的地 |
| pax_count | Integer | NULLABLE 出行人数 |
| message | Text | 需求描述 |
| status | String(20) | DEFAULT 'pending'（pending / contacted / resolved / closed） |
| admin_notes | Text | NULLABLE 管理员备注 |

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
- **文件结构**: `messages/{locale}/common.json`（静态 import 加载）
- **支持语言**: en（英语）、zh（简体中文）、es（西班牙语）
- **URL 模式**: `/{locale}/...` 前缀模式
- **语言检测**: 基于 `Accept-Language` 请求头，默认英语
- **切换方式**: Header 下拉菜单，替换 URL 语言前缀
- **翻译键**: 15+ 命名空间，400+ 翻译键

### 10.3 后端内容国际化

- 每个多语言实体对应一个翻译表，`locale` 列区分
- 翻译表外键关联主表，CASCADE 删除
- 主表存储语言无关数据
- 读取策略：请求的语言 → 英语 → 第一个可用翻译

### 10.4 翻译表清单

| 主表 | 翻译表 | 多语言字段 |
|------|--------|------------|
| `tours` | `tour_translations` | name, subtitle, description, itinerary (JSON), highlights (JSON), includes (JSON), excludes (JSON), meta_title, meta_description |
| `destinations` | `destination_translations` | name, description, meta_title, meta_description |
| `attractions` | `attraction_translations` | name, description, ticket_info, opening_hours, meta_title, meta_description |
| `base_services` | — | name_{locale} 分列模式（name_zh, name_es, name_fr） |

---

## 11. 技术架构

### 11.1 系统架构

```
CDN / Nginx (:80)
     │
     ├── Next.js 15 Frontend (:3000) ── SSR + CSR
     │
     └── FastAPI Backend (:8000)
              │
     ┌────────┼────────────┐
     │        │            │
  PostgreSQL  Redis 7    Elasticsearch 8
     16     (Cache+BR)   (Search)
     │        │
     └────────┼────────────┐
          Celery Worker  Celery Beat
          (Async Tasks)  (Scheduler)
```

### 11.2 请求流程

```
浏览器 → Nginx → Next.js (SSR) → FastAPI → Service Layer → CRUD → DB
                                ↑               ↓
                             Redis Cache    Elasticsearch
```

### 11.3 架构层次

| 层次 | 职责 | 技术 |
|------|------|------|
| **路由层** | 请求路由、参数解析、响应 JSON | FastAPI Router |
| **Service 层** | 业务逻辑编排、缓存、事务协调 | `app/services/` |
| **CRUD 层** | 数据访问、ORM 操作、缓存失效 | `app/crud/` |
| **Model 层** | 数据模型定义、关系映射 | SQLAlchemy ORM |

### 11.4 Docker 服务

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| Nginx | nginx:alpine | 80 | 反向代理 |
| PostgreSQL | postgres:16-alpine | 5432 | 主数据库 |
| Redis | redis:7-alpine | 6379 | 缓存 + Celery Broker |
| Elasticsearch | elasticsearch:8.17.0 | 9200 | 全文搜索 |
| Backend | 自构建 | 8000 | FastAPI 应用 |
| Frontend | 自构建 | 3000 | Next.js 应用 |
| Celery Worker | 自构建 | — | 异步任务执行 |
| Celery Beat | 自构建 | — | 定时任务调度 |
| MailHog | mailhog/mailhog | 8025/1025 | 开发邮件捕获 |

### 11.5 依赖清单

#### 前端 (Next.js 15)
next, react, react-dom, next-intl, zustand, tailwindcss, shadcn/ui, lucide-react, stripe-js, sonner, react-hook-form, zod

#### 后端 (Python 3.12+)
fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, alembic, pydantic, pydantic-settings, python-jose, passlib, bcrypt, redis[hiredis], elasticsearch[async], stripe, celery[redis], sendgrid, slowapi, httpx, tenacity, google-auth

---

## 12. 数据模型总览

### 12.1 ER 关系概要

```
User (1) ──── (N) Order (N) ──── (N) OrderPassenger
User (1) ──── (N) Review (N) ──── (1) Tour
User (1) ──── (N) Wishlist (N) ──── (1) Tour
User (1) ──── (N) AttractionWishlist (N) ──── (1) Attraction
User (1) ──── (N) CustomTourRequest (N) ──── (N) CustomTourSegment (N) ──── (N) CustomTourService
                                                                       └── (N) SelectedTour

Destination (1) ──── (N) Tour (通过 destination_ids 数组)
Destination (1) ──── (N) Attraction (1) ──── (N) AttractionTicket
                                    └── (N) AttractionMedia (≤8)

Tour (1) ──── (N) TourTranslation
Tour (1) ──── (N) TourDate
Tour (1) ──── (N) TourImage
Tour (1) ──── (N) Review

Destination (1) ──── (N) DestinationTranslation
Attraction (1) ──── (N) AttractionTranslation
CustomTourSegment (0..1) ──── (1) Destination (通过 destination_id)
CustomTourSegment (0..1) ──── (1) 自定义目的地文本

Enquiry (独立表) — 咨询表单，不关联其他表
```

### 12.2 核心模型字段

#### User (users)
| 字段 | 类型 | 约束 |
|------|------|------|
| id | UUID | PK |
| email | String(255) | UNIQUE, NOT NULL |
| name | String(100) | NOT NULL |
| hashed_password | String(255) | NULLABLE |
| avatar_url | String(500) | NULLABLE |
| google_id | String(255) | UNIQUE, NULLABLE |
| is_admin | Boolean | DEFAULT false |
| locale | String(10) | DEFAULT 'en' |

#### Tour (tours)
| 字段 | 类型 | 约束 |
|------|------|------|
| id | UUID | PK |
| slug | String(200) | INDEX |
| serial_number | String(10) | NULLABLE（4位数字） |
| status | String(20) | DEFAULT 'draft' |
| type | String(30) | group_tour / private_tour |
| duration_days | SmallInteger | NOT NULL |
| sort_order | SmallInteger | DEFAULT 0 |
| start_price | Float | DEFAULT 0 |
| destination_ids | ARRAY(UUID) | PG 数组 |
| deleted_at | DateTime(tz) | NULLABLE（软删除） |

#### Destination (destinations)
| 字段 | 类型 | 约束 |
|------|------|------|
| id | UUID | PK |
| slug | String(100) | UNIQUE, NOT NULL |
| area_code | String(10) | NULLABLE（如 010） |

#### CustomTourRequest (custom_tour_requests)
| 字段 | 类型 | 约束 |
|------|------|------|
| id | UUID | PK |
| user_id | UUID | FK |
| status | String(30) | DEFAULT 'draft' |
| destination_id | UUID | NULLABLE（可空） |
| start_date / end_date | Date | NULLABLE |

#### BaseService (base_services)
| 字段 | 类型 | 约束 |
|------|------|------|
| id | UUID | PK |
| name | String(200) | NOT NULL |
| unit_type | String(20) | per_day / per_pax / per_trip |
| name_zh / name_es | String(200) | NULLABLE（多语言分列） |

#### Enquiry (enquiries)
| 字段 | 类型 | 约束 |
|------|------|------|
| id | UUID | PK |
| name | String(100) | NOT NULL |
| email | String(255) | NOT NULL |
| phone | String(50) | NULLABLE |
| destination | String(200) | NULLABLE |
| pax_count | Integer | NULLABLE |
| message | Text | NULLABLE |
| status | String(20) | DEFAULT 'pending' |
| admin_notes | Text | NULLABLE |
| created_at | DateTime | NOT NULL |

### 12.3 唯一约束清单

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
| enquiries | — | 无唯一约束（咨询表单允许多次提交） |

---

## 13. API 端点完整列表

### 13.1 公开接口（无需认证）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查（版本/ES状态/Stripe配置/OAuth配置） |
| POST | `/api/v1/auth/register` | 用户注册 |
| POST | `/api/v1/auth/login` | 用户登录 |
| POST | `/api/v1/auth/google` | Google OAuth 登录 |
| POST | `/api/v1/auth/google/dev` | 开发环境模拟 Google 登录 |
| GET | `/api/v1/tours` | 旅游产品列表（分页/难度筛选/主题筛选） |
| GET | `/api/v1/tours/{slug_or_id}` | 旅游产品详情 |
| GET | `/api/v1/tours/{tour_id}/dates` | 团期列表 |
| GET | `/api/v1/destinations` | 目的地列表 |
| GET | `/api/v1/destinations/{slug}` | 目的地详情 |
| GET | `/api/v1/destinations/{slug}/tours` | 目的地下的旅游产品 |
| GET | `/api/v1/destinations/{slug}/attractions` | 目的地下的景点（按 sort_order） |
| GET | `/api/v1/reviews/tour/{tour_id}` | 评价列表（分页） |
| GET | `/api/v1/search` | 全文搜索（筛选/排序/聚合） |
| GET | `/api/v1/attractions` | 景点列表（按目的地筛选） |
| GET | `/api/v1/attractions/{id}` | 景点详情（含媒体/门票） |
| GET | `/api/v1/attractions/{id}/tickets` | 景点门票类型 |
| POST | `/api/v1/payments/create-intent` | 创建 Stripe Checkout Session |
| POST | `/api/v1/payments/stripe-webhook` | Stripe Webhook 回调 |
| POST | `/api/v1/custom-tours/quote` | 定制旅程报价计算 |
| POST | `/api/v1/custom-tours/requests` | 提交定制旅程请求 |
| GET | `/api/v1/custom-tours/requests` | 获取用户的定制请求列表 |
| GET | `/api/v1/custom-tours/requests/{id}` | 获取定制请求详情 |
| POST | `/api/v1/enquiries` | 提交咨询表单（姓名/邮箱/电话/目的地/人数/需求） |

### 13.2 用户接口（需 JWT 认证）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/auth/me` | 获取当前用户信息 |
| POST | `/api/v1/orders` | 创建订单 |
| GET | `/api/v1/orders` | 用户订单列表 |
| GET | `/api/v1/orders/{order_id}` | 订单详情 |
| POST | `/api/v1/reviews` | 创建评价 |
| GET | `/api/v1/users/me/profile` | 获取个人资料 |
| PATCH | `/api/v1/users/me/profile` | 更新个人资料 |
| GET | `/api/v1/wishlist` | 旅游产品收藏列表 |
| POST | `/api/v1/wishlist/{tour_id}` | 添加收藏 |
| DELETE | `/api/v1/wishlist/{tour_id}` | 移除收藏 |
| GET | `/api/v1/wishlist/attractions` | 景点收藏列表 |
| POST | `/api/v1/wishlist/attractions/{attraction_id}` | 添加景点收藏 |
| DELETE | `/api/v1/wishlist/attractions/{attraction_id}` | 移除景点收藏 |

### 13.3 管理接口（需管理员 JWT 认证）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/admin/stats` | 仪表盘统计数据 |
| GET | `/api/v1/admin/tours` | 旅游产品列表 |
| POST | `/api/v1/admin/tours` | 创建旅游产品 |
| GET | `/api/v1/admin/tours/{tour_id}` | 产品详情（含翻译/图片/团期） |
| PATCH | `/api/v1/admin/tours/{tour_id}` | 部分更新产品 |
| PUT | `/api/v1/admin/tours/{tour_id}` | 完整替换更新 |
| DELETE | `/api/v1/admin/tours/{tour_id}` | 软删除产品 |
| POST | `/api/v1/admin/upload` | 上传图片/视频（≤60MB） |
| DELETE | `/api/v1/admin/tours/{id}/images/{image_id}` | 删除图片/视频 |
| GET | `/api/v1/admin/tours/{id}/dates` | 团期列表 |
| POST | `/api/v1/admin/tours/{id}/dates` | 新增团期 |
| PATCH | `/api/v1/admin/tours/{id}/dates/{date_id}` | 更新团期 |
| DELETE | `/api/v1/admin/tours/{id}/dates/{date_id}` | 删除团期 |
| GET | `/api/v1/admin/orders` | 订单管理列表 |
| PATCH | `/api/v1/admin/orders/{order_id}/status` | 更新订单状态 |
| GET | `/api/v1/admin/users` | 用户管理列表 |
| GET | `/api/v1/admin/reviews` | 评价管理列表 |
| PATCH | `/api/v1/admin/reviews/{review_id}` | 审核评价 |
| POST | `/api/v1/admin/reindex` | 重建搜索索引 |
| GET | `/api/v1/admin/destinations` | 目的地管理列表 |
| POST | `/api/v1/admin/destinations` | 创建目的地 |
| GET | `/api/v1/admin/destinations/{id}` | 目的地详情 |
| PUT | `/api/v1/admin/destinations/{id}` | 更新目的地 |
| DELETE | `/api/v1/admin/destinations/{id}` | 删除目的地 |
| GET | `/api/v1/admin/base-services` | 基础服务列表 |
| POST | `/api/v1/admin/base-services` | 创建基础服务 |
| PUT | `/api/v1/admin/base-services/{id}` | 更新基础服务 |
| DELETE | `/api/v1/admin/base-services/{id}` | 删除基础服务 |
| GET | `/api/v1/admin/attractions` | 景点管理列表 |
| GET | `/api/v1/admin/attractions/{id}` | 景点详情 |
| PATCH | `/api/v1/admin/attractions/{id}` | 更新景点 |
| POST | `/api/v1/admin/attractions/{id}/media` | 添加景点媒体 |
| DELETE | `/api/v1/admin/attractions/{id}/media/{media_id}` | 删除景点媒体 |
| PUT | `/api/v1/admin/attractions/{id}/media/reorder` | 媒体排序 |
| GET | `/api/v1/admin/custom-tours` | 定制旅程请求列表 |
| GET | `/api/v1/admin/custom-tours/{id}` | 定制旅程请求详情 |
| PATCH | `/api/v1/admin/custom-tours/{id}` | 更新定制旅程状态/报价 |
| GET | `/api/v1/admin/enquiries` | 咨询列表（支持 status 筛选） |
| GET | `/api/v1/admin/enquiries/{id}` | 咨询详情 |
| PATCH | `/api/v1/admin/enquiries/{id}` | 更新咨询状态/备注 |
| DELETE | `/api/v1/admin/enquiries/{id}` | 删除咨询记录 |

> **总计**: 70+ 唯一 API 端点（不含 /health；公开 24 + 用户 13 + 管理 42）

### 13.4 API 统一响应格式

```json
// 成功
{ "code": 200, "data": { ... }, "message": "ok" }

// 分页
{ "code": 200, "data": [...], "message": "ok", "meta": { "total": 100, "page": 1, "page_size": 12 } }

// 错误
{ "detail": "Resource not found", "error_code": "NOT_FOUND" }
```

---

## 14. 前端路由与组件

### 14.1 完整路由表

| 路由 | 页面文件 | 类型 | 功能 | 认证 |
|------|----------|------|------|------|
| `/` | `app/layout.tsx` | SSR | 根布局 | — |
| `/:locale` | `app/[locale]/layout.tsx` | SSR | 全局布局 | — |
| `/:locale` | `app/[locale]/page.tsx` | SSR | 首页 | — |
| `/:locale/tours` | `app/[locale]/tours/page.tsx` | SSR | 旅游列表 | — |
| `/:locale/tours/[slug]` | `app/[locale]/tours/[slug]/page.tsx` | SSR+C | 旅游详情 | — |
| `/:locale/destinations` | `app/[locale]/destinations/page.tsx` | SSR | 目的地列表 | — |
| `/:locale/destinations/[slug]` | `app/[locale]/destinations/[slug]/page.tsx` | SSR | 目的地详情 | — |
| `/:locale/custom-tour` | `app/[locale]/custom-tour/page.tsx` | CSR | 自定制旅程 | — |
| `/:locale/search` | `app/[locale]/search/page.tsx` | CSR | 全文搜索 | — |
| `/:locale/auth` | `app/[locale]/auth/page.tsx` | CSR | 登录/注册 | — |
| `/:locale/checkout` | `app/[locale]/checkout/page.tsx` | CSR | 结账 | User |
| `/:locale/checkout/success` | `app/[locale]/checkout/success/page.tsx` | CSR | 支付成功 | User |
| `/:locale/user/orders` | `app/[locale]/user/orders/page.tsx` | CSR | 我的订单 | User |
| `/:locale/user/profile` | `app/[locale]/user/profile/page.tsx` | CSR | 个人资料 | User |
| `/:locale/user/wishlist` | `app/[locale]/user/wishlist/page.tsx` | CSR | 我的收藏 | User |
| `/:locale/admin` | `app/[locale]/admin/page.tsx` | CSR | 管理仪表盘 | Admin |
| `/:locale/admin/tours` | `app/[locale]/admin/tours/page.tsx` | CSR | 管理旅游列表 | Admin |
| `/:locale/admin/tours/create` | `app/[locale]/admin/tours/create/page.tsx` | CSR | 创建旅游 | Admin |
| `/:locale/admin/tours/[id]/edit` | `app/[locale]/admin/tours/[id]/edit/page.tsx` | CSR | 编辑旅游 | Admin |
| `/:locale/admin/tours/[id]/dates` | `app/[locale]/admin/tours/[id]/dates/page.tsx` | CSR | 管理团期 | Admin |
| `/:locale/admin/orders` | `app/[locale]/admin/orders/page.tsx` | CSR | 管理订单 | Admin |
| `/:locale/admin/reviews` | `app/[locale]/admin/reviews/page.tsx` | CSR | 评价审核 | Admin |
| `/:locale/admin/destinations` | `app/[locale]/admin/destinations/page.tsx` | CSR | 管理目的地 | Admin |
| `/:locale/admin/base-services` | `app/[locale]/admin/base-services/page.tsx` | CSR | 基础服务管理 | Admin |
| `/:locale/admin/custom-tours` | `app/[locale]/admin/custom-tours/page.tsx` | CSR | 定制旅程管理 | Admin |
| `/:locale/admin/attractions` | `app/[locale]/admin/attractions/page.tsx` | CSR | 景点管理 | Admin |
| `/:locale/admin/enquiries` | `app/[locale]/admin/enquiries/page.tsx` | CSR | 咨询管理 | Admin |

> SSR = 服务端渲染, CSR = 客户端渲染, SSR+C = 混合渲染

### 14.2 核心组件树

```
Layout (app/[locale]/layout.tsx)
├── Header
│   ├── Logo
│   ├── NavLinks（旅游 / 目的地 / 搜索 / 定制旅程）
│   ├── LanguageSwitcher（en / zh / es）
│   └── AuthSection（登录/注册 → 用户菜单）
├── <page content>
└── Footer

TourCard（复用组件）
├── Image (next/image)
├── RatingBadge
├── DifficultyBadge
├── PriceDisplay
├── WishlistButton
└── BookNowButton

TourDetailClient
├── Breadcrumb
├── ImageGallery（图片+视频混合）
├── TourInfo（评分/元信息/描述/行程）
├── ReviewsSection（ReviewCard + ReviewForm）
├── StickyBookingSidebar（DateSelector + PaxCounter + PriceCalculator）
└── WishlistButton

CustomTourPage
├── SegmentList → SegmentCard（×N）
│   ├── DestinationPicker（系统/自定义）
│   ├── DateRangePicker
│   ├── AttractionSelector
│   └── TourSelector
├── BaseServicePanel
├── PromptPresets（3 模板）
├── PriceSummary
└── SubmitButton

AttractionInfoModal
├── MediaCarousel（≤8 张）
├── AttractionDetail
├── TicketSelector
└── BookNowButton

InquiryForm（挂载于 [locale]/layout.tsx 全局 Layout）
├── FloatingButton（全站右下角浮动触发，所有页面可见）
├── DialogForm（姓名/邮箱/电话/目的地/人数/需求描述）
├── LoadingState / SuccessAnimation
└── ErrorToast
```

### 14.3 骨架屏组件清单

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
| (global) loading.tsx | 页面级通用加载态 |

---

## 15. 部署与运维

### 15.1 容器化部署

- **容器化**: Docker + Docker Compose
- **生产环境**: 阿里云 ECS
- **反向代理**: Nginx（前端 + 后端统一入口 `:80`）

### 15.2 环境变量配置

| 配置项 | 说明 |
|--------|------|
| `database_url` | PostgreSQL 异步连接串 |
| `redis_url` | Redis 连接串 |
| `elasticsearch_url` | ES 连接串 |
| `secret_key` | JWT 签名密钥 |
| `stripe_secret_key / stripe_public_key` | Stripe API 密钥 |
| `sendgrid_api_key` | SendGrid 邮件 API 密钥 |
| `google_client_id / google_client_secret` | Google OAuth 凭证 |
| `cors_origins` | CORS 白名单 |
| `frontend_url` | 前端 URL |
| `debug / environment` | 运行环境标识 |

### 15.3 种子数据

启动时通过 `docker compose exec backend python /app/scripts/seed_data.py` 填充：

| 类别 | 数量 | 说明 |
|------|------|------|
| 🏙️ 目的地 | 3 | 北京(010) / 南京(025) / 西安(029) |
| 🏛️ 旅游产品 | 30 | 北京 28 + 南京 1 + 西安 1，含序列号，覆盖全部 12 种主题 |
| 🏛️ 景点 | 45 | 每城市 15 个景点（中英双语） |
| 🏛️ 景点媒体 | 225 | 每景点 4-6 个媒体文件 |
| 🔧 基础服务 | 9 | 接送机/导游/车辆/住宿/餐饮（含三语名称+描述） |
| 👤 用户 | 4 | 管理员 1 + 演示用户 3 |
| 💬 评论 | 12 | 中英文混合，已审核通过 |
| 📅 团期 | 202 | 未来 2-3 个月可选日期 |
| 🖼️ 产品图片 | 60+ | 每个产品 2-3 张 SVG 占位图 |

**默认账号**:
| 角色 | 邮箱 | 密码 |
|------|------|------|
| 管理员 | admin@echotours.com | Admin123! |
| 用户 | zhangsan@example.com | Test1234! |
| 用户 | lisi@example.com | Test1234! |
| 用户 | john@example.com | Test1234! |

---

## 16. 非功能性需求

### 16.1 性能指标

| 指标 | 目标 | 备注 |
|------|------|------|
| 页面加载时间 | < 1s SSR | 服务端渲染 |
| API 响应时间 | < 200ms | 含缓存命中 |
| 数据库连接池 | pool_size=10, max_overflow=20 | asyncpg |
| ES 索引重建 | < 30s | 12 产品 × 2 语言 |
| 速率限制 | 120 req/min | slowapi |

### 16.2 缓存策略

| 数据 | 策略 | TTL |
|------|------|-----|
| 旅游列表 | Redis 缓存 | 120s |
| 旅游详情 | Redis 缓存 | 300s |
| 团期 | Redis 缓存（下单时清除） | 60s |
| 搜索 | ES 全文索引 | — |
| 页面 | ISR 增量静态再生 | 120-300s |

### 16.3 安全体系

| 类别 | 措施 |
|------|------|
| **密码** | bcrypt 哈希 |
| **认证** | JWT (HS256, 24h) + Bearer |
| **权限** | `get_current_admin_user` 依赖检查 |
| **CORS** | 白名单配置 |
| **SQL注入** | ORM 参数化查询 |
| **速率限制** | slowapi 120 req/min |
| **输入验证** | Pydantic 严格校验 |
| **错误信息** | 不泄漏堆栈细节 |

### 16.4 异常处理层次

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

---

## 17. 附录

### 17.1 测试架构

```
后端测试（467 项通过）:
tests/
├── test_core/              (14) — 异常层次、响应格式
├── test_crud/              (86) — CRUD 全量
├── test_services/          (40) — 业务逻辑
├── test_api/              (257) — API 集成 + 业务流程
├── test_cache/             (15) — Redis 缓存
├── test_search/            (18) — ES 搜索
├── test_tasks/             (13) — Celery 任务
├── test_negative_path.py   (14) — 逆向操作
├── test_edge_cases.py      (10) — 边界场景
├── test_regression.py      (12) — 跨模块回归
├── test_security.py        (17) — 安全渗透
└── test_concurrency.py     (13) — 并发竞态

E2E 测试（19 Playwright spec 文件）:
tests/e2e/
├── 核心功能: auth / tours / checkout / search / homepage / destinations
├── 用户中心: user-center / reviews / payment-verification
├── 管理后台: admin
├── 多语言: i18n / search-extended
├── 异常: error-pages / negative-flow
└── 回归: regression-wishlist / regression-order / regression-auth / ...

Python E2E 自动化:
scripts/e2e_test.py — 16 步全业务流程（公开浏览→用户操作→后台管理）
```

### 17.2 版本历史

| 版本 | 日期 | 主要变化 |
|------|------|----------|
| v1.0 | Phase 1 | 基础框架搭建（认证/产品/订单/支付） |
| v2.0-2.6 | Phase 2 | Redis 缓存 / ES 搜索 / 评价+目的地+收藏 / Celery / 前端 / 管理后台 |
| v2.7 | 2026-06-05 | 管理后台多语言编辑支持 / 评价后自动通知（Celery） / Google OAuth + Stripe 支付 / 前端 i18n 补全（171键×3语言） / Nginx 独立配置 / WishlistButton 接入 TourCard+TourDetail / Playwright E2E 扩展至 13 个 spec / Dcoker Compose 新增 Nginx+MailHog / 结算页 auth 竞态修复 / 全量回归 346 后端 + 127 E2E 通过 / GitHub v2.7 Release |
| v3.0 | 2026-06-05 | Attractions 收藏（独立 wishlist 表+API） / Attractions 直接下单（门票表+订单扩展+结算页支持） / Destinations Bug 批量修复（产品筛选/点击导航/测试稳定性） / 库存原子递减 + 超卖防护 |
| v3.1 | 2026-06-05 | 逆向操作测试 14 项 + 边界测试 10 项 / 跨模块回归测试 12 项 / 6 个回归 E2E spec / CI 回归安全门禁 / 3 个后端 Bug 修复（mock 支付/字段长度） / PRD v1 产品设计文档（1483 行） / Top Attractions 弹窗（AttractionInfoModal + 媒体轮播） / Admin 景点管理后台（6 个 API + 多语言编辑 + 媒体管理） |
| v3.2 | 2026-06-05 | Admin Tours sort_order 排序字段全栈实现 / 自定制旅程完整功能（多段行程 + 基础服务 + 导语预设 + 报价计算 + 超管管理） / Admin 目的地完整 CRUD / 自定义目的地输入（custom_destination） / 景点选择链接修复（AttractionInfoModal 集成） / 种子数据更新（9 基础服务 + 4 用户 + 225 媒体） |
| v3.3 | 2026-06-06 | 25 个新测试（Admin Destinations CRUD + Custom Tour custom_destination） / i18n MISSING_MESSAGE 修复（ESM 缓存 → 静态 import） / AttractionInfoModal null 防御性修复 / DB schema 同步（nullable 修复 + 表重建） / 异步懒加载修复（lazy="selectin"） / Admin Tours 序列号（area_code-serial 格式 + 自动生成） / Admin Tours 删除按钮（软删除） / Destination area_code 字段 |
| v3.4 | 2026-06-07 | 竞品对标分析（Odynovo Tours 六大维度差距报告 + P0-P3 路线图） / 主题标签系统全栈实现（12 主题 + TourCard 彩色徽章 + 搜索筛选 + Admin 管理） / PRD 更新至 v3.4 |
| v3.5 | 2026-06-07 | 搜索主题修复（ES keyword 映射 + 聚合降级重试） / 北京 Tours 扩展至 30 款产品（半日 10 + 一日 6 + 多日 12，覆盖全部 12 主题） / 全站咨询表单浮动弹窗（InquiryForm 组件，挂载于全局 Layout） / 24/7 电话展示（Header+Footer） / Admin 咨询管理（列表/状态/备注/删除，三语翻译 19 键） / PRD 更新至 v3.5 |
| **v4.0** | **2026-06-07** | **PRD 文档全版本整合** — 汇集 v2.7 至 v3.5 全部功能，补充 Enquiry 模型定义与管理流程，更新种子数据统计至最新值，完善竞品对标进展标记，添加咨询管理功能章节。功能地图 + 数据模型 + API 列表 + 路由表 + 组件树全面同步。 |
| **v4.1** | **2026-06-07** | **全局 InquiryForm + 测试数据清理体系** — InquiryForm 从首页迁移至全局 Layout（所有页面可见）；测试数据清理脚本扩展（覆盖 dup/upd/del 模式 + ES 索引清理）；新增 E2E 后置清理 `zz-cleanup.spec.ts`（DB + ES + Redis 三层验证）；Profile 页面 `userLocale` 变量引用 Bug 修复。后端 467 项通过 / E2E 151 项全通过 / ES 索引 90 文档。 |

---

### 17.3 竞品对标分析：Odynovo Tours 功能差距报告

> **对标日期**: 2026-06-06  
> **对标网站**: [https://www.odynovotours.com/](https://www.odynovotours.com/)  
> **分析范围**: 首页、产品体系、目的地覆盖、营销功能、内容生态、商业模式  
> **核心结论**: Odynovo 是运营 20+ 年的全球定制游运营商，覆盖 80+ 目的地（六大洲），而 Echo Tours 目前仅覆盖 3 个中国城市。两者商业模式不同（人工定制 vs 自助预订），但在产品丰富度、营销转化、内容生态方面存在显著差距。

---

#### 17.3.1 Odynovo 网站信息提取

从 Odynovo 官网提取的关键信息：

| 维度 | 内容 |
|------|------|
| **产品定位** | Tailor-Made Private Tours（定制私家团），Award-Winning 服务 |
| **覆盖范围** | 80+ 目的地，覆盖亚洲、中东、非洲、欧洲、拉丁美洲、大洋洲六大洲 |
| **运营历史** | 20+ 年（2005-2026） |
| **客户满意度** | 98.5% 客户评价为 Excellent |
| **服务语言** | English / Español / Français |
| **联系渠道** | 电话（US/AU）+ 邮件 + 在线表单，24/7 客服 |
| **外部评价** | TripAdvisor / Google / Trustpilot / Product Review |
| **资质认证** | Travelife Partner（可持续旅游认证） |

**导航结构（一级、二级菜单）:**

```
Odynovo 导航结构
├── Destinations（目的地）
│   ├── Popular Destinations（热门目的地 A-Z: Australia / China / Egypt / Greece / India / Italy / Japan / Morocco / Peru / Portugal / South Africa / South Korea / Thailand / The Philippines / Turkey / Vietnam）
│   ├── Japan & Asia（亚洲分区: 东南亚/东亚/中亚/西亚/南亚）
│   ├── Egypt & Middle East（埃及与中东）
│   ├── Morocco & Africa（摩洛哥与非洲）
│   ├── Italy & Europe（意大利与欧洲: 北欧/南欧/西欧）
│   ├── Peru & Latin America（秘鲁与拉美）
│   ├── Australia & Pacific（澳大利亚与太平洋）
│   └── View All Destinations (A-Z)
│
├── Tours（旅游产品）
│   ├── Trending Tours（热门推荐: Early Bird / 日本红叶 / 中国团 / 埃及 / 泰国 / 秘鲁 / 南非 / 埃及+摩洛哥 / 意大利+西班牙+希腊）
│   ├── Travel Styles（旅行风格: Luxury / Women-Only / Festival / Family / Group）
│   └── (Pre-Designed Private Tours 列表)
│
├── Inspiration（灵感）
│   ├── Hot Topic（热门话题: 2026最佳目的地 / 日本花火大会 / 泰国满月派对 / 撒哈拉最佳时间 / 印度节日 / 韩国夏季 / 旅行视频）
│   ├── Guides By Destination（目的地指南: China / Morocco / Egypt / Peru / Greece / Portugal / India / South Korea / Italy / Thailand / Japan / Turkey / Malaysia / Vietnam）
│   ├── Travel Calendar（旅行日历: 按月推荐 + 2026全年）
│   └── More Inspiration & Tips（更多灵感）
│
├── About Us（关于我们）
│   ├── Why Odynovo
│   ├── Reviews（客户评价）
│   ├── Meet Our Team（团队介绍）
│   ├── Awards（奖项展示）
│   ├── Why Private Tour
│   ├── Responsible Travel（Travelife Partner）
│   ├── Our Story（20周年）
│   └── Words from CEO
│
├── Agent Hub（代理商门户）
├── Tailor My Trip（定制旅程入口，全站固定）
└── 语言切换: English / Español / Français
```

**首页页面结构:**

| 区域 | 内容 |
|------|------|
| Header | Logo + 导航栏 + 电话 + Agent Hub + 语言切换 + "Tailor My Trip" 按钮 |
| Hero Banner | 促销标语 + CTA 按钮（当前: "Japan Exclusive Tours" / "Early Booking Deals" / "China Private Tours" / "Best Southeast Asia Tours"） |
| 品牌标语 | "ODYNOVO - Your Way to Discover The World"，介绍文案（80+ destinations, 98.5% excellent） |
| 热门目的地区 | 9 个目的地卡片（Japan / China / Vietnam / Thailand / Italy / Egypt / Morocco / India / Peru）+ "View All Destinations" |
| 热门产品区 | Hottest Private Tours，每个卡片含天数+城市列表+CTA |
| 多国联游区 | Popular Multi-Country Tours（泰柬越/中日/新马+巴厘/埃摩/西葡/秘巴） |
| 主题旅游区 | Tours by Theme（Family / Honeymoon / Festival / Luxury / Women's / Food / Wildlife / Beach） |
| 定制咨询表单 | "Customize Your Own Trip" 表单（Trip Ideas / Email / Phone / Name）+ 电话备选 |
| 博客/指南区 | "See Our Ideas & Tips for Traveling" 文章卡片 |
| 品牌故事区 | "Odynovo – Crafting Unforgettable Journeys for 20+ Years" + 客户评价引用 |
| 客户快照区 | 全球客户旅行照片墙 |
| Newsletter 订阅 | 订阅送 USD 50 Travel Coupon |
| Footer | 热门目的地链接 / Company 链接 / Resources 链接 / 联系方式 / 版权 / Cookie Policy |

---

#### 17.3.2 功能差异全景对比

##### 17.3.2.1 目的地范围 — 最大差距

| 维度 | Odynovo Tours | Echo Tours | 差距级别 |
|------|--------------|------------|----------|
| 目的地数量 | 80+ 全球目的地 | 3 个中国城市（北京/南京/西安） | ❌ P0 |
| 覆盖大洲 | 亚洲、欧洲、非洲、美洲、大洋洲 | 仅中国 | ❌ P0 |
| 多国联游产品 | 泰柬越(15天)、中日(15天)、西葡(12天) 等 | 不支持（产品单一目的地） | ❌ P0 |
| 多语言覆盖 | EN/ES/FR | EN/ZH/ES | ⚠️ 方向不同 |

##### 17.3.2.2 产品体系

| 维度 | Odynovo Tours | Echo Tours | 差距级别 |
|------|--------------|------------|----------|
| 产品类型 | Pre-designed + Fully Tailor-made 混合 | 标准化产品 + 自定制旅程 | ✅ 模式接近 |
| 旅行主题/风格 | Family / Honeymoon / Festival / Luxury / Women-Only / Food / Wildlife / Beach | 仅 `group_tour` / `private_tour` | ❌ P0 |
| 多国联游产品 | 完整的多国联游产品线 | 无 | ❌ P0 |
| 天数在产品列表展示 | 卡片上直接显示 "X Days" | 仅在详情页显示 | ⚠️ P2 |
| 热门/Hot 标签 | HOT 徽章标注热门产品 | 无 | ❌ P1 |
| 早鸟/促销标签 | "Early Bird Deals" 独立分类 | 无 | ❌ P1 |
| 价格展示策略 | 询价模式（不显示具体价格） | 明码标价 | ⚠️ 模式差异 |

##### 17.3.2.3 营销与转化功能

| 功能 | Odynovo Tours | Echo Tours | 差距级别 |
|------|--------------|------------|----------|
| 首页咨询表单 | 底部固定 "Customize Your Own Trip" 表单 | 仅独立的 custom-tour 页面 | ❌ P1 |
| 24/7 电话客服 | 顶部+底部固定显示 US/AU 电话号码 | 无 | ❌ P1 |
| Newsletter 订阅 | 订阅送 $50 优惠券 | 无 | ❌ P1 |
| 旅行视频区 | "Spotlight Travel Videos" 板块 | 无 | ❌ P2 |
| 奖项与认证展示 | 多处显示 award-winning 标识 + Travelife Partner | 无 | ❌ P2 |
| 外部评价聚合 | TripAdvisor/Google/Trustpilot 集成 | 仅内部评价系统 | ❌ P1 |
| 客户成功案例 | 客户旅行照片快照墙 | 无 | ❌ P2 |

##### 17.3.2.4 内容营销体系（CMS）

| 功能 | Odynovo Tours | Echo Tours | 差距级别 |
|------|--------------|------------|----------|
| 博客/旅行指南系统 | 大量目的地指南、旅游攻略文章 | ❌ 完全没有 | ❌ P2 |
| Travel Calendar | 按月推荐旅行目的地 | 无 | ❌ P2 |
| 目的地指南页面 | 每个目的地独立指南 | 无 | ❌ P2 |
| 团队展示 | "Meet Our Team" 专家介绍 | 无 | ❌ P2 |
| 公司故事 | 完整品牌故事、使命、20年历程 | 无 | ❌ P2 |
| 可持续旅游 | Travelife Partner 认证、责任旅游页面 | 无 | ❌ P3 |
| 常见问题 FAQ | 未提取到，推测有 | 无 | ❌ P2 |

##### 17.3.2.5 商业模式差异

```
Odynovo 模式（重人工服务）:              Echo Tours 模式（自助预订）:
用户浏览 → 提交咨询表单 → 旅行专家沟通     用户浏览 → 自助下单 → Stripe 支付
→ 定制方案 → 报价 → 确认 → 支付           → 自动确认 → 出行 → 评价
```

| 维度 | Odynovo | Echo Tours |
|------|---------|------------|
| 获客方式 | 表单询价 + 电话咨询 | 自助浏览 + 搜索 |
| 支付流程 | 人工报价后支付 | 实时库存 + 在线支付 |
| 定制能力 | 人工深度定制（旅行专家） | 系统自定制（多段行程 + 基础服务） |
| 服务密度 | 高（专人跟进） | 低（自助为主） |
| 可扩展性 | 受限于人工团队 | 高（系统自动化） |

##### 17.3.2.6 Echo Tours 有但 Odynovo 不突出的功能

| 功能 | Echo Tours | 说明 |
|------|-----------|------|
| **全文搜索 (Elasticsearch)** | ✅ | Odynovo 网站未显示搜索框 |
| **景点门票系统** | ✅ 独立门票购买 | Odynovo 未强调此功能 |
| **在线支付 (Stripe)** | ✅ 实时支付 | Odynovo 是询价→报价→支付流程 |
| **用户注册/登录** | ✅ JWT + Google SSO | Odynovo 无用户系统（询价匿名模式）|
| **收藏/心愿单** | ✅ 旅游+景点双收藏 | Odynovo 无此功能 |
| **管理后台** | ✅ 完整 Admin Dashboard | Odynovo 是传统旅游公司模式 |
| **自定制旅程** | ✅ 多段行程 + 基础服务 | Odynovo 通过人工客服完成 |

---

#### 17.3.3 差距优先级排序与建议路线图

##### P0 — 核心差距（影响产品定位）

| # | 差距 | 建议方案 | 预估工作量 | 进展 |
|---|------|----------|-----------|------|
| 1 | **目的地范围太窄**（仅 3 个中国城市） | 扩展目的地数据模型，设计全球区域体系（大洲→国家→城市层级），导入 50+ 全球目的地种子数据 | 中 | ⬜ 待实现 |
| 2 | **产品主题/分类缺失** | 新增 `theme` 标签字段，支持 Family / Honeymoon / Luxury / Festival / Wildlife / Beach / Food / Women-Only 等分类 | 小 | ✅ v3.4 |
| 3 | **多目的地/多国联游产品** | 利用现有 `destination_ids` 数组扩展多目的地关联，产品列表按目的地筛选时支持多城市匹配 | 中 | ⬜ 待实现 |

##### P1 — 营销转化（提升转化率）

| # | 差距 | 建议方案 | 预估工作量 | 进展 |
|---|------|----------|-----------|------|
| 4 | **全站咨询表单** | 开发 InquiryForm 组件（全局 Layout 浮动，所有页面可用），收集 Triples: 需求描述、联系方式、人数 | 小 | ✅ v3.5/v4.1 |
| 5 | **24/7 客服电话展示** | 全局 Header/Footer 显示联系电话 + 在线客服入口 | 小 | ✅ v3.5 |
| 6 | **Newsletter 订阅系统** | 集成邮件订阅功能（SendGrid 已有），管理后台管理订阅用户，发送营销邮件 | 中 | ⬜ 待实现 |
| 7 | **Hot/推荐标签系统** | Tour 模型增加 `is_hot` / `is_featured` / `badge` 字段，在前端列表/卡片上显示标签 | 小 | ⬜ 待实现 |
| 8 | **外部评价集成** | 开发 ReviewWidget 组件，展示 TripAdvisor/Google 评分引用（可链接跳转） | 小 | ⬜ 待实现 |

##### P2 — 内容生态与品牌建设

| # | 差距 | 建议方案 | 预估工作量 | 进展 |
|---|------|----------|-----------|------|
| 9 | **博客/旅行指南系统** | 新增 BlogPost 模型（多语言），管理后台文章 CRUD，前端 `/blog/` 路由 + SEO | 大 | ⬜ 待实现 |
| 10 | **Travel Calendar** | 开发季节性推荐页面，基于月份展示最佳目的地 | 中 | ⬜ 待实现 |
| 11 | **公司故事/团队/About 页面** | 静态页面 + 多种语言翻译 | 小 | ⬜ 待实现 |
| 12 | **奖项与认证展示** | 管理后台维护奖项列表，首页/About 页展示 | 小 | ⬜ 待实现 |
| 13 | **旅行视频库** | 支持在 Tour 详情页关联 YouTube/Vimeo 视频，首页展示视频板块 | 中 | ⬜ 待实现 |

##### P3 — 高级商业功能

| # | 差距 | 建议方案 | 预估工作量 | 进展 |
|---|------|----------|-----------|------|
| 14 | **Agent Hub (B2B 代理门户)** | 新增 agent 角色/权限，代理佣金管理，独立 B2B 报价系统 | 大 | ⬜ 待实现 |
| 15 | **早鸟优惠/促销管理** | 促销 `start_date` / `end_date` / `discount` 字段 + 管理后台界面 | 中 | ⬜ 待实现 |
| 16 | **可持续旅游/责任旅游页面** | 静态页面 + 认证标识展示 | 小 | ⬜ 待实现 |
| 17 | **法语/日语等多语言扩展** | 新增 `fr` / `ja` locale，翻译键扩展，翻译表支持新 locale | 中 | ⬜ 待实现 |

---

#### 17.3.4 近期行动建议

**建议优先处理的 3 个高杠杆改进（进度更新）：**

1. **扩展目的地数据模型支持全球区域** — 这是所有后续扩展的基础，且现有数据模型已有不错的抽象（Destination + Translation + `area_code`），只需增加 `country` / `region` / `continent` 层级即可 ⬜ 待实现
2. **新增主题标签系统** — 改动最小（单字段），但对用户体验的提升最明显（家庭游客/蜜月游客一眼找到需要的产品） ✅ v3.4
3. **全站咨询表单 + 电话展示** — 获客成本最低的改进，能显著提高定制旅程的询价转化率 ✅ v3.5/v4.1

**后续高优先级方向（v4.x 规划）：**

1. **多国联游产品支持** — 利用现有 `destination_ids` 数组扩展，支持跨城市/跨国旅游线路
2. **Newsletter 订阅系统** — 集成 SendGrid 邮件订阅，前台收集 + 后台管理 + 批量发送
3. **Hot/推荐标签** — Tour 模型增加 `is_hot` / `badge` 字段，产品列表/详情页醒目标识

**短期不考虑的方向（与 Echo Tours 自助预订定位不符）：**
- Agent Hub B2B 系统（偏离 C 端定位，除非有规划）
- 完全人工客服模式（应坚持系统自动化路线）
- 迁移到询价模式（当前 Stripe 在线支付链路已经成熟）
