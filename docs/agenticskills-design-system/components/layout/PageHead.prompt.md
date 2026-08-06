Opens every interior page — category, about, changelog, submit, workflows.

```jsx
<PageHead
  crumbs={<Breadcrumbs items={[{label:'Index',href:'/'},{label:'Web Development'}]} />}
  eyebrow="Category 01 / 16"
  title={<>Web <em>Development</em></>}
  lede="Frontend frameworks, React, Next.js, and modern web tooling."
>
  <StatRow items={[{ v:'15', l:'Skills' },{ v:'847K', l:'Total installs' }]} />
</PageHead>
```