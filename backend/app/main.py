from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.calendar import router as calendar_router
from app.api.config import router as config_router
from app.api.editorial import router as editorial_router
from app.api.events import router as events_router
from app.api.health import router as health_router
from app.api.jobs import router as jobs_router
from app.api.library import router as library_router
from app.api.media import router as media_router
from app.core.database import SessionLocal, init_database
from app.core.seed import seed_initial_config


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_database()
    with SessionLocal() as db:
        seed_initial_config(db)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Rancho Content Studio API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^(http://(127\.0\.0\.1|localhost):\d+|tauri://localhost)$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router, prefix="/api")
    app.include_router(config_router, prefix="/api")
    app.include_router(editorial_router, prefix="/api")
    app.include_router(events_router, prefix="/api")
    app.include_router(jobs_router, prefix="/api")
    app.include_router(library_router, prefix="/api")
    app.include_router(calendar_router, prefix="/api")
    app.include_router(media_router, prefix="/api")
    return app


app = create_app()
