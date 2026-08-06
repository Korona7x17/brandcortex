# Session Log – 2026-08-06_05
Tags: [Voice][Thai][Copy][Generation][Merge]
Repo: brandcortex@751ac81 on **main** (merged scaffold/thaiswim-facebook-mvp, not pushed)
Context loaded: continuation of session 04 (same day)

## Notes

**The complaint.** User, on the pre-written first comment: calling an older person by bare name is
"a damn sin" — add `คุณ` before the name, always. They were right about scope: it was not one line.
`templates.py` printed the swimmer's name bare in the caption's identity line, again in the first
comment (`📊 สถิติและอันดับทั้งหมดของ {name}`), and again in the club angle — and the seed config's
one approved few-shot example did it too, so the model was being *taught* the mistake.

**Where the code was.** `main` tracked two files; the whole project lived on
`scaffold/thaiswim-facebook-mvp`. The working tree had been left on `main` with a partial untracked
remnant of `apps/` (dirs + `__pycache__`, no `.py` sources), which read as data loss until the branch
was checked. Switched branches — the uncommitted doc edits carried over, the untracked
`apps/web/lib/*.ts` files don't exist on the branch so nothing was clobbered.

**Fixed at three levels, not one.** A prompt instruction alone would drift; a template fix alone
leaves the model path open.

1. `_person(facts, config)` is the only route a name takes into ThaiSwim copy, and it prefixes the
   honorific read from `brand_config.voice.honorific`. Returns `""` for a nameless card, so the
   fallback is a line needing no name — never a lone `คุณ` or the old `—` placeholder.
2. `voice.Honorific` + `voice.check_names()` **reject** a draft that drops it, caption and first
   comment alike. Prefixed mentions are stripped before looking for a bare one, so naming someone
   twice is judged on both mentions. Scoped to declared locales (`th`); English copy exempt.
   `names_in(facts, rules)` reads the name off config-declared `name_fields`, so core learns which
   fields hold people without learning whose — `test_core_is_brand_agnostic` still passes.
3. The writer system prompt states the rule, and the approved example now reads `คุณริน สืบสงวน`.

**Then the register changed.** User: the pre-written text is "a bit dry", and supplied a post they
wrote by hand — 🏆 headline carrying the number, `ขอแสดงความยินดีกับ คุณ<name> จาก <club>`, the
achievement closing on 👏, arrows on the link nudge. Applied to `sweep` and `longevity` (the
achievement and age-group angles the sample is written for); `plain`, `breadth`, `standout`, `club`
stay factual. So the reviewer now picks register as well as angle, and register is carried through
both halves of a variant — a warm caption over a flat first comment reads as two people writing one
post. Two first-comment banks (5 reporting / 4 warm), named and general lines alternating.

**Emoji ceiling, twice.** Went 1 → 4 to admit the reference shape, then the user capped it at 1–2 and
it settled at **2**: 🏆 and 👏 stay (they carry the congratulation), the 👉/👇 arrows came off the
nudge (that line already says where the link is). The stored example was trimmed to match, otherwise
the model is shown a caption its own validator would reject. **This is an owner decision, not the
learning loop's** — §10.4 holds, `voice.*` is still structurally unproposable.

**A test that would have gone quiet.** `test_stacked_emoji_is_rejected` hardcoded 🔥🔥🔥 against the
old ceiling of 1. At 4 it passed the validator and the test failed loudly; at 2 it would have passed
*silently* while asserting nothing. Now derives the count from `brand_config`.

**Guidance softened** on request ("softer but not cheesy"): the old brief opened with "name the
achievement plainly and let it stand" — accurate but cold, and the reason the copy read dry. Now
warmth is sourced from respect and from the numbers, with adjectives named as the thing to avoid
(no สุดยอด, no น่าทึ่ง, nothing a stranger would say). The four `banned_phrases` are untouched.

Merged to `main` with `--no-ff` (751ac81) at the user's request. 190 pass / 9 skip on main after.

## Artifacts

- `apps/api/src/brandcortex/core/generation/voice.py@4903de` — Honorific, check_names, names_in
- `apps/api/src/brandcortex/core/generation/engine.py@e90a93` — names+locale into both check paths;
  first comment held to the naming rule; `intro_line` recorded only when the caption used it
- `apps/api/src/brandcortex/adapters/source/thaiswim/templates.py@656eec` — `_person`, `_from`,
  `_assemble_warm`, COMMENTS_TH / COMMENTS_WARM_TH, warm `_sweep_th` / `_longevity_th`
- `apps/api/seeds/thaiswim.brand_config.json@0a0dc8` — voice.honorific, max_emoji 2, softened
  tone + guidance, second approved example
- `apps/api/tests/unit/test_honorific.py`, `apps/api/tests/unit/test_congratulatory_register.py`
- Commits: 66c5bad (the work) · 751ac81 (merge to main)

C: A person's name is never written bare in Thai copy — `คุณ` + name, caption and first comment
   alike. Enforced by validator, not only by prompt; falls back to a no-name line when uncertain
C: Emoji ceiling is 2, and both emoji carry the congratulation — the nudge carries none
C: Register is per-variant and carried through caption AND first comment together
C: Voice rules are the owner's to change and no one else's; the loop still cannot propose them
D: D-2026-08-06-06 honorific as a config-declared, validated voice rule (three levels, not one)
D: D-2026-08-06-07 two registers, ceiling 2, guidance rewritten around respect not adjectives
Δ: `main` went from 2 tracked files to 324 — the whole scaffold landed in one merge commit
Δ: Warm angles ignore the dealt intro, so `intro_history` no longer retires unseen lines
Q: Nothing pushed — `origin/scaffold/thaiswim-facebook-mvp` still at 1400de5, `main` not pushed
Q: Untracked `apps/web/lib/*.ts` overlap in purpose with the `apps/web/` code the merge brought in
Q: Unchanged: R2 + cron worker, insights fetcher, design-system folder, dev Clerk secret rotation
→: Push `main` (and decide the branch's fate); reconcile the stray `apps/web/lib` files
→: R2 → cron worker → insights fetcher; first production compose still pending
