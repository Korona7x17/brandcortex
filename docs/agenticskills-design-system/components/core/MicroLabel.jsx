import React from 'react';

export function MicroLabel({children,size='micro',as:As='span',...rest}){
  return <As className={size==='nano'?'ds-nano':'ds-micro'} {...rest}>{children}</As>;
}