# Project Snapshot — BrandCortex

Last updated: 2026-08-07 (session 01)

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
  The *owner* may still change it — the emoji ceiling moved 1→2 on 2026-08-06 to admit the
  congratulatory register. That is their call, and the loop still cannot propose it.
- **A person's name is never written bare in Thai copy.** `คุณ` + name, caption and first comment
  alike, enforced by `voice.check` and not only by the prompt. Prefix, locales and the name-bearing
  `facts` keys are declared in `brand_config`, so core stays brand-agnostic. When the honorific is
  uncertain, fall back to a line that needs no name.
- **Two caption registers, picked per post by the reviewer.** Reporting (no emoji) and
  congratulatory (🏆 headline · `ขอแสดงความยินดีกับ คุณ<name> จาก <club>` · 👏 · plain link nudge).
  Register carries through the caption *and* its first comment together.
- **No scene-setting opener, no inspirational sign-off.** Both tell the reader how to feel about a
  fact the card already shows — the advertising voice this brand is defined against. A post is a
  fact, a person, a nudge, and it stops. Variants must differ in *shape*, not only in wording.
- **A swimmer's post never leads with the club.** It is the swimmer's achievement; the club is
  prominent on line two, which is reason enough for it to repost.
- **Deploying code and applying config are separate acts.** `brand_config` is a database row and the
  seed JSON is only its reviewed source. Seed-on-boot (D-2026-08-06-08) closes the gap, but refuses
  to overwrite a row edited in `/settings/voice` — that conflict belongs to a human. Armed in
  production 2026-08-06; each boot logs what it did.
- **Verify a deploy by its `status`, not by any symptom.** Railway keeps the previous container
  serving when a build fails, so `/health`, existing log lines *and the running container's own
  contents* all answer for the old build — a failed deploy and an absent one are indistinguishable
  from outside. That ambiguity produced three wrong conclusions across two days.
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
D-2026-08-06-01 pages_read_user_content Added · -02/-03 fail-closed auth · -04 publish refuses
foreign-host links · -05 volume now, R2 before the cron worker · **-06 honorific is a config-declared
voice rule enforced by validator, not prompt** · **-07 two registers, emoji ceiling 1→2** ·
**-08 seed brand_config on boot behind two fingerprints** · **-09 no opener/sign-off, variants
differ by form, the club never leads**.
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
apps/web/     Next.js dashboard: queue · /new composer · /settings/voice · variant picker,
              schedule panel, copy buttons. Reads the tenant from brand_config, never hardcoded.
packages/contracts/   content-item envelope JSON Schema (versioned, never edited)
apps/api/seeds/thaiswim.brand_config.json   voice, intro banks (th+en), hashtags, north_star
```

**The seam:** `card_renders(id, kind, subject, params, snapshot, createdAt)`, polled read-only.
`kind` → source_type; `params` rebuilds the render URL; `snapshot` **is** the facts. No asset bucket —
cards render on demand from a CORS-open URL and are captured at draft time into BrandCortex's own
store. Canonical links and `season` are derived by the adapter.

## Current Focus

**201 pass / 9 skip.** Now LIVE at brandcortex.app; everything merged to `main` and pushed
(5d744d4). Both platforms deploy on push to `main`; the API applies `brand_config` at boot and logs it. Working end to end and *persisted*: `card_renders` row → content
item → checked Thai copy → `posts` row with captured card, frozen facts, UTM campaign and features →
review API (queue, diff, card bytes, edit, approve, publish). Verified against a real migrated SQLite
database, not only fixtures.

Alembic baseline exists and `alembic check` reports no drift. Seed loader:
`uv run python -m brandcortex.db.seed seeds/thaiswim.brand_config.json`.

**The publish path is written and tested against a fake Graph** (16 tests: photo upload, first
comment, expired tokens, rate limits, and the photo-live-comment-dead case). The scheduler honours
the brand's own policy and returns its reasons. The model writes captions with templates as fallback.

Still stubs: insights fetcher, reflection agent, publisher cron worker. **A real Page has been
reached** (2026-08-06) — the Meta wall fell to one "+ Add" on `pages_read_user_content`, the PAGE
token is encrypted in `channel_tokens` and never expires, and a post went live. Scheduled posts still
do not fire in production: no cron worker, and cards sit on a service volume that cannot be shared.

Credentials in `.env` (gitignored, 600): App ID `1278952477505548`, App Secret set, Fernet key
generated, Page ID `1223598310834457` (ThaiSwim.com, user is full admin).

## Open Questions

- **ANTHROPIC_API_KEY expires 2026-11-03** (added 2026-08-05, 90 days). Rotate by
  2026-10-27. On expiry the caption writer falls back to templates — the queue keeps
  working, the copy gets plainer. **The account currently has no credits**, so that fallback is
  already what runs on every draft.

- **Ruff's line-length gate has never passed.** 281 E501s, all docstring prose at 101–104 against a
  100 limit, repo-wide and predating 2026-08-05. Paragraph reflow, or raise the limit? One line either
  way. Do **not** retry a line-by-line wrap — see R-2026-08-05-01.
- **RESOLVED 2026-08-06 (kept as the lesson): Meta rejected `pages_read_user_content`** — a scope the app has never held and that no request of
  ours contains. It survived: a hand-built OAuth URL with five explicit scopes, `auth_type=rerequest`,
  Login-for-Business `config_id` with both token types, publishing the app, setting the privacy URL,
  and all five permissions showing Ready for testing. **Untried:** clicking "+ Add" on that
  permission so it stops being invalid (it is already in the adapter's `FUTURE_PERMISSIONS`), and
  reading the actual request in the browser network tab. Do not send the user round Meta's UI again
  without one of those — 2026-08-05 burned hours on it.
- **Superseded (resolved): Meta token blocked** — carries 3 of 5 scopes. Graph API Explorer caches an invalid scope
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
