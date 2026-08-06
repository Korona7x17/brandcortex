import React from 'react';

export function Navbar({active,links=[],brand='AgenticSkills',search=true,searchLabel='Search 143 skills…',cta,ctaHref='/submit',...rest}){
  const [head,...tail] = brand.split(/(?=Skills)/);
  return (
    <header className="ds-nav" {...rest}>
      <nav className="ds-wrap ds-nav__inner">
        <a href="/" className="ds-brand">
          <span className="ds-brand__mark">{brand[0]}</span>
          <span className="ds-brand__name">{head}<span>{tail.join('')}</span></span>
        </a>
        <div className="ds-nav__links">
          {links.map(l=><a key={l.href} href={l.href} {...(active===l.id?{'data-active':''}:{})}>{l.label}</a>)}
        </div>
        <div className="ds-nav__actions">
          {search && (
            <button className="ds-searchtrigger">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
              <span>{searchLabel}</span><kbd>⌘K</kbd>
            </button>
          )}
          {cta && <a className="ds-btn" href={ctaHref}>{cta} <span className="ds-btn__arrow">→</span></a>}
        </div>
      </nav>
    </header>
  );
}