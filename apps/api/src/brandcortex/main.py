"""FastAPI application entrypoint for brandcortex.app.

    uv run uvicorn brandcortex.main:app --reload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from brandcortex.api import auth
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

    _seed_brand_configs()

    try:
        registry.bootstrap()
    except Exception:  # noqa: BLE001 — see docstring
        logger.exception("adapter bootstrap failed; brand and channel routes are unavailable")
    yield


def _seed_brand_configs() -> None:
    """Bring `brand_config` up to date with the reviewed seed files, unless it has been edited.

    Voice used to live in a file that shipped with every deploy and in a row nothing updated, so a
    reviewed change could be merged, deployed and tested green while every post the product made
    still used the old rules. This closes that gap. It refuses to overwrite a row that was edited in
    the app — see `db.bootstrap_config` for why that case belongs to a human.

    Logged and swallowed, like the adapter bootstrap below: a config that cannot be applied is worth
    an API that starts and tells you so.
    """
    settings = get_settings()
    if not settings.seed_on_boot:
        return
    try:
        from pathlib import Path

        from brandcortex.db import bootstrap_config
        from brandcortex.db.session import session_scope

        with session_scope() as session:
            results = bootstrap_config.apply_all(session, Path(settings.seed_dir))
            session.commit()
        for line in results:
            logger.info("brand_config bootstrap: %s", line)
    except Exception:  # noqa: BLE001 — see docstring
        logger.exception("brand_config bootstrap failed; the API is serving whatever the row holds")


def _configure_logging(level: str) -> None:
    """Give `brandcortex.*` loggers somewhere to go.

    Without this, nothing below WARNING reaches the platform log: uvicorn configures its own loggers
    and leaves the root one at its default. The first production boot of `bootstrap_config` printed
    nothing at all for that reason — a subsystem whose whole purpose is preventing silent no-ops,
    silent when it works. `force=True` because uvicorn may have installed a root handler first.
    """
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(levelname)s [%(name)s] %(message)s",
        force=True,
    )


def create_app() -> FastAPI:
    settings = get_settings()
    _configure_logging(settings.log_level)
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

    # Health is the one open surface — it is what the platform's checks and a locked-out operator
    # both need first. Everything else can read drafts or publish to a live Page, so everything
    # else requires a verified session (api/auth.py; fail closed).
    app.include_router(health.router)
    session_required = [Depends(auth.require_session)]
    app.include_router(brands.router, dependencies=session_required)
    app.include_router(content_items.router, dependencies=session_required)
    app.include_router(posts.router, dependencies=session_required)
    app.include_router(insights.router, dependencies=session_required)
    app.include_router(playbook.router, dependencies=session_required)
    return app


app = create_app()
