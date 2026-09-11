from __future__ import annotations

from fastapi import FastAPI

from backend.app.routers.allocations import router as allocations_router
from backend.app.routers.brief import router as brief_router
from backend.app.routers.escalations import router as escalations_router
from backend.app.routers.flags import router as flags_router

app = FastAPI(title="Mentor Intelligence API")

app.include_router(allocations_router)
app.include_router(brief_router)
app.include_router(flags_router)
app.include_router(escalations_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
