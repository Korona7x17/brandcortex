import React from 'react';

export function Tag({children,variant='default',...rest}){
  const m = {default:'',solid:' ds-tag--solid',ink:' ds-tag--ink'};
  return <span className={'ds-tag'+(m[variant]||'')} {...rest}>{children}</span>;
}