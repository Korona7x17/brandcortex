import React from 'react';

export function Button({children,variant='primary',arrow,href,disabled,type='button',...rest}){
  const cls = 'ds-btn' + (variant==='ghost' ? ' ds-btn--ghost' : '');
  const inner = <>{children}{arrow && <span className="ds-btn__arrow">{arrow===true?'→':arrow}</span>}</>;
  if(href && !disabled) return <a className={cls} href={href} {...rest}>{inner}</a>;
  return <button className={cls} type={type} disabled={disabled} style={disabled?{opacity:.4,cursor:'not-allowed'}:undefined} {...rest}>{inner}</button>;
}