# ThaiSwim integration — the seam as it actually exists

Findings from reading `dev/thaiswim` (Next.js 14 pnpm monorepo, Prisma + Postgres, Clerk-gated admin,
Railway). This supersedes the assumptions in `BrandCortex-architecture.md` §4.2–§4.3 and §5.1 where the
two disagree; the architecture doc was written before the card engines were inspected.

## What already exists

| Piece | Path | Note |
| --- | --- | --- |
| Swimmer card PNG | `apps/web/app/api/card/swimmer/route.tsx` | 1080×1350 fixed, `?slug=` or `?id=`, Thai only |
| Event card PNG | `apps/web/app/api/card/event/route.tsx` | 1080×**variable** height, `?stroke&dist&gender&age&course&n&lang` |
| Shared data builders | `packages/database/src/card-payload.ts` | `swimmerCardPayload`, `eventCardPayload`, `eventCardKey` |
| Swimmer studio | `apps/admin/app/tools/share-swimmer/page.tsx` | search → preview → download → copy profile link |
| Event studio | `apps/admin/app/tools/share-event/page.tsx` | selectors → preview → download → copy rankings link |
| Publish history | `apps/admin/app/api/card-history/route.ts` + `card_renders` table | written on **Download**, not on preview |

## Four differences from the architecture doc

### 1. There is no asset bucket, and none is needed

The doc assumed cards land in a shared bucket and travel as `asset.storage_key`. They don't. Cards are
rendered on demand by next/og from a URL that is fully determined by its query params, served with
`Access-Control-Allow-Origin: *` and cached at the edge (event: `s-maxage=86400`, swimmer:
`s-maxage=3600`). BrandCortex fetches the PNG from that URL at publish time.

This removes a whole moving part from Phase 0 — no shared bucket, no credentials, no write path from
ThaiSwim into storage. The seam becomes one read-only DB read plus one public HTTP GET.

**Capture the PNG at draft time and publish those bytes.** The studio's Download button already freezes
the image — the admin saves a file and posts that file — and BrandCortex should do the same rather than
re-fetching at publish or handing Facebook a `url` for Meta to fetch. Same one HTTP GET either way; it
just happens at draft, so what the reviewer approves is byte-for-byte what ships and the render timing
is never in question. The stored copy doubles as the archive of what was published.

(The `card_renders.snapshot` field and the studio's "differs" badge address a different, longer-horizon
question — whether a card posted months ago still matches today's data. That's a property of the
history view, not something the publish path needs to check.)

### 2. `card_renders` *is* the handoff table

The doc proposed adding a `content_items` table. It already exists under another name, with a better
shape:

```
card_renders( id, kind, subject, targetId, label, params JSONB,
              snapshot JSONB, fileName, createdBy, createdAt )
```

* `kind` (`"swimmer" | "event"`) → `source_type`
* `params` → the exact query the card engine was called with; regenerates the render URL exactly
* `snapshot` → the resolved values the PNG displayed → this **is** the `facts` payload
* `subject` → stable grouping key (a swimmer slug, or `stroke-distance-gender-ageGroup-course`)
* `label` → human-readable heading
* `createdAt` → `generated_at`

Critically, the publish-status semantics the doc asks for in §4.4 are **already correct**. The route's
own comment: recorded "when the admin clicks Download, NOT on preview renders." So a `card_renders` row
already means "content generated / available", never "posted". Nothing to split, nothing to fix.

The snapshot is also resolved server-side from the same builders the PNG uses — the client sends only
*which* card. So a row cannot claim numbers the image never showed. That guarantee is what makes it
safe for BrandCortex to generate copy from `snapshot` without re-deriving anything.

**Intake:** poll `card_renders` by `createdAt`. The only change ThaiSwim needs is an optional `queued`
boolean if you want the admin to opt cards in individually rather than BrandCortex taking everything.
Recommend deferring that — take everything and let the review queue be the filter.

### 3. Canonical links are derived, not stored

Both studios build the link in the browser and never persist it:

```ts
// swimmer
`${SITE}/swimmers/${slug}`
// event
`${SITE}/rankings?stroke=${stroke}&dist=${dist}&gender=${gender}&age=${age}&course=${course}`
```

`params` carries everything needed to rebuild both, so the source adapter derives them. That's fine, but
it means the link format lives in two places now — if ThaiSwim's routes change, the adapter breaks
silently. Cheap insurance: have `card-history` POST persist the canonical link into `params`.

### 4. The real `facts` keys differ from the doc's sketch

The doc guessed at field names. The actual snapshots:

**swimmer** — `name` (Thai), `romanized`, `club`, `province`, `ageGroups[]`, `goldCount`,
`goldStrokes`, `multiGold`, `rankedCount`, `topRank`, `rows[≤16]{stroke,distance,course,rank,timeMs,time,ageGroup}`

**event** — `stroke`, `distance`, `gender`, `ageGroup`, `course`, `n`, `rowCount`,
`rows[]{rank,timeMs,time,name,club,province,isRelayLeadoff}`

Mapping to the doc's §4.2 sketch: `first_rank_count` → `goldCount`, `strokes_covered` → `goldStrokes`,
`champion_name`/`champion_time` → `rows[0].name` / `rows[0].time`.

Three things the doc assumed aren't in the snapshots. **None need a card-engine change** — the adapter
derives all three:

* **`season`** — computed at render time by `rankingPairLabel()`, which is just
  `` `${year-1}-${year}` `` off the UTC year. §6.3 opens the event post with the season, so
  `mapping.season_label` mirrors that one line against `generated_at`.
* **`event_count`** — `resultCount` (every swim on record) exists in `swimmerCardPayload` but isn't
  written to the snapshot. `rankedCount` is, and "9 national #1s across 9 ranked events" is the truer
  sentence anyway, so §6.2 uses that.
* **`wow_factor`** doesn't exist anywhere. The adapter computes it — correctly so, since judging what's
  remarkable needs the sport.

## The one ask on the ThaiSwim side

**A read-only Postgres role** for BrandCortex, scoped to `card_renders` (+ `swimmers` for the Phase 2
opportunity scanner). Not a code change — a grant — and it makes the read-only seam something the
database enforces rather than something we remember.

Nothing else. The card engines stay exactly as they are.

Two consequences of leaving them alone:

* **Locale falls back rather than being read.** The event card engine takes `?lang=th|en` and the studio
  has a working toggle, but `card-history` omits `lang` from its POST, so recorded rows carry no
  language and `mapping.resolve_locale` falls back to `brand_config.default_locale` (`th`). The swimmer
  route has no `lang` at all, so that image is Thai whatever the caption locale says.

  This is a data limit, not a design decision — nothing on our side is hardcoded to Thai, because brand
  #2 is expected to be an English site. If you later want English event posts from ThaiSwim, add `lang`
  to the `card-history` POST body (one line, in the history route, not the card engine) and author an
  `en` intro bank; the adapter and engine need no change.
* **The canonical link stays derived** in `mapping.canonical_link` rather than persisted. If ThaiSwim's
  `/swimmers/:slug` or `/rankings` query format ever changes, that function breaks silently — the
  contract test in `tests/unit/test_thaiswim_links.py` pins the formats so it breaks loudly instead.

## Event card height is variable

The swimmer card is a fixed 1080×1350. The event card is `1080 × (452 + rows×130 + 176)` — roughly
1018px (3 rows) to 1928px (10 rows). So the envelope leaves `height` unset for event cards. Feed
cropping is expected and acceptable; the full card is one tap away.
