`# Echo Tours — AWS 云平台部署指南

> **适用版本**: v2.7+  
> **最后更新**: 2026-07-13（根据实际 ECS 部署经验修订）  
> **目标读者**: 运维 / 后端开发人员  
> **前置要求**: AWS 账号、Docker、Git、基本 Linux 操作

---

## 目录

1. [项目架构概览](#1-项目架构概览)
2. [AWS 架构设计](#2-aws-架构设计)
3. [方式一：从本地目录部署到 AWS](#3-方式一从本地目录部署到-aws)
   - [3.1 EC2 + Docker Compose（推荐低成本方案）](#31-ec2--docker-compose推荐低成本方案)
   - [3.2 ECR + ECS Fargate（全托管方案）](#32-ecr--ecs-fargate全托管方案)
4. [方式二：通过 GitHub Actions 部署到 AWS](#4-方式二通过-github-actions-部署到-aws)
5. [两种部署方式对比](#5-两种部署方式对比)
6. [部署后验证与运维](#6-部署后验证与运维)
7. [常见问题与排错](#7-常见问题与排错)

---

## 1. 项目架构概览

### 1.1 服务组件

Echo Tours 由以下 **8 个服务** 组成，均为 Docker 容器化部署：

| # | 服务 | 基础镜像 | 资源需求 | 依赖 | 说明 |
|---|------|---------|---------|------|------|
| 1 | **nginx** | nginx:alpine | ~50 MB | frontend, backend | 反向代理，统一入口 :80 |
| 2 | **postgres** | postgres:16-alpine | 1-2 GB | — | 主数据库，持久化存储 |
| 3 | **redis** | redis:7-alpine | ~200 MB | — | 缓存 + Celery 消息代理 |
| 4 | **elasticsearch** | elasticsearch:8.17.0 | ~1 GB | — | 全文搜索（JVM heap 512MB） |
| 5 | **migrations** | 项目自建 | — | postgres | 一次性运行，`alembic upgrade head` |
| 6 | **backend** | 项目自建 (Python 3.12) | 300-500 MB | postgres, redis, migrations | FastAPI uvicorn workers |
| 7 | **frontend** | 项目自建 (Node 20) | 300-500 MB | backend | Next.js SSR（dev 模式更高） |
| 8 | **celery_worker** | 同 backend 镜像 | ~200 MB | postgres, redis | 异步任务 |
| 9 | **celery_beat** | 同 backend 镜像 | ~100 MB | redis | 定时调度器 |

> **实测最低总内存**: ~4.5 GB（含 ES）/ ~3 GB（不含 ES）
>
> **推荐生产配置**: **8 GB RAM，2 vCPU+**（`t4g.large` 或 `t3a.large`）
>
> ⚠️ 2 GB 实例（如 `t4g.small`）在开启 ES 后会触发 OOM Kill，建议至少 4 GB。

### 1.2 网络架构（Docker Compose 内部）

```
                         ┌─────────────┐
                         │   nginx:80   │  ← 统一入口
                         └──────┬──────┘
                    ┌───────────┼───────────┐
                    ▼                       ▼
             ┌──────────┐          ┌──────────────┐
             │ frontend │          │   backend    │
             │ :3000    │          │   :8000      │
             └──────────┘          └──────┬───────┘
                    ┌─────────────────────┼─────────────────────┐
                    ▼                     ▼                     ▼
             ┌──────────┐          ┌──────────┐          ┌──────────┐
             │ postgres │          │  redis   │          │  ES      │
             │ :5432    │          │  :6379   │          │  :9200   │
             └──────────┘          └──────────┘          └──────────┘
                                            │
                                     ┌──────┴──────┐
                                     │   celery_   │
                                     │   worker    │
                                     └─────────────┘
```

### 1.3 请求路由（Nginx 规则）

| 路径 | 目标 | 说明 |
|------|------|------|
| `/api/*` | backend → :8000 | REST API |
| `/docs`, `/openapi.json` | backend → :8000 | API 文档 |
| `/health` | backend → :8000 | 健康检查 |
| `/_next/webpack-hmr` | frontend → :3000 | WebSocket（开发用） |
| `/*`（其他） | frontend → :3000 | SSR 页面 |

---

## 2. AWS 架构设计

### 2.1 推荐架构（中高成本 → 上到下成本递减）

```
                          ┌─────────────┐
                          │  Route 53   │  → echo-tours.com
                          └──────┬──────┘
                                 ▼
                          ┌─────────────┐
                          │   ACM SSL   │  → *.echo-tours.com
                          └──────┬──────┘
                                 ▼
                          ┌─────────────┐
                          │   ALB :443  │  → 应用负载均衡
                          └──────┬──────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
          ┌─────────────────┐      ┌─────────────────┐
          │  ECS Fargate    │      │  ECS Fargate    │
          │  - frontend     │      │  - backend      │
          │  - nginx(可选)  │      │  - celery_worker│
          └─────────────────┘      │  - celery_beat  │
                    │              └────────┬────────┘
                    │                       │
                    ▼                       ▼
          ┌─────────────────┐      ┌─────────────────┐
          │   RDS for       │      │  ElastiCache    │
          │   PostgreSQL    │      │  for Redis      │
          └─────────────────┘      └─────────────────┘
                    │
                    ▼
          ┌─────────────────┐
          │   OpenSearch    │  → 可选
          └─────────────────┘
```

### 2.2 AWS 服务映射

| 项目服务 | AWS 方案 A（省钱版） | AWS 方案 B（全托管版） | 方案 B 预估月费 |
|---------|-------------------|---------------------|---------------|
| **nginx** | EC2 内置 | ALB 替代 | ~$18 |
| **postgres** | EC2 容器内 | RDS PostgreSQL (db.t4g.micro) | ~$15 |
| **redis** | EC2 容器内 | ElastiCache Redis (cache.t4g.micro) | ~$13 |
| **elasticsearch** | EC2 容器内 | OpenSearch (t3.small.search) | ~$18 |
| **backend** | EC2 容器内 | ECS Fargate (0.5vCPU, 1GB) x 2 | ~$30 |
| **frontend** | EC2 容器内 | ECS Fargate (0.5vCPU, 1GB) | ~$15 |
| **celery_worker** | EC2 容器内 | ECS Fargate (0.25vCPU, 512MB) | ~$8 |
| **celery_beat** | EC2 容器内 | 合并到 worker 任务 | 含在上方 |
| **容器注册** | — | ECR (基础存储费) | ~$1 |
| **负载均衡** | — | ALB (最少 1 个 LCU) | ~$18 |
| **DNS** | — | Route 53 (托管区) | ~$0.5 |

> **方案 A 预估月费**: **~$35–55**（t4g.small EC2 + EBS）
> **方案 B 预估月费**: **~$130–180**（全托管，不含流量费）
> **节省提示**: 关闭 Elasticsearch（全栈搜索降级为数据库搜索），可再省 ~$18/月

### 2.3 VPC 网络规划

```
┌──────────────────────────────────────────────────────────┐
│  VPC: 10.0.0.0/16                                        │
│                                                           │
│  ┌────────────────────┐   ┌────────────────────────────┐  │
│  │  公有子网 (Public)   │   │   私有子网 (Private)         │  │
│  │  10.0.1.0/24        │   │   10.0.2.0/24              │  │
│  │                     │   │                            │  │
│  │  - NAT Gateway      │   │  - ECS 任务（backend）      │  │
│  │  - ALB              │   │  - ECS 任务（celery）       │  │
│  │  - Bastion Host     │   │  - RDS                     │  │
│  │  (方案 A: EC2 在此)  │   │  - ElastiCache             │  │
│  └────────────────────┴─┐   │  - OpenSearch             │  │
│                          │   └────────────┬───────────────┘  │
│                          │                │                  │
│                          ▼                ▼                  │
│                    ┌─────────────────────────────┐          │
│                    │  ECR (容器镜像仓库)            │          │
│                    └─────────────────────────────┘          │
└──────────────────────────────────────────────────────────┘
```

### 2.4 安全组规划

| 安全组 | 入站规则 | 出站规则 | 关联资源 |
|--------|---------|---------|---------|
| **sg-alb** | :443 (0.0.0.0/0) | 全部 | ALB |
| **sg-ecs** | :3000 (仅 sg-alb), :8000 (仅 sg-alb) | 全部 | ECS 任务 |
| **sg-rds** | :5432 (sg-ecs) | 全部 | RDS |
| **sg-redis** | :6379 (sg-ecs) | 全部 | ElastiCache |
| **sg-es** | :9200 (sg-ecs) | 全部 | OpenSearch |
| **sg-ec2** (方案 A) | :80 (0.0.0.0/0), :22 (你的 IP) | 全部 | EC2 |

---

## 3. 方式一：从本地目录部署到 AWS

### 3.1 EC2 + Docker Compose（推荐低成本方案）

> **适合场景**: 预算有限、运维人力少、希望最大程度复用现有 `docker-compose.prod.yml`  
> **核心思路**: 将项目文件 rsync 到 EC2，在 EC2 上直接运行 Docker Compose

#### 3.1.1 前置准备

```bash
# 1. 安装 AWS CLI
# macOS:
brew install awscli
# Linux:
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install

# 2. 配置 AWS 凭证
aws configure
# AWS Access Key ID [None]: AKIA...
# AWS Secret Access Key [None]: ...
# Default region name [None]: ap-southeast-1  # 新加坡，或 ap-northeast-1 东京
# Default output format [None]: json

# 3. 安装 Docker（如果本地没有）
docker --version  # 确认已安装
```

#### 3.1.2 第一步：创建 EC2 实例

```bash
# 参数说明（根据实际需要调整）
export AWS_REGION="ap-southeast-1"
export INSTANCE_NAME="echo-tours-prod"
export KEY_NAME="echo-tours-key"

# 1. 创建密钥对（用于 SSH 登录）
aws ec2 create-key-pair \
  --key-name "$KEY_NAME" \
  --query 'KeyMaterial' \
  --output text > ~/.ssh/${KEY_NAME}.pem
chmod 400 ~/.ssh/${KEY_NAME}.pem

# 2. 创建安全组
SG_ID=$(aws ec2 create-security-group \
  --group-name "echo-tours-sg" \
  --description "Echo Tours production" \
  --query 'GroupId' \
  --output text)

# 3. 添加入站规则
aws ec2 authorize-security-group-ingress \
  --group-id "$SG_ID" \
  --protocol tcp --port 80 --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-id "$SG_ID" \
  --protocol tcp --port 22 --cidr $(curl -s ifconfig.me)/32  # 仅允许你当前的 IP

# 4. 启动 EC2 实例（t4g.small = ARM Graviton，便宜）
INSTANCE_ID=$(aws ec2 run-instances \
  --image-id resolve:ssm:/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64 \
  --instance-type t4g.small \
  --key-name "$KEY_NAME" \
  --security-group-ids "$SG_ID" \
  --block-device-mappings 'DeviceName=/dev/xvda,Ebs={VolumeSize=20,VolumeType=gp3}' \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME}]" \
  --query 'Instances[0].InstanceId' \
  --output text)

# 5. 分配弹性 IP（保持重启后 IP 不变）
EIP=$(aws ec2 allocate-address --query 'PublicIp' --output text)
aws ec2 associate-address --instance-id "$INSTANCE_ID" --public-ip "$EIP"

echo "EC2 实例 IP: $EIP"
echo "SSH 命令: ssh -i ~/.ssh/${KEY_NAME}.pem ec2-user@$EIP"
```

#### 3.1.3 第二步：在 EC2 上初始化环境

```bash
# SSH 登录
ssh -i ~/.ssh/${KEY_NAME}.pem ec2-user@$EIP

# 安装 Docker（Amazon Linux 2023）
sudo dnf update -y
sudo dnf install -y docker
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ec2-user  # 登出重登录生效

# 安装 Docker Compose
# Amazon Linux 2023 推荐安装独立版 docker-compose（兼容性最好）
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 也尝试安装插件版（两者可共存）
sudo dnf install -y docker-compose-plugin 2>/dev/null || true

# 升级 Docker Buildx（新版 docker compose 需要 buildx >= 0.17.0）
BUILDX_VERSION=$(curl -s https://api.github.com/repos/docker/buildx/releases/latest | grep "tag_name" | cut -d'"' -f4)
ARCH=$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/')
curl -LO "https://github.com/docker/buildx/releases/download/${BUILDX_VERSION}/buildx-${BUILDX_VERSION}.linux-${ARCH}"
mkdir -p ~/.docker/cli-plugins
chmod +x buildx-${BUILDX_VERSION}.linux-${ARCH}
mv buildx-${BUILDX_VERSION}.linux-${ARCH} ~/.docker/cli-plugins/docker-buildx

# 验证
docker --version
docker-compose --version
docker buildx version
```

> **⚠ 重要**: SSH 登出后重新登录，使 `sudo usermod` 生效：
> ```bash
> exit
> ssh -i ~/.ssh/${KEY_NAME}.pem ec2-user@$EIP
> docker info  # 确认无需 sudo 也能运行
> ```
>
> **⚠ 注意命令差异**: `docker-compose`（独立版，带连字符）和 `docker compose`（插件版，空格）功能相同。本文档统一使用 `docker compose`，如果系统只装了独立版，请替换为 `docker-compose`。

#### 3.1.4 第三步：从本地部署到 EC2

**方法 A：使用 rsync 直接推送（推荐）**

```bash
# 在本地开发机器上执行

# 同步项目文件到 EC2（排除不必要的文件）
rsync -avz --progress \
  --exclude 'node_modules' \
  --exclude '.next' \
  --exclude '__pycache__' \
  --exclude '.venv' \
  --exclude 'venv' \
  --exclude '.git' \
  --exclude '.idea' \
  --exclude '*.log' \
  --exclude '.env' \
  -e "ssh -i ~/.ssh/${KEY_NAME}.pem" \
  ./ ec2-user@$EIP:~/echo-tours/
```

**方法 B：Git clone（EC2 上直接拉取仓库）**

```bash
# SSH 到 EC2 后执行
ssh -i ~/.ssh/${KEY_NAME}.pem ec2-user@$EIP

# 安装 Git
sudo dnf install -y git

# 克隆仓库（必须使用 Personal Access Token，密码认证已禁用）
# 格式: git clone https://<token>@github.com/<org>/<repo>.git
git clone https://ghp_xxxxxxxxxxxx@github.com/你的用户名/EchoTourist.git ~/echo-tours
cd ~/echo-tours
```

> ⚠️ GitHub 从 2021 年 8 月起不再支持密码认证。必须使用 **Personal Access Token (PAT)**：
> 1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
> 2. 生成新 token，勾选 `repo` 权限
> 3. Fine-grained token 需额外设置 **Contents: Read and Write** 才能 push

#### 3.1.5 第四步：配置环境变量与部署

```bash
# SSH 到 EC2
ssh -i ~/.ssh/${KEY_NAME}.pem ec2-user@$EIP

cd ~/echo-tours

# 创建 .env 文件
# 方式 1: 从 .env.example 复制并修改
cp .env.example .env
nano .env

# ⚠ 必须修改的关键配置项：
#   DATABASE_URL        → postgresql+asyncpg://...（EC2 内的 postgres 会自动配置）
#   SECRET_KEY          → 运行 openssl rand -hex 32 生成
#   CORS_ORIGINS        → http://你的域名或IP
#   FRONTEND_URL        → http://你的域名或IP

# 方式 2: 如果已在本地准备好 .env，scp 上传
# scp -i ~/.ssh/${KEY_NAME}.pem .env ec2-user@$EIP:~/echo-tours/.env
```

**生成安全的 SECRET_KEY：**

```bash
# 在 EC2 上执行
openssl rand -hex 32
# 复制输出，粘贴到 .env 的 SECRET_KEY 字段
```

**使用 setup.sh 一键部署（推荐）：**

```bash
# 在 EC2 上执行
cd ~/echo-tours
bash scripts/setup.sh --with-seed     # --with-seed 会在部署后填充演示数据
```

setup.sh 会自动完成：
1. ✅ 检查 Docker + Docker Compose
2. ✅ 判断 .env 是否存在
3. ✅ 拉取基础镜像（postgres, redis, nginx, ES）
4. ✅ 构建后端和前端生产镜像
5. ✅ 启动全部 8 个服务
6. ✅ 执行数据库迁移（alembic upgrade head）
7. ✅ 验证健康检查
8. ✅ 填充演示数据（如指定 `--with-seed`）

**或手动分步执行：**

```bash
# 构建镜像
docker compose -f docker-compose.prod.yml build backend frontend celery_worker celery_beat migrations

# 启动所有服务
docker compose -f docker-compose.prod.yml up -d

# 查看状态
docker compose -f docker-compose.prod.yml ps

# 验证健康检查
curl -s http://localhost/health
```

#### 3.1.6 完整一键部署脚本

你也可以直接使用项目自带 `scripts/deploy.sh`：

```bash
# 本地执行（会自动 rsync → SSH → setup）
bash scripts/deploy.sh \
  --cloud ec2 \
  --ssh-user ec2-user \
  --ssh-host $EIP \
  --env prod
```

> 该脚本会：测试 SSH 连接 → 检查远程 Docker → 同步项目文件 → 远程执行 setup.sh

#### 3.1.7 配置 Nginx 和域名（可选）

如果需要绑定自定义域名并配置 SSL：

```bash
# 1. 购买域名后，在 Route 53 创建 A 记录指向 EC2 的弹性 IP
#   记录类型: A - IPv4 address
#   值: $EIP（你的 EC2 弹性 IP）

# 2. 安装 certbot 自动申请 SSL 证书
sudo dnf install -y certbot python3-certbot-nginx

# 3. 申请证书（需要域名已解析）
sudo certbot --nginx -d echo-tours.com -d www.echo-tours.com

# 4. 证书自动续期
sudo crontab -l | { cat; echo "0 3 * * * /usr/bin/certbot renew --quiet"; } | sudo crontab -

# 5. 修改 nginx.conf 监听 443 + 80 重定向
# 或使用 ALB + ACM（方式二会详细介绍）
```

#### 3.1.8 EC2 部署的系统服务化

让 Docker Compose 随系统自动启动：

```bash
# 创建 systemd 服务
sudo tee /etc/systemd/system/echo-tours.service << 'EOF'
[Unit]
Description=Echo Tours Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ec2-user/echo-tours
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml down
StandardOutput=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable echo-tours
sudo systemctl start echo-tours
```

---

### 3.2 ECR + ECS Fargate（全托管方案）

> **适合场景**: 预算充足、需要高可用、不想管理服务器
> **核心思路**: 本地构建镜像 → 推送至 ECR → ECS Fargate 部署

#### 3.2.1 第一步：创建 ECR 仓库

```bash
export AWS_REGION="ap-southeast-1"
export AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)

# 创建两个镜像仓库
aws ecr create-repository --repository-name echo-tours/backend \
  --image-scanning-configuration scanOnPush=true

aws ecr create-repository --repository-name echo-tours/frontend \
  --image-scanning-configuration scanOnPush=true

# 验证
aws ecr describe-repositories --query 'repositories[].repositoryUri'
```

#### 3.2.2 第二步：本地构建并推送镜像到 ECR

```bash
# 登录 ECR
aws ecr get-login-password --region "$AWS_REGION" | \
  docker login --username AWS --password-stdin \
  "$AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com"

# 构建并推送后端镜像
docker build -t echo-tours/backend:latest -f src/backend/Dockerfile --target prod src/backend/
docker tag echo-tours/backend:latest $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/echo-tours/backend:latest
docker push $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/echo-tours/backend:latest

# 构建并推送前端镜像
docker build \
  --build-arg NEXT_PUBLIC_API_URL= \
  --build-arg NEXT_PUBLIC_STRIPE_PUBLIC_KEY=你的公钥 \
  -t echo-tours/frontend:latest -f src/frontend/Dockerfile --target prod src/frontend/
docker tag echo-tours/frontend:latest $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/echo-tours/frontend:latest
docker push $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/echo-tours/frontend:latest
```

也可以使用项目自带脚本：

```bash
export AWS_ACCOUNT="你的账号ID"
export AWS_REGION="ap-southeast-1"

bash scripts/deploy.sh --cloud aws --build-only
```

> 如需 `deploy.sh` 推送后也更新 ECS 服务，先创建好 ECS 集群和服务，再运行不带 `--build-only` 的脚本。

#### 3.2.3 第三步：创建托管基础服务

**创建 RDS PostgreSQL：**

```bash
# 创建子网组
aws rds create-db-subnet-group \
  --db-subnet-group-name echo-tours-rds-subnet \
  --subnet-ids subnet-xxx subnet-yyy \
  --db-subnet-group-description "Echo Tours RDS Subnet"

# 创建 RDS 实例（db.t4g.micro 是免费套餐级别）
aws rds create-db-instance \
  --db-instance-identifier echo-tours-postgres \
  --db-instance-class db.t4g.micro \
  --engine postgres \
  --engine-version 16.3 \
  --master-username echo_tours_admin \
  --master-user-password '你的强密码' \
  --allocated-storage 20 \
  --storage-type gp3 \
  --db-subnet-group-name echo-tours-rds-subnet \
  --db-name echo_tours \
  --backup-retention-period 7 \
  --deletion-protection \
  --tags Key=Name,Value=EchoToursPostgres

# 等待创建完成（约 5-8 分钟）
aws rds wait db-instance-available \
  --db-instance-identifier echo-tours-postgres

# 获取端点地址
RDS_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier echo-tours-postgres \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text)
echo "RDS Endpoint: $RDS_ENDPOINT"  # 例如: echo-tours-postgres.xxx.ap-southeast-1.rds.amazonaws.com
```

**创建 ElastiCache Redis：**

```bash
# 创建子网组
aws elasticache create-cache-subnet-group \
  --cache-subnet-group-name echo-tours-redis-subnet \
  --cache-subnet-group-description "Echo Tours Redis Subnet" \
  --subnet-ids subnet-xxx subnet-yyy

# 创建 Redis 集群（cache.t4g.micro）
aws elasticache create-cache-cluster \
  --cache-cluster-id echo-tours-redis \
  --cache-node-type cache.t4g.micro \
  --engine redis \
  --engine-version 7.1 \
  --num-cache-nodes 1 \
  --cache-subnet-group-name echo-tours-redis-subnet \
  --tags Key=Name,Value=EchoToursRedis

# 等待创建完成（约 5 分钟）
aws elasticache wait cache-cluster-available \
  --cache-cluster-id echo-tours-redis

# 获取端点地址
REDIS_ENDPOINT=$(aws elasticache describe-cache-clusters \
  --cache-cluster-id echo-tours-redis \
  --show-cache-node-info \
  --query 'CacheClusters[0].CacheNodes[0].Endpoint.Address' \
  --output text)
echo "Redis Endpoint: $REDIS_ENDPOINT"  # 例如: echo-tours-redis.xxx.ng.0001.apse1.cache.amazonaws.com
```

**创建 OpenSearch（可选）：**

```bash
aws opensearch create-domain \
  --domain-name echo-tours-search \
  --engine-version OpenSearch_2.11 \
  --cluster-config 'InstanceType=t3.small.search,InstanceCount=1' \
  --ebs-options 'EBSEnabled=true,VolumeSize=20,VolumeType=gp3' \
  --vpc-options 'SubnetIds=subnet-xxx,SubnetIds=subnet-yyy' \
  --access-policies '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"AWS":"*"},"Action":"es:ESHttp*","Resource":"arn:aws:es:ap-southeast-1:账号ID:domain/echo-tours-search/*"}]}'

ES_ENDPOINT=$(aws opensearch describe-domain \
  --domain-name echo-tours-search \
  --query 'DomainStatus.Endpoint' \
  --output text)
echo "OpenSearch Endpoint: $ES_ENDPOINT"
```

#### 3.2.4 第四步：创建 ALB 与应用环境

**创建 Application Load Balancer：**

```bash
# 创建安全组
SG_ALB_ID=$(aws ec2 create-security-group \
  --group-name echo-tours-alb-sg \
  --description "ALB for Echo Tours" \
  --vpc-id vpc-xxx \
  --query 'GroupId' --output text)
aws ec2 authorize-security-group-ingress \
  --group-id "$SG_ALB_ID" \
  --protocol tcp --port 443 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress \
  --group-id "$SG_ALB_ID" \
  --protocol tcp --port 80 --cidr 0.0.0.0/0

# 创建目标组（后端：backend:8000 → target group port 8000）
aws elbv2 create-target-group \
  --name echo-tours-backend-tg \
  --protocol HTTP --port 8000 \
  --target-type ip \
  --vpc-id vpc-xxx \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3

# 创建目标组（前端：frontend:3000 → target group port 3000）
aws elbv2 create-target-group \
  --name echo-tours-frontend-tg \
  --protocol HTTP --port 3000 \
  --target-type ip \
  --vpc-id vpc-xxx \
  --health-check-path / \
  --health-check-interval-seconds 30

# 创建 ALB
ALB_ARN=$(aws elbv2 create-load-balancer \
  --name echo-tours-alb \
  --subnets subnet-xxx subnet-yyy \
  --security-groups "$SG_ALB_ID" \
  --scheme internet-facing \
  --type application \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text)

# 获取 ALB DNS 名称
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --load-balancer-arns "$ALB_ARN" \
  --query 'LoadBalancers[0].DNSName' \
  --output text)
echo "ALB DNS: $ALB_DNS"  # 例如: echo-tours-alb-xxx.ap-southeast-1.elb.amazonaws.com
```

#### 3.2.5 第五步：创建 ECS 集群与服务

**创建 ECS 集群：**

```bash
aws ecs create-cluster --cluster-name echo-tours-prod
```

**注册任务定义（后端 + Celery 共享此定义）：**

```bash
# 后端任务定义
cat > backend-task-def.json <<EOF
{
  "family": "echo-tours-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::${AWS_ACCOUNT}:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/echo-tours/backend:latest",
      "essential": true,
      "portMappings": [{"containerPort": 8000, "protocol": "tcp"}],
      "environment": [
        {"name": "DEBUG", "value": "false"},
        {"name": "DATABASE_URL", "value": "postgresql+asyncpg://echo_tours_admin:密码@${RDS_ENDPOINT}:5432/echo_tours"},
        {"name": "DATABASE_URL_SYNC", "value": "postgresql://echo_tours_admin:密码@${RDS_ENDPOINT}:5432/echo_tours"},
        {"name": "REDIS_URL", "value": "redis://${REDIS_ENDPOINT}:6379/0"},
        {"name": "CORS_ORIGINS", "value": "https://${ALB_DNS}"},
        {"name": "FRONTEND_URL", "value": "https://${ALB_DNS}"}
      ],
      "secrets": [
        {"name": "SECRET_KEY", "valueFrom": "arn:aws:ssm:${AWS_REGION}:${AWS_ACCOUNT}:parameter/echo-tours/SECRET_KEY"},
        {"name": "SENDGRID_API_KEY", "valueFrom": "arn:aws:ssm:${AWS_REGION}:${AWS_ACCOUNT}:parameter/echo-tours/SENDGRID_API_KEY"},
        {"name": "STRIPE_SECRET_KEY", "valueFrom": "arn:aws:ssm:${AWS_REGION}:${AWS_ACCOUNT}:parameter/echo-tours/STRIPE_SECRET_KEY"},
        {"name": "STRIPE_WEBHOOK_SECRET", "valueFrom": "arn:aws:ssm:${AWS_REGION}:${AWS_ACCOUNT}:parameter/echo-tours/STRIPE_WEBHOOK_SECRET"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/echo-tours-backend",
          "awslogs-region": "${AWS_REGION}",
          "awslogs-stream-prefix": "backend"
        }
      }
    }
  ]
}
EOF

aws ecs register-task-definition --cli-input-json file://backend-task-def.json
```

**前端任务定义（注意 `--target prod` 构建参数）：**

```bash
cat > frontend-task-def.json <<EOF
{
  "family": "echo-tours-frontend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::${AWS_ACCOUNT}:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "frontend",
      "image": "${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/echo-tours/frontend:latest",
      "essential": true,
      "portMappings": [{"containerPort": 3000, "protocol": "tcp"}],
      "environment": [
        {"name": "NODE_ENV", "value": "production"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/echo-tours-frontend",
          "awslogs-region": "${AWS_REGION}",
          "awslogs-stream-prefix": "frontend"
        }
      }
    }
  ]
}
EOF

aws ecs register-task-definition --cli-input-json file://frontend-task-def.json
```

> **⚠ 关于 ALB 和 nginx**: 在 ECS Fargate 方案中，ALB 直接替代 nginx 的反向代理功能。
> 你需要配置 ALB 的**监听器规则**：
> - 路径 `/api/*` → 转发到后端目标组 (:8000)
> - 路径 `/health`, `/docs`, `/openapi.json` → 转发到后端目标组 (:8000)
> - 默认路径 `/*` → 转发到前端目标组 (:3000)

**创建 ECS 服务：**

```bash
# 后端 ECS 服务
aws ecs create-service \
  --cluster echo-tours-prod \
  --service-name echo-tours-backend \
  --task-definition echo-tours-backend \
  --launch-type FARGATE \
  --desired-count 2 \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-ecs-id],assignPublicIp=DISABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=backend,containerPort=8000" \
  --deployment-configuration "minimumHealthyPercent=50,maximumPercent=200" \
  --health-check-grace-period-seconds 60 \
  --enable-execute-command

# 前端 ECS 服务
aws ecs create-service \
  --cluster echo-tours-prod \
  --service-name echo-tours-frontend \
  --task-definition echo-tours-frontend \
  --launch-type FARGATE \
  --desired-count 1 \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-ecs-id],assignPublicIp=DISABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=frontend,containerPort=3000" \
  --health-check-grace-period-seconds 60
```

#### 3.2.6 将 Secrets 存入 AWS Systems Manager Parameter Store

```bash
# 敏感信息不应写在 .env 或任务定义硬编码中，而是存入 Parameter Store
aws ssm put-parameter \
  --name /echo-tours/SECRET_KEY \
  --value "你的随机密钥" \
  --type SecureString

aws ssm put-parameter \
  --name /echo-tours/SENDGRID_API_KEY \
  --value "SG.xxx" \
  --type SecureString

aws ssm put-parameter \
  --name /echo-tours/STRIPE_SECRET_KEY \
  --value "sk_live_xxx" \
  --type SecureString

aws ssm put-parameter \
  --name /echo-tours/STRIPE_WEBHOOK_SECRET \
  --value "whsec_xxx" \
  --type SecureString
```

---

## 4. 方式二：通过 GitHub Actions 部署到 AWS

> **适合场景**: 团队协作开发、追求 CI/CD 自动化、"git push 即部署"
> **核心思路**: GitHub Actions 自动构建 → 推送镜像 → 触发 ECS 滚动更新

### 4.1 架构设计

```
  你 push 代码到 GitHub main 分支
            │
            ▼
   ┌─────────────────┐
   │  GitHub Actions  │
   │   ┌───────────┐  │
   │   │  CI:      │  │  ← 并行 lint + test + typecheck
   │   │  ci.yml   │  │
   │   └───────────┘  │
   │        │         │
   │        ▼         │
   │   ┌───────────┐  │
   │   │  CD:      │  │  ← 构建镜像，推送至 ECR
   │   │  deploy   │  │
   │   │  .yml     │  │
   │   └───────────┘  │
   └────────┬─────────┘
            │
            ▼
   ┌─────────────────┐
   │  AWS ECR        │  ← Amazon Elastic Container Registry
   │  (镜像仓库)       │
   └────────┬─────────┘
            │
            ▼
   ┌─────────────────┐
   │  AWS ECS        │  ← Fargate 滚动更新，零停机
   │  (服务更新)       │
   └─────────────────┘
```

### 4.2 前置准备：GitHub Secrets

在 GitHub 仓库 → Settings → Secrets and variables → Actions 中添加以下 Secrets：

| Secret 名称 | 说明 | 获取方式 |
|------------|------|---------|
| `AWS_ACCESS_KEY_ID` | AWS 访问密钥 | AWS IAM → 创建用户 → 附加 AmazonECS_FullAccess 策略 |
| `AWS_SECRET_ACCESS_KEY` | AWS 访问密钥 | 同上 |
| `AWS_REGION` | 部署区域 | 例如 `ap-southeast-1` |
| `AWS_ACCOUNT_ID` | AWS 账号 ID | AWS 控制台或 `aws sts get-caller-identity` |
| `DATABASE_URL` | RDS 连接串 | `postgresql+asyncpg://user:pass@host:5432/echo_tours` |
| `DATABASE_URL_SYNC` | Sync 连接串 | `postgresql://user:pass@host:5432/echo_tours` |
| `REDIS_URL` | Redis 连接 | `redis://host:6379/0` |
| `SECRET_KEY` | JWT 密钥 | `openssl rand -hex 32` |
| `SENDGRID_API_KEY` | 邮件（可选） | SendGrid |
| `STRIPE_SECRET_KEY` | 支付（可选） | Stripe Dashboard |
| `STRIPE_PUBLIC_KEY` | Stripe 公钥 | Stripe Dashboard |
| `STRIPE_WEBHOOK_SECRET` | Stripe Webhook | Stripe Dashboard |
| `CORS_ORIGINS` | CORS 域名 | 例如 `https://echo-tours.com` |
| `FRONTEND_URL` | 前端域名 | 例如 `https://echo-tours.com` |

### 4.3 创建服务角色（需手动配置一次）

```bash
# 1. 创建 ECS 任务执行角色（允许 ECS 拉取 ECR 镜像、写入 CloudWatch）
aws iam create-role \
  --role-name ecsTaskExecutionRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ecs-tasks.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'
aws iam attach-role-policy \
  --role-name ecsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# 2. 创建 GitHub Actions OIDC 提供者（更安全的免密钥认证）
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com

# 3. 创建 IAM 角色，允许 GitHub Actions OIDC 扮演
# 📄 详见: https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services
# (限于篇幅，此处省略 OIDC 角色详细 JSON，参考上述链接)
```

### 4.4 更新 `deploy.yml` 以推送到 ECR 并更新 ECS

当前 `deploy.yml` 将镜像推送到 ghcr.io。我们需要为其增加 AWS ECR 推送 + ECS 更新的能力。

在 `.github/workflows/deploy.yml` 中增加以下内容（或新建 `deploy-aws.yml`）：

<details>
<summary>点击展开 deploy-aws.yml 完整配置</summary>

```yaml
name: Deploy to AWS ECS

on:
  push:
    branches: [main]
    paths-ignore:
      - 'docs/**'
      - '**.md'
      - '.gitignore'
  workflow_dispatch:
    inputs:
      environment:
        description: '部署环境'
        required: true
        default: 'production'
        type: choice
        options:
          - staging
          - production

env:
  AWS_REGION: ${{ secrets.AWS_REGION }}
  ECR_REGISTRY: ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.${{ secrets.AWS_REGION }}.amazonaws.com
  ECR_REPO_BACKEND: echo-tours/backend
  ECR_REPO_FRONTEND: echo-tours/frontend
  ECS_CLUSTER: echo-tours-prod
  ECS_SERVICE_BACKEND: echo-tours-backend
  ECS_SERVICE_FRONTEND: echo-tours-frontend

jobs:
  ci:
    name: CI Checks
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: pip install ruff && ruff check src/backend/
        name: Lint backend
      - run: cd src/frontend && npm ci --legacy-peer-deps && npm run lint && npm run typecheck
        name: Lint frontend

  build-and-push:
    name: Build & Push to ECR
    runs-on: ubuntu-latest
    needs: [ci]
    permissions:
      id-token: write
      contents: read

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::${{ secrets.AWS_ACCOUNT_ID }}:role/github-actions-ecr-role
          aws-region: ${{ secrets.AWS_REGION }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build, tag, and push backend image to ECR
        id: build-backend
        env:
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPO_BACKEND:latest \
            -t $ECR_REGISTRY/$ECR_REPO_BACKEND:$IMAGE_TAG \
            -f src/backend/Dockerfile --target prod src/backend/
          docker push $ECR_REGISTRY/$ECR_REPO_BACKEND --all-tags
          echo "image=$ECR_REGISTRY/$ECR_REPO_BACKEND:$IMAGE_TAG" >> $GITHUB_OUTPUT

      - name: Build, tag, and push frontend image to ECR
        id: build-frontend
        env:
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build \
            --build-arg NEXT_PUBLIC_API_URL=${{ secrets.CORS_ORIGINS }} \
            --build-arg NEXT_PUBLIC_STRIPE_PUBLIC_KEY=${{ secrets.STRIPE_PUBLIC_KEY }} \
            -t $ECR_REGISTRY/$ECR_REPO_FRONTEND:latest \
            -t $ECR_REGISTRY/$ECR_REPO_FRONTEND:$IMAGE_TAG \
            -f src/frontend/Dockerfile --target prod src/frontend/
          docker push $ECR_REGISTRY/$ECR_REPO_FRONTEND --all-tags
          echo "image=$ECR_REGISTRY/$ECR_REPO_FRONTEND:$IMAGE_TAG" >> $GITHUB_OUTPUT

  deploy:
    name: Deploy to ECS
    runs-on: ubuntu-latest
    needs: [build-and-push]
    permissions:
      id-token: write
      contents: read

    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::${{ secrets.AWS_ACCOUNT_ID }}:role/github-actions-ecs-role
          aws-region: ${{ secrets.AWS_REGION }}

      - name: Deploy backend service
        run: |
          aws ecs update-service \
            --cluster $ECS_CLUSTER \
            --service $ECS_SERVICE_BACKEND \
            --force-new-deployment \
            --no-cli-pager

      - name: Deploy frontend service
        run: |
          aws ecs update-service \
            --cluster $ECS_CLUSTER \
            --service $ECS_SERVICE_FRONTEND \
            --force-new-deployment \
            --no-cli-pager

      - name: Wait for backend deployment to stabilize
        run: |
          aws ecs wait services-stable \
            --cluster $ECS_CLUSTER \
            --services $ECS_SERVICE_BACKEND

      - name: Wait for frontend deployment to stabilize
        run: |
          aws ecs wait services-stable \
            --cluster $ECS_CLUSTER \
            --services $ECS_SERVICE_FRONTEND

      - name: Verify deployment
        run: |
          ALB_DNS=$(aws elbv2 describe-load-balancers \
            --names echo-tours-alb \
            --query 'LoadBalancers[0].DNSName' \
            --output text)
          echo "✅ ALB: http://${ALB_DNS}/health"
          curl -s -o /dev/null -w "Health Check: %{http_code}" "https://${ALB_DNS}/health"
```

</details>

### 4.5 使用方式

```bash
# 日常开发流程
git checkout -b feature/my-feature
git add .
git commit -m "feat(tours): add new tour filters"
git push origin feature/my-feature

# 创建 PR → CI 自动运行
# 合并到 main → CD 自动部署

# 如果需要手动触发特定环境的部署：
# GitHub → Actions → Deploy to AWS ECS → Run workflow
# 选择 staging 或 production 环境
```

> **CI `ci.yml`** 已有完整的测试流水线（ruff lint + pytest + E2E Playwright + Docker 构建验证）。
> CD 部署可在 CI 通过后自动触发。

### 4.6 本地远程部署 vs GitHub CI/CD 部署的区别

| 方面 | GitHub Actions CI/CD | 本地远程部署 (rsync+SSH) |
|------|---------------------|----------------------|
| **触发方式** | `git push` 自动触发 | 手动运行 deploy.sh 或 rsync |
| **构建位置** | GitHub 自托管 Runner | 本地开发机器 |
| **镜像仓库** | ECR（AWS 托管） | 镜像直接在目标机器构建 |
| **部署策略** | 蓝绿部署 / 滚动更新 | 停旧 → 起新（有短暂中断） |
| **回滚** | 回退 Git commit 重新部署 | 需要手动重新 rsync 旧版本 |
| **团队协作** | 成员只需 push 代码 | 需要成员有 SSH 密钥和部署知识 |

---

## 5. 两种部署方式对比

### 5.1 核心维度对比

| 维度 | 方式一：本地目录部署 | 方式二：GitHub Actions CI/CD |
|------|-------------------|-----------------------------|
| **部署方式** | `rsync` + SSH 或 docker push + 手动命令 | 自动化流水线，`git push` 即部署 |
| **适合团队规模** | 1–2 人（小团队） | 2 人以上或需要 CI 流程 |
| **构建位置** | 本地开发机 → 推送/同步到 AWS | GitHub Runner 自动构建 |
| **部署速度** | ⭐⭐⭐ (依赖上传带宽) | ⭐⭐⭐⭐ (GitHub Runner 网络快) |
| **操作复杂度** | ⭐⭐⭐⭐⭐ (只需运行脚本) | ⭐⭐⭐ (需要配置 Secrets + IAM) |
| **回滚速度** | ⭐⭐ (手动 rsync 旧版本) | ⭐⭐⭐⭐ (重新部署旧 commit) |
| **一致性保证** | ⭐⭐⭐ (依赖本地环境) | ⭐⭐⭐⭐⭐ (隔离的 Runner) |
| **安全性** | ⭐⭐⭐ (需要管理 SSH 密钥) | ⭐⭐⭐⭐⭐ (OIDC 免密钥) |
| **审计追踪** | ⭐⭐ (谁部署了哪个版本？) | ⭐⭐⭐⭐⭐ (Git commit + Actions log) |
| **零停机部署** | ❌ (docker compose 重启有中断) | ✅ (ECS 滚动更新) |
| **自动扩缩容** | ❌ (单机固定资源) | ✅ (ECS 可配置 auto scaling) |
| **监控告警** | ⭐ (需自行配置) | ⭐⭐⭐ (CloudWatch + ECS 内置) |
| **月运行成本** | ~$35–55 (t4g.small) | ~$130–180 (含 RDS/ALB/Redis) |

### 5.2 选择建议

| 你的情况 | 推荐方案 | 理由 |
|---------|---------|------|
| 单人开发者，预算有限 | **方式一 EC2 + Docker Compose** | 月费最低，与本地开发环境一致 |
| 小团队，需要审批流程 | **方式二 GitHub CI/CD** | 代码审查 → 自动部署，规范 |
| 需要高可用 (99.9%+) | **方式二 ECS Fargate** | 多 AZ 部署，自动恢复 |
| 快速验证 / Demo / 实验 | **方式一 EC2** | 5 分钟就能部署完成 |
| 正式生产环境 | **方式一 EC2 + systemd + CB** | 经济实惠且可靠 |
| 企业级生产环境 | **方式二 ECS Fargate + RDS** | 托管服务，运维最小化 |

### 5.3 混合部署策略（推荐）

```
本地开发 ──→ 开发分支 ──→ GitHub ──→ CI 自动测试
                │                      │
                ▼                      ▼
          合并到 main ──────────→ CD 自动构建镜像 → ECR
                                              │
                                              ▼
                                     ECS Fargate 滚动更新
                                              │
                                     ┌────────┴────────┐
                                     ▼                  ▼
                                 ECR + ECS          EC2 (备用)
                               （主要生产环境）     （低成本灾备）
```

**实施步骤**：
1. 日常开发使用 **方式二**（GitHub → ECR → ECS）
2. 同时在 EC2 保留一份 **方式一** 的部署作为备用环境
3. 主生产环境（ECS）正常对外服务时，EC2 运行最小副本（1 个 backend + 1 个 frontend）
4. ECS 出问题时，DNS 切换到 EC2 IP（RDS 共享，数据不丢）

---

## 6. 部署后验证与运维

### 6.1 快速验证

```bash
# 健康检查
curl -s http://你的域名/health

# 预期输出（示例）:
# {"status":"healthy","version":"2.7.0","elasticsearch":"connected","stripe":"mock","google_oauth":"not_configured"}

# API 测试
curl -s http://你的域名/api/v1/tours | head -c 200

# 前端访问
# 在浏览器打开 http://你的域名
```

### 6.2 查看日志

**EC2 + Docker Compose 方案：**

```bash
# 查看所有服务日志
docker compose -f docker-compose.prod.yml logs -f

# 查看特定服务
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
docker compose -f docker-compose.prod.yml logs -f nginx

# 最后 100 行
docker compose -f docker-compose.prod.yml logs --tail=100 backend
```

**ECS Fargate 方案（CloudWatch）：**

```bash
# 查看后端日志（最近 1 小时）
aws logs tail /ecs/echo-tours-backend --since 1h

# 查看前端日志
aws logs tail /ecs/echo-tours-frontend --since 1h

# 持续跟踪
aws logs tail /ecs/echo-tours-backend --follow
```

### 6.3 数据库备份

**方式一 EC2（容器内）：**

```bash
# 手动备份
docker exec $(docker ps -q -f name=postgres) pg_dump \
  -U postgres echo_tours > ~/backups/echo_tours_$(date +%Y%m%d).sql

# 自动备份（crontab）
0 3 * * * docker exec $(docker ps -q -f name=postgres) pg_dump -U postgres echo_tours \
  | gzip > ~/backups/echo_tours_$(date +\%Y\%m\%d).sql.gz -c
```

**方式二 ECS + RDS（自动备份）：**

```bash
# 查看备份配置
aws rds describe-db-instances \
  --db-instance-identifier echo-tours-postgres \
  --query 'DBInstances[0].BackupRetentionPeriod'

# 手动创建快照
aws rds create-db-snapshot \
  --db-instance-identifier echo-tours-postgres \
  --db-snapshot-identifier echo-tours-$(date +%Y%m%d)
```

### 6.4 部署更新流程

**方式一 EC2 更新：**

```bash
# 1. 同步最新代码
rsync -avz --exclude 'node_modules' --exclude '.next' --exclude '__pycache__' \
  --exclude '.venv' --exclude '.git' \
  -e "ssh -i ~/.ssh/echo-tours-key.pem" \
  ./ ec2-user@$EIP:~/echo-tours/

# 2. SSH 到 EC2
ssh -i ~/.ssh/echo-tours-key.pem ec2-user@$EIP

# 3. 重新构建并重启
cd ~/echo-tours
docker compose -f docker-compose.prod.yml build backend frontend
docker compose -f docker-compose.prod.yml up -d
```

**方式二 EC2 使用 deploy.sh 更新：**

```bash
bash scripts/deploy.sh \
  --cloud ec2 \
  --ssh-user ec2-user \
  --ssh-host $EIP \
  --env prod
```

**方式二 CI/CD 更新（零停机）：**

只需 `git push`，等待 GitHub Actions 完成即可。ECS 滚动更新保证：
- 先启动新版本容器
- 新容器通过健康检查后，再停止旧容器
- 整个过程对用户透明，零停机

### 6.5 监控告警推荐

```bash
# 设置 CloudWatch 告警（EC2 CPU > 80%）
aws cloudwatch put-metric-alarm \
  --alarm-name echo-tours-ec2-cpu-high \
  --alarm-description "EC2 CPU > 80% for 5 minutes" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=InstanceId,Value=i-xxx \
  --alarm-actions arn:aws:sns:ap-southeast-1:xxx:echo-tours-alerts
```

---

## 7. 常见问题与排错

### 7.1 首次部署常见错误（2026-07 实测）

以下是 2026 年 7 月首次在 AWS EC2 (Amazon Linux 2023, x86_64) 上部署 EchoTour 时遇到的实际问题及修复方案。

#### 7.1.1 Backend 不断重启：ImportError

**症状**: Backend 容器反复崩溃，`docker-compose logs backend` 显示：
```
ImportError: cannot import name 'get_current_user_optional' from 'app.api.dependencies'
```

**根因**: `src/backend/app/api/v1/custom_tours.py` 从错误的模块导入了 `get_current_user_optional`。

**修复**: 将导入路径从 `app.api.dependencies` 改为 `app.api.v1.auth`（v2.8 已修复并推送）。

#### 7.1.2 Celery Beat 文件权限错误

**症状**: Celery Beat 不断重启，日志显示：
```
PermissionError: [Errno 13] Permission denied: 'celerybeat-schedule'
```

**根因**: 容器以 `app` 用户运行，但 `/app` 通过 volume 挂载宿主机代码，无写权限。

**修复**: 在 `docker-compose.yml` 中为 celery_beat 的 command 添加 `-s /tmp/celerybeat-schedule`：
```yaml
command: celery -A app.tasks.celery_app beat --loglevel=info -s /tmp/celerybeat-schedule
```

#### 7.1.3 Nginx 502 — Host is unreachable

**症状**: 浏览器访问返回 `502 Bad Gateway`，nginx 日志显示：
```
connect() failed (113: Host is unreachable) while connecting to upstream
```

**根因**: 分批重建容器时，部分容器留在旧 Docker 网络中，跨网络 DNS 无法解析。

**修复**: 执行完全重建：
```bash
docker-compose down
docker-compose up -d
```

#### 7.1.4 Frontend `next: not found` / `Cannot find module`

**症状**: Frontend 容器崩溃，日志显示 `sh: next: not found` 或 `Cannot find module '/app/server.js'`。

**根因**: 匿名卷 `- /app/node_modules` 覆盖了新镜像的 node_modules；或旧镜像 target 不匹配。

**修复**:
```bash
docker-compose down frontend
docker-compose rm -f -v frontend       # -v 删除匿名卷
docker-compose build --no-cache frontend
docker-compose up -d frontend nginx
```

#### 7.1.5 数据为空 — 需要运行 Seed 脚本

**症状**: 部署完成后网站能访问，但 tours/目的地等数据为空。

**修复**: 使用 `--with-seed` 标志运行 setup.sh，或手动执行：
```bash
docker-compose exec backend python scripts/seed_data.py
```

---

### 7.2 EC2 内存不足导致容器退出

**症状**: 容器频繁重启，`docker logs` 无异常，`dmesg` 看到 `oom-kill`

**解决**:
```bash
# 检查内存使用
free -h

# 增加 swap（尤其是 t4g.small 只有 2GB）
sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 持久化 swap
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 或关闭 Elasticsearch（节省 1GB）
# 编辑 docker-compose.prod.yml，注释掉 elasticsearch 服务
```

### 7.2 ECS 任务启动失败

**症状**: ECS 服务反复启动/停止，CloudWatch 日志无输出

**检查**:
```bash
# 1. ECS 任务停止原因
aws ecs describe-services \
  --cluster echo-tours-prod \
  --services echo-tours-backend \
  --query 'services[0].events'

# 2. 查看最近停止的任务
aws ecs list-tasks \
  --cluster echo-tours-prod \
  --desired-status STOPPED \
  --query 'taskArns' | head -5

aws ecs describe-tasks \
  --cluster echo-tours-prod \
  --tasks <task-arn> \
  --query 'tasks[0].stoppedReason'
```

### 7.3 数据库连接失败

**常见原因**:
- RDS 安全组未允许 ECS 任务或 EC2 的访问
- `.env` 中的 `DATABASE_URL` 使用了 localhost，应改为 RDS 端点
- RDS 在私有子网，需要 NAT Gateway 或 VPC Endpoint

**修复**:
```bash
# 确认安全组
aws ec2 describe-security-groups \
  --group-ids sg-rds-id \
  --query 'SecurityGroups[0].IpPermissions'

# 从 EC2 测试连接
psql "postgresql://echo_tours_admin:密码@${RDS_ENDPOINT}:5432/echo_tours" -c "SELECT 1"
```

### 7.4 CORS 跨域错误

**症状**: 前端可以加载但 API 请求被浏览器拦截（浏览器控制台 CORS 错误）

**修复**:
- 确保 `.env` 中 `CORS_ORIGINS` 包含了前端域名
- ALB 方案：确保前端请求是相对路径（`/api/v1/...`）而不是绝对路径

### 7.5 静态资源 404（Next.js standalone）

**症状**: 前端页面能加载，但 JS/CSS 静态资源返回 404

**原因**: Next.js standalone 构建需要将 `.next/static` 复制到部署目录

**确认**:
```bash
# 检查 Docker 构建日志是否有资源复制步骤
docker logs <frontend-container> 2>&1 | grep -i static

# 或检查镜像内 .next 目录结构
docker run --rm echo-tours-frontend:latest ls -la .next/static
```

### 7.6 部署脚本报错

**症状**: `bash scripts/setup.sh` 或 `deploy.sh` 中途报错

**通用排查步骤**:
```bash
# 1. 确认 Docker 运行中
systemctl status docker

# 2. 确认 .env 存在且格式正确
cat .env | grep -v '^#' | grep '=' | wc -l

# 3. 手动分步执行
docker compose -f docker-compose.prod.yml build --no-cache backend
docker compose -f docker-compose.prod.yml up -d postgres redis
sleep 10
docker compose -f docker-compose.prod.yml up -d backend frontend

# 4. 查看各容器状态
docker compose -f docker-compose.prod.yml ps
```

---

## 附录

### A. 成本估算总结

| 方案 | 实例 | 内存 | 存储 | 月费估算 | 适用场景 |
|------|------|------|------|---------|---------|
| EC2 `t4g.medium` + Docker Compose | 2vCPU | 4 GB | gp3 30GB | ~$25 | 开发测试 |
| **EC2 `t4g.large` + Docker Compose** 🏆 | 2vCPU | 8 GB | gp3 50+100GB | **~$55** | 小规模生产（推荐起步） |
| EC2 `t4g.xlarge` + Docker Compose | 4vCPU | 16 GB | gp3 50+200GB | ~$110 | 中等规模 |
| ECS Fargate + RDS + ElastiCache | — | — | — | ~$130–180 | 全托管 / 高可用 |
| 混合部署（ECS 主 + EC2 备） | — | — | — | ~$170–235 | 企业级 / 高可靠性 |

> **实测建议**: 起步用 `t4g.large`（8 GB），所有 8 个服务（含 ES）运行稳定。`t4g.small`（2 GB）会在启动 ES 后触发 OOM。

### B. 关键命令速查

```bash
# ── EC2 部署速查 ──
rsync -avz --exclude={node_modules,.next,__pycache__,.venv,.git} -e "ssh -i key.pem" ./ user@host:~/echo-tours/
bash scripts/setup.sh                              # EC2 上运行
bash scripts/deploy.sh --cloud ec2 --ssh-user user --ssh-host $IP   # 本地推送

# ── ECR + ECS 速查 ──
aws ecr get-login-password | docker login --username AWS --password-stdin $ACCOUNT.dkr.ecr.$REGION.amazonaws.com
docker build -t echo-tours/backend:latest -f src/backend/Dockerfile --target prod src/backend/
docker tag ... && docker push ...
aws ecs update-service --cluster echo-tours-prod --service echo-tours-backend --force-new-deployment

# ── 运维速查 ──
docker compose -f docker-compose.prod.yml logs -f --tail=100 backend
docker compose -f docker-compose.prod.yml restart frontend
docker compose -f docker-compose.prod.yml exec postgres pg_dump -U postgres echo_tours > backup.sql
```

### C. 相关文档

- [项目 README](../README.md) — 项目整体介绍
- [开发进展文档](development-progress.md) — 版本历史和路线图
- [测试覆盖计划](test-coverage-plan.md) — 测试策略
- AWS ECS 开发指南: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/
- Docker Compose 部署文档: https://docs.docker.com/compose/production/

---

> **下一步建议**: 如果你是首次部署，建议先选择 **方式一 EC2 + Docker Compose** 快速上线，运营稳定后再迁移到 **方式二 ECS Fargate** 实现自动扩缩容和零停机部署。
