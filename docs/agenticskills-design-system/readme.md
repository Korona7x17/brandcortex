# AgenticSkills Design System

> **Reusing this in another project:** say *"use the design system from my **agenticskills** project"* and paste this link —
> `https://claude.ai/.../p/019de1f6-20e6-717c-ab67-b237bad915da`
> (or just open this project and copy the URL from your address bar). That's all that's needed; the files get pulled in directly.

A monochrome, editorial design system for **AgenticSkills** — a curated directory of AI agent skills (`SKILL.md` files) and MCP servers for Claude Code, OpenAI Codex, Cursor, Gemini CLI, and 18+ other agent platforms.

The product is an *index*, not a marketplace: skills are editorially curated, ranked S–C, and free. The design system exists to make that positioning legible — it reads like a developer reference manual or a trade publication, not a SaaS landing page.

---

## Sources

| Source | What it gave us |
|---|---|
| **This project's monochrome redesign** (`index.html`, `skill.html`, `category.html`, `mcp.html`, `workflows.html`, `learn.html`, `submit.html`, `about.html`, `changelog.html`) | Ground truth for every token, component, and layout in this system. |
| `design_handoff_agenticskills_monochrome/` | Developer handoff README documenting the same designs for implementation. |
| **Attached local folder `agenticskills/`** — a Next.js 15 App Router codebase (Tailwind, `lucide-react`, shadcn-derived `components/ui`) | The original pre-redesign product: information architecture, routes, data schema, category taxonomy, and the `lucide-react` icon dependency. |

> **Note on the codebase.** The attached folder was readable when the redesign was built (routes, components, and `lib/data.ts` were all read) but the local file tools were disconnected at the time this design system was authored. Everything below derives from the redesign files in this project, which are fully present. If you re-attach the folder, the useful cross-checks are `app/globals.css` (original token names) and `public/` (any real logo or icon assets — this system currently has none).

**There is no logo.** No brand mark was present in any source. The wordmark is rendered as plain type — "Agentic" in ink, "Skills" in mute — beside a 28px ink square holding the letter `A`. Do not draw, generate, or approximate a logo; if a real mark exists, drop it into `assets/` and swap the `.ds-brand__mark` contents.

---

## Content fundamentals

**Voice: an editor, not a marketer.** Copy states what is true and stops. It never sells, never hedges, and never explains its own significance.

**Casing.** Sentence case for all headlines and body copy. UPPERCASE only for mono micro-labels (eyebrows, stat captions, tags, column headers) — never for a sans headline. Title Case appears only in proper nouns and skill names.

**Person.** Second person for instructions to the reader ("Your agent gains the new capability"). First-person plural for editorial positions ("We don't index everything"). Never first-person singular.

**Sentence shape.** Full sentences with real punctuation. Em dashes are used sparingly, for a genuine aside. Lists are parallel and unpunctuated at line ends.

**Numbers.** Always numerals, never spelled out — "143 skills", "18 platforms", "2.4M installs/mo". Counts are specific; if you don't have the number, cut the claim rather than rounding to "hundreds of".

**Emoji: never.** Not in UI, not in copy, not in changelogs. The system uses line glyphs and mono symbols (`↓ ↑ → ↗ ★ ✓ ·`) instead.

**Examples from the product:**

- Hero: *"The curated index of skills that make agents useful."* — states the object, not a benefit.
- Sub: *"Find, compare, and install skills that are actually maintained — no slop, no noise."* — the one place the voice shows an edge, and it earns it.
- Principle: *"Curation over completeness. We don't index everything."* — a position, stated plainly.
- Principle: *"Editorial, not paid placement. We don't accept money to rank skills higher. Featured means we'd recommend it."*
- Empty/absent content: *"AgenticSkills is an independent directory. Not affiliated with Anthropic, OpenAI, or any platform vendor."*
- Section headers use a numbered eyebrow plus a two-word title with one italic accent: `02 · Featured` / "Editor's *picks*".

**What to avoid.** Marketing intensifiers ("powerful", "seamless", "supercharge" beyond the one legacy instance), metadiscourse ("here's why this matters"), the "this, not that" construction, and any sentence whose job is to introduce the next sentence.

---

## Visual foundations

### Colour

**Pure neutrals. There is no hue anywhere in the system.** Thirteen greys from `#0a0a0a` to `#ffffff`, plus a small on-ink set for the two inverted surfaces. The pre-redesign product used a blue/violet gradient brand, colour-coded categories, green S-ranks and amber warnings; all of that collapsed to a single tonal scale.

Hierarchy is carried by **weight, scale, and hairlines** — never by colour. Where the old system reached for green to mean "best", this one inverts a pill to black. Where it reached for blue to mean "primary", this one fills the button with ink.

Only two surfaces invert: the **newsletter band** and the **About stats block**. Both are full-bleed `--ink` with paper text. The terminal and install-command panels are also ink, but they are components, not page surfaces.

### Type

Three families, each with exactly one job.

- **Geist** (sans) — everything structural. Weights 400/500/600 only; 700 is never used. All headings are 500 with negative tracking (−0.02em to −0.035em) and tight leading (0.94–1.0 at display sizes).
- **Geist Mono** — every piece of metadata. Eyebrows, stat numerals, tags, timestamps, install paths, table headers, code. If text is small, grey and structural, it is mono uppercase with wide tracking (0.12–0.16em).
- **Instrument Serif italic** — **one accent word per headline**, and nothing else. Never upright, never in a paragraph, never more than one per heading. It is the system's only ornament.

Measure is capped in `ch`, not by container width: 60ch for ledes, 62ch for prose, 32ch for card body copy, 18ch for display headlines.

### Layout

One container for the whole product: `max-width: 1280px; padding: 0 32px`. There is no narrow variant.

**The hairline grid is the core layout device.** Every card collection is a CSS Grid with `gap: 0`, where the wrapper draws top and left borders and each cell draws right and bottom. Separation is the border. Floating cards with margins between them do not exist in this system.

A variant (`--ink`) bands a single row with black rules top and bottom — used for Editor's picks and related-skill rows, where one row needs to read as emphasised.

Vertical rhythm: 64 / 80 / 96 / 120px between major regions. Card padding: 18 (dense) / 24 (standard) / 28–32 (featured).

### Backgrounds

Flat surfaces only. Alternating sections step from `--paper` to `--paper-2`. Two exceptions:

- A **48×48px dotted grid** (`--line-3` on paper), radially masked so it fades out — used on the homepage and MCP heroes only.
- **Diagonal stripe placeholders** (`repeating-linear-gradient(45deg, --paper-3, --paper-4)`) standing in for imagery and avatars.

No gradients as decoration. No glow blobs, no blurred colour washes, no noise overlays. The pre-redesign hero had two 120px-blurred colour orbs; both are gone.

### Imagery

**The system ships none.** No photography, no illustration, no third-party brand marks. Article cards and team avatars use the stripe placeholder, and platform logos are 2-letter monograms in ink-bordered squares.

This is deliberate: an honest gap reads better than filler, and generated art would break the document tone immediately. When real imagery arrives it should be **black and white or heavily desaturated**, with a documentary rather than lifestyle register — think trade-press photography, not stock.

### Borders, radius, elevation

- **Radius is zero.** Buttons, cards, inputs, tags, pills, panels — all square. The only exceptions in the entire system are the 6px status dot (`50%`) and the 3px `<kbd>` chip in the search trigger.
- **Shadows do not exist.** No `box-shadow` anywhere. All separation is hairlines and surface tone.
- **Hairlines** come in four weights: `--line` (default), `--line-3` (faint, background grids), `--ink` (emphasis — featured rows, install panels, primary buttons), and dashed `--line` (in-card foot separators).

### Cards

A card is a padded region inside a hairline grid. It has no border of its own, no radius, no shadow. It hovers by shifting one surface step (`--paper` → `--paper-2`, or `--paper-3` for category cells). Structure is consistent: head row (title + rank), description, tag run, then a foot pinned with `margin-top: auto` above a dashed rule carrying stats and an affordance.

### Motion

Deliberately minimal — the page should read as a document, not an experience.

- **`pulse`** — 2s ease-in-out infinite on the live status dot, opacity 0.3 → 1.
- **`blink`** — 1s steps(1) on the terminal cursor.
- **Hover nudge** — buttons lift `translateY(-1px)`; arrows travel 2px. 150ms `ease`.
- **Card hover** — background steps one surface, 200ms.

**No** scroll-jacking, parallax, reveal-on-scroll, page transitions, skeleton shimmer, or spring physics. The pre-redesign product animated nearly every section in on scroll with Framer Motion; none of that survives.

### States

- **Hover** — surface step for cards, ink inversion for ghost buttons, ink text for muted links, 2px arrow travel.
- **Active / selected** — inversion to ink fill with paper text. This is the system's single selection signal (segmented controls, chips, S-rank, featured tags).
- **Focus** — border darkens from `--line` to `--ink`. No ring, no glow, no offset outline.
- **Disabled** — `opacity: 0.4`, `cursor: not-allowed`. No colour change.
- **Press** — no dedicated state; the hover lift resolves on click.

### Transparency and blur

Used exactly once: the sticky navbar is `rgba(255,255,255,.85)` with `backdrop-filter: saturate(180%) blur(12px)`. Nowhere else. No frosted cards, no scrim overlays, no protection gradients — the system has no full-bleed imagery to protect text against.

### Responsive

Three breakpoints. `980px` collapses multi-column grids to 2-up and stacks heroes; `768px` stacks workflow rows and moves the TOC above content; `640px` collapses everything to 1-up and hides the ticker feed. Mobile navigation is **not implemented** — add a drawer using your app's own sheet primitive.

---

## Iconography

**Line glyphs only.** Every icon is stroke-only on `currentColor`, `fill: none`, stroke width 1.6 (display) to 2 (small inline marks), with round caps and joins. No filled icons, no duotone, no colour, no icon font, no emoji.

**Sizes.** 14px inline in buttons and meta rows · 18px in category cells (inside a 36px ink-bordered square) · 20–22px in step glyphs (inside a 56px square).

**Source.** The redesign hand-codes its SVG paths inline. Those exact paths are collected in `components/core/Icon.jsx` as the `ICONS` map — that is the canonical set. The original Next.js codebase depended on **`lucide-react`**, and the hand-coded paths are Lucide-shaped (same 24×24 viewBox, same stroke conventions), so Lucide at `strokeWidth={1.6}` is the correct fallback for any glyph outside the map.

> **Substitution flagged:** no icon assets were available to copy from the sources, so the set in `Icon.jsx` is transcribed from the redesign's own inline SVG. For production, install `lucide-react` and use it directly at the stroke weights above — the visual result is equivalent and the set is complete.

**Non-glyph symbols.** The system leans on typographic marks rendered in mono rather than icons: `↓` installs, `★` stars, `→` forward, `↗` leaves the page, `✓` verified, `·` separator, `/` breadcrumb separator. Prefer these over icons in dense metadata rows.

**Brand marks.** None are shipped. Platforms and MCP servers are represented by 2-letter monograms in a 36–42px ink-bordered square. If you license real marks, keep the square footprint and swap only the glyph.

---

## Fonts

| Role | Family | Weights |
|---|---|---|
| Sans | **Geist** | 300, 400, 500, 600, 700 (only 400/500/600 used) |
| Mono | **Geist Mono** | 400, 500, 600 |
| Serif accent | **Instrument Serif** | italic 400 |

> **Flagged:** no font binaries existed in the sources, so all three load from Google Fonts via `tokens/fonts.css`. All three are genuinely available there — these are the real families, not substitutes. Self-host for production (`next/font` or equivalent) to remove the render-blocking request.

---

## Index

**Root**
- `styles.css` — the global entry point. Import this one file. Contains `@import` lines only.
- `readme.md` — this guide.
- `SKILL.md` — Agent Skills manifest for use in Claude Code.

**`tokens/`** — CSS custom properties, one file per concern.
`fonts.css` · `colors.css` · `typography.css` · `spacing.css` · `borders.css` · `motion.css`

**`styles/`** — `base.css` (reset + document defaults) · `primitives.css` (`ds-*` utility classes) · `components.css` (classes backing each JSX component).

**`components/`** — 27 primitives in six groups.

| Group | Components |
|---|---|
| `core/` | Button · Tag · Rank · MicroLabel · Monogram · Breadcrumbs · Icon |
| `layout/` | HairlineGrid · SectionHead · PageHead · StatRow |
| `navigation/` | Ticker · Navbar · Footer · TableOfContents |
| `forms/` | Input · FormField · SegmentedControl · SearchInput · NewsletterForm |
| `content/` | SkillCard · FeatureCard · CategoryCard · ArticleCard · StepCard |
| `code/` | Terminal · InstallPanel |

Each has `<Name>.jsx`, `<Name>.d.ts` (props contract), and `<Name>.prompt.md` (what & when, usage, variants). Each directory has one `@dsCard`-tagged HTML showing its states.

**`ui_kits/directory/`** — click-through recreations of the product: homepage, skill detail, category browse, MCP directory, and the submission form.

**`guidelines/foundations/`** — 21 specimen cards across Colors, Type, Spacing, and Brand.

**`assets/`** — currently empty of brand marks by design (see *Sources*). Drop a real logo here if one is produced.

### Intentional additions

- **`Icon`** — the sources hand-code SVG paths inline rather than exposing a component. Wrapping them gives consumers one named set and one stroke convention instead of copy-pasted paths.

---

## Using this system

1. Link `styles.css`. Every token and primitive class comes with it.
2. Compose from `components/` — do not re-implement Button, Tag, or the grid inside a screen.
3. Wrap every card collection in `HairlineGrid`. Never add gaps between cards.
4. Reach for weight and scale before you reach for anything else. If you find yourself wanting a colour, you want an inversion.
5. One serif italic accent per headline. Zero is fine; two is wrong.
