Page-position trail. Sits directly above the page eyebrow on every non-home page.

```jsx
<Breadcrumbs items={[
  { label: 'Index', href: '/' },
  { label: 'Productivity', href: '/categories/productivity' },
  { label: 'Find Skills' }
]} />
```

Drop `href` on the final crumb — it renders in ink to mark the current page.