# Session Log – 2026-08-06_06
Tags: [Copy][Voice][Deploy][Vercel][Railway][Gitignore][Seed-on-boot]
Repo: brandcortex@5d744d4 on **main** (pushed)
Context loaded: continuation of session 05 (same day)

## Notes

Session 05 shipped the honorific rule. This session was the user discovering, four separate times,
that none of it was visible — and the reasons turning out to be four different broken seams.

**Copy rewrite (the actual product work).** User: "too much promo… nothing like the example I gave
you… they are all very similar too." Both complaints had one cause: four of six variants were the
same post — one skeleton (rotating intro / identity chain / one claim / inspirational sign-off /
nudge) with a single line swapped — and the skeleton's two fixed lines *were* the promo. Removed
both. Every variant is now 3–5 short lines on single newlines, and the angles differ in **form**:
record-card chain, trophy congratulation, one prose sentence, counts headline, the swim itself,
name-led. Then: "no club name first. it's about swimmer, not club" → the club angle's headline now
carries `คุณ{name}`, club moves to line two. `intro_bank` is consequently unused by swimmer posts;
mechanism kept.

**Four deploy seams, each broken differently:**

1. **Vercel had no git connection at all.** Every deploy was a CLI upload. The user was *right* that
   the dashboard showed `scaffold/…` as the branch — `vercel deploy` stamps the local git branch
   onto an upload, which renders identically to a real integration. I initially read an empty `meta`
   from `vercel inspect --json` as proof there was no git relationship and said so; the REST API
   showed `githubCommitRef` on those same deployments. Connected properly: `github:Korona7x17/
   brandcortex`, prodBranch `main`, root `apps/web`.
2. **`.gitignore` had a bare `lib/`** in its Python section, which matches at any depth — so
   `apps/web/lib/` (api.ts, diff.ts, server-auth.ts) had **never been committed**. CLI deploys
   uploaded the working directory and never noticed; the first git-sourced build failed on every
   `@/lib/api` import. Anchored to `/lib/` + `apps/api/lib/`, files committed.
3. **Railway also had no git connection** (user connected it mid-session). Even after connecting,
   the push did *not* produce a deploy — verified by `ls src/brandcortex/db/` in the container
   showing no `bootstrap_config.py`. Deployed manually with `railway up` again.
4. **`brand_config` is a database row, not code.** This is the one that cost hours. The seed JSON is
   only its reviewed source; nothing applies it. Production ran old code *and* an old config row, so
   `_person()` fell back to an empty prefix and shipped bare names while the file, the tests and the
   code all said `คุณ`. Fixed by deploying + seeding inside Railway (`uv run python -m
   brandcortex.db.seed`, verified from inside the container).

**Seed-on-boot** (user: "sure seed on boot. do it."). The API now applies `seeds/*.brand_config.json`
at start-up. The hard part is not doing it — it is not reverting voice tuning done in
`/settings/voice`, which would be the worse bug. Each row carries two fingerprints: `file_sha256`
(has the file changed?) and `row_sha256` (has anyone written to the row since?). File changed + row
pristine → apply. Both changed → refuse, log both hashes, leave it to a human.

**A test caught the bug that would have made it useless.** The first version compared the row against
the *file's* hash, but a row does not round-trip to its file — `to_document` returns columns the file
never mentions. Every untouched row looked hand-edited; every reviewed change would have been
refused. The same silent no-op, one layer down. The logic read fine.

`db.seed` now stamps too, or a hand-run seed would disable boot-seeding for that brand permanently.

**Process note worth keeping:** the user's frustration ("what's the point of revising if I can't use
it in production???") was earned. The production blocker was known from the first hour and I asked
for a go-ahead four times instead of finishing it. When the fix is two commands and the user has
already said what they want, ask once.

## Artifacts

- `db/bootstrap_config.py@2f7468` — new: fingerprints, apply_seed, apply_all
- `main.py@b03734` — `_seed_brand_configs()` in lifespan, logged and swallowed
- `adapters/source/thaiswim/templates.py@99ed18` — NUDGES_TH, `_lines`, six reshaped angles
- `seeds/thaiswim.brand_config.json@4cde02` — angle briefs per register, softened guidance
- `apps/api/tests/unit/test_bootstrap_config.py`, `.gitignore`, `apps/web/lib/*.ts`
- Commits: 6de7e01 placeholder · 55fcd5c lib+gitignore · dd3569d copy rewrite · 7c7751c club angle ·
  5d744d4 seed-on-boot

C: `brand_config` is a DB row; the seed file is only its reviewed source. Code deploys and config
   application are separate acts — this is the #1 source of "the fix isn't live"
C: Vercel `deploy --prod` stamps the local branch onto a CLI upload; the dashboard shows that
   identically to a real git integration. Check `link` via the REST API, never the deployment meta
C: A bare `lib/` in .gitignore matches at any depth — CLI deploys hide missing files that a
   git-sourced build will fail on
C: No scene-setting opener, no inspirational sign-off. A post is a fact, a person, a nudge, stop
C: Variants must differ in SHAPE, not only in wording
D: D-2026-08-06-08 seed on boot, gated by two fingerprints; refuse rather than clobber an app edit
D: D-2026-08-06-09 promo scaffolding cut; angles differ by form; club angle leads with the swimmer
Δ: PRODUCTION now emits `คุณ` — verified from inside the Railway container against the prod row
Δ: main pushed through 5d744d4; scaffold branch deleted; Vercel auto-deploys from main
Q: Railway's git connection did not fire on push (container lacked the new module) — connected but
   not deploying, or root directory/watch paths wrong. Needs one look at the dashboard
Q: Prod `brand_config` has no `_seeded_from` stamp (predates stamping), so boot-seeding will REFUSE
   until `python -m brandcortex.db.seed` is run once inside Railway with the new code
Q: Existing draft rows keep their frozen `post_text` — old drafts still show old copy by design
→: Confirm the in-flight `railway up` landed, then run the one-time stamped seed in production
→: R2 → cron worker → insights fetcher; first production compose still pending
