import React from 'react';

export function CategoryCard({name,count,description,topSkills=[],index,icon,href,...rest}){
  const Root = href ? 'a' : 'div';
  return (
    <Root className="ds-card ds-catcard" href={href} style={{color:'inherit'}} {...rest}>
      {index && <span className="ds-catcard__num">{index}</span>}
      {icon && <div className="ds-catcard__icon">{icon}</div>}
      <div>
        <h3 className="ds-card__name" style={{fontSize:'var(--type-card-xs)'}}>{name}</h3>
        {count!=null && <span className="ds-card__by">{count} skills</span>}
      </div>
      {description && <p className="ds-card__desc" style={{fontSize:'12px'}}>{description}</p>}
      {topSkills.length>0 && <div className="ds-catcard__top">{topSkills.join(' · ')}</div>}
    </Root>
  );
}