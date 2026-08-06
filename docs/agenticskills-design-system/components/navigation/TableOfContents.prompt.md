Right rail on long-form pages (skill detail, articles). Sticks at 80px.

```jsx
<TableOfContents activeId={active} onSelect={setActive} items={[
  { id:'overview', label:'Overview' },
  { id:'usage', label:'Usage' }
]} />
```

Drive `activeId` from an IntersectionObserver over the section headings.