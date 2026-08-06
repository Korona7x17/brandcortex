import React from 'react';

export function Breadcrumbs({items,...rest}){
  return (
    <nav className="ds-crumbs" {...rest}>
      {items.map((it,i)=>(
        <React.Fragment key={i}>
          {i>0 && <span className="ds-crumbs__sep">/</span>}
          {it.href ? <a href={it.href}>{it.label}</a> : <span className="ds-crumbs__here">{it.label}</span>}
        </React.Fragment>
      ))}
    </nav>
  );
}