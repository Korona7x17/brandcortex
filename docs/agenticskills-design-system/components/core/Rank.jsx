import React from 'react';

export function Rank({rank,suffix='-rank',...rest}){
  return <span className={'ds-rank'+(rank==='S'?' ds-rank--s':'')} {...rest}>{rank}{suffix}</span>;
}