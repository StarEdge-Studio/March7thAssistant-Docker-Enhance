FROM --platform=$BUILDPLATFORM node:22-alpine AS webui-builder
WORKDIR /webui
RUN corepack enable && corepack prepare pnpm@9.15.9 --activate
COPY webui/package.json webui/pnpm-lock.yaml* webui/vite.config.mjs webui/tailwind.config.js webui/postcss.config.js webui/index.html ./
COPY webui/src ./src
RUN pnpm install --no-frozen-lockfile && pnpm run build

FROM python:3.14.5-slim-bookworm

# ======================
# Build args (architecture)
# ======================
ARG TARGETARCH
ARG DEBIAN_FRONTEND=noninteractive
ENV DEBIAN_FRONTEND=${DEBIAN_FRONTEND}

# ======================
# Python optimization
# ======================
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ======================
# Virtualenv
# ======================
ENV VIRTUAL_ENV="/opt/venv"
ENV UV_PROJECT_ENVIRONMENT=$VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# ======================
# Timezone
# ======================
ENV TZ=Asia/Shanghai

# ======================
# App environment variables
# ======================
ENV MARCH7TH_CLOUD_GAME_ENABLE=true
ENV MARCH7TH_BROWSER_HEADLESS_ENABLE=true
ENV MARCH7TH_BROWSER_HEADLESS_RESTART_ON_NOT_LOGGED_IN=false
# 默认使用官方源下载浏览器；如果下载缓慢，可以改为 true 启用镜像下载
ENV MARCH7TH_BROWSER_DOWNLOAD_USE_MIRROR=false
# 单账号运行完成后立即退出，由 WebUI 调度器接管多账号顺序队列
ENV MARCH7TH_AFTER_FINISH=Exit
# 标记从 Docker 启动，避免控制台阻塞
ENV MARCH7TH_DOCKER_STARTED=true
# 前端设计语言主题：m3e (默认 Material 3 Expressive) 或 simple (轻量简洁版)
ENV WEBUI_THEME=m3e

WORKDIR /m7a

COPY pyproject.toml uv.lock ./
COPY webui/requirements.txt ./webui/requirements.txt

# ======================
# System dependencies
# ======================
RUN \
    # 如果需要使用国内源，可以取消下面一行的注释
    # sed -i 's/deb.debian.org/mirrors.cloud.tencent.com/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get install -yq --no-install-recommends \
    # Lightweight init for proper zombie reaping (PID 1)
    tini \
    # Dependencies for OpenCV
    libgl1 \
    # Dependencies for headless Chrome
    libglib2.0-0 \
    libnss3 \
    libfontconfig1 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libxkbcommon0 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libgtk-3-0 \
    ca-certificates \
    fonts-liberation \
    \
    # -------- arm64 only --------
    && if [ "$TARGETARCH" = "arm64" ]; then \
        apt-get install -yq --no-install-recommends \
            chromium \
            chromium-driver ; \
    fi \
    \
    && rm -rf /var/lib/apt/lists/*

# ======================
# Python deps
# ======================
COPY --from=ghcr.io/astral-sh/uv:0.11.15 /uv /uvx /bin/
RUN uv sync --only-group docker
    # 如果需要使用国内源，可以取消下面一行的注释
    # RUN uv sync --only-group docker --index-url https://mirrors.cloud.tencent.com/pypi/simple/
RUN uv pip install -r webui/requirements.txt

COPY build.py ./

RUN if [ "$TARGETARCH" != "arm64" ]; then \
        python build.py --task browser ; \
    else \
        echo "Skipping browser build on arm64"; \
    fi

COPY . .
COPY --from=webui-builder /webui/static ./webui/static

RUN python build.py --task ocr \
    && rm -rf ./logs \
    && rm -f config.yaml

# ======================
# arm64 browser env
# ======================
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/usr/bin/tini", "--", "/entrypoint.sh"]
CMD ["python", "webui/main.py"]
