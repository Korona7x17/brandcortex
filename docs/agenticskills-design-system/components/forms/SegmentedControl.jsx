import React from 'react';

export function SegmentedControl({options=[],value,onChange,...rest}){
  return (
    <div className="ds-seg" {...rest}>
      {options.map(o=>{
        const v = typeof o==='string'?o:o.value, l = typeof o==='string'?o:o.label;
        return <button key={v} type="button" {...(value===v?{'data-on':''}:{})} onClick={()=>onChange&&onChange(v)}>{l}</button>;
      })}
    </div>
  );
}