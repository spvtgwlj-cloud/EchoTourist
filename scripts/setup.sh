#!/bin/bash
# ═══════════════════════════════════════════════════
# Echo Tours — 一键式部署脚本
#
# 在任何安装了 Docker 的 Mac / Linux / AWS EC2 上：
#
#   git clone <repo-url>
#   cd Echo-Website
#   bash scripts/setup.sh
#
# 脚本会自动完成：
#   1. 检查 Docker + Docker Compose 环境
#   2. 生成 .env 配置文件（含安全密钥）
#   3. 构建所有生产 Docker 镜像
#   4. 启动所有服务（数据库、缓存、后端、前端等）
#   5. 执行数据库迁移
#   6. 显示访问地址
#
# 可选参数：
#   --skip-build    跳过 Docker 构建（仅启动已有镜像）
#   --skip-migrate  跳过数据库迁移
#   --with-seed     启动后填充演示数据
#   --help          显示帮助信息
# ═══════════════════════════════════════════════════

set -euo pipefail

# ── 颜色 ──────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ── 配置 ──────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="docker-compose.prod.yml"
SKIP_BUILD=false
SKIP_MIGRATE=false
WITH_SEED=false

# ── 帮助信息 ──────────────────────────────────
show_help() {
    cat << EOF
用法: bash scripts/setup.sh [选项]

选项:
  --skip-build    跳过 Docker 构建（仅启动已有镜像）
  --skip-migrate  跳过数据库迁移
  --with-seed     启动后填充演示数据
  --help          显示此帮助信息

示例:
  bash scripts/setup.sh                    # 首次完整部署
  bash scripts/setup.sh --skip-build       # 快速启动已有环境
  bash scripts/setup.sh --with-seed        # 部署并填充演示数据
EOF
    exit 0
}

# ── 解析参数 ──────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-build)   SKIP_BUILD=true;   shift ;;
        --skip-migrate) SKIP_MIGRATE=true; shift ;;
        --with-seed)    WITH_SEED=true;    shift ;;
        --help)         show_help ;;
        *) echo -e "${RED}未知参数: $1${NC}"; show_help ;;
    esac
done

# ═══════════════════════════════════════════════════
# 步骤 1: 检查环境
# ═══════════════════════════════════════════════════
echo -e "${CYAN}[1/6] 检查运行环境...${NC}"

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ 未找到 Docker。请先安装 Docker Desktop。${NC}"
    echo "   macOS: https://docs.docker.com/desktop/install/mac-install/"
    echo "   Linux: curl -fsSL https://get.docker.com | sh"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} Docker $(docker --version | cut -d' ' -f3 | tr -d ',' | head -c 8)"

# 检查 Docker Compose
if ! docker compose version &> /dev/null 2>&1; then
    # 检查旧版 docker-compose
    if command -v docker-compose &> /dev/null; then
        echo -e "  ${YELLOW}⚠ 使用旧版 docker-compose，建议升级 Docker Desktop${NC}"
        COMPOSE_CMD="docker-compose"
    else
        echo -e "${RED}❌ Docker Compose 不可用。${NC}"
        echo "   请升级到最新版 Docker Desktop。"
        exit 1
    fi
else
    COMPOSE_CMD="docker compose"
fi
echo -e "  ${GREEN}✓${NC} Docker Compose 可用"

# 检查内存（仅 macOS）
if [[ "$OSTYPE" == "darwin"* ]]; then
    MEM_TOTAL=$(sysctl -n hw.memsize 2>/dev/null | awk '{print $1/1024/1024/1024}')
    MEM_TOTAL=${MEM_TOTAL%.*}
    if [[ $MEM_TOTAL -lt 4 ]]; then
        echo -e "  ${YELLOW}⚠ 系统内存仅 ${MEM_TOTAL}GB，推荐至少 8GB${NC}"
    else
        echo -e "  ${GREEN}✓${NC} 系统内存: ${MEM_TOTAL}GB"
    fi

    # 检查 Docker Desktop 资源限制
    if command -v jq &> /dev/null; then
        DOCKER_SETTINGS="$HOME/Library/Group Containers/group.com.docker/settings.json"
        if [[ -f "$DOCKER_SETTINGS" ]]; then
            DOCKER_MEM=$(jq -r '.memoryMiB // empty' "$DOCKER_SETTINGS" 2>/dev/null)
            if [[ -n "$DOCKER_MEM" && $DOCKER_MEM -lt 4096 ]]; then
                echo -e "  ${YELLOW}⚠ Docker Desktop 内存仅 ${DOCKER_MEM}MB"
                echo -e "    建议设置为 4GB+: Docker Desktop → Settings → Resources${NC}"
            fi
        fi
    fi
fi

# ═══════════════════════════════════════════════════
# 步骤 2: 配置 .env 文件
# ═══════════════════════════════════════════════════
echo -e "${CYAN}[2/6] 配置环境变量...${NC}"

cd "$PROJECT_DIR"

if [[ ! -f ".env" ]]; then
    if [[ -f ".env.example" ]]; then
        cp .env.example .env
        echo -e "  ${GREEN}✓${NC} 已从 .env.example 创建 .env"

        # 生成安全密钥
        if command -v openssl &> /dev/null; then
            NEW_SECRET=$(openssl rand -hex 32)
            # macOS sed 与 Linux sed 语法不同
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "s/change-me-to-a-long-random-string-at-least-32-chars/$NEW_SECRET/" .env
                sed -i '' "s/dev-secret-key-change-in-production/$NEW_SECRET/" .env
                sed -i '' "s/change-me-in-production-use-a-long-random-string/$NEW_SECRET/" .env
            else
                sed -i "s/change-me-to-a-long-random-string-at-least-32-chars/$NEW_SECRET/" .env
                sed -i "s/dev-secret-key-change-in-production/$NEW_SECRET/" .env
                sed -i "s/change-me-in-production-use-a-long-random-string/$NEW_SECRET/" .env
            fi
            echo -e "  ${GREEN}✓${NC} 已生成随机 JWT 密钥"
        fi

        echo -e "  ${YELLOW}⚠ 请检查并更新以下配置（可选）：${NC}"
        echo -e "      Stripe:    STRIPE_SECRET_KEY, STRIPE_PUBLIC_KEY"
        echo -e "      Google:    GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET"
        echo -e "      SendGrid:  SENDGRID_API_KEY"
        echo -e "      CORS:      CORS_ORIGINS (生产域名)"
        echo -e "  ${YELLOW}  编辑: nano .env${NC}"
    else
        echo -e "${RED}❌ 未找到 .env.example 文件${NC}"
        exit 1
    fi
else
    echo -e "  ${GREEN}✓${NC} .env 已存在，保留现有配置"
fi

# ═══════════════════════════════════════════════════
# 步骤 3: 拉取基础镜像
# ═══════════════════════════════════════════════════
echo -e "${CYAN}[3/6] 预拉取基础镜像...${NC}"

# 并行拉取基础镜像
docker pull postgres:16-alpine &
PID_PG=$!
docker pull redis:7-alpine &
PID_RD=$!
docker pull nginx:alpine &
PID_NG=$!
# ES 镜像较大，后台拉取
docker pull elasticsearch:8.17.0 &
PID_ES=$!

# 等待完成（捕获退出码防止脚本中断）
wait $PID_PG 2>/dev/null && echo -e "  ${GREEN}✓${NC} postgres:16-alpine" || echo -e "  ${YELLOW}⚠ postgres 拉取失败（构建时会自动拉取）${NC}"
wait $PID_RD 2>/dev/null && echo -e "  ${GREEN}✓${NC} redis:7-alpine" || echo -e "  ${YELLOW}⚠ redis 拉取失败${NC}"
wait $PID_NG 2>/dev/null && echo -e "  ${GREEN}✓${NC} nginx:alpine" || echo -e "  ${YELLOW}⚠ nginx 拉取失败${NC}"
wait $PID_ES 2>/dev/null && echo -e "  ${GREEN}✓${NC} elasticsearch:8.17.0" || echo -e "  ${YELLOW}⚠ ES 拉取失败（服务启动时会自动拉取）${NC}"

# ═══════════════════════════════════════════════════
# 步骤 4: 构建 Docker 镜像
# ═══════════════════════════════════════════════════
echo -e "${CYAN}[4/6] 构建生产镜像...${NC}"

if [[ "$SKIP_BUILD" == "true" ]]; then
    echo -e "  ${YELLOW}⏭ 跳过构建（使用已有镜像）${NC}"
else
    echo -e "  ${YELLOW}⏳ 正在构建后端和前端镜像（首次约 3-5 分钟）...${NC}"
    $COMPOSE_CMD -f "$COMPOSE_FILE" build backend frontend celery_worker celery_beat migrations
    echo -e "  ${GREEN}✓${NC} 镜像构建完成"
fi

# ═══════════════════════════════════════════════════
# 步骤 5: 启动服务
# ═══════════════════════════════════════════════════
echo -e "${CYAN}[5/6] 启动服务...${NC}"

$COMPOSE_CMD -f "$COMPOSE_FILE" up -d

# 等待服务就绪
echo -e "  ${YELLOW}⏳ 等待数据库就绪...${NC}"
sleep 5
$COMPOSE_CMD -f "$COMPOSE_FILE" exec -T postgres bash -c \
    'for i in $(seq 1 30); do pg_isready -U postgres -d echo_tours > /dev/null 2>&1 && echo "ready" && exit 0; sleep 2; done; exit 1' 2>/dev/null \
    && echo -e "  ${GREEN}✓${NC} PostgreSQL 已就绪" \
    || echo -e "  ${YELLOW}⚠ PostgreSQL 等待超时（后台可能仍在启动）${NC}"

# 单独运行迁移（如果 compose 中的迁移容器未正确处理）
if [[ "$SKIP_MIGRATE" == "false" ]]; then
    echo -e "  ${YELLOW}⏳ 执行数据库迁移...${NC}"
    # 等待 migrations 容器完成（最多 60 秒）
    for i in $(seq 1 30); do
        STATUS=$($COMPOSE_CMD -f "$COMPOSE_FILE" ps migrations --format json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('State',''))" 2>/dev/null || echo "")
        if [[ "$STATUS" == "exited" ]]; then
            EXIT_CODE=$($COMPOSE_CMD -f "$COMPOSE_FILE" ps migrations --format json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('ExitCode',-1))" 2>/dev/null || echo "-1")
            if [[ "$EXIT_CODE" == "0" ]]; then
                echo -e "  ${GREEN}✓${NC} 数据库迁移完成"
            else
                echo -e "  ${YELLOW}⚠ 迁移退出码 $EXIT_CODE（可能需要手动执行）${NC}"
            fi
            break
        fi
        sleep 2
    done
fi

# ═══════════════════════════════════════════════════
# 步骤 6: 完成
# ═══════════════════════════════════════════════════
echo -e "${CYAN}[6/6] 验证服务状态...${NC}"

sleep 3
$COMPOSE_CMD -f "$COMPOSE_FILE" ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null | head -20

# 健康检查
HEALTH_CHECK=$($COMPOSE_CMD -f "$COMPOSE_FILE" exec -T nginx curl -s -o /dev/null -w "%{http_code}" http://localhost/health 2>/dev/null || echo "000")
if [[ "$HEALTH_CHECK" == "200" ]]; then
    echo -e "  ${GREEN}✓${NC} 后端健康检查通过 (HTTP $HEALTH_CHECK)"
else
    echo -e "  ${YELLOW}⚠ 后端健康检查返回 $HEALTH_CHECK（服务可能仍在启动）${NC}"
fi

# 填充演示数据
if [[ "$WITH_SEED" == "true" ]]; then
    echo -e "  ${YELLOW}⏳ 填充演示数据...${NC}"
    $COMPOSE_CMD -f "$COMPOSE_FILE" exec -T backend python scripts/seed_data.py 2>/dev/null \
        && echo -e "  ${GREEN}✓${NC} 演示数据已填充" \
        || echo -e "  ${YELLOW}⚠ 演示数据填充失败（可稍后手动执行: make seed）${NC}"
fi

# ── 显示访问地址 ──────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   🎉 Echo Tours 部署完成！           ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════╣${NC}"
echo -e "${GREEN}║${NC}   Frontend:  ${CYAN}http://localhost${NC}"
echo -e "${GREEN}║${NC}   API:       ${CYAN}http://localhost/api/v1${NC}"
echo -e "${GREEN}║${NC}   Docs:      ${CYAN}http://localhost/docs${NC}"
echo -e "${GREEN}║${NC}                                      ${NC}"
echo -e "${GREEN}║${NC}   Postgres:  ${CYAN}localhost:${POSTGRES_PORT:-5432}${NC}"
echo -e "${GREEN}║${NC}   Redis:     ${CYAN}localhost:${REDIS_PORT:-6379}${NC}"
echo -e "${GREEN}║${NC}   ES:        ${CYAN}localhost:${ES_PORT:-9200}${NC}"
echo -e "${GREEN}║${NC}                                      ${NC}"
echo -e "${GREEN}║${NC}   管理命令:  ${CYAN}make logs${NC}  ${CYAN}make down${NC}  ${CYAN}make restart${NC}"
echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
