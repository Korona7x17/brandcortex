import React from 'react';

export function Monogram({name,size=42,children,...rest}){
  const words = (name||'').trim().split(/\s+/).filter(Boolean);
  const initials = children || (words.length > 1
    ? words.map(w=>w[0]).join('').slice(0,2).toUpperCase()
    : (words[0]||'').slice(0,2).toUpperCase());
  return <div className="ds-monogram" style={{width:size,height:size,fontSize:Math.round(size/3)}} {...rest}>{initials}</div>;
}