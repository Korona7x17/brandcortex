const { Ticker, Navbar, Footer, NewsletterForm } = window;

function Shell({ active, route, go, children, newsletter = true }) {
  return (
    <div>
      <Ticker feed={DATA.tickerFeed} />
      <div onClick={(e) => {
        const a = e.target.closest('a[href^="#"]');
        if (a) { e.preventDefault(); go(a.getAttribute('href').slice(1)); }
      }}>
        <Navbar active={active} links={DATA.nav} cta="Submit a Skill" ctaHref="#submit" />
      </div>
      {children}
      {newsletter && (
        <NewsletterForm
          title={<>The weekly <em>dispatch</em>.</>}
          body="New skills, creator spotlights, and workflow notes. One email per week. No spam, no tracking pixels."
          fine="Free forever · Unsubscribe anytime · 12,400 readers" />
      )}
      <div onClick={(e) => {
        const a = e.target.closest('a[href^="#"]');
        if (a) { e.preventDefault(); go(a.getAttribute('href').slice(1)); }
      }}>
        <Footer
          blurb="The curated index for AI agent skills. Independent, open source, and not affiliated with any platform vendor."
          columns={DATA.footerColumns}
          left="© 2026 AgenticSkills · Built for developers, by developers"
          right="v2.4.1 · Indexed Apr 30 2026" />
      </div>
    </div>
  );
}

Object.assign(window, { Shell });
