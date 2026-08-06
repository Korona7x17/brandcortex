import React from 'react';

export function Input({multiline,...rest}){
  return multiline
    ? <textarea className="ds-input" {...rest} />
    : <input className="ds-input" {...rest} />;
}