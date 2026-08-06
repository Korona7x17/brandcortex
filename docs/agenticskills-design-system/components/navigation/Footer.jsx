import React from 'react';

export function Footer({brand='AgenticSkills',blurb,columns=[],left,right,...rest}){
  const [head,...tail] = brand.split(/(?=Skills)/);
  return (
    <footer className="ds-footer" {...rest}>
      <div className="ds-wrap">
        <div className="ds-footer__grid">
          <div className="ds-footer__brand">
            <a href="/" className="ds-brand">
              <span className="ds-brand__mark">{brand[0]}</span>
              <span className="ds-brand__name">{head}<span>{tail.join('')}</span></span>
            </a>
            {blurb && <p>{blurb}</p>}
          </div>
          {columns.map(col=>(
            <div className="ds-footer__col" key={col.title}>
              <h4>{col.title}</h4>
              <ul>{col.links.map(l=><li key={l.href}><a href={l.href}>{l.label}</a></li>)}</ul>
            </div>
          ))}
        </div>
        <div className="ds-footer__bot"><span>{left}</span><span>{right}</span></div>
      </div>
    </footer>
  );
}