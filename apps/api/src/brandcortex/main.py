"""FastAPI application entrypoint for brandcortex.app.

    uv run uvicorn brandcortex.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from brandcortex.api.routes import content_items, health, insights, playbook, posts
from brandcortex.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Bind brand and channel keys to implementations. The only place either is allowed to appear.
    # TODO(phase-1): enable once the ThaiSwim and Facebook adapters are implemented.
    # from brandcortex.adapters import registry
    # registry.bootstrap()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="BrandCortex",
        description=(
            "AI content engine that generates, publishes, and self-improves brand content "
            "across channels."
        ),
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None if settings.env == "production" else "/docs",
    )

    app.include_router(health.router)
    app.include_router(content_items.router)
    app.include_router(posts.router)
    app.include_router(insights.router)
    app.include_router(playbook.router)
    return app


app = create_app()
