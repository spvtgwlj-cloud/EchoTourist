# ── dev ──────────────────────────────────────────
# 开发环境：热重载 + 开发依赖
# ────────────────────────────────────────────────
FROM python:3.12-slim AS dev
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ── prod ────────────────────────────────────────
# 生产环境：压缩安装，非 root 用户，健康检查
# ────────────────────────────────────────────────
FROM python:3.12-slim AS prod
WORKDIR /app
RUN addgroup --system app && adduser --system --ingroup app app
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY . .
USER app
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
