"""Database engines and session factories.

Two engines, deliberately:

* ``engine`` — BrandCortex's own database. Read/write. Everything we own.
* ``brand_engine`` — the brand DB seam. Read-only by contract; bind a read-only role in ``BRAND_DB_URL``
  so the guarantee is enforced by Postgres rather than by discipline. Used only by source adapters to
  poll ``content_items``. Never write here, and never write a ``posted`` flag back to a brand.

TODO(phase-0): decide open decision #2 — shared vs separate physical server. Logical separation as
written holds either way, so this can be settled at deploy time.
"""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from brandcortex.config import get_settings


@lru_cache
def get_engine() -> Engine:
    return create_engine(get_settings().database_url, pool_pre_ping=True, future=True)


@lru_cache
def get_brand_engine() -> Engine:
    """Engine for the brand DB seam. Raises if no brand DB is configured."""
    url = get_settings().brand_db_url
    if not url:
        raise RuntimeError("BRAND_DB_URL is not configured; source adapters cannot poll the seam")
    return create_engine(url, pool_pre_ping=True, future=True)


@lru_cache
def _session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False, future=True)


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a transactional session."""
    with _session_factory()() as session:
        yield session
