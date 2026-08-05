"""FastAPI application entrypoint for brandcortex.app.

    uv run uvicorn brandcortex.main:app --reload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from brandcortex.api.routes import brands, content_items, health, insights, playbook, posts
from brandcortex.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Bind brand and channel keys to implementations, then serve.

    A failure here is logged rather than raised. Bootstrap reads `brand_config`, so an unseeded or
    unreachable database would otherwise take the whole API down — including the endpoints that
    would have told you why. Unregistered adapters make the routes that need one return a clear
    error, which is a better first thing to see than a container that will not start.

    Workers call `registry.bootstrap()` directly and do let it raise: a publisher with no channel
    adapter has nothing useful to do.
    """
    from brandcortex.adapters import registry

    try:
        registry.bootstrap()
    except Exception:  # noqa: BLE001 — see docstring
        logger.exception("adapter bootstrap failed; brand and channel routes are unavailable")
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

    # The review dashboard runs as its own origin, so the browser needs permission to call this API
    # from it. Origins come from config and default to local development only — a wildcard here would
    # let any page a reviewer has open drive the approve and publish endpoints.
    if settings.cors_allow_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_allow_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PATCH", "DELETE"],
            allow_headers=["*"],
        )

    app.include_router(health.router)
    app.include_router(brands.router)
    app.include_router(content_items.router)
    app.include_router(posts.router)
    app.include_router(insights.router)
    app.include_router(playbook.router)
    return app


app = create_app()
