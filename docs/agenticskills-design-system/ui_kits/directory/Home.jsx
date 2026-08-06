const { Button, Tag, Icon, MicroLabel, HairlineGrid, SectionHead, StatRow,
        SkillCard, FeatureCard, CategoryCard, StepCard, Terminal,
        SearchInput, SegmentedControl } = window;

function Hero({ go }) {
  return (
    <section style={{position:'relative',padding:'96px 0 80px',borderBottom:'1px solid var(--line)',overflow:'hidden'}}>
      <div style={{position:'absolute',inset:0,pointerEvents:'none',opacity:.7,
        backgroundImage:'linear-gradient(var(--line-3) 1px,transparent 1px),linear-gradient(90deg,var(--line-3) 1px,transparent 1px)',
        backgroundSize:'48px 48px',
        maskImage:'radial-gradient(ellipse at 50% 30%, #000 0%, #000 40%, transparent 75%)',
        WebkitMaskImage:'radial-gradient(ellipse at 50% 30%, #000 0%, #000 40%, transparent 75%)'}} />
      <div className="ds-wrap" style={{position:'relative',display:'grid',gridTemplateColumns:'1.4fr 1fr',gap:64}}>
        <div>
          <span style={{display:'inline-flex',alignItems:'center',gap:10,padding:'6px 10px',border:'1px solid var(--line)',background:'var(--paper)',
            fontFamily:'var(--font-mono)',fontSize:11,letterSpacing:'.12em',textTransform:'uppercase',color:'var(--mute-1)'}}>
            <span className="ds-dot ds-dot--live" />Index 143 / Updated 04.30.26
          </span>
          <h1 style={{fontSize:'clamp(48px,6.4vw,88px)',fontWeight:500,lineHeight:.94,letterSpacing:'-.035em',margin:'24px 0 0'}}>
            The curated index<br />of skills <em className="ds-accent">that make</em><br />agents useful.
          </h1>
          <p style={{marginTop:28,fontSize:18,color:'var(--mute-1)',maxWidth:'54ch',lineHeight:1.55}}>
            A directory for Claude Code, Codex, Cursor, Gemini CLI, and 18 other agent platforms.
            Find, compare, and install skills that are actually maintained — no slop, no noise.
          </p>
          <div style={{marginTop:40,display:'flex',gap:12,flexWrap:'wrap'}}>
            <Button arrow onClick={() => go('home', 'index')}>Browse the index</Button>
            <Button variant="ghost" arrow="↗" onClick={() => go('submit')}>Submit a skill</Button>
          </div>
          <StatRow items={[
            {v:'143',l:'Skills'},{v:'16',l:'Categories'},{v:'18',l:'Platforms'},{v:'100%',l:'Open Source'}]} />
        </div>
        <Terminal meta="00:00:42" cursor>
          <span className="dim"># find a skill</span>{'\n'}
          <span className="pr">$</span> <span className="cmd">npx skills search "react"</span>{'\n'}
          <span className="ok">→ 12 results · sorted by installs</span>{'\n\n'}
          <span className="pr">$</span> <span className="cmd">npx skills add vercel-labs/react-best-practices</span>{'\n'}
          <span className="ok">  fetching SKILL.md… ok</span>{'\n'}
          <span className="ok">  verifying signature… ok</span>{'\n'}
          <span className="ok">  installed → ~/.claude/skills/</span>{'\n\n'}
          <span className="pr">$</span> <span className="cmd">claude</span>{'\n'}
          <span className="dim"># your agent now knows React patterns.</span>{'\n'}
          <span className="pr">$</span>{' '}
        </Terminal>
      </div>
      <div className="ds-wrap" style={{marginTop:64,paddingTop:28,borderTop:'1px solid var(--line)',
        display:'flex',alignItems:'center',justifyContent:'space-between',flexWrap:'wrap',gap:18}}>
        <MicroLabel>Works across</MicroLabel>
        <ul style={{listStyle:'none',margin:0,padding:0,display:'flex',flexWrap:'wrap',gap:28}}>
          {['Claude Code','OpenAI Codex','Cursor','Gemini CLI','GitHub Copilot','Windsurf','Cline','Aider'].map(n =>
            <li key={n} style={{fontFamily:'var(--font-mono)',fontSize:12,color:'var(--mute-1)',textTransform:'uppercase',letterSpacing:'.1em'}}>{n}</li>)}
        </ul>
        <MicroLabel>+10 more →</MicroLabel>
      </div>
    </section>
  );
}

function Home({ go }) {
  const [filter, setFilter] = React.useState('All');
  const shown = filter === 'All' ? DATA.skills : DATA.skills.filter(s => s.category === filter);
  return (
    <main>
      <Hero go={go} />

      <section style={{padding:'96px 0',borderBottom:'1px solid var(--line)'}}>
        <div className="ds-wrap">
          <SectionHead index="02 · Featured" title={<>Editor's <em>picks</em></>} cta="All featured →" ctaHref="#category" />
          <HairlineGrid columns={3} variant="ink">
            {DATA.featured.map(s => <FeatureCard key={s.slug} {...s} onClick={() => go('skill')} style={{cursor:'pointer'}} />)}
          </HairlineGrid>
        </div>
      </section>

      <section id="index" style={{padding:'96px 0',borderBottom:'1px solid var(--line)',background:'var(--paper-2)'}}>
        <div className="ds-wrap">
          <SectionHead index="03 · Index" title={<>Browse <em>everything</em></>}
            desc="Filter by category, platform, or quality. Sort by installs, recency, or alphabetical. 143 entries." />
          <div style={{display:'flex',gap:12,flexWrap:'wrap',padding:'18px 0',
            borderTop:'1px solid var(--line)',borderBottom:'1px solid var(--line)',marginBottom:32}}>
            <SearchInput placeholder="Search skills, authors, tags…" count={shown.length} />
            <SegmentedControl value={filter} onChange={setFilter}
              options={['All','Productivity','Web Dev','Design','Testing','Backend','DevOps','Security']} />
          </div>
          <HairlineGrid columns={3}>
            {shown.map(s => <SkillCard key={s.name} {...s} onClick={() => go('skill')} style={{cursor:'pointer'}} />)}
          </HairlineGrid>
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginTop:32}}>
            <MicroLabel>Showing {shown.length} of 143</MicroLabel>
            <button className="ds-btn ds-btn--ghost" style={{fontFamily:'var(--font-mono)',fontSize:11,letterSpacing:'.14em',textTransform:'uppercase'}}>Load more →</button>
          </div>
        </div>
      </section>

      <section style={{padding:'96px 0',borderBottom:'1px solid var(--line)'}}>
        <div className="ds-wrap">
          <SectionHead index="04 · Categories" title={<>By <em>discipline</em></>}
            desc="16 categories spanning the practical surface area of AI-assisted development." />
          <HairlineGrid columns={4}>
            {DATA.categories.map((c, i) => (
              <CategoryCard key={c.n} index={'C' + String(i+1).padStart(2,'0')} name={c.n} count={c.c}
                description={c.d} topSkills={c.t} icon={<Icon name={c.i} />}
                onClick={() => go('category')} style={{cursor:'pointer'}} />
            ))}
          </HairlineGrid>
        </div>
      </section>

      <section style={{padding:'96px 0',borderBottom:'1px solid var(--line)',background:'var(--paper-2)'}}>
        <div className="ds-wrap">
          <SectionHead index="05 · Method" title={<>From discovery <em>to deploy</em>, in a minute.</>}
            desc="Three steps. One open standard. Works across every supported agent." />
          <HairlineGrid columns={3}>
            <StepCard step="Step 01" title="Discover" glyph={<Icon name="search" size={22} />}
              description="Browse 143 verified skills across 16 categories. Filter by platform, quality tier, and use case."
              command="agenticskills.io/browse" />
            <StepCard step="Step 02" title="Install" glyph={<Icon name="terminal" size={22} />}
              description="One-command CLI install, or drop the SKILL.md into your agent's skills folder. No registry lock-in."
              command="$ npx skills add author/skill" />
            <StepCard step="Step 03" title="Run" glyph={<Icon name="rocket" size={22} />}
              description="Your agent gains the capability immediately. The same SKILL.md works across 18 platforms."
              command="→ skill loaded · 18 platforms" />
          </HairlineGrid>
        </div>
      </section>

      <section style={{padding:'96px 0',borderBottom:'1px solid var(--line)'}}>
        <div className="ds-wrap">
          <SectionHead index="06 · Reach" title={<>One standard. <em>Every</em> platform.</>}
            desc="Skills follow the open SKILL.md spec, adopted by 18+ agents and growing." />
          <HairlineGrid columns={3}>
            {DATA.platforms.map(p => (
              <div key={p.n} className="ds-card" style={{flexDirection:'row',alignItems:'center',gap:14,padding:'18px 20px'}}>
                <div className="ds-monogram" style={{width:42,height:42,fontSize:13}}>{p.n.split(' ').map(w=>w[0]).join('').slice(0,2)}</div>
                <div>
                  <div style={{fontSize:14,fontWeight:500}}>{p.n}</div>
                  <code style={{fontFamily:'var(--font-mono)',fontSize:11,color:'var(--mute-2)'}}>{p.p}</code>
                </div>
              </div>
            ))}
          </HairlineGrid>
        </div>
      </section>
    </main>
  );
}

Object.assign(window, { Home });
