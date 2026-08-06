Sits above the navbar on every page — the system's one piece of ambient live signal.

```jsx
<Ticker feed={[
  { v:'+12', l:'new this week' },
  { v:'2.4M', l:'installs/mo' },
  { v:'18', l:'platforms tracked' }
]} />
```

The leading dot pulses on a 2s loop. That plus the terminal cursor are the only ambient animations in the system.