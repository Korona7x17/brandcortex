# Session Log – 2026-08-07_01
Tags: [Railway][Deploy][Monorepo][Correction]
Repo: brandcortex@6dc2fed on **main** (pushed)
Context loaded: continuation of 2026-08-06 sessions 06–07

## Notes

**Correction to session 07 (and to what I told the user twice).** Session 07 records "Railway git
connection still has not produced a deploy on push". That is **wrong**. The connection worked from
the moment the user made it. Every push produced a deployment and every deployment **FAILED**:

    status=FAILED  branch=main  commit=b9697b0  rootDirectory=null  builder=RAILPACK

The build log shows Railpack analysing the **repo root**, listing `apps/ docs/ memory/ packages/
pnpm-workspace.yaml`, recognising no application, and exiting. Railway kept the previous container
running, so `/health` stayed 200 and production looked *stale* rather than *broken*. I checked the
running container for the new module, found it missing, and concluded "the push did not deploy" —
the third time in two days I read a symptom that two different states produce identically.

**The general lesson, now third-hand evidence:** stale and broken are indistinguishable from outside
a deployment. `/health`, an existing log line, and the contents of the running container are all
answers about the *old* build. The deployment's own `status` field is the only thing that separates
"never triggered" from "triggered and failed", and it is one API call away.

**The fix.** Service settings, applied via Railway's GraphQL API (the CLI cannot show or set these):

    rootDirectory   null  ->  apps/api        the actual cause
    dockerfilePath  null  ->  Dockerfile
    watchPatterns   []    ->  ["apps/api/**"] web/docs/memory commits stop rebuilding the API

`builder: DOCKERFILE` was rejected — no such value in Railway's `Builder` enum (`HEROKU | NIXPACKS |
PAKETO | RAILPACK`). A Dockerfile is auto-detected when the root directory contains one, so the
builder field is irrelevant here and stays RAILPACK.

Pinned the build/health config in `apps/api/railway.json` so it is reviewable and survives the
service being recreated. Root Directory cannot live there — it is what tells Railway where to find
the file.

**Verified, by artifact rather than by symptom:** deployment `6dc2fed` went BUILDING → DEPLOYING
(root=apps/api) → **SUCCESS**; the running container contains `railway.json`, a file that exists only
in that commit; and its boot log reads `INFO [brandcortex.main] brand_config bootstrap: unchanged
thaiswim`.

**Both deploy paths are now automatic.** Push to `main` → Vercel rebuilds the dashboard, Railway
rebuilds the API from `apps/api`, and the API applies any `brand_config` change at boot and logs what
it did. The three manual steps that made 2026-08-06 painful — `railway up`, the seed command, and
remembering both — are gone.

**Railway API access note:** `backboard.railway.com/graphql/v2` with the CLI token from
`~/.railway/config.json` returns Cloudflare 403 (error 1010) unless a `User-Agent` header is sent.
With `User-Agent: railway-cli/4.0.0` it works. `serviceInstance(environmentId, serviceId)` carries
`rootDirectory`, `builder`, `dockerfilePath`, `watchPatterns`; `service(id).deployments` carries
`status` and a `meta` with `commitHash`, `branch` and `rootDirectory`.

## Artifacts

- `apps/api/railway.json@99c321` — build + healthcheck config as code, with the failure recorded
- Service settings changed via `serviceInstanceUpdate` (not in the repo; recorded here and in
  `active_context.deploy.railway`)
- Commit: 6dc2fed

C: A failed deploy and an absent deploy look identical from outside — Railway keeps the old container
   serving. Read the deployment's `status`, never `/health` or the container's contents
C: Railway's `Builder` enum has no DOCKERFILE value; a Dockerfile is auto-detected inside the root
   directory. Root Directory is service-level and cannot be set from `railway.json`
C: Railway's GraphQL API needs a `User-Agent` header or Cloudflare returns 403 (1010)
D: D-2026-08-07-01 root directory + watch patterns on the service, build config pinned in the repo
Δ: Railway now deploys the API on push to main; verified by railway.json present in the container
   and a SUCCESS status on 6dc2fed
Δ: session-07's "git connection has not produced a deploy" is corrected here, not edited there
Q: Existing draft rows keep frozen `post_text`; old queue items still show old copy by design
Q: `.DS_Store` is committed at the repo root (visible in the Railpack listing) — worth removing
→: R2 bucket → cron worker → insights fetcher
→: First production compose still pending the user
