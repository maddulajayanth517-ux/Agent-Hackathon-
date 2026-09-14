import asyncio
import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from .database import engine
from .routers import alerts, allocations, announcements, audit, brief, corrections, dashboard, meetings, messages, reports, flags, escalations, schedules, policy, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    connection = engine.connect()
    connection.close()
    task = None
    if os.getenv("REMINDER_SCHEDULER_ENABLED", "true").lower() == "true":
        from .scheduler import reminder_scheduler
        task = asyncio.create_task(reminder_scheduler(), name="mentoring-reminders")
    try:
        yield
    finally:
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        engine.dispose()


# Empty by default (every route keeps its existing path — this is what local
# dev and a split backend+frontend deployment both use). Set to "/api" only
# when this backend is packaged into the combined single-container image
# alongside the built frontend (see FRONTEND_PROXY_URL below), so backend
# routes stop colliding with same-named frontend pages such as /reports or
# /announcements.
API_PREFIX = os.getenv("API_PREFIX", "").rstrip("/")

app = FastAPI(
    title="Agent-45 Mentoring Intelligence Platform",
    description=(
        "Production-oriented backend for mentoring, "
        "meeting management, action tracking, RBAC, "
        "compliance reporting, and auditability."
    ),
    version="1.0.0",
    docs_url=f"{API_PREFIX}/docs",
    redoc_url=f"{API_PREFIX}/redoc",
    openapi_url=f"{API_PREFIX}/openapi.json",
    lifespan=lifespan,
)


_default_origins = "http://localhost:3000,http://127.0.0.1:3000"
_cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", _default_origins).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.get(f"{API_PREFIX}/", tags=["System"])
def root():
    return {
        "service": "Agent-45 Mentoring Intelligence Platform",
        "status": "online",
        "version": app.version,
    }


@app.get(f"{API_PREFIX}/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "database": "configured",
    }

app.include_router(allocations.router, prefix=API_PREFIX)
app.include_router(brief.router, prefix=API_PREFIX)
app.include_router(dashboard.router, prefix=API_PREFIX)
app.include_router(flags.router, prefix=API_PREFIX)
app.include_router(meetings.router, prefix=API_PREFIX)
app.include_router(reports.router, prefix=API_PREFIX)
app.include_router(escalations.router, prefix=API_PREFIX)
app.include_router(alerts.router, prefix=API_PREFIX)
app.include_router(schedules.router, prefix=API_PREFIX)
app.include_router(policy.router, prefix=API_PREFIX)
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(corrections.router, prefix=API_PREFIX)
app.include_router(audit.router, prefix=API_PREFIX)
app.include_router(messages.router, prefix=API_PREFIX)
app.include_router(announcements.router, prefix=API_PREFIX)


# Only present in the combined single-container deployment: FastAPI owns the
# one exposed port, and anything that isn't one of the API routes above is
# forwarded to the Next.js server running as a sibling process on this
# internal-only URL. Registered last so it only ever catches requests that
# didn't match a real API route (see docker/start.sh).
_frontend_proxy_url = os.getenv("FRONTEND_PROXY_URL")
if _frontend_proxy_url:
    _proxy_client = httpx.AsyncClient(base_url=_frontend_proxy_url.rstrip("/"), timeout=30.0)

    @app.api_route(
        "/{full_path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
        include_in_schema=False,
    )
    async def proxy_to_frontend(full_path: str, request: Request) -> Response:
        upstream = await _proxy_client.request(
            request.method,
            f"/{full_path}",
            params=request.query_params,
            headers={k: v for k, v in request.headers.items() if k.lower() not in {"host", "content-length"}},
            content=await request.body(),
        )
        excluded_headers = {"content-encoding", "transfer-encoding", "connection"}
        headers = {k: v for k, v in upstream.headers.items() if k.lower() not in excluded_headers}
        return Response(content=upstream.content, status_code=upstream.status_code, headers=headers)
