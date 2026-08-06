import React from 'react';

export function StepCard({step,title,description,command,glyph,...rest}){
  return (
    <div className="ds-card ds-stepcard" {...rest}>
      {step && <div className="ds-stepcard__n">{step}</div>}
      {glyph && <div className="ds-stepcard__glyph">{glyph}</div>}
      <h3>{title}</h3>
      {description && <p>{description}</p>}
      {command && <code className="ds-stepcard__cmd">{command}</code>}
    </div>
  );
}