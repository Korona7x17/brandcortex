# @brandcortex/web

Next.js review dashboard for brandcortex.app.

```bash
npm install
npm run dev        # http://localhost:3000, expects the API on :8000
npm run typecheck
```

Holds no channel credentials. Every publish, edit, and approval goes through the BrandCortex API, which
is the single holder of every channel permission — the brand's own site carries none either.

| Route | Phase | Purpose |
| --- | --- | --- |
| `/drafts` | 1 | Review queue: list, edit, approve — the human-in-the-loop gate |
| `/calendar` | 2 | Scheduled slots; alternation and spacing at a glance |
| `/analytics` | 2 | Slices Facebook's own insights can't give |
| `/playbook` | 2 | Active rules, proposals with evidence, approve / roll back |

Caption and first comment are always separate fields. They are separate publishes — the caption is the
photo post, the first comment carries the link — and merging them in the UI would invite someone to
paste the link into the caption, which is exactly what costs reach.
