import React from 'react';

export function PageHead({crumbs,eyebrow,title,lede,children,...rest}){
  return (
    <section className="ds-pagehead" {...rest}>
      <div className="ds-wrap">
        {crumbs}
        {eyebrow && <span className="ds-micro" style={{display:'block',marginTop:crumbs?'32px':0}}>{eyebrow}</span>}
        <h1 className="ds-pagehead__title">{title}</h1>
        {lede && <p className="ds-pagehead__lede">{lede}</p>}
        {children}
      </div>
    </section>
  );
}