const { Tag, Rank, MicroLabel, Breadcrumbs, HairlineGrid, SectionHead,
        InstallPanel, TableOfContents, SkillCard } = window;

function SkillDetail({ go }) {
  const [active, setActive] = React.useState('overview');
  return (
    <main>
      <section style={{padding:'48px 0 56px',borderBottom:'1px solid var(--line)'}}>
        <div className="ds-wrap">
          <div onClick={(e)=>{const a=e.target.closest('a[href^="#"]');if(a){e.preventDefault();go(a.getAttribute('href').slice(1));}}}>
            <Breadcrumbs items={[{label:'Index',href:'#home'},{label:'Productivity',href:'#category'},{label:'Find Skills'}]} />
          </div>
          <div style={{display:'grid',gridTemplateColumns:'1fr auto',gap:48,alignItems:'start',marginTop:32}}>
            <div>
              <h1 style={{fontSize:'clamp(40px,5.4vw,72px)',fontWeight:500,letterSpacing:'-.03em',lineHeight:.98,margin:0}}>
                Find <em className="ds-accent">Skills</em>
              </h1>
              <div style={{display:'flex',gap:14,alignItems:'center',flexWrap:'wrap',marginTop:18,
                fontFamily:'var(--font-mono)',fontSize:12,color:'var(--mute-2)',textTransform:'uppercase',letterSpacing:'.12em'}}>
                <span>By <span style={{color:'var(--ink)'}}>Vercel Labs</span></span>
                <span style={{display:'inline-flex',alignItems:'center',gap:5,border:'1px solid var(--ink)',padding:'3px 7px',color:'var(--ink)'}}>✓&nbsp; Official partner</span>
                <span>S-rank</span><span>MIT License</span><span>Updated 02.15.26</span>
              </div>
              <p style={{marginTop:28,fontSize:18,color:'var(--mute-1)',maxWidth:'62ch',lineHeight:1.55}}>
                The meta-skill for skill discovery. Search, compare, and install across the entire AgenticSkills
                ecosystem from inside your agent — a package manager for AI capabilities.
              </p>
              <div style={{marginTop:28,display:'flex',flexWrap:'wrap',gap:6}}>
                <Tag variant="solid">Productivity</Tag><Tag>Open Source</Tag>
                <Tag>Discovery</Tag><Tag>Installation</Tag><Tag>Meta</Tag>
              </div>
            </div>
            <InstallPanel
              stats={[{v:'271K',l:'Installs'},{v:'3,240',l:'Stars'},{v:'98%',l:'Compat'},{v:'v3.2',l:'Latest'}]}
              methods={[
                {label:'CLI',command:'$ npx skills add vercel-labs/find-skills',note:'via CLI'},
                {label:'Manual',command:'# Drop SKILL.md into ~/.claude/skills/',note:'no CLI'},
                {label:'Git',command:'$ git clone github.com/vercel-labs/find-skills',note:'from source'}]} />
          </div>
        </div>
      </section>

      <section className="ds-wrap" style={{display:'grid',gridTemplateColumns:'1fr 320px',gap:64,padding:'80px 0',borderBottom:'1px solid var(--line)'}}>
        <article className="ds-prose">
          <h2>Overview</h2>
          <p>Find Skills enables your AI agent to discover, search, and install skills from the AgenticSkills index
            without leaving the conversation. It provides a unified interface for browsing categories, checking
            platform compatibility, and one-command installation across every supported agent.</p>
          <p>Think of it as a package manager for AI agent capabilities — <code>npm</code> for prompts, but with
            quality ranking and platform-aware installation paths built in.</p>
          <blockquote>"The meta-skill that finally made our agent setup repeatable across teams. Onboarding a new
            developer now takes minutes." — Adoption note, infrastructure team at Stripe</blockquote>
          <h2>Usage</h2>
          <p>Once installed, ask your agent to find skills in plain language. It queries the index, returns ranked
            matches, and offers to install on confirmation.</p>
          <pre><code>{`> find a skill for postgres migrations
→ 4 matches · sorted by quality

  S  supabase-postgres        82,100 installs
  A  prisma-best-practices    36,200 installs
  A  using-neon               18,900 installs
  B  raw-sql-helpers           4,800 installs

> install supabase-postgres
✓ skill installed → ~/.claude/skills/supabase-postgres`}</code></pre>
          <h3>What it gives your agent</h3>
          <ul>
            <li>Natural-language search across 143 indexed skills</li>
            <li>Quality-aware ranking, weighted by installs and recency</li>
            <li>Per-platform install paths for every supported agent</li>
            <li>Conflict detection when two skills overlap in scope</li>
            <li>Offline-first cache with a weekly index refresh</li>
          </ul>
          <h2>Compatibility</h2>
          <p>Find Skills follows the open SKILL.md spec and works on any agent that supports it. Platform-specific
            install paths are detected automatically.</p>
          <h2>Maintained by</h2>
          <p>Vercel Labs, with contributions from the AgenticSkills community. Issues are triaged within 48 hours.</p>
        </article>
        <TableOfContents activeId={active} onSelect={setActive} items={[
          {id:'overview',label:'Overview'},{id:'usage',label:'Usage'},
          {id:'capabilities',label:'Capabilities'},{id:'compat',label:'Compatibility'},
          {id:'maint',label:'Maintained by'}]} />
      </section>

      <section style={{padding:'80px 0',background:'var(--paper-2)',borderBottom:'1px solid var(--line)'}}>
        <div className="ds-wrap">
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-end',marginBottom:32}}>
            <div>
              <MicroLabel>Compatibility</MicroLabel>
              <h2 style={{fontSize:32,fontWeight:500,letterSpacing:'-.02em',margin:'8px 0 0'}}>
                Tested on <em className="ds-accent">9 platforms</em></h2>
            </div>
            <MicroLabel>Last verified 04.30.26</MicroLabel>
          </div>
          <HairlineGrid columns={4}>
            {[['Claude Code',1],['OpenAI Codex',1],['Cursor',1],['Gemini CLI',1],
              ['GitHub Copilot',1],['Windsurf',1],['Cline',0],['Aider',0]].map(([n,ok]) => (
              <div key={n} style={{padding:18,display:'flex',justifyContent:'space-between',alignItems:'center',gap:10,background:'var(--paper)'}}>
                <span style={{fontSize:14,fontWeight:500}}>{n}</span>
                <span style={{fontFamily:'var(--font-mono)',fontSize:11,letterSpacing:'.12em',textTransform:'uppercase',color:ok?'var(--ink)':'var(--mute-2)'}}>
                  <span className={'ds-dot'+(ok?'':' ds-dot--off')} style={{marginRight:6}} />{ok?'Verified':'Untested'}
                </span>
              </div>
            ))}
          </HairlineGrid>
        </div>
      </section>

      <section style={{padding:'80px 0',borderBottom:'1px solid var(--line)'}}>
        <div className="ds-wrap">
          <SectionHead index="Related" title={<>Also <em>in productivity</em></>} cta="All in category →" ctaHref="#category" />
          <HairlineGrid columns={3} variant="ink">
            <SkillCard name="Skill Creator" author="Anthropic" rank="A" official installs="35K" stars="492"
              platforms={['Claude','Codex']} description="Meta-skill that helps you write a SKILL.md that follows the spec." />
            <SkillCard name="Brainstorming" author="Patrick Collison" rank="B" installs="38K" stars="410"
              platforms={['Claude','Multi']} description="Structured ideation: divergent passes, then convergent ranking." />
            <SkillCard name="Loki Mode" author="Latent Labs" rank="A" installs="22K" stars="318"
              platforms={['Claude','Codex']} description="Plan-then-execute orchestration for long-running agent tasks." />
          </HairlineGrid>
        </div>
      </section>
    </main>
  );
}

Object.assign(window, { SkillDetail });
