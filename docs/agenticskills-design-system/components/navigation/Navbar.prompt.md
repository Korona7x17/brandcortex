Sticky header used on every page.

```jsx
<Navbar
  active="skills"
  links={[
    { id:'skills', label:'Skills', href:'/' },
    { id:'mcp', label:'MCP Servers', href:'/mcp' },
    { id:'learn', label:'Learn', href:'/learn' }
  ]}
  cta="Submit a Skill"
/>
```

The brand mark is a 28px ink square holding the first letter — a type lockup, not a logo. Mobile nav is not implemented; add a drawer using your app's own sheet primitive.