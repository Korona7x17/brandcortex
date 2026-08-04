# Rejected Ideas

## R-2026-08-04-01 — Runtime drift check between caption and live-rendered card

Proposed a `drift_check` comparing draft-time facts against a re-fetch at publish. User challenged the
premise; they were right. The studio already freezes the image by downloading it, and BrandCortex
fetching at publish *introduced* a window that didn't otherwise exist. Replaced by capturing the PNG at
draft time (D-2026-08-04-01). Superseded, not deferred.

## R-2026-08-04-02 — Hardcoding `locale = "th"` throughout

Briefly hardened after "no need for English cards". Reversed: English is needed for future
English-language tenants. Locale is now resolved per item. Kept as a warning — a constant is cheap to
add and expensive to find later.

## R-2026-08-04-03 — Adding a skeptic agent to the caption path

Considered after the graph-engineering discussion. Rejected as disproportionate: three sentences of
Thai, already covered by numeric grounding + voice validator + human review. Adding an LLM reviewer
there costs latency and money to second-guess something a person reads anyway. Adversarial review
belongs only in the learning loop, where model output silently becomes instructions for every future post.

## R-2026-08-04-04 — OAuth dialog via redirect URI for the Meta token

Three attempts (facebook.com redirect, thaiswim.com redirect, two Graph versions). Blocked by App
Domains rules and then by "No redirect URI in the params". Graph API Explorer separately blocked by a
cached invalid scope. Abandoned in favour of the System User route (D-2026-08-04-T03), which needs no
redirect and no dialog.
