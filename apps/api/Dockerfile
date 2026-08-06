# BrandCortex API. Build context: apps/api (self-contained — pyproject, lockfile, alembic all here).
#
# The start command migrates before serving. Alembic upgrades are additive and versioned, so a
# deploy that rolls back still runs against a schema the previous code understands; the alternative
# — a human remembering to migrate — is how a deploy ships code that queries a column that is not
# there yet.
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.6 /uv /uvx /bin/

WORKDIR /app

# Dependency layer first, so code edits do not re-resolve the world.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY . .
RUN uv sync --frozen --no-dev

# $PORT comes from the platform (Railway sets it); 8000 is the local fallback.
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn brandcortex.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
