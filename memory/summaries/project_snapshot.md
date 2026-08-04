# Project Snapshot — BrandCortex

Last updated: 2026-08-04

AI content engine that generates, publishes and self-improves brand content across channels.
Home `brandcortex.app`. Tenant #1 **ThaiSwim** (`dev/thaiswim`). Channel #1 **Facebook**.

Authority: `docs/BrandCortex-architecture.md`. **`docs/thaiswim-integration.md` overrides it** where
they disagree (§4.2–4.3, §5.1) — the spec was written before the ThaiSwim card engines were read.
Working conventions in `CLAUDE.md`.

## Active Constraints

- **Core never learns brand or channel identity.** No brand string or adapter import in `core/`;
  AST-enforced, docstrings exempt. Adapters resolved at runtime via `adapters/registry`.
- **No multi-tenant layer until brand #2 is real.** `brand` is a keyed column, not a subsystem.
- **Link in the first comment, never the caption.** Photo reach + Meta's ~2-links/month body cap. A
  photo whose link comment failed is a broken post, not a partial success.
- **House voice is fixed, not optimizable.** `voice.*` structurally unproposable by the learning loop.
- **North star = UTM sessions + amplification.** Reactions recorded, weighted 0.0, never targeted.
- **Brand DB is read-only to us.** Never write a `posted` flag back. `card_renders` already means
  "generated/available"; "posted to channel" is ours alone.
- **ThaiSwim's card engines are not to be modified.** Anything the snapshot lacks is derived our side.
- **Nothing grades its own work.** computation > reality > withheld reasoning > inverted burden >
  diverse lenses > human.

## Key Decisions

D-2026-08-04-01 capture PNG at draft, not publish · -02 `card_renders` is the handoff table, no bucket
· -03 locale resolved not assumed, card engines untouched · -04 no self-review ladder · -05 z-score
before weighting, missing metric excludes never zeroes · -06 brand templates live with the adapter ·
-07 failed drafts raise, never silently repaired · -08 event captions use `rowCount` not `n` ·
-09 Alembic baseline deferred to autogenerate. Stack: T01 FastAPI+Next.js · T02 permutation test ·
T03 Meta stays in Dev mode, System User is the token path. Full text in `memory/decisions/`.

## Where things are

```
apps/api/src/brandcortex/
  core/       generation (engine, templates, voice, claims, intro_rotation)
              learning (verification, skeptic, playbook, reflection, features)
              analytics (outcomes, utm, aggregator), scheduling, orchestrator
  adapters/   base.py protocols + registry; source/thaiswim/*; channel/facebook/*
  db/models/  8 tables per spec §5.2
apps/web/     Next.js dashboard — routes exist, still stubs
packages/contracts/   content-item envelope JSON Schema (versioned, never edited)
apps/api/seeds/thaiswim.brand_config.json   voice, intro banks (th+en), hashtags, north_star
```

**The seam:** `card_renders(id, kind, subject, params, snapshot, createdAt)`, polled read-only.
`kind` → source_type; `params` rebuilds the render URL; `snapshot` **is** the facts. No asset bucket —
cards render on demand from a CORS-open URL and are captured at draft time into BrandCortex's own
store. Canonical links and `season` are derived by the adapter.

## Current Focus

**97 pass / 9 skip.** Working offline end to end: `card_renders` row → content item → checked Thai copy
(numeric grounding + voice), both swimmer and event cards.
Still stubs: orchestrator persistence, Facebook adapter I/O, insights fetcher, reflection agent, web
dashboard. No DB provisioned, no Alembic baseline.

Credentials in `.env` (gitignored, 600): App ID `1278952477505548`, App Secret set, Fernet key
generated, Page ID `1223598310834457` (ThaiSwim.com, user is full admin).

## Open Questions

- **Meta token blocked** — carries 3 of 5 scopes. Graph API Explorer caches an invalid scope
  (`pages_read_user_content`) which kills every OAuth dialog, so Meta reissues from the stale grant.
  App config is correct; all five show "Ready for testing". **Untried: System User via Business
  Settings** — never expires, no dialog. User was heavily frustrated by this; approach gently.
- Graph version: `.env` pins v21.0, console is on v26.0. Pin deliberately or move up?
- `per_reach: true` on `utm_sessions` optimizes session *rate*, not total traffic. Product call.
- Verification thresholds (8/arm, p≤0.05, 50% stability) → ~2–3 weeks before any comparison is
  evaluable at 1–2 posts/day. Product call, not statistical.
- Phase 3 second channel: IG suits swimmer cards (1080×1350) but not tall event boards.

## Next Actions

1. Real React dashboard — mockup at https://claude.ai/code/artifact/07628879-ccba-42d1-aab6-1383e94dd3cd
   **or** orchestrator + DB so drafts persist. User's call.
2. Retry the Meta token via System User.
3. `uv sync && uv run alembic revision --autogenerate -m "initial schema"` once Postgres is up.
