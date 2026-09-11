from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine
from .routers import allocations, brief, meetings, reports, flags, escalations


@asynccontextmanager
async def lifespan(app: FastAPI):
    connection = engine.connect()
    connection.close()
    yield
    engine.dispose()


app = FastAPI(
    title="Agent-45 Mentoring Intelligence Platform",
    description=(
        "Production-oriented backend for mentoring, "
        "meeting management, action tracking, RBAC, "
        "compliance reporting, and auditability."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.get(
    "/",
    tags=["System"],
)
def root():
    return {
        "service": "Agent-45 Mentoring Intelligence Platform",
        "status": "online",
        "version": app.version,
    }


@app.get(
    "/health",
    tags=["System"],
)
def health_check():
    return {
        "status": "healthy",
        "database": "configured",
    }

app.include_router(allocations.router)
app.include_router(brief.router)
app.include_router(flags.router)
app.include_router(meetings.router)
app.include_router(reports.router)
app.include_router(escalations.router)