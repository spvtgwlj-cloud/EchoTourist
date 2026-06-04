# 在线旅游平台系统架构设计文档

> 项目：类 Odynovo Tours 全栈旅游网站
> 版本：v1.0
> 日期：2026年6月3日

---

## 目录

1. [架构总览](#1-架构总览)
2. [技术选型](#2-技术选型)
3. [系统架构分层详解](#3-系统架构分层详解)
4. [多语言架构设计](#4-多语言架构设计)
5. [数据库设计](#5-数据库设计)
6. [支付系统设计](#6-支付系统设计)
7. [预订引擎设计](#7-预订引擎设计)
8. [搜索系统设计](#8-搜索系统设计)
9. [安全架构](#9-安全架构)
10. [部署架构](#10-部署架构)
11. [性能优化策略](#11-性能优化策略)
12. [监控与运维](#12-监控与运维)

---

## 1. 架构总览

### 1.1 架构哲学

基于研究结论和行业最佳实践，本项目采用 **"模块化单体优先（Modular Monolith First）"** 策略。

> **核心决策依据**：调研确认，在团队规模<10人、供应商<3家的情况下，直接采用微服务架构会导致开发速度降低4-12倍，基础设施成本增加35-40%。推荐从模块化单体起步，随着业务规模增长逐步拆分。

### 1.2 架构演进路线

```
阶段1 MVP（0-6月）        阶段2 扩展（6-12月）       阶段3 规模化（12-24月）
┌──────────────────┐    ┌─────────────────────┐    ┌──────────────────────┐
│  模块化单体架构    │ →  │  水平拆分关键模块     │ →  │  按领域拆分微服务     │
│                  │    │                     │    │                      │
│  Web App         │    │  Web App            │    │  API Gateway          │
│  + API           │    │  + API              │    │  ├─ Booking Service   │
│  + DB            │    │  + Search(ES独立)    │    │  ├─ Payment Service  │
│  + Cache         │    │  + Queue(消息队列)    │    │  ├─ Search Service   │
│                  │    │  + Worker(异步任务)   │    │  ├─ User Service     │
│  后端团队: 3-5人   │    │                     │    │  ├─ CMS Service      │
│  部署: 2台ECS     │    │  后端团队: 5-8人     │    │  ├─ AI Service       │
│                  │    │  部署: 4台ECS         │    │  └─ Notification     │
└──────────────────┘    └─────────────────────┘    └──────────────────────┘
```

---

## 2. 技术选型

### 2.1 技术栈全景

| 层级 | 技术选择 | 版本 | 选型理由 |
|------|---------|------|---------|
| **前端框架** | Next.js 15 (React 19) | 15.x | SSR/SSG/ISR全支持，优秀的多语言方案，SEO友好 |
| **前端UI** | Tailwind CSS 4 + Shadcn/ui | 4.x | 快速原型，主题一致性好，RTL支持 |
| **状态管理** | Zustand + React Query (TanStack Query) | 5.x | 轻量、简洁、服务端状态缓存 |
| **后端语言** | Python 3.12+ (FastAPI) | 3.12+ | 类型提示、高性能异步、AI生态优势 |
| **API模式** | REST + GraphQL (hybrid) | — | 搜索/浏览用GraphQL，事务操作用REST |
| **主数据库** | PostgreSQL 16 | 16.x | ACID事务、JSON支持、GIS扩展（PostGIS） |
| **搜索引擎** | Elasticsearch 8.x | 8.x | 全文搜索、多语言分析器、地理查询 |
| **缓存** | Redis 7 | 7.x | 会话管理、热点缓存、消息队列 |
| **消息队列** | RabbitMQ / Redis Stream | — | 异步任务（邮件、通知、数据同步） |
| **对象存储** | AWS S3 / GCS / MinIO | — | 图片、文档、备份 |
| **CDN** | CloudFront / Cloud CDN | — | 静态资源加速，全球分发 |
| **容器编排** | Docker + Docker Compose (初期) → Kubernetes (后期) | — | 标准化部署，平滑迁移 |
| **CI/CD** | GitHub Actions | — | 集成测试+自动部署 |
| **监控** | Prometheus + Grafana + Sentry | — | 指标监控+错误追踪 |
| **日志** | ELK Stack (Elasticsearch + Logstash + Kibana) | — | 集中式日志管理 |

### 2.2 前端技术明细

```
Frontend Stack
├── Framework: Next.js 15 (App Router)
├── UI Components: Shadcn/ui + Radix UI Primitives
├── Styling: Tailwind CSS 4 + CSS Modules (scoped)
├── i18n: next-intl (国际化框架)
├── State: Zustand (客户端) + TanStack Query (服务端)
├── Forms: React Hook Form + Zod (表单验证)
├── Maps: Mapbox GL JS / Google Maps API (地图展示)
├── Animation: Framer Motion (交互动效)
├── Analytics: Plausible / Google Analytics 4
├── Testing: Playwright (E2E) + Vitest (UT) + Storybook (UI)
└── PWA: next-pwa (离线能力)
```

### 2.3 后端技术明细

```
Backend Stack
├── Web Framework: FastAPI (ASGI, Python 3.12+)
├── ORM: SQLAlchemy 2.0 + Alembic (迁移)
├── Validation: Pydantic v2 (数据校验)
├── Auth: JWT + OAuth2 (Auth0/Firebase) + OTP
├── Task Queue: Celery + Redis (异步任务)
├── Search Client: Elasticsearch DSL
├── Payment: Stripe + Adyen (支付编排)
├── AI/ML: OpenAI API / Anthropic API + LangChain
├── Email: SendGrid / AWS SES
├── SMS: Twilio
├── Cache: Redis (async ioredis client)
└── Testing: pytest + pytest-asyncio + locust (性能)
```

---

## 3. 系统架构分层详解

### 3.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        客户端层 (Client)                             │
│    ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐   │
│    │  Web App │  │  Mobile  │  │ WeChat   │  │ 第三方API客户端 │   │
│    │ (Next.js)│  │ (React   │  │ MiniProg │  │ (B2B Partners) │   │
│    │          │  │  Native) │  │          │  │                │   │
│    └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────┬────────┘   │
└─────────┼──────────────┼──────────────┼────────────────┼───────────┘
          │              │              │                │
          └──────────────┴──────────────┴────────────────┘
                              │ HTTPS/WSS
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CDN & 负载均衡层                                  │
│    ┌─────────────────┐        ┌──────────────────────────────┐     │
│    │   CloudFront/   │        │      Nginx/Ingress Nginx     │     │
│    │   Cloud CDN     │ ────── │   (TLS Termination+Ratelimit)│     │
│    └─────────────────┘        └──────────────┬───────────────┘     │
└──────────────────────────────────────────────┼─────────────────────┘
                                                │
                                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      API 网关层                                      │
│    ┌──────────────────────────────────────────────────────────┐     │
│    │            FastAPI Gateway / Kong Gateway                │     │
│    │  (路由 | 认证 | 限流 | 日志 | 请求验证 | API版本管理)     │     │
│    └──────────────┬─────────────────────┬─────────────────────┘     │
└───────────────────┼─────────────────────┼───────────────────────────┘
                    │                     │
     ┌──────────────┼───────────┐   ┌─────┴──────────┐
     ▼              ▼           ▼   ▼                ▼
┌─────────┐ ┌────────────┐ ┌──────┐ ┌──────────┐ ┌──────────┐
│ 产品服务  │ │ 用户服务    │ │预订  │ │ 支付     │ │ CMS      │
│ Product  │ │ User       │ │Booking│ │ Payment  │ │ Content  │
│ Service  │ │ Service    │ │Svc   │ │ Service  │ │ Service  │
└────┬─────┘ └─────┬──────┘ └──┬───┘ └────┬─────┘ └────┬─────┘
     │              │           │          │            │
     ▼              ▼           ▼          ▼            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      数据层 (Data Layer)                             │
│  ┌────────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────────────┐  │
│  │PostgreSQL  │ │Redis     │ │Elastic   │ │S3/GCS Object Store  │  │
│  │(主数据库)   │ │(缓存/    │ │search    │ │(图片/文档/日志备份)  │  │
│  │+ Read Repl │ │ Session) │ │(搜索)    │ │                     │  │
│  └────────────┘ └──────────┘ └──────────┘ └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      基础设施层                                      │
│    ┌──────────────┐  ┌─────────────┐  ┌──────────────────────┐    │
│    │  Container   │  │ CI/CD       │  │  Monitoring &        │    │
│    │  Orchestrator│  │ (GitHub     │  │  Observability       │    │
│    │  (K8s/ECS)   │  │  Actions)   │  │  (Prometheus+Grafana)│    │
│    └──────────────┘  └─────────────┘  └──────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 服务模块定义

#### 3.2.1 阶段1（模块化单体模式）

```
单体应用中的模块边界（代码层面隔离，部署层面统一）：
┌──────────────────────────────────────────────────────────────┐
│                    单体应用 (FastAPI)                          │
│  ┌───────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐  │
│  │ product   │ │ user     │ │ booking  │ │ payment       │  │
│  │ module    │ │ module   │ │ module   │ │ module        │  │
│  ├───────────┤ ├──────────┤ ├──────────┤ ├───────────────┤  │
│  │ › tours   │ │ › auth   │ │ › cart   │ │ › checkout   │  │
│  │ › dests   │ │ › user   │ │ › order  │ │ › transaction│  │
│  │ › cats    │ │ › wallet │ │ › confrm │ │ › refund     │  │
│  ├───────────┤ ├──────────┤ ├──────────┤ ├───────────────┤  │
│  │ cms       │ │ search   │ │ notify   │ │ ai            │  │
│  │ module    │ │ module   │ │ module   │ │ module        │  │
│  ├───────────┤ ├──────────┤ ├──────────┤ ├───────────────┤  │
│  │ › pages   │ │ › query  │ │ › email  │ │ › planner    │  │
│  │ › blogs   │ │ › index  │ │ › sms    │ │ › recommend  │  │
│  │ › seo     │ │ › filter │ │ › push   │ │ › translate  │  │
│  └───────────┘ └──────────┘ └──────────┘ └───────────────┘  │
│                                                              │
│  共享层：common/ (DB models, exceptions, utils, configs)     │
└──────────────────────────────────────────────────────────────┘
```

#### 3.2.2 阶段2（水平拆分重点模块）

当出现以下信号时拆分：
- 搜索成为性能瓶颈 → 独立Search Service + ES集群
- 异步任务积压 → 独立Worker + 消息队列
- 支付合规要求隔离 → 独立Payment Service

---

## 4. 多语言架构设计

### 4.1 总体策略

采用 **"代码国际化(i18n) + 内容翻译管理(TMS) + 区域化部署"** 三层架构。

### 4.2 架构设计

```
┌──────────────────────────────────────────────────────────────────┐
│                     i18n 多层翻译架构                              │
│                                                                  │
│  层级1: UI文案（运行时加载）                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  next-intl                                                │   │
│  │  ├─ /messages/zh.json  (中文UI文案)                      │   │
│  │  ├─ /messages/en.json  (英文UI文案)                      │   │
│  │  ├─ /messages/es.json  (西班牙语UI文案)                  │   │
│  │  └─ 运行时按用户locale加载, 支持SSR/SSG                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  层级2: 业务内容（数据库中存储）                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  数据库翻译表设计                                           │   │
│  │  tours 表 ←→ tour_translations 表 (locale, title, desc) │   │
│  │  destinations ←→ dest_translations                       │   │
│  │  categories ←→ category_translations                     │   │
│  │  查询时 JOIN translations WHERE locale = :lang           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  层级3: SEO内容（CMS管理）                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  CMS多语言内容管理                                          │   │
│  │  ├─ 每个页面可创建多个语言版本                               │   │
│  │  ├─ 翻译工作流: 原文→AI预翻译→人工校对→发布               │   │
│  │  └─ 支持按语言配置不同的Meta/OG标签                        │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

### 4.3 多语言SEO策略

```html
<!-- 多语言URL结构 -->
/en/tours/great-wall-hiking         → 英文版
/zh/tours/great-wall-hiking         → 中文版
/es/tours/senderismo-gran-muralla   → 西班牙语版

<!-- hreflang 标签示例 -->
<link rel="alternate" hreflang="en" href="https://example.com/en/tours/great-wall-hiking" />
<link rel="alternate" hreflang="zh" href="https://example.com/zh/tours/great-wall-hiking" />
<link rel="alternate" hreflang="es" href="https://example.com/es/tours/senderismo-gran-muralla" />
<link rel="alternate" hreflang="x-default" href="https://example.com/en/tours/great-wall-hiking" />
```

### 4.4 翻译管理流程

```
┌──────────┐    ┌──────────────┐    ┌──────────┐    ┌──────────┐
│ 创建内容  │ → │ AI预翻译     │ → │ 人工校对  │ → │ 发布上线  │
│ (管理员)  │    │ (LLM API)    │    │ (译员)   │    │          │
└──────────┘    └──────────────┘    └──────────┘    └──────────┘
                                                    │
                                                    ▼
                                            ┌──────────────┐
                                            │ CDN缓存刷新   │
                                            │ + sitemap更新 │
                                            └──────────────┘
```

### 4.5 多语言性能优化（关键）

基于调研结果，Next.js多语言应用在100+locale时SSR时间会从60ms退化到600ms以上。优化策略：

| 优化项 | 方案 | 预期效果 |
|--------|------|---------|
| 翻译文件按需加载 | 只加载当前语言的翻译 | 减少50-70%内存占用 |
| 静态生成(SSG) + ISR | 常用页面预构建，按需更新 | SSR时间降低80% |
| 翻译缓存 | Redis缓存解析后的翻译 | 减少反复解析 |
| 服务端翻译剪枝 | 只传递当前页面实际使用的key | 减少传输量60% |
| CDN边缘计算 | Cloudflare Workers等边缘处理语言重定向 | 0ms冷启动 |

---

## 5. 数据库设计

### 5.1 核心ER关系

```
[tours] 1──N [tour_translations]
[tours] 1──N [tour_dates]        (价格日历)
[tours] 1──N [tour_images]
[tours] N──M [destinations]      (中间表)
[tours] N──M [categories]
[tours] N──M [tags]

[users] 1──N [orders]
[users] 1──N [reviews]
[users] 1──N [wishlists]

[orders] 1──1 [payments]
[orders] N──M [addons]
[orders] 1──N [order_passengers]

[reviews] N──1 [tours]
[reviews] N──1 [users]

[destinations] 1──N [dest_translations]
[categories] 1──N [cat_translations]
```

### 5.2 核心表结构

#### tours（旅游产品表）

```sql
CREATE TABLE tours (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug            VARCHAR(200) NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'draft', -- draft|published|archived
    type            VARCHAR(30) NOT NULL, -- group_tour|private_tour|customizable
    duration_days   SMALLINT NOT NULL,
    duration_nights SMALLINT NOT NULL DEFAULT 0,
    max_pax         SMALLINT, -- 最大成团人数
    min_pax         SMALLINT DEFAULT 1,
    start_price     DECIMAL(10,2), -- 起价（按币种）
    currency        VARCHAR(3) DEFAULT 'USD',
    difficulty      VARCHAR(20), -- easy|moderate|challenging
    highlights      TEXT[], -- Postgres array for structured data
    includes        TEXT[],
    excludes        TEXT[],
    -- 地点信息
    departure_city  VARCHAR(100),
    destination_ids UUID[],
    -- 评分
    avg_rating      DECIMAL(2,1) DEFAULT 0,
    review_count    INTEGER DEFAULT 0,
    -- 元数据
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    published_at    TIMESTAMPTZ,
    -- 索引
    deleted_at      TIMESTAMPTZ -- 软删除
);

-- 核心索引
CREATE INDEX idx_tours_status ON tours(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_tours_slug ON tours(slug);
CREATE INDEX idx_tours_price ON tours(start_price) WHERE status = 'published';
CREATE INDEX idx_tours_duration ON tours(duration_days) WHERE status = 'published';
CREATE INDEX idx_tours_rating ON tours(avg_rating DESC) WHERE status = 'published';
CREATE INDEX idx_tours_destinations ON tours USING GIN(destination_ids);
```

#### tour_translations（产品翻译表）

```sql
CREATE TABLE tour_translations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tour_id     UUID NOT NULL REFERENCES tours(id) ON DELETE CASCADE,
    locale      VARCHAR(10) NOT NULL, -- 'en', 'zh', 'es', 'ja', etc.
    name        VARCHAR(300) NOT NULL,
    subtitle    VARCHAR(500),
    description TEXT,
    itinerary   JSONB,          -- 行程安排的多语言JSON
    meta_title       VARCHAR(200),
    meta_description VARCHAR(300),
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tour_id, locale)
);

CREATE INDEX idx_tour_translations_locale ON tour_translations(locale);
CREATE INDEX idx_tour_translations_name ON tour_translations USING GIN(to_tsvector('simple', name));
```

#### tour_dates（价格日历表）

```sql
CREATE TABLE tour_dates (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tour_id     UUID NOT NULL REFERENCES tours(id) ON DELETE CASCADE,
    start_date  DATE NOT NULL,
    end_date    DATE NOT NULL,
    price_per_pax DECIMAL(10,2) NOT NULL,
    currency    VARCHAR(3) DEFAULT 'USD',
    availability SMALLINT NOT NULL DEFAULT 0, -- 剩余名额
    status      VARCHAR(20) DEFAULT 'available', -- available|limited|sold_out|cancelled
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tour_id, start_date)
);

CREATE INDEX idx_tour_dates_tour_date ON tour_dates(tour_id, start_date);
CREATE INDEX idx_tour_dates_available ON tour_dates(tour_id, start_date) 
    WHERE status = 'available' AND availability > 0;
```

#### orders（订单表）

```sql
CREATE TABLE orders (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_no        VARCHAR(30) UNIQUE NOT NULL, -- 可读订单号: TOUR-20260603-XXXX
    user_id         UUID REFERENCES users(id),
    tour_id         UUID NOT NULL REFERENCES tours(id),
    tour_date_id    UUID REFERENCES tour_dates(id),
    status          VARCHAR(30) NOT NULL DEFAULT 'pending',
    -- pending|confirmed|in_progress|completed|cancelled|refunded
    pax_count       SMALLINT NOT NULL,
    -- 价格信息
    subtotal        DECIMAL(12,2) NOT NULL,
    discount        DECIMAL(12,2) DEFAULT 0,
    tax             DECIMAL(12,2) DEFAULT 0,
    total           DECIMAL(12,2) NOT NULL,
    currency        VARCHAR(3) DEFAULT 'USD',
    -- 联系人
    contact_name    VARCHAR(100),
    contact_email   VARCHAR(200),
    contact_phone   VARCHAR(30),
    special_requests TEXT,
    -- 元数据
    source          VARCHAR(30), -- web|mobile|wechat|api
    locale          VARCHAR(10), -- 下单时的语言
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created ON orders(created_at DESC);
CREATE INDEX idx_orders_no ON orders(order_no);
```

### 5.3 PostgreSQL 扩展与优化

```sql
-- 启用扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";  -- 地理空间查询
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- 模糊搜索支持
CREATE EXTENSION IF NOT EXISTS "citext";   -- 大小写不敏感文本

-- 全文搜索（Elasticsearch作为主力，PostgreSQL作为后备）
-- 使用物化视图加速多语言查询
CREATE MATERIALIZED VIEW mv_tour_search AS
SELECT 
    t.id,
    tt.name,
    tt.description,
    t.slug,
    t.start_price,
    t.avg_rating,
    t.duration_days,
    t.max_pax,
    tt.locale
FROM tours t
JOIN tour_translations tt ON t.id = tt.tour_id
WHERE t.status = 'published' AND t.deleted_at IS NULL;

-- 自动更新 updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_tours_updated_at 
    BEFORE UPDATE ON tours 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

### 5.4 缓存策略

| 数据类型 | 缓存策略 | TTL | 存储 |
|---------|---------|-----|------|
| 产品详情 | Cache-Aside | 1小时 | Redis |
| 热门目的地 | Cache-Aside | 6小时 | Redis |
| 搜索结果 | Cache-Aside | 10分钟 | Redis |
| 用户会话 | Write-Through | 24小时 | Redis |
| 翻译文案 | Cache-Aside | 1小时 | Redis |
| 价格日历 | Cache-Aside | 5分钟 | Redis |
| API频率限制 | Counter | 滑动窗口 | Redis |
| HTML页面 | CDN | 按TTL设置 | CloudFront/CDN |

---

## 6. 支付系统设计

### 6.1 支付架构

```
┌─────────────────────────────────────────────────────────────┐
│                    支付编排层                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Payment Orchestration Service                        │  │
│  │  路由规则: 按金额/地区/币种/支付方式自动选择最优通道   │  │
│  └──────────┬──────────┬──────────┬─────────────────────┘  │
│             │          │          │                        │
│    ┌────────┴──┐ ┌────┴─────┐ ┌──┴────────────┐          │
│    │ Stripe   │ │  Adyen   │ │  本地支付网关   │          │
│    │          │ │          │ │                │          │
│    │ 信用卡   │ │ 全球卡   │ │ 支付宝/微信    │          │
│    │ ApplePay │ │ 本地方法  │ │ Pix(BR)       │          │
│    │ GooglePay│ │ 3DS验证  │ │ SPEI(MX)      │          │
│    └──────────┘ └──────────┘ │ OVO(ID)       │          │
│                              │ GCash(PH)     │          │
│                              └────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 支付方式支持路线图

| 阶段 | 支付方式 | 覆盖地区 |
|------|---------|---------|
| **MVP** | Stripe（信用卡+Apple Pay） | 全球 |
| **P1** | PayPal | 全球（欧美为主） |
| **P1** | 支付宝+微信支付 | 中国 |
| **P1** | 银联国际卡 | 中国+亚太 |
| **P2** | Pix | 巴西 |
| **P2** | Mercado Pago | 拉丁美洲 |
| **P2** | iDEAL | 荷兰 |
| **P2** | Sofort/Klarna | 德国/北欧 |
| **P3** | 加密货币(USDT) | 全球 |

### 6.3 交易处理流程

```
┌──────────┐    ┌───────────┐    ┌──────────┐    ┌───────────┐
│ 用户提交  │ → │ 支付编排层 │ → │ 支付网关  │ → │ 银行/钱包  │
│ 支付请求  │    │ 路由决策   │    │ 3DS验证   │    │ 扣款      │
└──────────┘    └─────┬─────┘    └─────┬────┘    └─────┬─────┘
                       │                │               │
                       ▼                ▼               ▼
                 ┌───────────┐   ┌──────────┐   ┌───────────┐
                 │ 创建交易   │   │ 验证结果  │   │ 确认回调   │
                 │ 记录(pending)│  │ 更新状态  │   │ 通知业务层 │
                 └───────────┘   └──────────┘   └─────┬─────┘
                                                       │
                                                       ▼
                                                ┌───────────┐
                                                │ 更新订单   │
                                                │ 发送确认   │
                                                │ 释放库存   │
                                                └───────────┘
```

### 6.4 关键安全措施

| 措施 | 描述 | 标准 |
|------|------|------|
| **PCI DSS 合规** | 通过Stripe/Adyen处理卡信息，不自持敏感数据 | Level 1 |
| **3DS 验证** | 3D Secure 2.0 强客户认证 | PSD2合规 |
| **Tokenization** | 使用支付令牌替代卡号存储 | PCI DSS |
| **加密** | 传输层TLS 1.3 + 存储层AES-256 | OWASP标准 |
| **风控** | 基于规则的异常交易检测 | 自定义+网关风控 |

---

## 7. 预订引擎设计

### 7.1 库存管理模型

```
                  ┌──────────────────────┐
                  │   库存管理核心模型    │
                  └──────────────────────┘

  固定日期产品（如一日游）      灵活日期产品（如定制游）
  ┌─────────────────────┐   ┌────────────────────────┐
  │ Product A           │   │ Product B（定制游）     │
  │ 日期: 2026-07-01    │   │ 价格: 按实际定制报价    │
  │ 库存: 20            │   │ 库存: 无限制（按需）    │
  │ 价格: $120/人       │   │ 响应: 24小时内确认      │
  └─────────────────────┘   └────────────────────────┘

  多日期产品（如多日团）
  ┌──────────────────────────────────────────────┐
  │ Product C（7日团）                            │
  │ ├─ 出发日期1: 2026-07-05 → 库存 15, $1500/人 │
  │ ├─ 出发日期2: 2026-07-12 → 库存 15, $1500/人 │
  │ └─ 出发日期3: 2026-07-19 → 库存 8, $1500/人  │
  └──────────────────────────────────────────────┘
```

### 7.2 预订状态机

```
                    ┌──────────┐
                    │ 待支付    │
                    │ Pending  │
                    └────┬─────┘
                         │ 支付成功
                         ▼
                    ┌──────────┐
               ┌─── │ 已确认   │ ←── 支付确认/人工确认
               │    │ Confirmed│
               │    └────┬─────┘
               │         │ 临出发
               │         ▼
               │    ┌──────────┐
               │    │ 进行中   │
               │    │ In Prog. │
               │    └────┬─────┘
               │         │ 行程结束
               │         ▼
               │    ┌──────────┐
               │    │ 已完成   │
               │    │Completed │
               │    └──────────┘
               │
               │ 取消流程
               ▼
          ┌──────────┐       ┌──────────┐
          │ 取消请求  │ ───→  │ 已取消   │
          │Cancelling│       │Cancelled │
          └──────────┘       └────┬─────┘
                                  │ 退款
                                  ▼
                            ┌──────────┐
                            │ 已退款   │
                            │ Refunded │
                            └──────────┘
```

### 7.3 并发控制（防止超卖）

```python
# 使用Redis悲观锁+PostgreSQL乐观锁双重保障
async def book_tour(tour_date_id: UUID, pax: int, user_id: UUID):
    lock_key = f"lock:tourt_date:{tour_date_id}"
    
    async with redis.lock(lock_key, timeout=10):
        # 读取最新库存
        tour_date = await db.get(TourDate, tour_date_id)
        
        if tour_date.availability < pax:
            raise InsufficientStockError()
        
        # 乐观锁：确认库存未被其他请求更改
        result = await db.execute(
            UPDATE tour_dates 
            SET availability = availability - :pax
            WHERE id = :id AND availability >= :pax
            RETURNING availability
        )
        
        if not result:
            raise ConcurrentBookingError()
        
        # 创建订单
        order = await create_order(...)
        
    return order
```

---

## 8. 搜索系统设计

### 8.1 Elasticsearch 索引设计

```json
{
  "index": "tours",
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 2,
    "analysis": {
      "analyzer": {
        "tours_combined": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "asciifolding", "edge_ngram"]
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
      "duration_days": { "type": "short" },
      "start_price": { "type": "float" },
      "currency": { "type": "keyword" },
      "avg_rating": { "type": "float" },
      "review_count": { "type": "integer" },
      "difficulty": { "type": "keyword" },
      "max_pax": { "type": "short" },
      "destination_ids": { "type": "keyword" },
      
      "name": {
        "type": "text",
        "analyzer": "tours_combined",
        "fields": {
          "keyword": { "type": "keyword" },
          "ngram": { "type": "text", "analyzer": "ngram_analyzer" }
        }
      },
      "description": { "type": "text", "analyzer": "standard" },
      "destination_name": { "type": "text", "analyzer": "standard" },
      "category_name": { "type": "text", "analyzer": "standard" },
      "tags": { "type": "keyword" },
      
      "highlights": { "type": "text", "analyzer": "standard" },
      "includes": { "type": "text", "analyzer": "standard" },
      
      "locale": { "type": "keyword" },
      "created_at": { "type": "date" },
      "published_at": { "type": "date" }
    }
  }
}
```

### 8.2 搜索功能矩阵

| 功能 | 实现方案 | 优先级 |
|------|---------|--------|
| 全文搜索 | Elasticsearch multi_match | P0 |
| 多语言搜索 | 按locale分索引或用language analyzer | P0 |
| 分面搜索 | Elasticsearch Aggregations | P0 |
| 智能提示 | Search-as-you-type + suggesters | P1 |
| 地理搜索 | PostGIS + Elasticsearch geo_shape | P1 |
| 搜索排序 | 自定义评分函数（价格/评分/热门度） | P1 |
| 个性化排序 | 用户行为权重+协同过滤 | P2 |
| 语义搜索 | Embedding + kNN搜索 | P2 |

---

## 9. 安全架构

### 9.1 安全层次

```
┌──────────────────────────────────────────────────────────┐
│                   安全层次模型                              │
├──────────────────────────────────────────────────────────┤
│  Layer 7: 应用层安全                                      │
│  ├─ JWT + OAuth 2.0 认证                                  │
│  ├─ RBAC 权限控制（管理员/供应商/用户）                    │
│  ├─ CSRF Token 保护                                       │
│  ├─ 输入验证（Pydantic + Zod）                             │
│  └─ Rate Limiting（按用户/IP/API）                         │
├──────────────────────────────────────────────────────────┤
│  Layer 6: API安全                                         │
│  ├─ HTTPS (TLS 1.3)                                       │
│  ├─ CORS 配置                                             │
│  ├─ API Key（B2B场景）                                    │
│  └─ 请求签名验证                                          │
├──────────────────────────────────────────────────────────┤
│  Layer 5: 数据安全                                        │
│  ├─ 数据库加密（TDE）                                     │
│  ├─ 敏感字段加密（AES-256）                                │
│  ├─ 数据脱敏（日志/展示）                                  │
│  └─ 备份加密                                              │
├──────────────────────────────────────────────────────────┤
│  Layer 4: 基础设施安全                                    │
│  ├─ VPC + 私有子网                                       │
│  ├─ Security Groups / Firewall                            │
│  ├─ WAF (Web Application Firewall)                       │
│  └─ DDoS 防护                                            │
├──────────────────────────────────────────────────────────┤
│  Layer 3: 合规与审计                                      │
│  ├─ GDPR / CCPA 合规                                     │
│  ├─ PCI DSS Level 1                                      │
│  ├─ 审计日志（所有关键操作）                               │
│  └─ 数据保留策略                                          │
└──────────────────────────────────────────────────────────┘
```

### 9.2 合规要求

| 法规 | 适用范围 | 要求 | 实现方式 |
|------|---------|------|---------|
| **GDPR** | 欧盟用户 | 数据最小化、明确同意、可删除权 | Cookie Consent + 用户数据管理面板 |
| **CCPA** | 加州用户 | 数据披露/删除权、Opt-out | 隐私中心页面 |
| **PCI DSS** | 信用卡支付 | 不自持卡号、SAQ评估 | 通过Stripe/Adyen处理 |
| **PIPL** | 中国用户 | 数据本地化、跨境传输评估 | 阿里云中国区部署（可选） |
| **LGPD** | 巴西用户 | 类似GDPR | 统一的隐私合规框架 |

---

## 10. 部署架构

### 10.1 AWS 部署架构（推荐首选）

```
┌──────────────────────────────────────────────────────────────────┐
│                        AWS 部署架构                                │
│                                                                  │
│  Route 53 (DNS)                                                  │
│       │                                                          │
│  CloudFront (CDN + WAF + SSL终止)                                │
│       │                                                          │
│  ┌────┴────┐                                                     │
│  │ ALB     │ (Application Load Balancer)                         │
│  └────┬────┘                                                     │
│       │                                                          │
│  ┌────┴──────────────────────────────────────────────────────┐  │
│  │  ECS Fargate (Serverless Container)                       │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ │  │
│  │  │ Web App  │ │ API Task │ │ Worker   │ │ Scheduled    │ │  │
│  │  │ (Next.js)│ │ (FastAPI)│ │ (Celery) │ │ Tasks (Cron) │ │  │
│  │  ├──────────┤ ├──────────┤ ├──────────┤ ├──────────────┤ │  │
│  │  │ auto     │ │ auto     │ │ auto     │ │ on-demand    │ │  │
│  │  │ scaling  │ │ scaling  │ │ scaling  │ │ scaling      │ │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│       │                                                         │
│  ┌────┴──────────────────────────────────────────────────────┐  │
│  │  数据层 (RDS + ElastiCache + OpenSearch + S3)             │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ │  │
│  │  │ RDS      │ │ElastiCache│ │OpenSearch│ │ S3           │ │  │
│  │  │PostgreSQL│ │ Redis    │ │  (ES)    │ │ (Images/Docs)│ │  │
│  │  │ Multi-AZ │ │ Cluster  │ │ Cluster  │ │              │ │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  附加服务:                                                       │
│  ├─ SES (邮件发送)                                               │
│  ├─ SNS (推送通知)                                               │
│  ├─ CloudWatch (监控/日志)                                       │
│  ├─ ACM (SSL证书管理)                                            │
│  ├─ Secrets Manager (密钥管理)                                   │
│  └─ CodePipeline (CI/CD)                                         │
└──────────────────────────────────────────────────────────────────┘
```

### 10.2 谷歌云 (GCP) 部署架构

```
┌──────────────────────────────────────────────────────────────────┐
│                       GCP 部署架构                                │
│                                                                  │
│  Cloud DNS                                                       │
│       │                                                          │
│  Cloud CDN + Cloud Load Balancing (SSL终止)                      │
│       │                                                          │
│  Cloud Armor (WAF + DDoS防护)                                    │
│       │                                                          │
│  ┌────┴──────────────────────────────────────────────────────┐  │
│  │  Google Kubernetes Engine (GKE) / Cloud Run                │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ │  │
│  │  │ Web App  │ │ API Pod  │ │ Worker   │ │ CronJob      │ │  │
│  │  │ (Next.js)│ │ (FastAPI)│ │ (Celery) │ │              │ │  │
│  │  │ Pod      │ │ Pod      │ │ Pod      │ │ Pod          │ │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│       │                                                         │
│  ┌────┴──────────────────────────────────────────────────────┐  │
│  │  数据层                                                     │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ │  │
│  │  │ Cloud SQL│ │ Memory-  │ │ Elastic  │ │ Cloud        │ │  │
│  │  │PostgreSQL│ │ store    │ │ Cloud    │ │ Storage      │ │  │
│  │  │ HA Config│ │ (Redis)  │ │  (ES)    │ │ (Images/Docs)│ │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  附加服务:                                                       │
│  ├─ Cloud Pub/Sub (消息队列)                                     │
│  ├─ Cloud Tasks (任务调度)                                       │
│  ├─ Vertex AI (AI/ML平台)                                        │
│  ├─ Cloud Translation API (翻译服务)                             │
│  ├─ Cloud Monitoring + Logging                                   │
│  ├─ Secret Manager                                               │
│  ├─ Cloud Build (CI/CD)                                          │
│  └─ Cloud Scheduler (定时任务)                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 11. 性能优化策略

### 11.1 前端性能

| 优化项 | 策略 | 目标 |
|--------|------|------|
| 首屏加载 | SSG + ISR 预构建，按需更新 | < 1s LCP |
| 图片优化 | Next.js Image + WebP/AVIF + CDN | < 100KB/图 |
| JS分包 | 按路由分包，减少首屏 bundle | < 150KB JS |
| 字体优化 | 字体子集化 + swap策略 | 无FOUT |
| 多语言 | 按需加载翻译JSON | < 50KB locale数据 |
| 缓存 | Service Worker + 本地缓存 | 离线可访问静态内容 |

### 11.2 后端性能

| 优化项 | 策略 | 目标 |
|--------|------|------|
| 数据库查询 | N+1检测 + 预加载 + 物化视图 | 99% < 50ms |
| API响应 | Redis缓存热门接口 | 99% < 100ms |
| 搜索 | ES查询优化 + 查询结果缓存 | 99% < 200ms |
| 图片处理 | 服务端预缩放 + CDN分发 | < 300ms加载 |
| 异步任务 | Celery + Redis Stream解耦耗时操作 | 非阻塞 |

### 11.3 数据层优化

```
读扩展策略:
┌──────────────┐      ┌──────────────┐
│  主库        │ ───→ │  只读副本x2   │
│  Primary     │      │  Read Replica│
│  (写操作)    │      │  (读操作)    │
└──────────────┘      └──────────────┘

缓存策略:
┌─────────────────────────────────┐
│  缓存层级                       │
│  Layer 1: CDN (静态资源 + 页面) │
│  Layer 2: Redis (API响应 + DB)  │
│  Layer 3: App本地缓存(热数据)    │
└─────────────────────────────────┘

数据库优化:
├─ 分区表: 按月分区orders表（大数据量）
├─ 连接池: PgBouncer (事务级连接池)
└─ 归档: 定期归档历史订单到冷存储
```

---

## 12. 监控与运维

### 12.1 监控体系

| 维度 | 工具 | 指标 |
|------|------|------|
| **应用性能(APM)** | Datadog / Sentry | 延迟、吞吐量、错误率、Apdex |
| **基础设施** | Prometheus + Grafana | CPU/内存/磁盘/网络 |
| **数据库** | pg_stat_statements + RDS监控 | 慢查询、连接数、IOPS |
| **业务指标** | 自定义仪表板 | 订单量、转化率、收入、用户增长 |
| **用户体验** | Google Analytics + RUM | LCP/FID/CLS Core Web Vitals |
| **安全** | WAF日志 + 入侵检测 | 异常请求模式、登录失败 |

### 12.2 关键SLO

| 指标 | 目标 | 测量周期 |
|------|------|---------|
| API可用性 | 99.9% | 月度 |
| 首页加载时间 | < 1.5s (P75) | 每日 |
| 搜索响应时间 | < 300ms (P95) | 每小时 |
| 预订确认时间 | < 2s (P99) | 每小时 |
| 支付成功率 | > 95% | 每日 |
| 支付处理时间 | < 5s (P95) | 每日 |

### 12.3 告警策略

```
Critical (立即响应):
├─ 服务宕机 / 5xx错误率 > 5%
├─ 支付失败率 > 3%
├─ 数据库连接池耗尽
└─ 磁盘空间 < 10%

Warning (工单响应):
├─ API延迟 > 500ms (P95)
├─ 错误率 > 1%
├─ 缓存命中率 < 80%
├─ CPU/内存 > 80%
└─ SSL证书 < 30天过期

Info (通知):
├─ 部署成功/失败
├─ 自动扩缩容事件
├─ 新版本发布
└─ 业务里程碑
```

---

## 附录：技术架构决策记录（ADR）

| ADR | 决策 | 备选方案 | 理由 |
|-----|------|---------|------|
| ADR-001 | 模块化单体 → 逐步拆分微服务 | 初始即微服务 | 团队规模<10，CNCF调查42%后悔微服务 |
| ADR-002 | FastAPI (Python) | Node.js/Go | AI生态优势，类型安全，性能足够 |
| ADR-003 | PostgreSQL + ES + Redis | MongoDB单栈 | ACID事务保障，搜索需求明确 |
| ADR-004 | Next.js SSR/SSG | SPA(React) | SEO关键需求，首屏性能 |
| ADR-005 | Stripe + 本地支付(Adyen) | 单一支付商 | 覆盖全球+本地支付需求 |
| ADR-006 | next-intl i18n | react-i18next | Next.js App Router原生的SSR支持 |

---

> **文档版本**：v1.0 | **最后更新**：2026-06-03
> **维护者**：架构团队
