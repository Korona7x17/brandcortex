# BRIEF_SUMMARY (2026-08-07)

C: **Never print a command's output when a secret was passed to it** — every CLI echoes its
arguments; Railway does. Success is `returncode == 0`; redact before printing any failure
C: A failed deploy and an absent one look identical from outside — read the deployment's `status`.
`railwayConfigFile` is repo-root-relative; `railway redeploy` reuses the OLD build config, only
`serviceInstanceDeployV2` picks up changed settings; a cron service needs its own config (no
healthcheck, restart NEVER) because it exits by design
C: Next renders only the changed segment on a soft nav — never let correctness depend on module
evaluation order. `/health/*` is unauthenticated: name conditions, never bucket/endpoint/path
D: -01 Railway builds apps/api · -02 server code gets `api` from the module registering its token
source · -03 in-process publisher (superseded same day) · **-04 cards in R2, publishing is its own
`*/5` cron service** · **-05 the secret-output rule, from the incident that produced it**
Δ: Railway git connection fixed; soft-nav 401 fixed; **scheduled posts FIRE** — first automatic
publish 04:34:06Z, photo + first comment
Δ: Cards in R2 (2 copied, verified byte-for-byte); `publisher` cron owns publishing;
`PUBLISHER_ENABLED=false` on api; volume kept as rollback; .DS_Store untracked
Q: INCIDENT — 3 secrets printed into the transcript. Postgres has no public proxy, so only
`FACEBOOK_APP_SECRET` is remotely usable and it cannot post. Rotation declined; owner deletes the
transcript. `publisher_loop.py` dormant until one real cron publish, then delete
→: watch a scheduled post fire via cron → delete publisher_loop.py; insights fetcher
