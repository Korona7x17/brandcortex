# Assets

**This folder is intentionally empty of brand marks.**

No logo, icon set, illustration, or photography existed in any of the sources
(see *Sources* in the root `readme.md`). Rather than draw or generate a mark,
the system renders the brand as plain type:

- **Wordmark** — "Agentic" in `--ink`, "Skills" in `--mute-2`, Geist 600 at 16px.
- **Brand mark** — a 28px `--ink` square containing the letter `A` in Geist Mono 600 / 12px.
  Implemented as `.ds-brand__mark`.
- **Third-party logos** — 2-letter monograms in ink-bordered squares (`Monogram` component).
  No real platform brand marks are shipped.

## If you have real assets

1. Drop SVGs here (`logo.svg`, `logo-mark.svg`).
2. Swap the contents of `.ds-brand__mark` in `styles/components.css`, keeping the
   28px square footprint and the ink fill.
3. For platform logos, keep the `Monogram` treatment — square, 1px ink border,
   36/42px — and replace only the glyph. Confirm licensing first.

## Icons

Icons are not stored here. The canonical line-glyph set is transcribed into
`components/core/Icon.jsx` as the `ICONS` map, matching the paths used in the
redesign source. For glyphs outside that set, use **Lucide** at `strokeWidth={1.6}`
— the original codebase depended on `lucide-react` and the shapes are compatible.
See the ICONOGRAPHY section of the root `readme.md`.
