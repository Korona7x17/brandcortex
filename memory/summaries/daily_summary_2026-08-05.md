# BRIEF_SUMMARY (2026-08-05)

C: BrandCortex now originates content, not only follows card_renders; it holds the schedule (Meta's
native scheduling can't attach the link comment); the model writes and code checks, never self-judges
D: Compose via ThaiSwim's public render API, never duplicate the engines; composed ids derived from
params; model writer primary with templates as fallback; angles/notation/claim-bindings are data in
brand_config; claims bound to the fact they must equal
Δ: facebook/{client,tokens,adapter,authorize}@fc6ba8 + publisher@f54b34 + scheduler@20c8e9 +
writer@7af7ff — full publish path, 16 tests vs a fake Graph. thaiswim: payload routes + privacy page
deployed. 154 pass. Commits 9a5717b, ef105d9.
Δ: claims@5f2e3e — was rejecting correct copy: `สระ 50 ม.` is a pool length, not a claim
Q: **Meta rejects `pages_read_user_content` — a scope the app never had and no request of ours
sends.** Survived explicit scopes, rerequest, both config types, publishing, privacy URL. Untried:
"+ Add" it; read the real request. Also: no dashboard auth (blocks deploy); ~280 E501
→: Resolve the scope injection, then token → one published post → insights → editor-preference loop
→: Meta-independent: Clerk auth, Railway deploy, R2 for cards
