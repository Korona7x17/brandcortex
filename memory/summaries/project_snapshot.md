# Project Snapshot — BrandCortex

Last updated: 2026-08-05

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
- **A published post whose link comment failed is broken, not partial.** Publish leaves it `failed`
  and recoverable and never reports success — the link is the entire reason the post exists.
- **Reviewer edits are held to the same numeric and link-placement checks as generated copy.** Those
  are not judgment; voice is checked too, and getting past it is a deliberate `brand_config` change.

## Key Decisions

D-2026-08-04-01 capture PNG at draft, not publish · -02 `card_renders` is the handoff table, no bucket
· -03 locale resolved not assumed, card engines untouched · -04 no self-review ladder · -05 z-score
before weighting, missing metric excludes never zeroes · -06 brand templates live with the adapter ·
-07 failed drafts raise, never silently repaired · -08 event captions use `rowCount` not `n` ·
-09 Alembic baseline deferred to autogenerate.
D-2026-08-05-01 rejected drafts persist as `failed`, ingest never raises (the engine still does) ·
-02 reviewer edits face the same hard checks, `posts.facts` frozen at draft · -03 UTM campaign is
`{type}-{8 hex}`, uniquely indexed, reversed by lookup · -04 status columns are Enum, never String ·
-05 ingest cursor is `max(source_generated_at)`, not a watermark · -06 brand_config round-trips via a
`settings` JSON column · -07 the orchestrator owns its commits, failures included · -08 asset store
picks filesystem vs S3 from `ASSET_BUCKET`'s shape · -09 API logs a bootstrap failure, workers raise.
Stack: T01 FastAPI+Next.js · T02 permutation test · T03 Meta Dev mode, System User is the token path ·
T04 tests build SQLite from models; `alembic check` is the migration contract.
Full text in `memory/decisions/`.

## Where things are

```
apps/api/src/brandcortex/
  core/       generation (engine, templates, voice, claims, intro_rotation)
              learning (verification, skeptic, playbook, reflection, features)
              analytics (outcomes, utm, aggregator), scheduling
              orchestrator.py  ingest -> edit -> approve -> schedule -> publish
              brand_config.py  config document <-> table
  adapters/   base.py protocols + registry; source/thaiswim/*; channel/facebook/*
  db/models/  8 tables per spec §5.2
apps/web/     DOES NOT EXIST — never scaffolded, despite CLAUDE.md's layout section
packages/contracts/   content-item envelope JSON Schema (versioned, never edited)
apps/api/seeds/thaiswim.brand_config.json   voice, intro banks (th+en), hashtags, north_star
```

**The seam:** `card_renders(id, kind, subject, params, snapshot, createdAt)`, polled read-only.
`kind` → source_type; `params` rebuilds the render URL; `snapshot` **is** the facts. No asset bucket —
cards render on demand from a CORS-open URL and are captured at draft time into BrandCortex's own
store. Canonical links and `season` are derived by the adapter.

## Current Focus

**135 pass / 9 skip.** Working offline end to end and now *persisted*: `card_renders` row → content
item → checked Thai copy → `posts` row with captured card, frozen facts, UTM campaign and features →
review API (queue, diff, card bytes, edit, approve, publish). Verified against a real migrated SQLite
database, not only fixtures.

Alembic baseline exists and `alembic check` reports no drift. Seed loader:
`uv run python -m brandcortex.db.seed seeds/thaiswim.brand_config.json`.

Still stubs: Facebook adapter `publish`/`fetch_insights`, publisher and insights workers, reflection
agent, web dashboard. **Nothing has reached a real Page.** No Postgres provisioned — the baseline has
only ever been applied to SQLite.

Credentials in `.env` (gitignored, 600): App ID `1278952477505548`, App Secret set, Fernet key
generated, Page ID `1223598310834457` (ThaiSwim.com, user is full admin).

## Open Questions

- **Ruff's line-length gate has never passed.** 281 E501s, all docstring prose at 101–104 against a
  100 limit, repo-wide and predating 2026-08-05. Paragraph reflow, or raise the limit? One line either
  way. Do **not** retry a line-by-line wrap — see R-2026-08-05-01.
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

1. Real React dashboard — the API returns everything it needs (mockup:
   https://claude.ai/code/artifact/07628879-ccba-42d1-aab6-1383e94dd3cd) **or** the Facebook publish
   path, which is writable offline against `respx` without a token.
2. Retry the Meta token via System User.
3. Provision Postgres and apply the baseline there — it has only ever run against SQLite.
4. Settle the E501 question so `ruff check` becomes a real gate.
