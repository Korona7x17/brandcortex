# @brandcortex/contracts

Cross-language definitions of the seams between systems. Nothing here imports anything; it is the one
place both the Python core and the TypeScript dashboard agree on.

| File | Seam |
| --- | --- |
| `schemas/content-item.schema.json` | Brand source adapter → BrandCortex core |

## Rule

The content-item envelope is versioned, not edited. A change that could break a producing brand means
publishing `content-item/v2.json` and teaching the ingest path to accept both — the Python mirror lives
at `apps/api/src/brandcortex/schemas/content_item.py` and must be updated in the same change.
