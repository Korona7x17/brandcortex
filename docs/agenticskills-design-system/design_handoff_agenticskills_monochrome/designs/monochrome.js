/* Shared chrome: ticker, navbar, footer, newsletter — injected by mono-chrome.js */

window.MonoChrome = {
  ticker: ({ version = "v2.4.1", date = "Apr 30 2026" } = {}) => `
    <div class="ticker">
      <div class="wrap ticker-inner">
        <span><span class="dot"></span>Index live · ${version} · ${date}</span>
        <div class="ticker-feed">
          <span><b>+12</b>&nbsp; new this week</span>
          <span><b>2.4M</b>&nbsp; installs/mo</span>
          <span><b>18</b>&nbsp; platforms tracked</span>
        </div>
        <span class="mono">[ ⌘K ]&nbsp; search</span>
      </div>
    </div>`,

  navbar: ({ active = "" } = {}) => `
    <header class="nav">
      <div class="wrap nav-inner">
        <a href="index.html" class="brand">
          <span class="brand-mark">A</span>
          <span class="brand-name">Agentic<span>Skills</span></span>
        </a>
        <nav class="nav-links">
          <a href="index.html" class="${active === 'skills' ? 'active' : ''}">Skills</a>
          <a href="mcp.html" class="${active === 'mcp' ? 'active' : ''}">MCP Servers</a>
          <a href="workflows.html" class="${active === 'workflows' ? 'active' : ''}">Workflows</a>
          <a href="learn.html" class="${active === 'learn' ? 'active' : ''}">Learn</a>
          <a href="changelog.html" class="${active === 'changelog' ? 'active' : ''}">Changelog</a>
        </nav>
        <div class="nav-actions">
          <button class="search-trigger">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
            <span>Search 143 skills…</span>
            <kbd>⌘K</kbd>
          </button>
          <a href="submit.html" class="btn">Submit a Skill <span class="arrow">→</span></a>
        </div>
      </div>
    </header>`,

  newsletter: () => `
    <section class="news">
      <div class="wrap">
        <h2>The weekly <em>dispatch</em>.</h2>
        <p>New skills, creator spotlights, and workflow notes. One email per week. No spam, no tracking pixels.</p>
        <form onsubmit="event.preventDefault();this.querySelector('input').value='';this.querySelector('button').textContent='Subscribed ✓'">
          <input type="email" placeholder="you@example.com" required />
          <button type="submit">Subscribe</button>
        </form>
        <p class="fine">Free forever · Unsubscribe anytime · 12,400 readers</p>
      </div>
    </section>`,

  footer: () => `
    <footer>
      <div class="wrap">
        <div class="foot-grid">
          <div class="foot-brand">
            <a href="index.html" class="brand">
              <span class="brand-mark">A</span>
              <span class="brand-name">Agentic<span>Skills</span></span>
            </a>
            <p>The curated index for AI agent skills. Independent, open source, and not affiliated with any platform vendor.</p>
          </div>
          <div class="foot">
            <h4>Product</h4>
            <ul>
              <li><a href="index.html">Browse</a></li>
              <li><a href="mcp.html">MCP Servers</a></li>
              <li><a href="workflows.html">Workflows</a></li>
              <li><a href="submit.html">Submit</a></li>
            </ul>
          </div>
          <div class="foot">
            <h4>Resources</h4>
            <ul>
              <li><a href="learn.html">Learn</a></li>
              <li><a href="changelog.html">Changelog</a></li>
              <li><a href="#">SKILL.md spec</a></li>
              <li><a href="#">API</a></li>
            </ul>
          </div>
          <div class="foot">
            <h4>Company</h4>
            <ul>
              <li><a href="about.html">About</a></li>
              <li><a href="#">Contact</a></li>
              <li><a href="#">Privacy</a></li>
              <li><a href="#">Terms</a></li>
            </ul>
          </div>
        </div>
        <div class="foot-bot">
          <span>© 2026 AgenticSkills · Built for developers, by developers</span>
          <span>v2.4.1 · Indexed Apr 30 2026</span>
        </div>
      </div>
    </footer>`,

  mount: ({ active = "" } = {}) => {
    document.querySelectorAll('[data-mc="ticker"]').forEach(el => el.outerHTML = MonoChrome.ticker());
    document.querySelectorAll('[data-mc="navbar"]').forEach(el => el.outerHTML = MonoChrome.navbar({ active }));
    document.querySelectorAll('[data-mc="newsletter"]').forEach(el => el.outerHTML = MonoChrome.newsletter());
    document.querySelectorAll('[data-mc="footer"]').forEach(el => el.outerHTML = MonoChrome.footer());
  }
};
