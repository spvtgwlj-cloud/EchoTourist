# ═══════════════════════════════════════════════════
# Echo Tours — Makefile
#
# 快速部署：
#   make setup       一键安装 + 构建 + 启动（推荐首次使用）
#   make prod        构建并启动生产环境
#   make dev         启动开发环境
#
# 日常运维：
#   make build       构建生产镜像
#   make up          启动生产服务
#   make down        停止所有服务
#   make restart     重启生产服务
#   make logs        查看日志
#   make psql        进入 PostgreSQL
#   make seed        填充演示数据
#   make test        运行后端测试
#   make clean       清理所有数据
# ═══════════════════════════════════════════════════

.PHONY: help setup build up down restart prod dev logs psql redis test seed clean check-docker

# ── 默认目标 ──────────────────────────────────
help:
	@echo "╔══════════════════════════════════════╗"
	@echo "║      Echo Tours 部署管理工具          ║"
	@echo "╠══════════════════════════════════════╣"
	@echo "║  部署                                ║"
	@echo "║    make setup     一键部署（首次）    ║"
	@echo "║    make prod      构建并启动生产环境  ║"
	@echo "║    make dev       启动开发环境        ║"
	@echo "║                                      ║"
	@echo "║  构建                                ║"
	@echo "║    make build     构建生产镜像        ║"
	@echo "║                                      ║"
	@echo "║  运维                                ║"
	@echo "║    make up        启动生产服务        ║"
	@echo "║    make down      停止所有服务        ║"
	@echo "║    make restart   重启生产服务        ║"
	@echo "║    make logs      查看日志            ║"
	@echo "║                                      ║"
	@echo "║  工具                                ║"
	@echo "║    make psql      进入 PostgreSQL     ║"
	@echo "║    make redis     打开 Redis CLI     ║"
	@echo "║    make seed      填充演示数据        ║"
	@echo "║    make test      运行后端测试        ║"
	@echo "║    make clean     清理所有数据 🧹    ║"
	@echo "╚══════════════════════════════════════╝"

# ── 部署 ──────────────────────────────────────

setup: check-docker
	@bash scripts/setup.sh

prod: check-docker build up
	@echo ""
	@echo "╔══════════════════════════════════════╗"
	@echo "║   🎉 Echo Tours 已启动！             ║"
	@echo "╠══════════════════════════════════════╣"
	@echo "║   Frontend:  http://localhost:80      ║"
	@echo "║   API:       http://localhost/api/v1  ║"
	@echo "║   Docs:      http://localhost/docs    ║"
	@echo "╚══════════════════════════════════════╝"

dev: check-docker
	docker compose up --build -d
	@echo ""
	@echo "╔══════════════════════════════════════╗"
	@echo "║   🚀 开发环境已启动！                 ║"
	@echo "╠══════════════════════════════════════╣"
	@echo "║   Frontend:  http://localhost:3000    ║"
	@echo "║   API:       http://localhost:8000    ║"
	@echo "║   Docs:      http://localhost:8000/docs║"
	@echo "╚══════════════════════════════════════╝"

# ── 构建 ──────────────────────────────────────

build: check-docker
	docker compose -f docker-compose.prod.yml build

# ── 运维 ──────────────────────────────────────

up: check-docker
	docker compose -f docker-compose.prod.yml up -d

down: check-docker
	docker compose -f docker-compose.prod.yml down

restart: down up

logs: check-docker
	docker compose -f docker-compose.prod.yml logs -f

# ── 工具 ──────────────────────────────────────

psql: check-docker
	@docker compose -f docker-compose.prod.yml exec postgres psql -U ${POSTGRES_USER:-postgres} echo_tours

redis: check-docker
	@docker compose -f docker-compose.prod.yml exec redis redis-cli

seed: check-docker
	@docker compose -f docker-compose.prod.yml exec backend python scripts/seed_data.py
	@docker compose -f docker-compose.prod.yml restart frontend
	@echo ""
	@echo "⚠️  演示数据已填充，请刷新浏览器（Cmd+Shift+R 强制刷新）以加载最新数据"

test: check-docker
	@docker compose -f docker-compose.prod.yml run --rm --no-deps backend pytest

clean: check-docker
	@echo "⚠️  即将删除所有容器、卷和镜像..."
	-docker compose -f docker-compose.prod.yml down -v --rmi all 2>/dev/null || true
	-docker compose -f docker-compose.yml down -v --rmi all 2>/dev/null || true
	@echo "✅ 清理完成"

# ── 依赖检查 ──────────────────────────────────

check-docker:
	@command -v docker > /dev/null 2>&1 || { echo "❌ Docker 未安装。请先安装 Docker Desktop: https://docs.docker.com/get-docker/"; exit 1; }
	@docker compose version > /dev/null 2>&1 || { echo "❌ Docker Compose 不可用。请升级 Docker Desktop。"; exit 1; }
