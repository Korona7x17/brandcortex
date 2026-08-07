# Session Log – 2026-08-07_03
Tags: [R2][Assets][Cron][Railway][Incident][Secrets]
Repo: brandcortex@cf4a256 on **main** (pushed)
Context loaded: continuation of 2026-08-07 sessions 01–02

## Notes

**Assets moved to R2, and the cron publisher that R2 unblocked now owns publishing.** Also one
incident that matters more than either: I leaked three production secrets into the session
transcript. That is written up last, but it is the part to read first.

### R2

Built the switch before the bucket existed, since only the bucket needed the owner's account.
`ObjectStore` gained `problems()` — what is wrong with this store *right now*, distinct from
`exists()`, which answers about one object and cannot tell a missing key from missing credentials.
That is exactly the distinction that matters the hour after a deployment is repointed. `/health/assets`
serves it. One `HeadBucket`: read-only, because the endpoint is unauthenticated and a probe that
wrote would let anyone run up storage operations. It names *conditions* and never the bucket,
endpoint, path or key — the reader already knows their own config, and nobody else should learn it
from us.

`services.migrate_assets` copies only what `posts.asset_storage_key` still names; orphans from
discarded drafts are not worth paying to store. Key format is identical on both backends, so nothing
is rewritten and no row is touched — a copy, not a migration. Two outcomes are loud and exit
non-zero: `missing` (a published post has lost the archive of what went out) and `mismatch` (two
deployments wrote independently; which copy survives is not a script's call).

Owner created `brandcortex-cards` and an Object Read & Write token scoped to it. I drove the
Cloudflare UI for the token form and stopped before the create button, so the secret never rendered
into a screenshot. Variables were set from `.env` by a script that printed only names.

Ran clean: `copied 2, missing 0, mismatch 0`, re-run `skipped 2`, both objects read back from R2 as
valid PNGs at 169,840 and 158,744 bytes. The volume is deliberately still mounted as a free rollback.

### The cron publisher

`publisher` service created, `rootDirectory=apps/api`, `cronSchedule=*/5 * * * *`. Two lessons:

* **`railwayConfigFile` resolves from the REPO ROOT, not the service's root directory.** `railway.
  worker.json` failed with "service config not found"; `apps/api/railway.worker.json` worked.
* **A cron service needs its own config file.** Sharing `railway.json` would give it the API's
  healthcheck, which a container that exits by design fails on every successful run. Hence
  `restartPolicyType: NEVER` too — the schedule starts the next run, and a restart loop would
  publish repeatedly.

Also: `railway redeploy` and `serviceInstanceRedeploy` reuse the *old* build config. Only
`serviceInstanceDeployV2` picks up changed service settings.

Confirmed by artifact: `SUCCESS root=apps/api`, log `publish cycle: {'due': 0, ...}`. Then
`PUBLISHER_ENABLED=false` on `api`. `publisher_loop.py` is left in the tree, dormant, until a real
scheduled post publishes through the cron — deletion is the one irreversible step and waiting costs
nothing.

### INCIDENT — three secrets leaked into the transcript

`railway add --service publisher --variables KEY=VALUE ...` echoes every value back to stdout as
`> Enter a variable KEY=VALUE`, **even when it arrives as a flag**. I printed the last 500 characters
of that output to confirm the command had worked. The tail of the alphabetical list was
`DATABASE_URL`, `FACEBOOK_APP_SECRET` and `TOKEN_ENCRYPTION_KEY`.

Twenty minutes earlier I had suppressed output on `railway variables --set` for exactly this reason
and printed only key names. I did not carry the rule to the next command. That is the whole failure.

**Assessment, after checking rather than guessing.** Postgres has no TCP proxy and no public
variables — it is reachable only at `postgres.railway.internal`. So:

| secret | usable by someone holding only the transcript |
|---|---|
| `FACEBOOK_APP_SECRET` | **yes** — Meta's OAuth endpoint is public |
| `DATABASE_URL` password | no — host unroutable from the internet |
| `TOKEN_ENCRYPTION_KEY` | no — decrypts ciphertext that lives only in that DB |

I had first called the Fernet key "the worst one". That was ranking before checking, and it was
wrong; corrected in the same conversation. The App Secret's actual reach is minting an app access
token (read app settings/insights, create test users, forge `appsecret_proof`). It **cannot** post
to the Page — that needs the Page token, encrypted in the unreachable database.

Meta no longer exposes a Reset control on App settings → Basic or → Advanced; it appears only after
"Show" + password. I did not click it, because the secret would have rendered into a screenshot and
leaked a second time. Advanced's visible "Reset" is for the **Client token**, which is a different
credential and must not be touched.

**Outcome:** rotation judged not worth it against a local-file exposure that cannot post. Agreed fix
is deleting the transcript file after the session. Rule written to the global `~/.claude/CLAUDE.md`
so it outlives this project.

## Artifacts

- `services/assets.py@752daa` — `problems()` on the protocol and both stores, `get_store(bucket)`
- `services/migrate_assets.py@704fe5` — referenced-keys copy, idempotent, loud on missing/mismatch
- `api/routes/health.py@b78a71` — `/health/assets`
- `tests/unit/test_asset_migration.py@59c92a` — 16 tests incl. S3 error wording and no-leak assertions
- `apps/api/railway.worker.json@fe4191` — cron build config: no healthcheck, restart NEVER
- `docs/deploy.md@e1e3e8` — §2b switch runbook, §3.3 retirement order
- `~/.claude/CLAUDE.md` (outside the repo) — the secret-output rule
- Commits: 22e1c2b .DS_Store · bd7417b R2 prep · cf4a256 worker config

C: **Never print a command's output when a secret was passed to it.** Assume every CLI echoes its
   arguments — Railway does. Success is `returncode == 0`; redact before printing any failure
C: `railwayConfigFile` is repo-root-relative, not root-directory-relative
C: A cron service must not inherit a server's healthcheck or restart policy — it exits by design
C: `railway redeploy` reuses the old build config; `serviceInstanceDeployV2` is what picks up
   changed service settings
C: `/health/*` is unauthenticated — it may say *that* a store is wrong, never *where* it is
D: D-2026-08-07-04 assets on R2, publishing moves to a cron service (retires -03)
D: D-2026-08-07-05 the secret-output rule, recorded with the incident that produced it
Δ: Cards live in R2; `/health/assets` reports `{"backend":"s3","ok":true}`; 2 objects copied and
   verified byte-for-byte; volume kept mounted as rollback
Δ: `publisher` cron service owns publishing; `PUBLISHER_ENABLED=false` on `api`
Δ: `.DS_Store` untracked (ignore rules never applied to an already-indexed file)
Q: `publisher_loop.py` still in the tree, dormant — delete after a real post publishes via cron
Q: Owner to delete the session transcript; App Secret rotation declined as disproportionate
Q: `api` and `publisher` now hold duplicate copies of every shared secret — project-level shared
   variables would give one source of truth. Not done; worth doing before a third service
→: watch the next scheduled post publish through the cron, then delete `publisher_loop.py`
→: insights fetcher
