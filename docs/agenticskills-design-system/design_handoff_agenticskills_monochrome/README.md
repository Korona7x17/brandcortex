# Handoff: AgenticSkills — Monochrome Redesign

## Overview

AgenticSkills is a curated directory for AI agent skills (SKILL.md files) and MCP servers. This handoff covers a complete monochrome redesign of the marketing + index surface — 9 pages spanning discovery, detail, browse, learn, submit, and about flows.

The design direction is **editorial, document-first, monochrome**: pure neutrals (no hue), Geist + Geist Mono + Instrument Serif italic accents, hairline rules and bordered grids in place of floating shadowed cards, mono numerals and uppercase micro-labels for all metadata. Inverted-ink (black-fill) pills replace colored S-rank/Featured badges.

## About the Design Files

The files in `designs/` are **design references created in HTML** — prototypes showing intended look and behavior, not production code to copy directly. The task is to **recreate these HTML designs in the target codebase's existing environment** (React/Next.js, Vue/Nuxt, etc.) using its established patterns, component primitives, and routing conventions.

If no environment exists yet, Next.js (App Router) with Tailwind is the recommended starting point — the design uses CSS Grid extensively, has minimal client-side interactivity, and would benefit from server components for the index/category/MCP/learn pages, all of which are mostly static content with light filtering.

The shared chrome (`monochrome.js`) is implemented as a runtime mount system because the prototype is plain HTML; in a real React/Vue codebase, replace it with proper components: `<TopTicker />`, `<Navbar active="…" />`, `<Newsletter />`, `<Footer />`.

## Fidelity

**High-fidelity.** Final typography, spacing, colors, hairline rules, and interaction patterns are all locked. Recreate pixel-perfectly using the target codebase's component library and styling system. The exact font stack, color tokens, and spacing scale are documented in `Design Tokens` below — these should map directly to your design system tokens (Tailwind config, CSS vars, theme object, etc.).

The data shown in the prototype (skill names, install counts, author names) is illustrative — wire to real data in production. Names like "Find Skills", "Frontend Design", "Vercel Labs", etc. are realistic placeholders, not commitments.

---

## Screens / Views

There are **9 pages** in the flow. Each is a standalone HTML file in `designs/`.

### 1. `index.html` — Homepage

**Purpose:** Land users, communicate the value (curated index), surface featured skills, and let them browse the full index + categories.

**Sections (top to bottom):**
1. **Designer notes** (collapsible) — keep this as a dev-only debug aid, omit in production.
2. **Status ticker** — black bar, full width, ticker feed of stats.
3. **Navbar** — sticky-feel hairline header, ⌘K search trigger, "Submit a Skill" CTA.
4. **Hero** — 2-column: left has eyebrow + headline (Geist 500 + Instrument Serif italic accent on `Skills`) + sub + CTAs + 4-stat row; right is a terminal install demo (dark, mono, 3 dots, blinking cursor). Below, full-width platforms strip (lockup of 8 platform marks + "+10 more").
5. **Featured (Editor's picks)** — 3 bordered cards in one row inside a 1px ink container border (top + bottom). Each card has: featured tag (inverted ink pill), S-rank label, name, by-line, description, platform tags, install/star stats, "Open ↗".
6. **Skills index (Browse everything)** — search input + chip filter row + sort dropdown, then a 3-column hairline grid of 12 skill cards.
7. **Categories (By discipline)** — 4×4 hairline grid of 16 categories; each cell has C01–C16 numbering, line-icon SVG, name, count, sample tags.
8. **How it works** — 3-step bordered grid (Discover, Install, Run) with line glyph + monospace command tag.
9. **Platforms** — 3-column ruled list with mono install paths/notes.
10. **Newsletter** — full-bleed ink (black) section, paper text, serif italic accent in headline.
11. **Footer** — paper background, hairline-divided 4-column.

**Layout structure:**
- `.wrap` is the page container: `max-width: 1280px; margin: 0 auto; padding: 0 32px`.
- All section grids are CSS Grid with `border-top: 1px solid var(--line); border-left: 1px solid var(--line)`, and each cell adds `border-right` and `border-bottom`. This is the project-wide pattern — never use shadows or floating cards.
- Featured/skill cards specifically use `border-top: 1px solid var(--ink); border-bottom: 1px solid var(--ink)` on the wrapper for the ink-rule emphasis.

### 2. `skill.html` — Skill Detail (e.g., "Find Skills")

**Purpose:** Per-skill page showing the long-form pitch, usage, compatibility, and related skills.

**Sections:**
1. **Hero** — breadcrumbs, large headline with serif italic accent, by-line meta row (author, verified pill, S-rank, license, updated date), lede, tag row. Right column: install panel (sticky-feeling card with 1px ink border) — distribution status row, 4-stat grid, install command in dark terminal-styled `<pre>` with copy button, segmented control for CLI / Manual / Git.
2. **Body + TOC** — 2-col layout: prose article on the left, sticky table-of-contents on the right (`position: sticky; top: 80px`). Prose has h2/h3/p/ul/pre/blockquote with hairline-dashed list bullets, ink-bordered code blocks, italic serif blockquote with left ink-rule.
3. **Compatibility matrix** — 4-col hairline grid of platforms, each row has a name + status (`Verified` / `Untested`) with a small dot indicator (filled ink for Verified, mute-3 grey for Untested).
4. **Related** — 3-col ink-rule-bordered grid of 3 related skills.
5. **Newsletter + Footer.**

**Install panel detail:**
- Outer panel: `border: 1px solid var(--ink)`.
- Header strip: padded row with mono micro-label "Distribution" + status "Live".
- Stats: 2×2 grid with `border-bottom: 1px solid var(--line)` between stats and install section.
- Install `<pre>`: full-bleed inside the panel, `background: var(--ink)`, `color: var(--paper)`, mono 13px. Copy button on the right is small + bordered + uppercase.
- Alt segmented control: 3 buttons in a hairline-bordered row, active state inverts (black bg, paper text).

### 3. `category.html` — Category Page (e.g., "Web Development")

**Purpose:** Browse all skills inside a single category.

**Sections:**
1. **Hero** (paper-2 bg) — breadcrumb, "Category 01 / 16" eyebrow, large headline with serif italic accent on the second word, lede, 4-stat hairline row (Skills count, Total installs, Officials, Last update).
2. **Filter bar** — inline search input + segmented chip filter (All / S-rank / Official / Open Source) + sort dropdown.
3. **Skill grid** — 3-col hairline grid (same pattern as homepage skills index).
4. **Sister categories** — 4-col hairline grid of "other" categories; each cell has name + count.
5. **Newsletter + Footer.**

### 4. `mcp.html` — MCP Server Directory

**Purpose:** Mirror surface for MCP servers (parallel to the skills index).

**Sections:**
1. **Hero** — has a faint dotted-grid background (radial mask at 60% 40%, `linear-gradient` 48×48px), 2-col: left is eyebrow + 3-line headline ("200+ trusted / MCP servers, / *one index*.") + lede + 4-stat hairline row; right is a `mcp.json` schema preview in a black/mono terminal-style block with syntax-colored keys/strings/comments.
2. **Editor's picks** — 3 ink-rule-bordered featured cards (GitHub, Stripe, AWS). Each has a 2-letter monogram in a 42px ink-bordered square, S-rank label, name, by-line, description, install/star foot.
3. **Browse servers** — 3-col hairline grid of MCP servers (smaller cards with 36px monogram).
4. **By integration** (categories) — 4-col hairline grid of 22 integration categories with mono numbering.
5. **Newsletter + Footer.**

### 5. `workflows.html` — Curated Workflow Bundles

**Purpose:** Showcase curated bundles of skills + MCP servers for common jobs.

**Sections:**
1. **Hero** (paper-2 bg) — breadcrumb, eyebrow, large two-line headline, lede.
2. **Workflows list** — vertical list (NOT a grid) with hairline `border-top` separators. Each row is a 3-col grid: `80px` workflow number column ("W.01"), main column (h3 with serif italic name + description + skill stack tags), right meta column (difficulty pill (Beginner = paper, Intermediate = paper-3 grey, Advanced = inverted ink), time + parts count, install count, "Open ↗"). Whole row hovers to paper-2.
3. **Newsletter + Footer.**

### 6. `learn.html` — Library / Long-form Articles

**Purpose:** House long-form guides and case studies.

**Sections:**
1. **Hero** — 2-col: eyebrow + large headline left, lede right.
2. **Featured article** (paper-2 bg) — 2-col: 4:3 placeholder image left (diagonal stripe pattern), meta + headline + summary + read-time/author/date right.
3. **Articles grid** — 6-button filter row (All / Skills / MCP / Patterns / Case studies / Reference) + 3-col hairline grid of 9 article cards. Each card is structured: 5:3 placeholder image (diagonal stripes) on top, padded body below with category + read-time meta row, h3, description, hairline-dashed foot with date + "Read ↗".
4. **Newsletter + Footer.**

### 7. `submit.html` — Skill Submission Form

**Purpose:** Form for submitting a new skill to the index.

**Sections:**
1. **Hero** — breadcrumb, "Form 01 · Submission" eyebrow, large headline with serif italic accent.
2. **Form + sidebar** — 2-col: form left (each field is a 240px label column + input column with hairline `border-bottom` between rows), 380px sticky sidebar right with 3 hairline-bordered cards: "What we look for" (ordered list), "Timeline" (Day 0 / Day 1–2 / Day 2–3), "Featured placement" (editorial-only note).
3. **Footer** (no newsletter on this page — it would be redundant since they're literally on a submission form).

**Form controls:**
- Text/email/textarea inputs: `1px solid var(--line)`, `var(--paper)` bg, focus → `border-color: var(--ink)`.
- Segmented controls (category, license): hairline-bordered button row, active = inverted ink.
- Platform multi-select: 3-col grid of checkbox labels with hairline borders, each label highlights paper-2 when its checkbox is checked (`label:has(input:checked)`).
- Submit button uses the standard `.btn` (ink fill).

### 8. `about.html` — Manifesto / About

**Purpose:** Tell the story, principles, team.

**Sections:**
1. **Hero** — breadcrumb, eyebrow, oversized headline with serif italic on "opinionated", lede.
2. **Principles** (paper-2 bg) — 3-col ink-rule-bordered grid: P.01 / P.02 / P.03 cards with serif italic accents in headlines.
3. **Story** — 2-col: 240px sticky label "Story · 2025–2026" left, prose right.
4. **Stats** — full-width black ink section (paper text), 4×2 grid of stats (border colors are `#1f1f1f` for dark-on-dark hairlines), large mono numerals.
5. **Team** — 4-col hairline grid: avatar placeholder (diagonal stripes), name, role micro-label, bio.
6. **Newsletter + Footer.**

### 9. `changelog.html` — Public Changelog

**Purpose:** Release log.

**Sections:**
1. **Hero** — breadcrumb, eyebrow, headline with serif italic.
2. **Timeline** — vertical list of releases. Each release is 200px sticky meta column (version, date, italic name) + entries column (h3 + summary + entries panel). The entries panel is hairline-bordered with rows; each row is `80px` "Added/Changed/Fixed" kind label + entry text.
3. **Subscribe block** — paper-2 bg, centered, single-row email + Subscribe button.
4. **Footer.**

---

## Interactions & Behavior

### Global

- **Top status ticker** — currently static; in production, animate the inner feed with `animation: ticker 30s linear infinite` translating left, looping. Keep the version + ⌘K labels on the outer ticker pinned (not scrolling).
- **Navbar** — `position: sticky; top: 0` with hairline border-bottom. Active link gets a `border-bottom: 2px solid var(--ink)` (or class `.active`).
- **⌘K search trigger** — clicking opens a command palette (not implemented in the prototype). Wire to your existing CmdK / Algolia / Pagefind integration.
- **Newsletter form** — submit handler currently sets the button text to "Subscribed ✓"; replace with a real subscribe API call.

### Homepage-specific

- **Designer notes block** — collapsible, toggled by the "Hide notes" button. Production should remove the block entirely.
- **Hero terminal** — has a blinking cursor (`@keyframes blink`). Static content; keep it static.
- **Featured cards & skill cards** — entire card is an anchor (`<a>`) to the skill detail page. Hover state: `background: var(--paper-2)`. The "Open ↗" arrow has a small `transform: translate(2px,-2px)` hover translate.

### Skill detail

- **Install command panel** — segmented control (CLI / Manual / Git) swaps the command in the `<pre>`. Implement via state: `selectedInstallType`, render the matching command. Copy button calls `navigator.clipboard.writeText(...)`.
- **TOC** — `position: sticky; top: 80px`; the active item gets a 2px left ink border. Wire with IntersectionObserver to highlight as user scrolls through sections.

### Filters

- **Chips** (category page, learn page, MCP categories) — single-select segmented controls. Clicking sets `.on` (ink bg, paper text), removes from siblings. Wire with router state (e.g., `?filter=s-rank`) so links are shareable.

### Form (submit page)

- Segmented buttons toggle `.on` exclusively within their `.seg` parent.
- Platform checkboxes use `:has(input:checked)` for the active label state — if your CSS pipeline doesn't support `:has()`, attach a JS click handler that toggles a class.

### Animations

Minimal motion. Only:
- **`@keyframes pulse`** — used by the live indicator dot (`.dot` in the ticker), 1.5s ease-in-out infinite, opacity 0.3 → 1 → 0.3.
- **`@keyframes blink`** — the terminal cursor, 1s steps(1) infinite, 50% opacity 0.
- **Hover translates** — `.btn .arrow` and `.open .arrow` translate ~2px on hover, 150ms ease-out.
- **No scroll-jacking, no parallax, no fade-in-on-scroll.** The aesthetic depends on the page feeling like a document, not an experience.

### Responsive

Breakpoints used in the prototypes:
- `980px` — most multi-column grids collapse to 2-col, hero 2-col stacks to 1-col.
- `768px` — workflow rows stack, skill detail body grid stacks (TOC moves above content).
- `640px` — all grids collapse to 1-col, footer collapses to 1-col.

Mobile nav is **not implemented** in the prototype — add a hamburger that opens a sheet/drawer for the nav links + the Submit CTA.

---

## State Management

This is a marketing/directory site — most pages are server-rendered static content. Per-page state needs:

- **Index/Category/Learn/MCP** — `selectedFilter` (chip), `searchQuery` (input), `sortBy` (dropdown). Query the index service or filter a static dataset.
- **Skill detail** — `selectedInstallType` (CLI/Manual/Git), nothing else interactive.
- **Submit** — standard form state. Validate client-side (required: name, author, GitHub URL, description, license). Submit to your review queue.
- **Newsletter / Subscribe** — single-field form, optimistic update on success.
- **Designer notes** (homepage only) — production should delete the block entirely; if kept for staging, a `localStorage`-persisted boolean is fine.

No global app state. No auth in this surface.

---

## Design Tokens

All tokens are defined in `designs/monochrome.css` and used via CSS variables. Map directly to your design system.

### Colors (pure neutrals — no hue)

| Token | Hex | Usage |
|---|---|---|
| `--ink` | `#0a0a0a` | Primary text, ink fills, ink rules |
| `--ink-2` | `#161616` | Secondary near-black |
| `--ink-3` | `#262626` | Body prose text |
| `--mute-1` | `#3d3d3d` | Strong-mute (lede, descriptions) |
| `--mute-2` | `#6b6b6b` | Standard mute (meta micro-labels) |
| `--mute-3` | `#9a9a9a` | Weakest mute (placeholders, untested status) |
| `--line` | `#e6e6e6` | Default hairline rule |
| `--line-2` | `#dcdcdc` | Slightly stronger hairline (code borders) |
| `--line-3` | `#f0f0f0` | Faint hairline (background grid) |
| `--paper` | `#ffffff` | Default surface |
| `--paper-2` | `#fafafa` | Section alt background |
| `--paper-3` | `#f4f4f4` | Subtle highlight (active chip alt, code bg) |
| `--paper-4` | `#ededed` | Stripe pattern second color |

Dark-section hairlines use `#1f1f1f` (about page stats block, terminal panel internals).

### Typography

- **Sans:** Geist (300, 400, 500, 600, 700) → CSS var `--sans`
- **Mono:** Geist Mono (400, 500, 600) → CSS var `--mono`
- **Serif (italic accents only):** Instrument Serif (italic) → CSS var `--serif`

The serif is used **only** for italicized accents inside headlines (e.g., "Editor's *picks*"). Never for body text, never upright.

**Typographic patterns:**

- **Headline (large)** — `font-family: var(--sans); font-weight: 500; letter-spacing: -0.03em; line-height: 0.96`. Sizes use `clamp()`: hero (48–88px), section (32–48px), card (18–28px).
- **Headline italic accent** — wrap accent words in `<em>`, restyle to `font-family: var(--serif); font-style: italic; font-weight: 400`.
- **Mono micro-label** — `font-family: var(--mono); font-size: 11px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--mute-2)`. Used for eyebrows, metadata, button labels, table-headers.
- **Mono numeral** — `font-family: var(--mono); font-feature-settings: "tnum"` for stats and numbered labels.
- **Body prose** — sans, 16px, line-height 1.7, color `var(--ink-3)`.
- **Lede** — sans, 17–18px, line-height 1.55, color `var(--mute-1)`, max-width ~60ch.

### Spacing scale

Sections use generous vertical padding: 64px / 80px / 96px between major regions. Card padding: 18px (small), 24px (default), 28–32px (large featured / principles).

The page container is **always** `max-width: 1280px; padding: 0 32px`. There is no narrower variant in use.

Grid gap is intentionally **0** for hairline grids — separation is by border, not gap.

### Border radius

**Zero.** No rounded corners on any UI element (buttons, cards, inputs, tags, pills, panels). The aesthetic is fully square.

The only exception: status indicator dots (`border-radius: 50%`) and the avatar placeholders (which are square but stripe-patterned).

### Shadows

**Zero.** No box-shadows anywhere. All separation is by hairlines (`1px solid var(--line)` or `var(--ink)`) and color (paper vs paper-2 vs ink).

### Hairline patterns

- **Default rule:** `1px solid var(--line)`.
- **Emphasis rule:** `1px solid var(--ink)` — used for featured rows, install panels, primary CTAs.
- **Dashed rule:** `1px dashed var(--line)` — used for in-card foot separators.
- **Dotted background grid:** `linear-gradient(var(--line-3) 1px, transparent 1px), linear-gradient(90deg, var(--line-3) 1px, transparent 1px); background-size: 48px 48px;` masked with a radial gradient — used only on the MCP hero background.

### Icons

**Inline SVG with `stroke="currentColor"`, `stroke-width: 1.6` to `2`, `fill: none`.** No icon font. No filled icons. All icons are line glyphs (search, arrow, check, calendar, lock, etc.). Sizes typically 12–22px. The platform/MCP "logos" are 2-letter monograms in a 36–42px square with a 1px ink border — never use real platform brand marks.

### Button patterns

- **Primary (`.btn`)** — `background: var(--ink); color: var(--paper); padding: 10px 18px; font-size: 13px; font-weight: 500; border: none; cursor: pointer; display: inline-flex; align-items: center; gap: 8px`. Arrow span on the right has 150ms transform hover.
- **Ghost (`.btn--ghost`)** — `background: transparent; color: var(--ink); border: 1px solid var(--ink)`. Hover swaps to `var(--paper-3)`.
- **Inverted ink pill (S-rank, Featured tag)** — `background: var(--ink); color: var(--paper); padding: 3px 8px; font-family: var(--mono); font-size: 10–11px; letter-spacing: 0.12em; text-transform: uppercase`.
- **Tag (default)** — `border: 1px solid var(--line); background: var(--paper); padding: 3px 8px; font-family: var(--mono); font-size: 11px; color: var(--mute-1); text-transform: uppercase; letter-spacing: 0.08em`.
- **Tag (`.tag.solid`)** — same but `background: var(--ink); color: var(--paper); border-color: var(--ink)`.
- **Chip / segmented control** — uppercase mono, 9–11px, 9–14px padding; active = ink bg + paper text; siblings hairline-divided.

---

## Assets

**No images, no real platform brand logos, no photography.** Everything is rendered with CSS or inline SVG.

- **Avatar / image placeholders** — `repeating-linear-gradient(45deg, var(--paper-3) 0 12px, var(--paper-4) 12px 24px)` for diagonal-stripe placeholder (used on About team avatars and Learn article images). Replace with real photography in production.
- **Platform monograms** — the first 1–2 letters of the platform name in a square with 1px ink border. Production should swap to the real logo (with brand permission) but the visual treatment (ink-bordered square, mono font) should stay.
- **Icons** — inline SVG, hand-coded line glyphs. Recreate using your icon library if you have one (Lucide / Phosphor `light` weight is the closest match).

### Fonts

Loaded from Google Fonts in `monochrome.css`:

```
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700&family=Geist+Mono:wght@400;500;600&family=Instrument+Serif:ital@0;1&display=swap');
```

In production, self-host these via `next/font` or your equivalent for faster loads + no FOUT.

---

## Files

In `designs/`:

| File | Purpose |
|---|---|
| `index.html` | Homepage |
| `skill.html` | Skill detail (example: "Find Skills") |
| `category.html` | Category browse (example: "Web Development") |
| `mcp.html` | MCP server directory |
| `workflows.html` | Curated workflow bundles |
| `learn.html` | Long-form library |
| `submit.html` | Skill submission form |
| `about.html` | Manifesto / about |
| `changelog.html` | Public changelog |
| `monochrome.css` | Shared CSS tokens + base primitives |
| `monochrome.js` | Runtime chrome injector (ticker + navbar + newsletter + footer). **Replace with proper components** in production. |

### Implementation suggestions

- **Routing:** map each HTML file to a route. Suggested URLs:
  - `/` → index
  - `/skills/:slug` → skill detail (use `find-skills` as the example slug)
  - `/categories/:slug` → category (e.g., `/categories/web-development`)
  - `/mcp` → MCP directory; `/mcp/:slug` for detail (mirror skill detail pattern)
  - `/workflows` → workflows list; `/workflows/:slug` for detail
  - `/learn` → library; `/learn/:slug` for article detail
  - `/submit` → form
  - `/about` → about
  - `/changelog` → changelog
- **Components to extract first:** `<TopTicker>`, `<Navbar active>`, `<Newsletter>`, `<Footer>`, `<MicroLabel>`, `<Tag>`, `<Rank>`, `<HairlineGrid>`, `<SkillCard>`, `<MCPCard>`, `<StatRow>`, `<InstallPanel>`, `<TableOfContents>`, `<Breadcrumbs>`. The rest of each page is one-off layout.
- **Data layer:** the prototype hardcodes skill / MCP / category / workflow / article arrays. Replace with your CMS / API / static data source. The shape used in the prototypes should map cleanly to a normalized schema.

---

## Open questions for the implementing developer

1. **Search:** ⌘K palette is a placeholder — wire to your existing search infrastructure (Algolia / Pagefind / Typesense / custom).
2. **Auth:** the submission form currently posts to nothing. Likely needs GitHub OAuth (since submissions point at GitHub repos) plus a review queue.
3. **Real MCP/skill data:** confirm the schema and feed source. The prototype doesn't take a stance on whether the index is generated from a public registry, scraped, or editorially maintained — but the editorial framing suggests a curated list with light automation.
4. **Mobile nav:** drawer/sheet pattern not specified. Pick whichever matches your codebase's existing nav primitive.
5. **Brand monograms vs real logos:** confirm you have permission/licensing to use real platform logos. If not, the monogram pattern shipped here is the safe fallback.
