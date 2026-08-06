The system's most-used card — index grids, category pages, search results.

```jsx
<HairlineGrid columns={3}>
  <SkillCard name="React Best Practices" author="Vercel Labs" official rank="S"
    description="Hooks, composition, performance, server components."
    category="Web Dev" platforms={['Claude','Cursor','Codex']}
    installs="198K" stars="2.4K" href="/skills/react-best-practices" />
</HairlineGrid>
```

Always place inside a `HairlineGrid` — the card draws no border of its own.