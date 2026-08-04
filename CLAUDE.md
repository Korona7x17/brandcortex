# CLAUDE.md — BrandCortex

AI content engine that generates, publishes, and self-improves brand content across channels.
Home: `brandcortex.app`. Tenant #1: **ThaiSwim**. Channel #1: **Facebook**.

Full spec: `docs/BrandCortex-architecture.md`. Read it before any non-trivial change — this file is the
working summary, that file is the authority.

**Exception:** `docs/thaiswim-integration.md` records what the ThaiSwim repo (`dev/thaiswim`) actually
contains, and **overrides the spec where they disagree** — §4.2, §4.3 and §5.1 were written before the
card engines were read. Short version: there is no *shared* bucket (cards render on demand from a
public URL; BrandCortex captures the PNG into its own store at draft time), and `card_renders` already
is the handoff table. The card engines are not to be modified — everything missing is derived our side.

## The one rule that shapes everything

**The core never learns brand or channel identity.** No `"thaiswim"` or `"facebook"` string may appear
in `core/`. Brands enter through source adapters, channels through channel adapters, specifics through
`brand_config` and the `playbook`. Adding brand #2 or channel #2 must be a config-and-adapter job.

Counterweight: **do not build the multi-tenant management layer until a real second brand exists.**
Neutral architecture yes; tenant machinery no. `brand` is a keyed column, not a subsystem.

## Layout

```
apps/api/                       FastAPI backend — core, adapters, workers
  src/brandcortex/
    core/                       brand- & channel-agnostic. NO adapter imports, NO brand strings.
      generation/               content item + brand_config + playbook -> {post_text, first_comment_text}
      scheduling/               slot assignment: alternation, spacing, preferred times
      learning/                 features, playbook, reflection agent, experiments
      analytics/                joins posts x features x insights; UTM
      orchestrator.py           wires ingest -> generate -> review -> schedule -> publish -> measure
    adapters/
      base.py                   SourceAdapter / ChannelAdapter protocols — the stable seams
      source/thaiswim/          content-item handoff from Share-Card Studio
      channel/facebook/         Graph API publish, first comment, tokens, insights
    db/models/                  SQLAlchemy models (see §5.2 of the spec)
    api/routes/                 HTTP surface for the review UI
    workers/                    ingest watcher, publisher, insights fetcher, reflection agent
apps/web/                       Next.js review dashboard (drafts, calendar, analytics, playbook)
packages/contracts/             content-item envelope JSON Schema + generated TS types
docs/                           architecture spec
```

Import direction is one-way: `api`/`workers` -> `core` -> `db`/`schemas`. `adapters` may import `core`
contracts; **`core` may never import `adapters`.** Adapters are resolved at runtime via
`adapters/registry.py`.

## Non-negotiable domain rules

- **Links go in the first comment, never the post body.** Facebook is trialing a ~2-links/month body
  cap; comments are exempt, and photo posts out-reach link posts. Every publish is: photo + caption,
  then immediately a comment carrying the canonical link.
- **The brand DB is the source of truth and is read-only to us.** BrandCortex references content by
  `content_id` and stores only its own post/learning state. Never write a `posted` flag back to the
  brand DB. "Downloaded/generated" (brand side) and "posted to channel" (our side) are different events
  — ThaiSwim's `card_renders` already means the former, written only on Download, never on preview.
- **Capture the card PNG at draft time and publish those bytes** (`services/assets.py:capture`). The
  studio's Download button already freezes the image this way. Never publish by handing Facebook a
  render URL — that would put the render timing in Meta's hands instead of ours.
- **House voice is a fixed constraint, not an optimizable lever.** Understated, factual, warm.
  Recognition, not advertising. No superlative drumroll, no stacked emojis, no cheesy lines, 0–1 emoji.
  Never echo the asset's on-image tagline in the copy. Voice lives in `brand_config`, but the learning
  loop is forbidden from tuning it — only the approval gate can change it.
- **North star is UTM-tracked sessions + amplification (shares/saves), never raw reactions.** This is
  the guardrail that stops the self-improving loop drifting into clickbait: hype wins reactions in the
  short term, and optimizing reactions would rediscover the voice the owner rejected. Reactions are
  recorded, never targeted.
- **Human-in-the-loop first.** Full auto-publish only after the generation engine has earned trust.
- **Every playbook change is versioned and revertible**, carries evidence + sample size + confidence,
  and is confidence-gated — never overreact to one post.
- **Nothing grades its own work.** See below; this is a structural rule, not a preference.

## No self-review

An agent that writes an answer and also rates its confidence in that answer is not a check. Neither is
a "fresh instance" of the same model handed the first one's reasoning — what you withhold matters more
than which weights you call. Four mechanisms cause it: shared context, shared priors, agreement bias,
and no ground truth. Each needs a different fix, applied in this order:

1. **Prefer a computation to a critic.** Code can't be persuaded, costs nothing, and is itself testable.
   `generation/claims.py` (every number in a caption must exist in `facts`) and
   `learning/verification.py` (sample floor, permutation test, leave-one-out stability) are both this.
   Reach for a model only after asking whether the question has an arithmetic answer.
2. **Let reality review it.** Every playbook rule records a falsifiable `prediction` *before* it
   activates and is scored against outcomes afterwards. A rule that fails its own prediction retires
   regardless of how clean its original evidence looked. The world is the one reviewer that does not
   share the model's priors.
3. **Withhold the writer's reasoning.** `skeptic.challenge()` takes the claim and the raw observations —
   never the reflection agent's analysis or self-reported confidence. Don't "helpfully" pass them.
4. **Invert the burden of proof.** Ask the model to *refute*, defaulting to refuted when uncertain.
   Never ask "is this good?"
5. **Diverse lenses, not more votes.** Four different questions (confound, multiplicity, consistency,
   generalization) beat four opinions on one question, which mostly correlate. Any single refutation
   blocks — majority voting is wrong when the lenses ask about different things.
6. **Audit the checker.** A skeptic that has rejected nothing is a ritual, not a safeguard. Check
   `skeptic.rejection_rate()` against reality, and keep `CALIBRATION_CASES` (known-bad findings it must
   reject) passing.

Where **not** to apply it: the caption path. Numeric grounding + voice validator + human review is
proportionate for three sentences. A skeptic agent there costs latency and money to second-guess
something a person reads anyway. All of this belongs in the learning loop, where a model's output
silently becomes the instructions for every future post.

## Out of scope (don't propose these)

Monitoring the general Facebook feed, other Pages, or groups — Meta removed the API (CrowdTangle shut
down 2024). No Facebook scraping. Brand sites carry no Meta permissions; BrandCortex holds all channel
credentials.

## Working conventions

- Python 3.12, FastAPI, SQLAlchemy 2.0 (typed `Mapped[]`), Alembic, Pydantic v2, `uv` for deps.
- Any schema change gets an Alembic migration in the same change. Never edit an applied migration.
- The content-item envelope (`packages/contracts/schemas/content-item.schema.json`) is the one interface
  to keep stable. Changing it means versioning it, not editing it.
- Secrets via env (`.env.example` is the manifest). Channel tokens are encrypted at rest in
  `channel_tokens` — never logged, never returned by an API route.
- **Locale is per-item and first-class — never hardcode one.** Templates, intro banks, and hashtag sets
  are all keyed by locale, and the adapter *resolves* the value (`mapping.resolve_locale`) rather than
  assuming it. ThaiSwim runs Thai in practice; brand #2 is expected to be English, so a `locale == "th"`
  constant anywhere is a bug waiting for that brand. Thai copy is first-class, not a translation of
  English — never "fix" Thai strings in the intro bank, hashtags, or templates.
- Two current ThaiSwim data limits, neither of them design decisions: the swimmer card route takes no
  `lang` (its image is Thai regardless), and `card-history` doesn't record the event card's `lang`, so
  event items fall back to `brand_config.default_locale`. Recording `lang` is a one-line change to the
  history route — not the card engine — and English event posts then work with no change on our side.
- Tests: `pytest`, `apps/api/tests/`. Adapters get contract tests against the protocol; core gets unit
  tests with fake adapters — never hit the Graph API in tests.

## Build phases (current: Phase 0/1)

- **Phase 0** — already done on the brand side. `card_renders` carries everything the envelope needs,
  so no new table, no shared bucket, and **no changes to the card engines**. What remains is ours: a
  read-only Postgres role scoped to `card_renders`; brandcortex.app stood up; Meta app registered and
  App Review + business verification started, which takes 1–2 weeks and blocks production publishing,
  so start it first.
- **Phase 1 (MVP)** — intake, generation engine (playbook-aware even while the playbook is empty),
  minimal review UI, Facebook adapter (photo + first comment), and `post_features` capture starting
  from the very first post so the learning loop has history when it turns on.
- **Phase 2** — calendar + scheduler, insights fetcher + dashboard, UTM wiring, reflection agent,
  experiments, content-opportunity scanner.
- **Phase 3** — own-Page inbox triage, Sentinet open-web listening, second channel adapter.

Learning is slow by design: at a few posts/day, meaningful signal takes weeks to months. Ship the
hand-authored priors from the spec on day one and let evidence tighten them.

## Open decisions (don't silently pick one)

1. ~~Handoff table-watch vs direct API as primary intake.~~ **Settled by the code:** table-watch on
   `card_renders`. There is no on-demand render API on the brand side; whether to build one is a
   Phase 2 question the opportunity scanner forces, since it wants cards nobody has made yet.
2. Shared vs separate physical DB server for brand DB and BrandCortex DB.
3. Unit label standard: `50 ม.` vs `50 เมตร` — must be one, everywhere. Note the card engines already
   render `${dist} ม.`, so captions should match unless the cards change too.
4. How much Phase 2 scheduling is automated vs human-chosen.
5. Whether Phase 1 posts immediately or always schedules. Drift argues for publishing soon after
   approval: the longer a card sits, the likelier the image no longer matches the caption.
6. Second channel for Phase 3: IG vs LINE vs email. IG is the natural fit — the cards are already
   1080-wide portrait graphics — but the swimmer card's 1080×1350 is IG-native while a 10-row event
   card at 1080×1928 is not.
