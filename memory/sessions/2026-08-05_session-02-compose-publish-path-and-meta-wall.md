# Session Log – 2026-08-05_02
Tags: [Compose][Model-writer][Scheduler][Facebook-publish][Meta-auth][Blocked]
Repo: brandcortex@ef105d9 on scaffold/thaiswim-facebook-mvp (unpushed) ·
thaiswim@e70ccfa on main (pushed, deployed to Vercel)
Context loaded: project_snapshot.md, daily_summary_2026-08-05.md, session-01

## Notes

Continued from session 1. User pushed back — correctly — that a review queue for cards made in
ThaiSwim's admin is "a caption writer with extra steps". Three rounds of scope followed, then a wall.

**BrandCortex can now originate content.** ThaiSwim's card routes turned out to be a public,
deterministic render API and its swimmer search is CORS-open, so composing needs no change to the
card engines. `/new` searches swimmers, previews the live render, and drafts. Numbers come from two
new ThaiSwim payload routes built on the same builders the PNG engine uses, so caption figures cannot
disagree with the image.

**The model writes now.** Templates were one caption with one of five openers; the user judged that
too thin and was right — six hand-written angles have a low ceiling and made me the bottleneck on a
Thai brand's voice. Angles are now data in `brand_config`, editable at `/settings/voice`, and an
LLM writes against them with templates as the fallback. Verified against a real (funded) key.

**Scheduler implemented** against the brand's own policy, returning the reasons for its choice so an
override is informed rather than a shrug.

**Meta blocked the whole day.** Publish path built and tested against a fake Graph; still no token.

## Bugs caught in own work

- `claims.check` rejected *correct* copy: `สระ 50 ม.` is a 50-metre pool, not a claim about the
  swim, so every event at a distance other than 50 failed. Brand notation now stripped before number
  extraction; three tests pin it, one proving the exemption is not a hole
- `unit_labels` were in config and never reached the prompt — the model wrote `เมตร` and raw `LCM`
  because nothing told it the standard. My omission, not a model limitation
- Regenerating a failed post 500'd: I parsed the canonical link out of the first comment, and a post
  that failed before drafting has none. Link now stored on the post
- Variants collided on regenerate (unique constraint) — old set now deleted and flushed first
- All six variants shared one intro after the first draft: rotation was excluding lines rather than
  ordering them, so a small bank offered six identical openers
- A funded API key made every ingest in the suite call Anthropic for real; tests hung. Pinned offline

## Artifacts

- api/src/brandcortex/adapters/channel/facebook/adapter.py@fc6ba8
- api/src/brandcortex/adapters/channel/facebook/client.py@0ba36f
- api/src/brandcortex/adapters/channel/facebook/tokens.py@793e62
- api/src/brandcortex/adapters/channel/facebook/authorize.py@9fe17f
- api/src/brandcortex/workers/publisher.py@f54b34
- api/src/brandcortex/core/scheduling/scheduler.py@20c8e9
- api/src/brandcortex/core/generation/writer.py@7af7ff
- api/src/brandcortex/core/generation/claims.py@5f2e3e
- api/src/brandcortex/api/routes/brands.py@f63f35
- api/tests/unit/test_facebook_publish.py@0e6b32
- api/tests/integration/test_publisher_worker.py@4847dc
- web/app/new/composer.tsx@740127
- web/app/settings/voice/editor.tsx@3c5776

## Status

154 passed, 9 skipped. `alembic check` clean. Three commits: 9a5717b compose+angles+tenant,
ef105d9 publish path, plus memory. **Nothing published to Facebook. The product does not yet do
the thing it exists for** — the user said so plainly and is right.

C: BrandCortex is now an *origin* of content, not only a follower of `card_renders` — this reopens
   open decision #1, and composed cards never appear in ThaiSwim's history (brand DB stays read-only)
C: BrandCortex holds the schedule; Meta's native scheduling is refused because a comment cannot
   attach to a post that does not exist, and a live card with no link is the failure to prevent
C: The model writes and code checks; it is never asked to judge its own caption
C: Brand notation, claim-to-fact bindings and angles are all data in `brand_config` — the user edits
   the voice without a code change
C: Tests never call Anthropic; a real key in the environment must not turn the suite into billing

D: See design_decisions.md D-2026-08-05-10..17; rejected_ideas.md R-2026-08-05-02..04

Δ: facebook/{client,tokens,adapter,authorize}.py — the whole publish path, 16 tests vs a fake Graph
Δ: workers/publisher.py@f54b34 — due posts, 6h lateness ceiling, per-post failure isolation
Δ: core/generation/writer.py@7af7ff — model writer behind a seam; templates are the fallback
Δ: core/scheduling/scheduler.py@20c8e9 — slot + reasons + what it had to relax
Δ: core/generation/claims.py@5f2e3e — +notation stripping, +claim-to-fact bindings
Δ: thaiswim: payload routes + card-snapshot.ts + privacy page, deployed to production

Q: **Meta login dialog rejects `pages_read_user_content` — a scope the app has never had and that no
   request of ours contains.** Survived: hand-built OAuth URL with five explicit scopes,
   `auth_type=rerequest`, Login-for-Business `config_id` (both token types), app published, privacy
   URL set, all five permissions Ready for testing. Untried: clicking "+ Add" on that permission so
   it stops being invalid; reading the actual request in the browser network tab
Q: `card-history` still holds its own copy of the snapshot shaping — two definitions can drift
Q: ~280 E501s (docstring prose at 101–104 vs a 100 limit) — reflow or raise the limit
Q: No auth on the dashboard; it cannot be deployed until there is

→: Resolve the scope injection — add the permission, or drive the browser and watch the request
→: Then: token → publish one post → insights fetcher → the editor-preference loop
→: Independent of Meta: Clerk auth, Railway deployment, R2 for captured cards
