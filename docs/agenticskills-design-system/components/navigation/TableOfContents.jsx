import React from 'react';

export function TableOfContents({title='On this page',items=[],activeId,onSelect,...rest}){
  return (
    <aside className="ds-toc" {...rest}>
      <h4>{title}</h4>
      <ul>
        {items.map(it=>(
          <li key={it.id} {...(activeId===it.id?{'data-on':''}:{})} onClick={()=>onSelect&&onSelect(it.id)}>{it.label}</li>
        ))}
      </ul>
    </aside>
  );
}