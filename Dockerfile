# syntax=docker/dockerfile:1.7

# Memecoin Cinema: research desk + control panel in one image.
#   build:  docker compose build
#   run:    docker compose up -d        (see docker-compose.yml)

ARG NODE_IMAGE=node:22-bookworm-slim
ARG GMGN_CLI_VERSION=1.5.0

# ---- 1. Build the React desk -------------------------------------------------
FROM ${NODE_IMAGE} AS ui-build
WORKDIR /build/ui

COPY ui/package.json ui/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --no-audit --no-fund

COPY ui/ ./
RUN npm run build

# ---- 2. Runtime: Node (for gmgn-cli) + Python (for the control panel) --------
FROM ${NODE_IMAGE} AS runtime
ARG GMGN_CLI_VERSION

LABEL org.opencontainers.image.title="memecoin-cinema" \
      org.opencontainers.image.description="Memecoin research desk: GMGN data, scoring agent and hard risk guards" \
      org.opencontainers.image.source="https://github.com/hosseinmirzapur/memecoin-cinema"

# python3 runs the server and pipeline; the Node image already provides npm.
# Apt versions are not pinned: the base image tag is pinned, and Debian security updates matter more.
# hadolint ignore=DL3008
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 \
 && rm -rf /var/lib/apt/lists/* \
 && npm install -g "gmgn-cli@${GMGN_CLI_VERSION}" \
 && npm cache clean --force

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
RUN chown node:node /app

# Application code only. Secrets (.env, ~/.config/gmgn) are mounted at run time, never copied.
COPY --chown=node:node agents.md ./
COPY --chown=node:node scripts ./scripts
COPY --chown=node:node .agents ./.agents
COPY --chown=node:node tests ./tests
COPY --from=ui-build --chown=node:node /build/ui/dist ./ui/dist

# Numeric UID so orchestrators can verify the non-root user without a passwd lookup.
USER 1000:1000
EXPOSE 8765

# Stdlib probe against a public route: no GMGN or Kilo quota is spent.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD ["python3", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/api/rules', timeout=4)"]

CMD ["python3", "scripts/ui_server.py", "--host", "0.0.0.0", "--port", "8765"]
