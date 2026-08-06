import React from 'react';

export function FormField({label,required,help,children,...rest}){
  return (
    <div className="ds-field" {...rest}>
      <label className="ds-field__label">
        {label}{required && <span className="ds-field__req"> — required</span>}
        {help && <span className="ds-field__help">{help}</span>}
      </label>
      <div>{children}</div>
    </div>
  );
}