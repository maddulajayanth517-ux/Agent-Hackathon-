# Combined single-container deployment: builds the Next.js frontend and
# packages it alongside the FastAPI backend in one image. The backend is the
# only exposed process — it proxies anything that isn't an API route to the
# frontend running internally (see docker/start.sh and backend/app/main.py).
# Build context must be the repository root (both backend/ and web/ are needed).

# ---- frontend build ----
FROM node:20-slim AS frontend-build
WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
# Baked into the client bundle at build time; relative path works because the
# backend proxies /api/* to itself and everything else to this frontend, so
# they end up same-origin once deployed.
ENV NEXT_PUBLIC_API_BASE_URL=/api
RUN npm run build

# ---- final image ----
FROM python:3.12-slim
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ backend/

# Next.js standalone output: a minimal self-contained server.js plus only the
# node_modules it actually needs. public/ and .next/static are not included
# by standalone mode and must be copied in separately (Next.js docs).
COPY --from=frontend-build /app/web/.next/standalone ./web
COPY --from=frontend-build /app/web/.next/static ./web/.next/static
COPY --from=frontend-build /app/web/public ./web/public

COPY docker/start.sh /app/start.sh
RUN chmod +x /app/start.sh

ENV PYTHONUNBUFFERED=1 \
    API_PREFIX=/api \
    FRONTEND_PROXY_URL=http://127.0.0.1:3000 \
    REMINDER_SCHEDULER_ENABLED=true

EXPOSE 8000
CMD ["/app/start.sh"]
