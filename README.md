# Echo Tours — 全栈旅游预订平台

基于 FastAPI + Next.js 15 的全栈旅游预订平台，支持多语言（中/英/西）、在线预订、支付、搜索、评论、收藏、管理后台。

## 快速开始

**仅需 Docker**，无需本地安装 Python/Node.js：

```bash
git clone https://github.com/spvtgwlj-cloud/EchoTourist.git
cd EchoTourist
bash scripts/setup.sh
```

启动后访问: http://localhost

## 系统要求

- **Docker** 24+（含 Docker Compose 插件）
- **内存** ≥ 4 GB（推荐 8 GB）
- **磁盘** ≥ 10 GB 可用空间

## 管理命令

| 命令 | 说明 |
|------|------|
| `make dev` | 启动开发环境（热重载） |
| `make prod` | 构建并启动生产环境 |
| `make logs` | 查看日志 |
| `make down` | 停止所有服务 |
| `make seed` | 填充演示数据 |
| `make test` | 运行后端测试 |

## 技术栈

| 层 | 技术 |
|---|------|
| 后端 | FastAPI (Python 3.12) |
| 前端 | Next.js 15 (React 19, TypeScript) |
| 数据库 | PostgreSQL 16 |
| 缓存 | Redis 7 |
| 搜索 | Elasticsearch 8.17 |
| 任务队列 | Celery |
| 容器化 | Docker + Docker Compose |

## 部署

- [AWS 部署指南](docs/deployment-aws-guide.md) — 支持 EC2 + Docker Compose / ECS Fargate / GitHub Actions CI/CD
- 一键部署: `bash scripts/deploy.sh --cloud aws`

## 文档

- [部署文档](docs/deployment-aws-guide.md)
- [项目状态](TODO.md) — 详细的功能完成情况

## CI/CD

| 流水线 | 触发 | 操作 |
|--------|------|------|
| CI (`ci.yml`) | Push/PR → main | Lint + 测试 + 构建 |
| CD (`deploy.yml`) | Push → main | 构建镜像 → ghcr.io |
