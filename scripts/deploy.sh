#!/bin/bash
# ═══════════════════════════════════════════════════
# Echo Tours — 生产部署脚本
#
# 用法：
#   bash scripts/deploy.sh                          # 本地部署 (Docker Compose)
#   bash scripts/deploy.sh --cloud aws              # 部署到 AWS ECS
#   bash scripts/deploy.sh --cloud gcp              # 部署到 GCP Cloud Run
#   bash scripts/deploy.sh --cloud ec2              # 部署到 AWS EC2 (远程 SSH)
#
# 选项：
#   --env <prod|staging>    部署环境 (默认: prod)
#   --cloud <aws|gcp|ec2>   云平台 (默认: local)
#   --ssh-user <user>       SSH 用户名 (EC2 部署)
#   --ssh-host <host>       SSH 主机地址 (EC2 部署)
#   --build-only            仅构建镜像，不部署
#   --help                  显示帮助
# ═══════════════════════════════════════════════════

set -euo pipefail

# ── 颜色 ──────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ── 默认值 ────────────────────────────────────
ENVIRONMENT="prod"
CLOUD="local"
BUILD_ONLY=false
SSH_USER=""
SSH_HOST=""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# ── 帮助信息 ──────────────────────────────────
show_help() {
    cat << EOF
Echo Tours — 生产部署脚本

用法:
  bash scripts/deploy.sh [选项]

本地 Docker Compose 部署:
  bash scripts/deploy.sh                          # 构建 + 启动
  bash scripts/deploy.sh --build-only             # 仅构建

AWS ECS 部署:
  bash scripts/deploy.sh --cloud aws --env prod

GCP Cloud Run 部署:
  bash scripts/deploy.sh --cloud gcp --env prod

AWS EC2 远程部署:
  bash scripts/deploy.sh --cloud ec2 --ssh-user ec2-user --ssh-host 1.2.3.4

选项:
  --env <prod|staging>     部署环境
  --cloud <local|aws|gcp|ec2>  目标平台
  --build-only             仅构建镜像
  --ssh-user <user>        SSH 用户名 (EC2)
  --ssh-host <host>        SSH 主机 (EC2)
  --help                   显示帮助
EOF
    exit 0
}

# ── 解析参数 ──────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --env)         ENVIRONMENT="$2";    shift 2 ;;
        --cloud)       CLOUD="$2";          shift 2 ;;
        --build-only)  BUILD_ONLY=true;     shift ;;
        --ssh-user)    SSH_USER="$2";       shift 2 ;;
        --ssh-host)    SSH_HOST="$2";       shift 2 ;;
        --help)        show_help ;;
        *) echo -e "${RED}未知参数: $1${NC}"; show_help ;;
    esac
done

cd "$PROJECT_DIR"

# ── 环境验证 ──────────────────────────────────
if [[ "$CLOUD" == "local" ]]; then
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker 未安装${NC}"
        exit 1
    fi
fi

# ═══════════════════════════════════════════════════
# 本地 Docker Compose 部署
# ═══════════════════════════════════════════════════
deploy_local() {
    echo -e "${CYAN}=== 本地生产部署 (Docker Compose) ===${NC}"

    if [[ ! -f ".env" ]]; then
        echo -e "${YELLOW}⚠ 未找到 .env 文件，运行 setup.sh 创建...${NC}"
        bash "$SCRIPT_DIR/setup.sh"
        return
    fi

    echo -e "  ${YELLOW}⏳ 构建镜像...${NC}"
    docker compose -f docker-compose.prod.yml build

    if [[ "$BUILD_ONLY" == "true" ]]; then
        echo -e "  ${GREEN}✓${NC} 镜像构建完成（未部署）"
        return
    fi

    echo -e "  ${YELLOW}⏳ 启动服务...${NC}"
    docker compose -f docker-compose.prod.yml up -d

    echo -e "  ${GREEN}✓${NC} 服务已启动"
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   🎉 Echo Tours 已就绪！${NC}"
    echo -e "${GREEN}╠══════════════════════════════════════╣${NC}"
    echo -e "${GREEN}║${NC}   Frontend:  ${CYAN}http://localhost${NC}"
    echo -e "${GREEN}║${NC}   API:       ${CYAN}http://localhost/api/v1${NC}"
    echo -e "${GREEN}║${NC}   Docs:      ${CYAN}http://localhost/docs${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
}

# ═══════════════════════════════════════════════════
# AWS ECS 部署
# ═══════════════════════════════════════════════════
deploy_aws() {
    echo -e "${CYAN}=== AWS ECS 部署 ===${NC}"

    # 检查必要的环境变量
    : "${AWS_ACCOUNT:?需要设置 AWS_ACCOUNT 环境变量}"
    : "${AWS_REGION:=us-east-1}"

    AWS_ECR="${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com"

    # 登录 ECR
    echo -e "  ${YELLOW}⏳ 登录 AWS ECR...${NC}"
    aws ecr get-login-password --region "$AWS_REGION" | \
        docker login --username AWS --password-stdin "$AWS_ECR"
    echo -e "  ${GREEN}✓${NC} ECR 登录成功"

    # 构建并推送镜像
    for SERVICE in backend frontend; do
        echo -e "  ${YELLOW}⏳ 构建并推送 ${SERVICE}...${NC}"

        if [[ "$SERVICE" == "backend" ]]; then
            docker build -t "${AWS_ECR}/echo-tours-${SERVICE}:${ENVIRONMENT}" \
                -f src/backend/Dockerfile --target prod src/backend/
        else
            docker build -t "${AWS_ECR}/echo-tours-${SERVICE}:${ENVIRONMENT}" \
                -f src/frontend/Dockerfile --target prod src/frontend/
        fi

        docker push "${AWS_ECR}/echo-tours-${SERVICE}:${ENVIRONMENT}"
        echo -e "  ${GREEN}✓${NC} ${SERVICE} 镜像已推送"
    done

    if [[ "$BUILD_ONLY" == "true" ]]; then
        echo -e "  ${GREEN}✓${NC} 镜像构建并推送完成（未更新 ECS 服务）"
        return
    fi

    # 更新 ECS 服务
    echo -e "  ${YELLOW}⏳ 更新 ECS 服务...${NC}"
    aws ecs update-service --cluster echo-tours-${ENVIRONMENT} \
        --service echo-tours-backend --force-new-deployment --no-cli-pager 2>/dev/null || \
        echo -e "  ${YELLOW}⚠ ECS 服务更新失败（请确认集群/服务名称）${NC}"
    aws ecs update-service --cluster echo-tours-${ENVIRONMENT} \
        --service echo-tours-frontend --force-new-deployment --no-cli-pager 2>/dev/null || \
        echo -e "  ${YELLOW}⚠ ECS 服务更新失败${NC}"

    echo -e "  ${GREEN}✓${NC} ECS 服务已触发重新部署"
    echo -e "  ${YELLOW}⏳ ECS 部署通常需要 2-5 分钟完成${NC}"
}

# ═══════════════════════════════════════════════════
# GCP Cloud Run 部署
# ═══════════════════════════════════════════════════
deploy_gcp() {
    echo -e "${CYAN}=== GCP Cloud Run 部署 ===${NC}"

    : "${GCP_PROJECT:?需要设置 GCP_PROJECT 环境变量}"
    : "${GCP_REGION:=us-central1}"

    GCR_HOST="${GCP_REGION}-docker.pkg.dev"
    GCR_REPO="${GCR_HOST}/${GCP_PROJECT}/echo-tours"

    # 确保 gcloud 已配置
    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}❌ 未安装 gcloud CLI${NC}"
        echo "   安装: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi

    # 登录 Artifact Registry
    echo -e "  ${YELLOW}⏳ 配置 gcloud 认证...${NC}"
    gcloud config set project "$GCP_PROJECT" 2>/dev/null || true

    # 构建并推送
    for SERVICE in backend frontend; do
        echo -e "  ${YELLOW}⏳ 构建并推送 ${SERVICE}...${NC}"
        gcloud builds submit \
            --tag "${GCR_REPO}/${SERVICE}:${ENVIRONMENT}" \
            --machine-type=e2-highcpu-8 \
            --timeout=900 \
            "src/${SERVICE}/" 2>/dev/null || {
            # fallback: 本地构建后推送
            docker build -t "${GCR_REPO}/${SERVICE}:${ENVIRONMENT}" \
                -f "src/${SERVICE}/Dockerfile" --target prod "src/${SERVICE}/"
            docker push "${GCR_REPO}/${SERVICE}:${ENVIRONMENT}"
        }
        echo -e "  ${GREEN}✓${NC} ${SERVICE} 镜像已推送"
    done

    if [[ "$BUILD_ONLY" == "true" ]]; then
        echo -e "  ${GREEN}✓${NC} 镜像已推送（未更新 Cloud Run 服务）"
        return
    fi

    # 部署 Cloud Run
    echo -e "  ${YELLOW}⏳ 部署 Cloud Run...${NC}"
    gcloud run deploy echo-tours-backend \
        --image "${GCR_REPO}/backend:${ENVIRONMENT}" \
        --region "$GCP_REGION" \
        --memory 512Mi \
        --cpu 1 \
        --min-instances 0 \
        --max-instances 5 \
        --allow-unauthenticated \
        --timeout 300 2>/dev/null || echo -e "  ${YELLOW}⚠ 后端部署失败${NC}"

    gcloud run deploy echo-tours-frontend \
        --image "${GCR_REPO}/frontend:${ENVIRONMENT}" \
        --region "$GCP_REGION" \
        --memory 512Mi \
        --cpu 1 \
        --min-instances 0 \
        --max-instances 5 \
        --allow-unauthenticated \
        --timeout 300 2>/dev/null || echo -e "  ${YELLOW}⚠ 前端部署失败${NC}"

    echo -e "  ${GREEN}✓${NC} Cloud Run 部署完成"
    echo -e "  ${YELLOW}ℹ 运行以下命令查看服务 URL:${NC}"
    echo "    gcloud run services list --region $GCP_REGION"
}

# ═══════════════════════════════════════════════════
# AWS EC2 远程部署
# ═══════════════════════════════════════════════════
deploy_ec2() {
    echo -e "${CYAN}=== AWS EC2 远程部署 ===${NC}"

    if [[ -z "$SSH_USER" || -z "$SSH_HOST" ]]; then
        echo -e "${RED}❌ 需要 --ssh-user 和 --ssh-host 参数${NC}"
        exit 1
    fi

    SSH_TARGET="${SSH_USER}@${SSH_HOST}"

    echo -e "  ${YELLOW}⏳ 测试 SSH 连接...${NC}"
    ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$SSH_TARGET" "echo connected" || {
        echo -e "${RED}❌ SSH 连接失败${NC}"
        exit 1
    }
    echo -e "  ${GREEN}✓${NC} SSH 连接成功"

    # 检查远程环境
    echo -e "  ${YELLOW}⏳ 检查远程环境...${NC}"
    ssh "$SSH_TARGET" "command -v docker > /dev/null 2>&1 || { echo 'DOCKER_MISSING'; exit 1; }" || {
        echo -e "  ${YELLOW}⏳ 远程安装 Docker...${NC}"
        ssh "$SSH_TARGET" "curl -fsSL https://get.docker.com | sh && sudo usermod -aG docker $SSH_USER" 2>/dev/null || true
    }

    # 同步项目文件（排除不必要的内容）
    echo -e "  ${YELLOW}⏳ 同步项目文件到远程服务器...${NC}"
    rsync -avz --progress \
        --exclude 'node_modules' \
        --exclude '.next' \
        --exclude '__pycache__' \
        --exclude '.env' \
        --exclude '.venv' \
        --exclude 'venv' \
        --exclude '.git' \
        --exclude '.idea' \
        --exclude '*.log' \
        "$PROJECT_DIR/" "$SSH_TARGET:~/echo-tours/"

    # 远程部署
    echo -e "  ${YELLOW}⏳ 远程执行部署...${NC}"
    ssh "$SSH_TARGET" "cd ~/echo-tours && bash scripts/setup.sh --skip-build" 2>/dev/null || {
        echo -e "  ${YELLOW}⏳ 首次部署，执行完整 setup...${NC}"
        ssh "$SSH_TARGET" "cd ~/echo-tours && bash scripts/setup.sh"
    }

    echo -e "  ${GREEN}✓${NC} EC2 部署完成"
    echo -e "  ${CYAN}   http://${SSH_HOST}${NC}"
}

# ═══════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════
case "$CLOUD" in
    local) deploy_local ;;
    aws)   deploy_aws ;;
    gcp)   deploy_gcp ;;
    ec2)   deploy_ec2 ;;
    *)
        echo -e "${RED}❌ 未知云平台: $CLOUD${NC}"
        echo "   支持: local, aws, gcp, ec2"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}=== 部署完成 ===${NC}"
