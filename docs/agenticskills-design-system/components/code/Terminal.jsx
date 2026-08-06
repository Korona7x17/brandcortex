import React from 'react';

export function Terminal({title='~/agent · zsh',meta,children,dots=true,cursor=false,...rest}){
  return (
    <div className="ds-terminal" {...rest}>
      <div className="ds-terminal__bar">
        {dots && <div className="ds-terminal__dots"><i/><i/><i/></div>}
        <span>{title}</span>
        <span>{meta}</span>
      </div>
      <pre>{children}{cursor && <span className="ds-terminal__cursor" />}</pre>
    </div>
  );
}