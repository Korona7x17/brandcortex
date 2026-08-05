# BRIEF_SUMMARY (2026-08-05)

C: Publish is atomic — a live photo whose link comment failed is `failed`, never partial; reviewer
edits meet the same numeric + link checks as generated copy; orchestrator owns its commits
D: Rejected drafts persist as `failed` (bulk ingest must not stop); UTM campaign short + uniquely
indexed, reversed by lookup; status columns are Enum not String; ingest cursor is
max(source_generated_at); brand_config round-trips via settings JSON
Δ: orchestrator@6da1aa + brand_config@c2f760 + utm@c39cce + assets@87aacb + review API@b813da →
card_renders row becomes a persisted, reviewable, publishable post. Alembic baseline@b2ea54
drift-free. 135 pass / 9 skip. Committed 1ab1f4b, not pushed.
Δ: enums@14772f — live bug fixed: String status loaded as bare str, so every `is PostStatus.X` was
silently False on a reloaded row; approve would have 409'd in production
Q: 281 E501s (prose 101-104 vs limit 100) — reflow or raise?; no Postgres; Meta token short 3
scopes; FB publish + insights still stubs, so nothing has reached a Page
→: React dashboard, or FB publish path against respx, or the System User token
