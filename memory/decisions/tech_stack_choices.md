# Tech Stack Choices

## D-2026-08-04-T01 — FastAPI + Next.js monorepo

**Rationale:** Chosen by the user over Python-only and TypeScript-only options. Matches the existing
GhostOps stack. Python 3.12, SQLAlchemy 2.0 typed, Alembic, Pydantic v2, `uv`; Next.js 15 + React 19
for the review dashboard.

**Status:** Accepted
**Date:** 2026-08-04
**Ref:** apps/api/pyproject.toml; apps/web/package.json

## D-2026-08-04-T02 — Permutation test over a parametric test for playbook verification

**Rationale:** Distribution-free, so it assumes nothing about engagement data that would be false
anyway. Seeded, so a stored verdict is recomputable during an audit. Reports `(hits+1)/(n+1)` so a
p-value is never claimed as exactly zero on 2000 shuffles.

**Status:** Accepted
**Date:** 2026-08-04
**Ref:** apps/api/src/brandcortex/core/learning/verification.py@d97502

## D-2026-08-04-T03 — Meta app stays in Development mode; System User is the intended token path

**Rationale:** Dev mode grants full Page permissions to app-role holders acting on Pages they
administer — exactly this deployment (one Page, owned by the app admin), so App Review may never be on
the critical path. `business_management` dropped from required permissions for the same reason. System
User tokens (Business Settings) never expire and skip the OAuth dialog entirely; this is what
`channel_tokens` was designed to hold.

**Status:** Accepted (token not yet obtained)
**Date:** 2026-08-04
**Ref:** apps/api/src/brandcortex/adapters/channel/facebook/adapter.py@f7847f
