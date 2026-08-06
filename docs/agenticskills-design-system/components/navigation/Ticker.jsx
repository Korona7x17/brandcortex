import React from 'react';

export function Ticker({version='v2.4.1',date='Apr 30 2026',feed=[],hint='[ ⌘K ]  search',...rest}){
  return (
    <div className="ds-ticker" {...rest}>
      <div className="ds-wrap ds-ticker__inner">
        <span><span className="ds-dot ds-dot--live"></span>Index live · {version} · {date}</span>
        <div className="ds-ticker__feed">
          {feed.map((it,i)=><span key={i}><b>{it.v}</b>&nbsp; {it.l}</span>)}
        </div>
        <span style={{fontFamily:'var(--font-mono)'}}>{hint}</span>
      </div>
    </div>
  );
}