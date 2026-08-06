import React from 'react';

export function InstallPanel({status='Live',statusLabel='Distribution',stats=[],methods=[],label='Install',note='via CLI',...rest}){
  const [i,setI] = React.useState(0);
  const [copied,setCopied] = React.useState(false);
  const cmd = methods[i]?.command || '';
  return (
    <aside className="ds-panel" {...rest}>
      <div className="ds-panel__h"><span>{statusLabel}</span><b>{status}</b></div>
      {stats.length>0 && (
        <div className="ds-panel__stats">
          {stats.map((s,n)=><div key={n}><div className="v">{s.v}</div><div className="l">{s.l}</div></div>)}
        </div>
      )}
      <div className="ds-panel__install">
        <div className="ds-panel__lbl"><span>{label}</span><span>{methods[i]?.note ?? note}</span></div>
        <pre className="ds-panel__cmd">
          <code>{cmd}</code>
          <button className="ds-panel__copy" onClick={()=>{navigator.clipboard&&navigator.clipboard.writeText(cmd.replace(/^\$\s*/,''));setCopied(true);}}>{copied?'Copied':'Copy'}</button>
        </pre>
        {methods.length>1 && (
          <div className="ds-seg" style={{marginTop:12,width:'100%'}}>
            {methods.map((m,n)=><button key={m.label} type="button" style={{flex:1}} {...(i===n?{'data-on':''}:{})} onClick={()=>{setI(n);setCopied(false);}}>{m.label}</button>)}
          </div>
        )}
      </div>
    </aside>
  );
}