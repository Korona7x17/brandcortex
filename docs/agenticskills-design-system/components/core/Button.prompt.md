Primary action control — use for CTAs, form submits, and nav actions.

```jsx
<Button arrow>Browse the index</Button>
<Button variant="ghost" arrow="↗" href="/submit">Submit a skill</Button>
```

Variants: `primary` (ink fill, default) and `ghost` (transparent, ink hairline, inverts on hover). Both are square — never add a radius. Set `arrow` for the 2px hover nudge; use `↗` for links that leave the page.