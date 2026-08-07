# BRIEF_SUMMARY (2026-08-07)

C: A failed deploy and an absent deploy are indistinguishable from outside — Railway keeps the old
container serving. Read the deployment's `status`. Railway's Builder enum has no DOCKERFILE; Root
Directory is service-level; Railway GraphQL needs a User-Agent or Cloudflare 403s (1010)
C: A Railway volume attaches to ONE service — no cron can publish while cards live on /data/cards
C: Next renders only the changed segment on a soft nav, so a root-layout side effect is not
guaranteed to have run — never let correctness depend on cross-module evaluation order
D: D-2026-08-07-01 rootDirectory=apps/api + watchPatterns; build config in apps/api/railway.json
D: -02 server code gets `api` from the module that registers its token source (silent nulls now raise)
D: -03 publish in-process behind a Postgres advisory lock until ASSET_BUCKET is object storage
Δ: Railway git connection FIXED — never broken; every push built at the repo root and failed
Δ: Soft-nav 401 ("missing bearer token") fixed — it was load order, not auth
Δ: **Scheduled posts FIRE.** First automatic publish 04:34:06Z, photo + first comment, due:1
published:1 failed:0 — verified by row state and Graph 200s, not by symptom
Q: the loop restarts with the API; a deploy mid-slot publishes on next boot. .DS_Store still committed
→: R2 → cron service (*/5) → delete publisher_loop.py; insights fetcher
