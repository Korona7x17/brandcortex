const { MicroLabel, Breadcrumbs, HairlineGrid, StatRow, SkillCard,
        SearchInput, SegmentedControl } = window;

function CategoryBrowse({ go }) {
  const [filter, setFilter] = React.useState('All');
  const list = filter === 'All' ? DATA.webDevSkills
    : filter === 'S-rank' ? DATA.webDevSkills.filter(s => s.rank === 'S')
    : DATA.webDevSkills.filter(s => s.official);
  return (
    <main>
      <section style={{padding:'48px 0 56px',borderBottom:'1px solid var(--line)',background:'var(--paper-2)'}}>
        <div className="ds-wrap">
          <div onClick={(e)=>{const a=e.target.closest('a[href^="#"]');if(a){e.preventDefault();go(a.getAttribute('href').slice(1));}}}>
            <Breadcrumbs items={[{label:'Index',href:'#home'},{label:'Web Development'}]} />
          </div>
          <div style={{marginTop:32}}><MicroLabel>Category 01 / 16</MicroLabel></div>
          <h1 style={{fontSize:'clamp(48px,6vw,84px)',fontWeight:500,letterSpacing:'-.03em',lineHeight:.96,margin:'18px 0 0'}}>
            Web <em className="ds-accent">Development</em>
          </h1>
          <p style={{marginTop:24,fontSize:17,color:'var(--mute-1)',maxWidth:'60ch',lineHeight:1.55}}>
            Frontend frameworks, React, Next.js, and modern web tooling. The most actively maintained part of the
            index — 15 skills, updated weekly.
          </p>
          <StatRow items={[
            {v:'15',l:'Skills'},{v:'847K',l:'Total installs'},{v:'12',l:'Officials'},{v:'02.18.26',l:'Last update'}]} />
        </div>
      </section>

      <div className="ds-wrap">
        <div style={{display:'flex',gap:12,flexWrap:'wrap',padding:'18px 0',borderBottom:'1px solid var(--line)'}}>
          <SearchInput placeholder="Search Web Development skills…" count={list.length} />
          <SegmentedControl value={filter} onChange={setFilter} options={['All','S-rank','Official']} />
        </div>
        <div style={{padding:'32px 0 80px'}}>
          <HairlineGrid columns={3}>
            {list.map(s => <SkillCard key={s.name} {...s} category="Web Dev" onClick={() => go('skill')} style={{cursor:'pointer'}} />)}
          </HairlineGrid>
        </div>
      </div>

      <section style={{padding:'80px 0',background:'var(--paper-2)',borderTop:'1px solid var(--line)'}}>
        <div className="ds-wrap">
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-end',marginBottom:32}}>
            <div>
              <MicroLabel>Adjacent</MicroLabel>
              <h2 style={{fontSize:32,fontWeight:500,letterSpacing:'-.02em',margin:'8px 0 0'}}>
                Other <em className="ds-accent">categories</em></h2>
            </div>
          </div>
          <HairlineGrid columns={4}>
            {DATA.categories.slice(1,9).map(c => (
              <a key={c.n} href="#category" onClick={(e)=>e.preventDefault()}
                 style={{padding:18,background:'var(--paper)',display:'flex',justifyContent:'space-between',alignItems:'center',gap:12,fontSize:14}}>
                <span>{c.n}</span>
                <span style={{fontFamily:'var(--font-mono)',fontSize:11,color:'var(--mute-2)',letterSpacing:'.1em'}}>{c.c} skills</span>
              </a>
            ))}
          </HairlineGrid>
        </div>
      </section>
    </main>
  );
}

Object.assign(window, { CategoryBrowse });
