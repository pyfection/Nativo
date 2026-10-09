FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# Install dependencies first for better layer caching
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy the backend package (the only thing the wheel target includes)
COPY backend ./backend

# Re-sync to install the project itself now that the source is present
RUN uv sync --frozen --no-dev

# Claude CLI for AI suggestions on Quick Contribute cards. Inert until the
# CLAUDE_CODE_OAUTH_TOKEN secret is set (see DEPLOYMENT.md).
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && curl -fsSL https://claude.ai/install.sh | bash -s stable \
    && install -m 755 "$(readlink -f /root/.local/bin/claude)" /usr/local/bin/claude \
    && rm -rf /root/.local /root/.claude /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app/backend

EXPOSE 8000

# Fly's release_command runs migrations; the web process just serves.
# --proxy-headers makes Starlette honor X-Forwarded-For from Fly's edge so
# rate limiting (and request.client.host) sees real client IPs.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
