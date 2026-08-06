import React from 'react';

export function StatRow({items,variant='default',columns,style,...rest}){
  const cols = columns || items.length;
  return (
    <div className={'ds-statrow'+(variant==='inverse'?' ds-statrow--inverse':'')}
         style={{gridTemplateColumns:`repeat(${cols},1fr)`,marginTop:variant==='inverse'?0:'48px',...style}} {...rest}>
      {items.map((it,i)=>(
        <div className="ds-statrow__item" key={i}>
          <div className="ds-statrow__v">{it.v}</div>
          <div className="ds-statrow__l">{it.l}</div>
        </div>
      ))}
    </div>
  );
}