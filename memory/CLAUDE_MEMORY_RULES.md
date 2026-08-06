# CLAUDE MEMORY RULES (Runtime)

- Load: project_snapshot + last daily summary + relevant decision files.
- Prefer Tier-A Brief unless `mode:full` is specified.
- Use line lists; avoid prose and code blocks.
- Reference artifacts by path@hash; no large pastes.
- Return at least one of: C: D: Δ: Q: →: in outputs.
- Respect caps: Brief ≤250 tokens, Full ≤900.
