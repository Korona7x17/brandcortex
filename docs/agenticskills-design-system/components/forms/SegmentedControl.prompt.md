One control covers every single-select in the system — filter chips, sort, licence, install method.

```jsx
<SegmentedControl value={filter} onChange={setFilter}
  options={['All','S-rank','Official','Open Source']} />
```

Always single-select. For multi-select, use a checkbox grid instead.