# brandcortex-api

FastAPI backend: the brand- and channel-agnostic core, the adapters that make it pluggable, and the
workers that drive the loop.

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn brandcortex.main:app --reload
uv run pytest
uv run ruff check src tests && uv run mypy src
```

## Import direction

```
api / workers  ->  core  ->  db / schemas
adapters       ->  schemas (+ the protocols in adapters/base.py)
```

`core` must never import `adapters.source.*` or `adapters.channel.*` — concrete adapters are resolved
at runtime through `adapters/registry.py`. Two tests in `tests/unit/test_core_is_brand_agnostic.py`
enforce this, and ruff's banned-api rule catches it at lint time.

## Where things go

| I want to... | Touch |
| --- | --- |
| Add a brand | `adapters/source/<brand>/` + a `brand_config` row + register in `registry.bootstrap` |
| Add a channel | `adapters/channel/<channel>/` + register in `registry.bootstrap` |
| Change how copy reads | `brand_config.voice` / `intro_bank`, or `core/generation/templates.py` |
| Change what the system learns | `core/learning/` |
| Change the seam | `schemas/content_item.py` **and** `packages/contracts` — versioned, not edited |
