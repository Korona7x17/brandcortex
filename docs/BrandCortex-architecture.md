# BrandCortex — Platform Architecture & Build Scope

*An AI content engine that generates, publishes, and self-improves brand content across channels. Home: **brandcortex.app**. First brand (tenant #1): **ThaiSwim.com**. First channel: **Facebook**.*

---

## 1. What BrandCortex is

A brand-agnostic service that takes content items from a brand's data, drafts copy in that brand's voice, publishes it through pluggable channel adapters, measures the results, and rewrites its own playbook over time to do better.

Two axes of pluggability sit around a fixed core:

- **Source adapters (brands / tenants)** feed content *in*. ThaiSwim is brand #1; its source adapter hooks the existing Share-Card Studio card engines.
- **Channel adapters** push content *out* and read back performance. Facebook is channel #1; Instagram / LINE / email / blog come later as new adapters.
- **The core** — generation, the self-improving playbook, the content calendar, analytics, orchestration — knows nothing about any specific brand or channel.

### Scope discipline (read this before building)
The name and domain are the platform's *ambition*; the current build is deliberately lean: **BrandCortex running ThaiSwim as the sole configured tenant, publishing to Facebook.** No `"thaiswim"` or `"facebook"` hardcoded in core logic — brand and channel specifics live in config and adapters — but **do not build the multi-tenant management layer until a real second brand exists.** Take the neutral architecture; defer the multi-tenant machinery. This avoids premature abstraction while keeping "add brand #2 / channel #2" a config-and-adapter job, not a rewrite.

## 2. What already exists (do not rebuild)

ThaiSwim's admin contains **Share-Card Studio**, two engines that already produce everything the ThaiSwim source adapter needs:

- **Event ranking card engine** — filters (stroke, distance, gender, age group, course, Top-N, language) → PNG + canonical **rankings link**. Has a publish/download history.
- **Profile card engine** — swimmer search → PNG + canonical **profile link**. Has a publish/download history.

Both already advise "post as a Facebook photo (more reach than a link post)" and "paste the link in the caption or first comment." BrandCortex automates exactly that.

## 3. Guiding principles

1. **The core never learns brand or channel identity.** Brands enter via source adapters, channels via channel adapters. Adding IG or a second brand touches only an adapter + config.
2. **The brand's data is the source of truth.** BrandCortex never copies a brand's domain data (rankings, swimmers); it references content items by id and stores only its own post/learning state.
3. **Each system writes only its own database.** BrandCortex and a brand's admin meet at one read-only seam (the content-item handoff) plus a shared asset bucket.
4. **Let the facts speak.** House voice is understated, factual, warm — no hype, no stacked emojis, no cheesy lines. (Voice is per-brand config.)
5. **Links go in the first comment** (Facebook) — sidesteps Meta's link-per-month cap and preserves photo-post reach.
6. **Human-in-the-loop first.** Full auto-publish only after the generation engine has earned trust.
7. **Optimize for the right metric.** North star is real traffic + amplification, never raw reactions (see §11 guardrails) — this is what stops the self-improving loop from drifting into clickbait.

## 4. System architecture

### 4.1 Component map

```
  BRAND ADMIN (e.g. ThaiSwim, tenant #1)          ┌──────────── BrandCortex (brandcortex.app) ───────────┐
  ┌─────────────────────────────────────┐         │                                                      │
  │ Brand DB (source of truth)           │         │  CORE (brand- & channel-agnostic)                    │
  │ Profile card engine ─┐               │         │   • Generation engine (brand-voice aware)            │
  │ Event card engine   ─┴─► content item│──seam──►│   • Content queue / calendar                         │
  │        (image + link + facts)        │  read-  │   • Self-improving playbook + reflection agent       │
  └─────────────────────────────────────┘  only   │   • Analytics / dashboard                             │
        ▲ SOURCE ADAPTER: "ThaiSwim cards"         │   • Orchestrator                                      │
        │ (produces content items)                 │                                                      │
        └── other brands later ──►                 │  CHANNEL ADAPTERS                                     │
                                                    │   • Facebook (#1): publish photo, first-comment,    │
                                                    │     tokens, insights                                 │
                                                    │   • Instagram / LINE / email / blog (later)          │
                                                    │                                                      │
                                                    │  BrandCortex DB (its own state, per brand)           │
                                                    └──────────────────────────────────────────────────────┘
```

### 4.2 The content-item handoff (the seam)

A **source adapter** emits a content item whenever the brand produces something postable. For ThaiSwim, that's on card render. This envelope is the one interface to keep stable.

```json
{
  "content_id": "uuid",
  "brand": "thaiswim",
  "source_type": "profile | event",
  "locale": "th | en",
  "asset": { "kind": "image", "storage_key": "bucket/path.png", "width": 1080, "height": 1350 },
  "canonical_link": "https://thaiswim.com/...",
  "facts": {
    "// profile": "",
    "name_th": "ริน สืบสงวน", "name_en": "Rin Suebsanguan",
    "club": "สมาคมราชกรีฑาสโมสร", "team": "สุราษฎร์ธานี",
    "age_group": "55-59", "first_rank_count": 9, "event_count": 9, "strokes_covered": 4,
    "// event": "",
    "stroke": "backstroke", "distance": "50m", "course": "LCM", "gender": "F",
    "season": "2025-2026", "top_n": 10, "champion_name": "ริน สืบสงวน", "champion_time": "42.06",
    "// generic hint": "", "wow_factor": 0.0
  },
  "generated_at": "2026-08-04T09:03:00+07:00"
}
```

Everything the generation engine needs is denormalized here. The core never reads the brand's raw tables.

### 4.3 Integration mechanism
- **Primary — handoff table (event-driven):** the source adapter writes each content item to a `content_items` table (asset to the bucket); BrandCortex watches and ingests. An admin "Queue to BrandCortex" button just flags a row.
- **Secondary — direct API (on-demand):** BrandCortex asks the adapter to render a specific item and gets the envelope back synchronously.

### 4.4 Publish-status semantics (lock now)
ThaiSwim's engines currently equate **download** with **publish**. Split the events: the engine's history = **content generated / available**; BrandCortex's DB = the authoritative **posted-to-channel** status, per channel. Never write a `posted` flag back into the brand DB.

## 5. Data model

### 5.1 Brand DB (ThaiSwim) — additions only
- `content_items` (handoff): `content_id`, `source_type`, `locale`, `asset_storage_key`, `canonical_link`, `facts` (JSON), `generated_at`, `queued` (bool).

### 5.2 BrandCortex DB — owned by the platform, keyed by brand
- `posts`: `id`, `content_id` (ref), `brand`, `channel`, `status` (draft | approved | scheduled | published | failed), `post_text`, `first_comment_text`, `scheduled_for`, `published_at`, `channel_post_id`, `channel_comment_id`, `error`.
- `post_features`: feature vector per post (see §10) — powers the learning loop.
- `post_insights`: per `channel_post_id` — reach, impressions, reactions, comments, shares, saves, link clicks; snapshotted over time.
- `intro_history`: recent intro lines per brand (enforces no-repeat rotation).
- `playbook`: versioned learned heuristics — `rule`, `evidence`, `sample_size`, `confidence`, `status` (proposed | active | retired), `brand`.
- `experiments`: active A/B tests — `lever`, `arms`, `allocation`, `results`, `status`.
- `channel_tokens`: encrypted per brand+channel (e.g. FB Page tokens), expiry, refresh metadata.
- `brand_config`: voice rules, hashtag sets, unit-label standard, tag targets, north-star metric weighting.

## 6. Generation engine spec (brand-voice aware)

Consumes a content item + `brand_config` + the active `playbook`, returns `{ post_text, first_comment_text }` per channel.

### 6.1 House voice (ThaiSwim config)
Understated, factual, warm. Recognition, not advertising. No superlative drumroll, no cheesy lines. Never repeat the asset's own on-image tagline (e.g. "อายุเป็นเพียงตัวเลข") in the copy.

**Never open with a scene-setting line, never close with an inspirational one.** Both tell the reader how to feel about a fact the card already shows them, which is the advertising voice this brand exists in opposition to. A post is a fact, a person, a nudge, and then it stops.

Two registers are in use, and the reviewer picks between them per post:

- **Reporting** — no emoji, no congratulation. The fact stated and left to stand.
- **Congratulatory** — the owner's own shape: `🏆` headline carrying the number → `ขอแสดงความยินดีกับ คุณ{name} จาก {club}` → the achievement with `👏` → a plain line saying the link is in the first comment → hashtags. Warm and direct, addressed to the reader *about* the swimmer.

Emoji ceiling is **2** (raised from 1 to admit the congratulatory shape). Both emoji carry the congratulation; the nudge carries none, because a line that already says where the link is doesn't need decorating. The reporting angles still carry no emoji at all. Warmth comes from respect and from the numbers, never from adjectives — neither register dramatises, and neither addresses the swimmer in the second person.

### 6.2 Profile post structure
No scene-setting opener and no inspirational sign-off — both were cut on 2026-08-06 as advertising
voice, and they were also why four of six variants were one post with a line swapped. Every variant is
now **3–5 short lines**: fact, person, nudge, hashtags. Single newlines, not blank lines.

Six angles, differing in **shape** as well as in what they notice:

| angle | register | shape |
|---|---|---|
| `plain` | reporting | swimmer's line · then the achievement in plain numbers |
| `sweep` | congratulatory | `🏆` count headline → `ขอแสดงความยินดีกับ คุณ{name} จาก {club}` → achievement + `👏` |
| `longevity` | reporting | one prose sentence: in this age group, {name} from {club} still holds N |
| `breadth` | reporting | counts headline → swimmer's line (the inverse order of `plain`) |
| `standout` | reporting | one swim — stroke · distance · pool · time · rank → swimmer's line |
| `club` | congratulatory | `🏆` **club** + count → `ขอแสดงความยินดีกับ คุณ{name}` + age group + `👏` |

**First comment:** rotate the matching bank in §6.5, in the same register as the caption. Always `คุณ`
before a person's name.

### 6.3 Event post structure
Category (season, stroke + distance + course, gender, age group) → "10 อันดับแรกของประเทศในฤดูกาลนี้" → personal hook "เวลาของคุณอยู่อันดับไหน?" (the card already shows the names — tease the reader's own rank) → link-in-comment nudge → hashtags. **First comment:** `{rankings_link}`.

### 6.4 Intro rotation bank — **retired for swimmer posts**
The rotating opener was the brand's advertising voice ("ทุกฤดูกาลมีนักว่ายน้ำที่ทำให้เราต้องหยุดมอง") and is
no longer used by any swimmer angle. The bank, `intro_history` and `intro_rotation` all remain: the
mechanism is sound and another structure may want one. The engine records an `intro_line` only when
the caption actually opens with it, so an unused line is never retired from the rotation.

### 6.5 First-comment bank (profile posts)
The line above the link, rotated with the closings so six variants don't all end the same way. Named and general lines alternate: the named ones carry the honorific, the general ones are right when the caption has already named the swimmer twice — and are the only option when the card carries no name.

Reporting register (`COMMENTS_TH`):
- `📊 สถิติทั้งหมดของคุณ{name} อยู่ที่นี่` — e.g. `📊 สถิติทั้งหมดของคุณไกรศรี บุตรวงษ์ อยู่ที่นี่`
- `📊 สถิติทั้งหมดอยู่ที่นี่`
- `📊 ดูสถิติและผลงานทั้งหมดของคุณ{name} ได้ที่นี่`
- `📊 ดูโปรไฟล์และสถิติทั้งหมดได้ที่นี่`
- `📊 สถิติและอันดับทั้งหมดอยู่ที่นี่`

Congratulatory register (`COMMENTS_WARM_TH`):
- `👉 ดูสถิติและโปรไฟล์ทั้งหมดของคุณ{name} ได้ที่นี่`
- `👉 สถิติและอันดับทั้งหมดอยู่ที่นี่`
- `🏆 ผลงานและสถิติทั้งหมดของคุณ{name} อยู่ที่นี่`
- `👉 ดูโปรไฟล์และสถิติทั้งหมดได้ที่นี่`

The canonical link follows on its own line in every case.

### 6.6 Rules
**Honorific (hard rule):** never write a person's name bare in Thai copy — always `คุณ` + name, in the post body and the first comment alike. `ไกรศรี บุตรวงษ์` → `คุณไกรศรี บุตรวงษ์`. Applies to every generated surface; if the honorific is uncertain, fall back to a general no-name line from §6.5 rather than dropping `คุณ`. Locale branch (th/en) off the content item. No-repeat intro within last N posts (check `intro_history`). Core hashtags `#ThaiSwim #ว่ายน้ำไทย #ว่ายน้ำมาสเตอร์ส` (+ optional `#MastersSwimming #swimmingthailand`). One unit-label standard (`50 ม.` **or** `50 เมตร`). Tag the club/team Page when known. All of the above read from `brand_config` + `playbook`, so the engine is not ThaiSwim-hardcoded.

## 7. Publishing pipeline (end to end)
1. Brand renders content → content item + asset written.
2. BrandCortex ingests (watch, or admin flag).
3. Generation engine drafts post + first comment (per channel), reading `playbook`.
4. **Human review / approve / edit** in the brandcortex.app UI.
5. Scheduler assigns a slot: source-type alternation (profile↔event), minimum spacing (no stacked posts), preferred high-engagement time.
6. Channel adapter publishes (FB: **photo** post + caption).
7. Adapter posts the **first comment** with the canonical link immediately.
8. Record `channel_post_id`, `channel_comment_id`, status → published.
9. Insights adapter snapshots performance over the next 24–48h.

## 8. Facebook channel adapter

- **API:** Graph API, Page access token.
- **Permissions (verify against current Graph API version):** `pages_manage_posts`, `pages_read_engagement`, `pages_manage_engagement`, `pages_show_list`; business verification via `business_management`.
- **Publish photo:** `POST /{page-id}/photos` + `message`. **Schedule:** `published=false` + `scheduled_publish_time`.
- **First comment:** `POST /{post-id}/comments` — comments are exempt from the link cap → unlimited links.
- **App Review + business verification** required for production; one-time, budget a week or two. Attaches to BrandCortex only — the brand's site carries no Meta permissions.
- **Tokens:** long-lived, encrypted in `channel_tokens`, with refresh.
- **Link-cap context:** Meta is testing a ~2-links/month-in-body limit unless subscribed (~$15–500/mo). First-comment links avoid it — the reason links never go in the body.

## 9. Analytics & dashboard

Reading your *own* Page/post insights is fully supported — none of the feed-monitoring restrictions apply. Because BrandCortex publishes the posts, it already holds every `channel_post_id`, so joining performance back to *which content, caption, format, and time produced it* is free — and that's the point: Facebook's native insights can't slice by your dimensions (source type, swimmer, age group, intro line, post time), but BrandCortex can.

- **Fetcher:** snapshots each post's insights a few times over its first 2–3 days (metrics settle; Meta occasionally renames metrics — pin to a Graph API version).
- **Dashboard (brandcortex.app):** joins `posts` × `post_features` × `post_insights`. Answers "profile vs event," "best time," "which intro line," "which age groups travel."
- **True traffic via UTM:** FB's link-click number is not your site's truth, and the link lives in a comment. Tag every link with **UTM params** and read real arrivals from site analytics (GA4 / Plausible). Treat site analytics as the source of truth for traffic; the two numbers won't match.

## 10. Self-improving loop

Loop: **generate → publish → measure → reflect → update playbook → generate better.** The mechanism is the versioned `playbook` the generation engine and scheduler read before acting, rewritten on a schedule by a reflection agent.

### 10.1 Features × outcomes
**Features (per post):** source type; intro line; hook style; post time (hour + weekday); age group; stroke/event; gender; club tagged (y/n); caption length; hashtag set; locale; `wow_factor`.
**Outcomes:** reach; engagement rate; **shares/saves** (amplification — highest value); comments; **UTM-tracked sessions** (north star). Reactions recorded but not targeted.

### 10.2 Analyses
Feature attribution vs the north star; timing model per source type; format/copy/intro ranking with fatigue detection; anomaly mining (with written hypotheses); **content-opportunity scan** — reads the brand DB for high-shareability items *not yet posted* (big margins, all-stroke sweeps, milestone #1 counts) and proactively queues them (turns data into new posts, not just tuning).

### 10.3 Applying improvement
Living `playbook` (evidence + sample size + confidence + status); scheduled reflection agent emits a human-readable "what I learned" report; deliberate one-lever-at-a-time experiments (bandit-style exploit/explore); confidence-gating (never overreact to one post; lean on hand-authored priors at low volume); approval gate for voice/strategy changes, auto-tune for low-risk knobs (timing); every change versioned + revertible.

### 10.4 Guardrails (from real project feedback)
North star = **UTM traffic + amplification, not raw reactions** — an engagement-maximizing loop drifts back to the hype/cheesy voice the owner rejected, because hype wins short-term reactions; metric choice prevents that. **House voice is a fixed constraint, not optimizable.** Anti-reward-hacking: cross-check FB clicks vs real sessions. Reversibility: roll back to any prior playbook version.

### 10.5 Cold-start
At a few posts/day, meaningful learning takes **weeks to months**. Ships with the priors from this design (useful day one), tightens as evidence accumulates. The value compounds; it is not instant.

## 11. Build scope by phase

### Phase 0 — Prerequisites
- ThaiSwim source adapter emits the **content-item handoff** (asset key + canonical link + `facts` + locale) alongside existing buttons.
- Create `content_items` table + shared asset bucket.
- Stand up brandcortex.app; register the Meta app; begin App Review + business verification.

### Phase 1 — MVP (core loop, ThaiSwim + Facebook)
- Source-adapter intake; **generation engine** (voice + templates + intro rotation + locale, playbook-aware from day one even if the playbook starts empty).
- Minimal review UI on brandcortex.app: list drafts, edit, approve.
- Facebook channel adapter: photo post + immediate first comment.
- BrandCortex DB: `posts`, `post_features` (capture starts now), `intro_history`, `channel_tokens`, `brand_config`.
- **Outcome:** card → drafted post + first comment → approve → publishes correctly with the link in the first comment.

### Phase 2 — Scheduling, analytics, learning
- Content calendar + scheduler worker (alternation, spacing, preferred times); native `scheduled_publish_time`.
- Insights fetcher + dashboard (§9); UTM wiring.
- Self-improving loop (§10): reflection agent, `playbook`, `experiments`, content-opportunity scanner.

### Phase 3 — Engagement & expansion
- Own-Page inbox triage: surface comments/mentions/tags, draft replies for approval.
- Wider listening via the **Sentinet** crawler on open-web sources (not the FB feed).
- Second channel adapter (IG / LINE / email) — proves the adapter seam.

## 12. Non-goals / constraints
- **Monitoring the general Facebook feed / other Pages / groups is out of scope** — Meta removed the API for it (CrowdTangle shut down 2024). Open-web listening via Sentinet covers part of it.
- No Facebook scraping (ToS / ban risk).
- BrandCortex carries all channel permissions; brand sites carry none.
- **No multi-tenant management layer until a real second brand exists** — neutral architecture yes, tenant machinery not yet.

## 13. Open decisions
1. Handoff **table-watch** vs **direct API** as primary intake (recommend table-watch; keep API for on-demand).
2. Same physical DB server for brand DB and BrandCortex DB, or separate (logical separation holds either way).
3. Standard unit label: `50 ม.` vs `50 เมตร`.
4. How much scheduling to automate in Phase 2 vs keep human-chosen.
5. Whether Phase 1 posts immediately or always schedules.
6. Second channel to prove the adapter seam in Phase 3 (IG vs LINE vs email).
