import React from 'react';

export function HairlineGrid({columns=3,variant='hairline',children,style,...rest}){
  const cls = 'ds-grid' + (variant==='ink' ? ' ds-grid--ink' : '');
  return <div className={cls} style={{gridTemplateColumns:typeof columns==='number'?`repeat(${columns},1fr)`:columns,...style}} {...rest}>{children}</div>;
}