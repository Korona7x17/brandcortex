import React from 'react';

export function SearchInput({count,...rest}){
  return (
    <div className="ds-searchinput">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
      <input {...rest} />
      {count!=null && <span className="ds-micro">{count}</span>}
    </div>
  );
}