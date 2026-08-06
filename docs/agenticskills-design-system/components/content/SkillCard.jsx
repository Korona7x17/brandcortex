import React from 'react';

import { Tag } from '../core/Tag';
import { Rank } from '../core/Rank';

export function SkillCard({name,author,description,category,platforms=[],installs,stars,official,rank,href,action='Open ↗',...rest}){
  const Root = href ? 'a' : 'div';
  return (
    <Root className="ds-card ds-skillcard" href={href} style={{color:'inherit'}} {...rest}>
      <div className="ds-card__head">
        <div>
          <h3 className="ds-card__name">
            {name}
            {official && <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{marginLeft:6,verticalAlign:-2}}><circle cx="12" cy="12" r="10"/><polyline points="8 12 11 15 16 9"/></svg>}
          </h3>
          {author && <div className="ds-card__by">By {author}</div>}
        </div>
        {rank && <Rank rank={rank} />}
      </div>
      {description && <p className="ds-card__desc">{description}</p>}
      <div className="ds-card__meta">
        {category && <Tag variant="solid">{category}</Tag>}
        {platforms.map(p=><Tag key={p}>{p}</Tag>)}
      </div>
      <div className="ds-card__foot">
        <span>{installs && `↓ ${installs}`}{installs && stars && ' · '}{stars && `★ ${stars}`}</span>
        <span>{action}</span>
      </div>
    </Root>
  );
}