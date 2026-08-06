import React from 'react';

export function ArticleCard({title,excerpt,category,readTime,date,image,href,action='Read ↗',...rest}){
  const Root = href ? 'a' : 'div';
  return (
    <Root className="ds-card ds-artcard" href={href} style={{color:'inherit'}} {...rest}>
      <div className="ds-artcard__img">{image || `[ ${(category||'article').toLowerCase()} ]`}</div>
      <div className="ds-artcard__body">
        <div className="ds-artcard__meta">
          {category && <span>{category}</span>}
          {readTime && <span>{readTime} read</span>}
        </div>
        <h3 className="ds-card__name" style={{fontSize:'var(--type-h5)'}}>{title}</h3>
        {excerpt && <p className="ds-card__desc">{excerpt}</p>}
        <div className="ds-card__foot"><span>{date}</span><span>{action}</span></div>
      </div>
    </Root>
  );
}