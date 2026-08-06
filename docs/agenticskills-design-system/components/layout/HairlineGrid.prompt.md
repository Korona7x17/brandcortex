Wraps every card collection in the system. Never set a gap — separation is the border.

```jsx
<HairlineGrid columns={3}>
  {skills.map(s => <SkillCard key={s.slug} {...s} />)}
</HairlineGrid>

<HairlineGrid columns={3} variant="ink">
  {featured.map(s => <FeatureCard key={s.slug} {...s} />)}
</HairlineGrid>
```

Use `ink` only for a single emphasised row (Editor's picks, related skills) — it bands the row with black rules top and bottom.