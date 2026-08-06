const { Shell, Home, SkillDetail, CategoryBrowse, McpDirectory, SubmitForm } = window;

const ROUTES = {
  home:     { active:'skills', newsletter:true,  render:(go)=><Home go={go} /> },
  skill:    { active:'skills', newsletter:true,  render:(go)=><SkillDetail go={go} /> },
  category: { active:'skills', newsletter:true,  render:(go)=><CategoryBrowse go={go} /> },
  mcp:      { active:'mcp',    newsletter:true,  render:()=><McpDirectory /> },
  submit:   { active:null,     newsletter:false, render:(go)=><SubmitForm go={go} /> }
};

function App() {
  const [route, setRoute] = React.useState('home');
  const go = (r, anchor) => {
    if (!ROUTES[r]) return;
    setRoute(r);
    requestAnimationFrame(() => {
      const el = anchor && document.getElementById(anchor);
      window.scrollTo(0, el ? Math.max(el.offsetTop - 80, 0) : 0);
    });
  };
  const r = ROUTES[route];
  return (
    <Shell active={r.active} route={route} go={go} newsletter={r.newsletter}>
      {r.render(go)}
    </Shell>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
