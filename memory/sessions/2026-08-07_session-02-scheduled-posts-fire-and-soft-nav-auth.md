# Session Log – 2026-08-07_02
Tags: [Auth][Next.js][Publisher][Railway][Production-first-post]
Repo: brandcortex@6b77160 on **main** (pushed)
Context loaded: continuation of 2026-08-07 session 01

## Notes

Two unrelated production faults reported together: "schedule post did not fire" and, on clicking
Queue, "Can't reach the API — unauthorized: missing bearer token".

**Fault 1 — the 401 was a load-order bug, not an auth bug.** `lib/api.ts` is imported by both
client and server components, so it may not import `@clerk/nextjs/server` (that poisons a client
bundle at build time). Its server-side token source was therefore *registered* by a bare
`import "@/lib/server-auth"` side effect in the root layout — which makes correctness depend on an
unrelated module being evaluated first. On a client-side navigation Next renders only the changed
segment, so an instance whose first request was a soft nav had never evaluated the layout: the call
went out with no `Authorization` header. A hard refresh renders the layout, registers the source,
and the same page works — which is why it read as intermittent. The user's own observation
("hard refresh shows the queue; clicking the link errors") is what pinned it; before that I was
chasing Clerk key/issuer mismatches, which the evidence never supported.

The fix removes the ordering question rather than fixing the order: `lib/api-server.ts` registers
the source **and re-exports the client**, so server code cannot obtain `api` without it. Six server
modules now import from there; `lib/server-auth.ts` is deleted and the root layout's side-effect
import with it. Two silent nulls became loud: an unregistered server call raises a named error, and
`auth()` failing is no longer caught and turned into "no token" — a wiring bug should not read as a
signed-out visitor.

**Fault 2 — nothing ran the publisher.** `workers/publisher.py` was complete and cron-shaped; the
missing piece was a *runner*. The blocker is physical, not code: a Railway cron is a separate
service and a Railway volume attaches to exactly one, so a cron container cannot read the card PNGs
it would publish (`ASSET_BUCKET=/data/cards`). Chosen (by the user, over R2-first): run the cycle
inside the API process, which is the process that has the volume mounted. `publisher.run_once` is
untouched — moving to a cron service after R2 is a deployment change, not a rewrite.

Two guarantees while it runs. **One publisher across the fleet**, via a Postgres session-level
advisory lock held on a *dedicated* connection — the orchestrator commits per post, and a pooled
connection that has committed may not be the one that comes back. Not because Railway runs one
replica today, but because "today" is a deployment setting and double-publishing is not recoverable.
And **a failed cycle logs and retries** rather than ending the loop: `run_once` already absorbs
per-post failures, so reaching that handler means the database or the registry is away, and both
come back.

`PUBLISHER_ENABLED` unset follows `BRANDCORTEX_ENV` — a deployment publishes, a laptop does not.
Neither is safe as a constant: a laptop posting to a live Page is the worse failure, and a deploy
that quietly publishes nothing is the bug this exists to fix.

**Shipped switched off, on purpose.** The user had answered "leave it scheduled" about the pending
02:22 post; the loop would have published it within 60s of booting. Set `PUBLISHER_ENABLED=false`
in production *before* pushing, verified the boot log, and handed over the switch. They flipped it
and redeployed themselves.

**First automatic publish, 04:34:06Z** — `due:1 published:1 failed:0`, photo `200 OK` then comment
`200 OK`, row `published` with both `channel_post_id` and `channel_comment_id` set. The pair that
has to succeed together did.

**One self-inflicted defect, caught in production and fixed.** The first boot logged
`publisher loop off (PUBLISHER_ENABLED unset and BRANDCORTEX_ENV=production)` while the variable was
explicitly `false`. A line whose only job is explaining why nothing publishes was pointing at the
wrong knob. Now it names the setting that actually decided, with a test per branch.

## Artifacts

- `apps/web/lib/api-server.ts@0cf2f4` — registers the token source and re-exports the client
- `apps/web/lib/api.ts@87e0ad` — unregistered server call raises; `lib/server-auth.ts` deleted
- `apps/api/src/brandcortex/workers/publisher_loop.py@f752c2` — `fleet_lock`, `cycle`, `run`, `start`
- `apps/api/src/brandcortex/main.py@c91d72` — loop started after the registry, cancelled on shutdown
- `apps/api/src/brandcortex/config.py@e093a7` — `publisher_enabled` property, interval
- `apps/api/tests/unit/test_publisher_loop.py@9438e9` — 13 tests (214 pass / 9 skip)
- `docs/deploy.md@933cee` — worker service marked "not what runs today", with the retirement path
- Commits: 60c7862 auth · 870a304 loop · 6b77160 log message

C: A Railway volume attaches to ONE service, so no cron service can publish while cards live on
   `/data/cards`. Object storage is the prerequisite, not a preference
C: Next renders only the changed segment on a soft nav — a module side effect in the root layout is
   NOT guaranteed to have run. Never let correctness depend on cross-module evaluation order
C: Advisory locks are held by a connection; a pooled connection that has committed may not come back.
   Hold the lock on a dedicated `engine.connect()` and unlock in `finally`
D: D-2026-08-07-02 server API access goes through the module that registers the token source
D: D-2026-08-07-03 publish in-process behind a fleet lock until ASSET_BUCKET is object storage
Δ: Scheduled posts FIRE in production — first automatic publish 2026-08-07 04:34:06Z, photo + first
   comment, verified by row state and Graph 200s, not by symptom
Δ: Soft-nav 401 fixed and live (Vercel Ready on 60c7862)
Q: The loop restarts with the API, so a deploy during a slot publishes on the next boot instead of
   missing it — acceptable now, gone once the cron service exists
Q: `.DS_Store` still committed at the repo root
→: R2 bucket → ASSET_* → cron service (*/5) → delete `publisher_loop.py`, set PUBLISHER_ENABLED=false
→: insights fetcher
