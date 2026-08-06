const { MicroLabel, HairlineGrid, SectionHead, StatRow, Terminal, Rank, Monogram } = window;

function McpDirectory() {
  return (
    <main>
      <section style={{position:'relative',padding:'96px 0 80px',borderBottom:'1px solid var(--line)',overflow:'hidden'}}>
        <div style={{position:'absolute',inset:0,opacity:.7,pointerEvents:'none',
          backgroundImage:'linear-gradient(var(--line-3) 1px,transparent 1px),linear-gradient(90deg,var(--line-3) 1px,transparent 1px)',
          backgroundSize:'48px 48px',
          maskImage:'radial-gradient(ellipse at 60% 40%, #000 0%, #000 40%, transparent 75%)',
          WebkitMaskImage:'radial-gradient(ellipse at 60% 40%, #000 0%, #000 40%, transparent 75%)'}} />
        <div className="ds-wrap" style={{position:'relative',display:'grid',gridTemplateColumns:'1.4fr 1fr',gap:64,alignItems:'center'}}>
          <div>
            <MicroLabel>02 · MCP Directory</MicroLabel>
            <h1 style={{fontSize:'clamp(48px,6.4vw,88px)',fontWeight:500,letterSpacing:'-.035em',lineHeight:.94,margin:'18px 0 0'}}>
              200+ trusted<br />MCP servers,<br /><em className="ds-accent">one index</em>.
            </h1>
            <p style={{marginTop:24,fontSize:18,color:'var(--mute-1)',maxWidth:'54ch',lineHeight:1.55}}>
              Official Model Context Protocol servers from GitHub, Stripe, AWS, Google, and 200+ more.
              Connect any tool to Claude, ChatGPT, Cursor, or any MCP-aware agent.
            </p>
            <StatRow items={[{v:'214',l:'Servers'},{v:'22',l:'Categories'},{v:'68',l:'Official'},{v:'100%',l:'Verified'}]} />
          </div>
          <Terminal title="mcp.json" meta="schema" dots={false}>
            <span className="c">{'// connect Stripe MCP server'}</span>{'\n'}
            {'{\n  '}<span className="k">"mcpServers"</span>{': {\n    '}<span className="k">"stripe"</span>{': {\n      '}
            <span className="k">"command"</span>{': '}<span className="s">"npx"</span>{',\n      '}
            <span className="k">"args"</span>{': ['}<span className="s">"-y"</span>{', '}<span className="s">"@stripe/mcp"</span>{'],\n      '}
            <span className="k">"env"</span>{': {\n        '}<span className="k">"STRIPE_API_KEY"</span>{': '}<span className="s">"sk_live_…"</span>{'\n      }\n    }\n  }\n}'}
          </Terminal>
        </div>
      </section>

      <section style={{padding:'96px 0',borderBottom:'1px solid var(--line)'}}>
        <div className="ds-wrap">
          <SectionHead index="03 · Featured" title={<>Editor's <em>picks</em></>} cta="All featured →" />
          <HairlineGrid columns={3} variant="ink">
            {DATA.mcpFeatured.map(s => (
              <div key={s.name} className="ds-card ds-featcard">
                <div className="ds-card__head">
                  <Monogram>{s.ic}</Monogram>
                  <Rank rank={s.rank} />
                </div>
                <div>
                  <h3 className="ds-featcard__title">{s.name}</h3>
                  <div className="ds-card__by" style={{marginTop:6}}>By {s.author}</div>
                </div>
                <p className="ds-card__desc" style={{fontSize:'var(--type-sm)'}}>{s.description}</p>
                <div className="ds-card__foot ds-card__foot--rule">
                  <span>↓ {s.installs} · ★ {s.stars}</span><span>Open ↗</span>
                </div>
              </div>
            ))}
          </HairlineGrid>
        </div>
      </section>

      <section style={{padding:'96px 0',background:'var(--paper-2)',borderBottom:'1px solid var(--line)'}}>
        <div className="ds-wrap">
          <SectionHead index="04 · Index" title={<>Browse <em>servers</em></>} desc="214 entries · sorted by installs" />
          <HairlineGrid columns={3}>
            {DATA.mcpServers.map(s => (
              <div key={s.name} className="ds-card" style={{minHeight:200}}>
                <div style={{display:'flex',alignItems:'center',gap:12}}>
                  <Monogram size={36}>{s.ic}</Monogram>
                  <div>
                    <h3 className="ds-card__name" style={{fontSize:16}}>{s.name}</h3>
                    <div className="ds-card__by">By {s.author}</div>
                  </div>
                </div>
                <p className="ds-card__desc">{s.d}</p>
                <div className="ds-card__foot"><span>↓ {s.installs} · ★ {s.stars}</span><span>Open ↗</span></div>
              </div>
            ))}
          </HairlineGrid>
        </div>
      </section>

      <section style={{padding:'96px 0',borderBottom:'1px solid var(--line)'}}>
        <div className="ds-wrap">
          <SectionHead index="05 · Categories" title={<>By <em>integration</em></>} desc="22 categories" />
          <HairlineGrid columns={4}>
            {['Developer Tools','Databases','Cloud','Communication','Productivity','Design','CRM','Analytics',
              'Payments','Storage','AI/ML','Security'].map((c,i) => (
              <div key={c} className="ds-card" style={{minHeight:120,gap:8}}>
                <MicroLabel size="nano">{String(i+1).padStart(2,'0')}</MicroLabel>
                <span style={{fontSize:14,fontWeight:500}}>{c}</span>
                <span style={{marginTop:'auto',fontFamily:'var(--font-mono)',fontSize:10,color:'var(--mute-2)',
                  letterSpacing:'.1em',textTransform:'uppercase'}}>{4 + ((i*7) % 18)} servers</span>
              </div>
            ))}
          </HairlineGrid>
        </div>
      </section>
    </main>
  );
}

Object.assign(window, { McpDirectory });
