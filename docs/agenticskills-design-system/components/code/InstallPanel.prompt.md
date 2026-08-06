Right column of the skill detail hero. Self-contained — owns its own copy and method state.

```jsx
<InstallPanel
  stats={[{v:'271K',l:'Installs'},{v:'3,240',l:'Stars'},{v:'98%',l:'Compat'},{v:'v3.2',l:'Latest'}]}
  methods={[
    { label:'CLI', command:'$ npx skills add vercel-labs/find-skills', note:'via CLI' },
    { label:'Manual', command:'# Drop SKILL.md into ~/.claude/skills/', note:'no CLI' },
    { label:'Git', command:'$ git clone github.com/vercel-labs/find-skills', note:'from source' }
  ]}
/>
```