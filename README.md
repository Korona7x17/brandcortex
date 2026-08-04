# BrandCortex

An AI content engine that generates, publishes, and self-improves brand content across channels.

Content items come in from a brand's data through a **source adapter**, the core drafts copy in that
brand's voice, a **channel adapter** publishes it and reads back performance, and a reflection agent
rewrites the playbook so the next batch does better.

Home: `brandcortex.app` · Brand #1: **ThaiSwim** · Channel #1: **Facebook**

- Architecture & build scope: [`docs/BrandCortex-architecture.md`](docs/BrandCortex-architecture.md)
- The ThaiSwim seam as it actually exists: [`docs/thaiswim-integration.md`](docs/thaiswim-integration.md)
  — overrides the architecture doc's §4.2–§4.3 and §5.1 where they disagree
- Working conventions for contributors and agents: [`CLAUDE.md`](CLAUDE.md)

## Layout

| Path | What lives there |
| --- | --- |
| `apps/api` | FastAPI backend: core engine, adapters, workers, DB |
| `apps/web` | Next.js review dashboard: drafts, calendar, analytics, playbook |
| `packages/contracts` | Content-item envelope JSON Schema — the stable seam |
| `docs` | Architecture spec |
| `scripts` | Dev helpers |

## Getting started

```bash
cp .env.example .env          # fill in both DB URLs and the channel credentials

# API
cd apps/api
uv sync
uv run alembic upgrade head
uv run uvicorn brandcortex.main:app --reload      # http://localhost:8000

# Web
cd apps/web
npm install
npm run dev                                        # http://localhost:3000
```

## Status

Phase 0/1 — scaffold in place, business logic not yet implemented. Every module under
`apps/api/src/brandcortex` carries a docstring stating its contract and what remains to be built.
