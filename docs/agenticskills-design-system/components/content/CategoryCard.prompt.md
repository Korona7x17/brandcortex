Four-up grid cell on the homepage and category index.

```jsx
<HairlineGrid columns={4}>
  <CategoryCard index="C01" name="Web Development" count={15}
    description="Frontend frameworks, React, Next.js, and modern web tooling."
    topSkills={['react-best-practices','frontend-design']}
    icon={<Icon name="layout" />} href="/categories/web-development" />
</HairlineGrid>
```

Icons are 18px line glyphs in a 36px ink-bordered square — never filled, never coloured.