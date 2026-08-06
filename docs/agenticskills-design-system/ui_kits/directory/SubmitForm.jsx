const { Button, MicroLabel, Breadcrumbs, Input, FormField, SegmentedControl } = window;

function SubmitForm({ go }) {
  const [cat, setCat] = React.useState('Web Dev');
  const [lic, setLic] = React.useState('MIT');
  const [sent, setSent] = React.useState(false);
  return (
    <main>
      <section style={{padding:'80px 0 56px',borderBottom:'1px solid var(--line)'}}>
        <div className="ds-wrap">
          <div onClick={(e)=>{const a=e.target.closest('a[href^="#"]');if(a){e.preventDefault();go(a.getAttribute('href').slice(1));}}}>
            <Breadcrumbs items={[{label:'Index',href:'#home'},{label:'Submit'}]} />
          </div>
          <div style={{marginTop:32}}><MicroLabel>Form 01 · Submission</MicroLabel></div>
          <h1 style={{fontSize:'clamp(40px,5vw,72px)',fontWeight:500,letterSpacing:'-.03em',lineHeight:.96,margin:'14px 0 0'}}>
            Submit a <em className="ds-accent">skill</em>.
          </h1>
          <p style={{marginTop:20,fontSize:17,color:'var(--mute-1)',maxWidth:'54ch',lineHeight:1.55}}>
            Free listings reviewed within 48 hours. We check for spec compliance, basic quality, and originality.
            No paywalls — featured placement is editorial.
          </p>
        </div>
      </section>

      <section className="ds-wrap" style={{display:'grid',gridTemplateColumns:'1fr 380px',gap:64,padding:'64px 0',borderBottom:'1px solid var(--line)'}}>
        <form onSubmit={(e) => { e.preventDefault(); setSent(true); }} style={{borderTop:'1px solid var(--line)'}}>
          <FormField label="Skill name" required help="Title case · max 60 char">
            <Input placeholder="e.g. React Best Practices" required />
          </FormField>
          <FormField label="Author" required help="Person or org name">
            <Input placeholder="e.g. Vercel Labs" />
          </FormField>
          <FormField label="GitHub URL" required help="SKILL.md must live in this repo">
            <Input placeholder="https://github.com/owner/repo" />
          </FormField>
          <FormField label="Short description" help="One sentence · 60–140 char">
            <Input multiline placeholder="What does it do, and who is it for?" />
          </FormField>
          <FormField label="Category" help="Pick the closest match">
            <SegmentedControl value={cat} onChange={setCat} options={['Web Dev','Backend','DevOps','AI/ML','Design','Other']} />
          </FormField>
          <FormField label="Licence" help="Open source preferred">
            <SegmentedControl value={lic} onChange={setLic} options={['MIT','Apache 2.0','BSD','Other']} />
          </FormField>
          <FormField label="Notes for the editor" help="Optional">
            <Input multiline placeholder="Known limitations, related skills to link, etc." />
          </FormField>
          <div style={{padding:'32px 0',display:'flex',justifyContent:'space-between',alignItems:'center',flexWrap:'wrap',gap:16}}>
            <MicroLabel>By submitting, you agree to the SKILL.md spec.</MicroLabel>
            <Button type="submit" arrow>{sent ? 'Submitted ✓ — we’ll email you in 48h' : 'Submit for review'}</Button>
          </div>
        </form>

        <aside style={{position:'sticky',top:80,alignSelf:'start',display:'flex',flexDirection:'column',gap:24}}>
          {[
            { h:'What we look for', b:(
              <ol style={{margin:0,paddingLeft:20,fontSize:13,color:'var(--mute-1)',lineHeight:1.7}}>
                <li>SKILL.md follows the open spec</li>
                <li>Description matches behaviour</li>
                <li>No agent-slop or filler content</li>
                <li>Permissive licence</li>
                <li>Tested on at least one platform</li>
              </ol>) },
            { h:'Timeline', b:(<div style={{fontSize:13,color:'var(--mute-1)',lineHeight:1.55,display:'flex',flexDirection:'column',gap:10}}>
                <span><b style={{color:'var(--ink)'}}>Day 0</b> — Submitted. Auto-checks run.</span>
                <span><b style={{color:'var(--ink)'}}>Day 1–2</b> — Editor reviews, runs platform tests.</span>
                <span><b style={{color:'var(--ink)'}}>Day 2–3</b> — Indexed and live, or returned with notes.</span>
              </div>) },
            { h:'Featured placement', b:(<p style={{margin:0,fontSize:13,color:'var(--mute-1)',lineHeight:1.55}}>
                Editorial only — we promote based on quality and fit, never paid placement.</p>) }
          ].map(c => (
            <div key={c.h} style={{border:'1px solid var(--line)',background:'var(--paper)'}}>
              <h4 style={{fontFamily:'var(--font-mono)',fontSize:11,letterSpacing:'.16em',textTransform:'uppercase',
                color:'var(--mute-2)',margin:0,padding:'14px 18px',borderBottom:'1px solid var(--line)',fontWeight:500}}>{c.h}</h4>
              <div style={{padding:18}}>{c.b}</div>
            </div>
          ))}
        </aside>
      </section>
    </main>
  );
}

Object.assign(window, { SubmitForm });
