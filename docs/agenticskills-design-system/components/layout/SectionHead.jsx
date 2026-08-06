import React from 'react';

export function SectionHead({index,title,desc,cta,ctaHref,...rest}){
  return (
    <div className="ds-sechead" {...rest}>
      {index && <span className="ds-micro">{index}</span>}
      <div><h2 className="ds-sechead__title">{title}</h2></div>
      {desc && <span className="ds-sechead__desc">{desc}</span>}
      {cta && <a className="ds-sechead__cta" href={ctaHref||'#'}>{cta}</a>}
    </div>
  );
}