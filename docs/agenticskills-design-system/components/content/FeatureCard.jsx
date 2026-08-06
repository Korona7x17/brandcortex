import React from 'react';

import { Tag } from '../core/Tag';

export function FeatureCard({name,author,description,platforms=[],installs,stars,rank='S',status='Official',label='Featured',href,...rest}){
  const Root = href ? 'a' : 'div';
  return (
    <Root className="ds-card ds-featcard" href={href} style={{color:'inherit'}} {...rest}>
      <div className="ds-card__head">
        <span className="ds-featcard__tag">{label}</span>
        <span className="ds-micro"><b style={{color:'var(--ink)',fontWeight:600}}>{rank}</b>-rank · {status}</span>
      </div>
      <div>
        <h3 className="ds-featcard__title">{name}</h3>
        {author && <div className="ds-card__by" style={{marginTop:6}}>By {author}</div>}
      </div>
      {description && <p className="ds-card__desc" style={{fontSize:'var(--type-sm)'}}>{description}</p>}
      <div className="ds-card__meta">{platforms.map(p=><Tag key={p}>{p}</Tag>)}</div>
      <div className="ds-card__foot ds-card__foot--rule">
        <span>{installs && `↓ ${installs}`}{installs && stars && ' · '}{stars && `★ ${stars}`}</span>
        <span>Open ↗</span>
      </div>
    </Root>
  );
}