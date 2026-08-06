# BRIEF_SUMMARY (2026-08-07)

C: A failed deploy and an absent deploy are indistinguishable from outside — Railway keeps the old
container serving, so /health, existing log lines and the container's own contents all answer for the
OLD build. Read the deployment's `status`. Railway's Builder enum has no DOCKERFILE (auto-detected in
the root directory); Root Directory is service-level and cannot live in railway.json; Railway's
GraphQL needs a User-Agent header or Cloudflare 403s (1010)
D: D-2026-08-07-01 rootDirectory=apps/api + dockerfilePath + watchPatterns=apps/api/**; build and
healthcheck config pinned in apps/api/railway.json
Δ: Railway git connection FIXED — it was never broken, every push built at the repo root and failed.
Verified by artifact: deployment 6dc2fed SUCCESS, railway.json present in the running container,
boot log "brand_config bootstrap: unchanged thaiswim"
Δ: Both platforms now deploy on push; railway up + the manual seed command are no longer needed
Q: session-07 recorded "git connection has not produced a deploy" — corrected in 2026-08-07 session 01
Q: old drafts keep frozen post_text; .DS_Store is committed at the repo root
→: R2 → cron worker → insights fetcher; first production compose still pending
