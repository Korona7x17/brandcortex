# Deploying BrandCortex

Three pieces, three homes. The dashboard (`apps/web`) goes to Vercel like any Next app; the API,
its Postgres and the publisher worker go to Railway, because the worker has to wake on its own
schedule and Vercel functions only wake when called; captured card PNGs go to R2, because a
container's disk does not survive a redeploy.

Auth is fail-closed end to end: an API deployed with no `CLERK_ISSUER` serves nothing but
`/health`. There is no order of operations that leaves the publish endpoints open on the internet.

## 1. Clerk (owner does this — needs the account)

1. [clerk.com](https://clerk.com) → Create application. Name: BrandCortex. Enable the sign-in
   methods you actually want (email code is plenty for one reviewer; add Google if preferred).
2. From the application's **API keys** page take three values:
   - Publishable key → `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
   - Secret key → `CLERK_SECRET_KEY`
   - Frontend API URL (looks like `https://xxx.clerk.accounts.dev`) → `CLERK_ISSUER`
3. Clerk instances start in development mode; that is fine for first deploy. Moving the instance
   to production mode later (custom domain, `clerk.brandcortex.app`) changes the issuer — update
   `CLERK_ISSUER` on Railway when that happens.
4. **Restrict sign-ups.** Clerk → User & Authentication → Restrictions → allowlist. This dashboard
   publishes to a live Facebook Page; a sign-in wall that anyone can register through is not a wall.

## 2. R2 (Cloudflare account)

1. R2 → Create bucket `brandcortex-cards`. No public access.
2. Create an API token scoped to that bucket, Object Read & Write.
3. Values for Railway:
   - `ASSET_BUCKET=brandcortex-cards`
   - `ASSET_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com`
   - `ASSET_ACCESS_KEY_ID` / `ASSET_SECRET_ACCESS_KEY` from the token
   - `ASSET_REGION=auto`

## 3. Railway — API + Postgres + worker

1. New project → **Postgres** (one click). Copy its `DATABASE_URL` (use the private/internal URL).
2. **API service**: New service → GitHub repo → root directory `apps/api` (it has the Dockerfile;
   the start command migrates then serves). Networking → Generate domain, or attach
   `api.brandcortex.app`.
3. **Worker service** — *not what runs today; see the note below.* Same repo and root directory,
   but override the start command: `uv run python -m brandcortex.workers.publisher`
   and set a **cron schedule** of `*/5 * * * *`. One cycle per run; the platform owns the restart
   policy. (Slots have minute precision, so five-minute polling publishes at most ~5 min late —
   well inside the 6h lateness ceiling.)

   > **While assets live on a volume, there is no worker service.** A Railway volume attaches to
   > exactly one service, so a cron container cannot read the card PNGs it would publish. Until
   > `ASSET_BUCKET` is a bucket rather than a path, the API publishes from inside its own process
   > (`workers/publisher_loop.py`, every `PUBLISHER_INTERVAL_SECONDS`), which is the process that
   > has the volume mounted. It takes a Postgres advisory lock, so adding replicas is safe.
   > Creating the worker service above is step one of retiring that loop; step two is deleting the
   > module and setting `PUBLISHER_ENABLED=false` on the API.
4. Environment variables, both services (Railway shared variables fit this):

   | Variable | Value |
   |---|---|
   | `BRANDCORTEX_ENV` | `production` |
   | `DATABASE_URL` | from the Postgres service |
   | `BRAND_SITE_URL` | `https://thaiswim.com` |
   | `ASSET_*` | from §2 |
   | `TOKEN_ENCRYPTION_KEY` | **the same key as local** — the Facebook Page token in `channel_tokens` is encrypted with it |
   | `ANTHROPIC_API_KEY` | from local .env |
   | `FACEBOOK_APP_ID` / `FACEBOOK_APP_SECRET` / `FACEBOOK_GRAPH_VERSION` / `FACEBOOK_PAGE_ID` | from local .env |
   | `CLERK_ISSUER` | from §1 |
   | `CLERK_AUTHORIZED_PARTIES` | `https://brandcortex.app` |
   | `CORS_ALLOW_ORIGINS` | `https://brandcortex.app` |

   Never set `AUTH_DISABLED` here. Its absence is what keeps the fail-closed default in force.
   `PUBLISHER_ENABLED` is the same shape in reverse: leaving it unset is what lets a deployment
   publish, and `BRANDCORTEX_ENV=local` is what stops a laptop doing the same.

5. Seed the production DB once (Railway shell or locally against the public `DATABASE_URL`):
   `uv run python -m brandcortex.db.seed seeds/thaiswim.brand_config.json`
   Then re-run the token flow against production —
   `FACEBOOK_PAGE_ACCESS_TOKEN` route of `authorize.py`, or copy the `channel_tokens` row — the
   row is portable **only** because `TOKEN_ENCRYPTION_KEY` is the same.

## 4. Vercel — dashboard

1. Import the repo; **root directory `apps/web`** (Vercel detects pnpm + Next).
2. Environment variables:
   - `NEXT_PUBLIC_API_URL=https://api.brandcortex.app` (or the generated Railway domain)
   - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` / `CLERK_SECRET_KEY` from §1
3. Domains → add `brandcortex.app`.

## 5. DNS (wherever brandcortex.app is registered)

- `brandcortex.app` → Vercel (they show the exact A/CNAME records on the domain page)
- `api.brandcortex.app` → CNAME to the Railway service domain

## Order that avoids dead ends

Clerk → R2 → Railway (API up, seeded, token in) → Vercel → DNS. The API can sit deployed and
locked with no dashboard pointing at it; the reverse — dashboard first — just renders sign-in and
then 401s until the API exists.

## What "deployed" must prove before it counts

1. `https://api.brandcortex.app/health` → `{"status": "ok"}` and `/posts` → **503/401, not data** —
   the lock engaged.
2. Signed out, `brandcortex.app` redirects to sign-in; an email outside the allowlist cannot get in.
3. Signed in, the queue renders and card images load (the `/card/[id]` proxy carries the session).
4. `GET /health/channels` on the API → `facebook: ok` (proves `channel_tokens` + encryption key
   made the trip).
5. A test draft composes, approves, schedules — and the worker's next cycle publishes it.
