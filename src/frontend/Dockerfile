# ── dev ──────────────────────────────────────────
# 开发环境：热重载，挂载源码
# ────────────────────────────────────────────────
FROM node:20-alpine AS dev
WORKDIR /app
COPY package.json .
RUN npm install --legacy-peer-deps
COPY . .
EXPOSE 3000
CMD npm run dev

# ── builder ─────────────────────────────────────
# 构建阶段：编译 TypeScript，生成 standalone 输出
# ────────────────────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_STRIPE_PUBLIC_KEY
ARG NEXT_PUBLIC_GOOGLE_CLIENT_ID
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_PUBLIC_STRIPE_PUBLIC_KEY=$NEXT_PUBLIC_STRIPE_PUBLIC_KEY \
    NEXT_PUBLIC_GOOGLE_CLIENT_ID=$NEXT_PUBLIC_GOOGLE_CLIENT_ID
COPY package.json .
RUN npm install --legacy-peer-deps
COPY . .
RUN npm run build

# ── prod ────────────────────────────────────────
# 生产环境：仅复制运行时必须的文件
# ────────────────────────────────────────────────
FROM node:20-alpine AS prod
WORKDIR /app
RUN addgroup --system app && adduser --system --ingroup app app
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
COPY --from=builder /app/messages ./messages
USER app
EXPOSE 3000
ENV NODE_ENV=production
CMD ["node", "server.js"]
