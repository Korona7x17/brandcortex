/* Illustrative content for the kit. Not production data. */
window.DATA = {
  nav: [
    { id:'skills', label:'Skills', href:'#home' },
    { id:'mcp', label:'MCP Servers', href:'#mcp' },
    { id:'workflows', label:'Workflows', href:'#workflows' },
    { id:'learn', label:'Learn', href:'#learn' },
    { id:'changelog', label:'Changelog', href:'#changelog' }
  ],
  tickerFeed: [
    { v:'+12', l:'new this week' },
    { v:'2.4M', l:'installs/mo' },
    { v:'18', l:'platforms tracked' }
  ],
  footerColumns: [
    { title:'Product', links:[{label:'Browse',href:'#home'},{label:'MCP Servers',href:'#mcp'},{label:'Workflows',href:'#'},{label:'Submit',href:'#submit'}] },
    { title:'Resources', links:[{label:'Learn',href:'#'},{label:'Changelog',href:'#'},{label:'SKILL.md spec',href:'#'},{label:'API',href:'#'}] },
    { title:'Company', links:[{label:'About',href:'#'},{label:'Contact',href:'#'},{label:'Privacy',href:'#'},{label:'Terms',href:'#'}] }
  ],
  featured: [
    { slug:'find-skills', name:'Find Skills', author:'Vercel Labs', rank:'S', status:'Official',
      description:'The meta-skill for skill discovery. Search, compare, and install across the entire index from inside your agent.',
      platforms:['Claude','Codex','Cursor','+5'], installs:'271.4K', stars:'3.2K' },
    { slug:'frontend-design', name:'Frontend Design', author:'Anthropic', rank:'S', status:'Official',
      description:'Aesthetic direction and component patterns for production frontends. Teaches agents to commit to a direction.',
      platforms:['Claude','Cursor','Codex','+3'], installs:'184.0K', stars:'2.1K' },
    { slug:'systematic-debugging', name:'Systematic Debugging', author:'Bryan Helmkamp', rank:'S', status:'Verified',
      description:'A four-step method — reproduce, isolate, hypothesize, fix — that keeps agents from flailing on hard bugs.',
      platforms:['Claude','Multi','Codex','+2'], installs:'96.8K', stars:'1.4K' }
  ],
  skills: [
    { name:'Find Skills', author:'Vercel Labs', category:'Productivity', rank:'S', official:true, installs:'271.4K', stars:'3.2K', platforms:['Claude','Codex','Cursor'], description:'The meta-skill for skill discovery — search, compare, and install across the index.' },
    { name:'React Best Practices', author:'Vercel Labs', category:'Web Dev', rank:'S', official:true, installs:'198.0K', stars:'2.4K', platforms:['Claude','Cursor','Codex'], description:'Modern React patterns: hooks, composition, performance, server components.' },
    { name:'Frontend Design', author:'Anthropic', category:'Design', rank:'S', official:true, installs:'184.0K', stars:'2.1K', platforms:['Claude','Cursor','Multi'], description:'Aesthetic direction and component patterns for production frontends.' },
    { name:'Systematic Debugging', author:'Bryan Helmkamp', category:'Testing', rank:'S', installs:'96.8K', stars:'1.4K', platforms:['Claude','Codex','Multi'], description:'A disciplined four-step debugging method that survives hard bugs.' },
    { name:'Supabase Postgres', author:'Supabase', category:'Backend', rank:'A', official:true, installs:'82.1K', stars:'1.1K', platforms:['Claude','Cursor','Codex'], description:'Type-safe queries, RLS, migrations, and edge functions.' },
    { name:'Vercel Deploy', author:'Vercel Labs', category:'DevOps', rank:'A', official:true, installs:'71.4K', stars:'940', platforms:['Claude','Cursor','Multi'], description:'Deploy any Next.js, Remix, or static project with the Vercel CLI.' },
    { name:'Beautiful Prose', author:'Tom MacWright', category:'Documents', rank:'A', installs:'58.2K', stars:'720', platforms:['Claude','Multi'], description:'Editorial voice for long-form writing — kills AI tells, restores rhythm.' },
    { name:'OWASP Top 10', author:'Snyk', category:'Security', rank:'A', installs:'46.7K', stars:'612', platforms:['Claude','Codex','Cursor'], description:'Audit code for the OWASP Top 10 with concrete fixes.' },
    { name:'Brainstorming', author:'Patrick Collison', category:'Productivity', rank:'B', installs:'38.4K', stars:'410', platforms:['Claude','Multi'], description:'Structured ideation: divergent passes, then convergent ranking.' }
  ],
  categories: [
    { n:'Web Development', c:15, i:'layout', d:'Frontend frameworks, React, Next.js, and modern web tooling.', t:['react-best-practices','frontend-design'] },
    { n:'Backend & APIs', c:10, i:'server', d:'Server-side development, databases, and API integration.', t:['supabase-postgres','better-auth'] },
    { n:'DevOps & Infra', c:14, i:'rocket', d:'Deployment, CI/CD, cloud infrastructure, and automation.', t:['vercel-deploy','terraform-codegen'] },
    { n:'Code Quality & Testing', c:15, i:'flask', d:'Testing, debugging, code review, and quality assurance.', t:['systematic-debugging','tdd'] },
    { n:'AI/ML Development', c:12, i:'brain', d:'Machine learning, model training, and generative AI.', t:['hugging-face-cli','imagegen'] },
    { n:'Data Science', c:6, i:'chart', d:'Visualization, scientific computing, and analytics.', t:['claude-d3js','jupyter'] },
    { n:'Content & Marketing', c:13, i:'pen', d:'Copywriting, content strategy, and marketing automation.', t:['copywriting','content-strategy'] },
    { n:'SEO & Growth', c:7, i:'trend', d:'Search optimization, analytics, and growth strategies.', t:['seo-audit','technical-seo'] },
    { n:'Design & UI/UX', c:9, i:'palette', d:'Design systems, accessibility, and UX patterns.', t:['web-design-guidelines','ui-ux-pro'] },
    { n:'Productivity', c:12, i:'zap', d:'Workflow optimization, ideation, and developer tools.', t:['find-skills','brainstorming'] },
    { n:'Document Creation', c:10, i:'file', d:'PDF generation, documentation, structured content.', t:['pdf','beautiful-prose'] },
    { n:'Security', c:12, i:'shield', d:'Auditing, static analysis, and vulnerability detection.', t:['audit-website','owasp-top-10'] },
    { n:'Database', c:5, i:'database', d:'Optimization, migrations, and data modeling.', t:['using-neon','prisma-bp'] },
    { n:'Mobile Development', c:7, i:'mobile', d:'React Native, iOS, Android, cross-platform.', t:['expo-patterns','mobile-ui'] },
    { n:'Agent Architecture', c:8, i:'blocks', d:'Multi-agent systems, MCP servers, orchestration.', t:['mcp-builder','loki-mode'] },
    { n:'Official Partners', c:8, i:'check', d:'Skills from official platform teams and verified partners.', t:['find-skills','vercel-deploy'] }
  ],
  webDevSkills: [
    { name:'React Best Practices', author:'Vercel Labs', rank:'S', official:true, installs:'198K', stars:'2.4K', platforms:['Claude','Cursor','Codex'], description:'Hooks, composition, performance, server components.' },
    { name:'Next Best Practices', author:'Vercel Labs', rank:'S', official:true, installs:'142K', stars:'1.8K', platforms:['Claude','Cursor','Codex'], description:'App Router, streaming, server actions, deployment patterns.' },
    { name:'Frontend Design', author:'Anthropic', rank:'S', official:true, installs:'184K', stars:'2.1K', platforms:['Claude','Cursor','Multi'], description:'Aesthetic direction and component patterns for production frontends.' },
    { name:'Tailwind Patterns', author:'Tailwind Labs', rank:'A', official:true, installs:'96K', stars:'1.1K', platforms:['Claude','Cursor'], description:'Idiomatic utility composition and design-token strategies.' },
    { name:'Astro Skill', author:'Astro Build', rank:'A', official:true, installs:'42K', stars:'640', platforms:['Claude','Multi'], description:'Content sites, MDX, view transitions, islands architecture.' },
    { name:'Accessibility Audit', author:'Deque Systems', rank:'A', installs:'28K', stars:'352', platforms:['Claude','Cursor','Multi'], description:'WCAG-aware code review and a11y-first refactoring guidance.' },
    { name:'SvelteKit Skill', author:'Svelte Society', rank:'A', installs:'31K', stars:'410', platforms:['Claude','Cursor'], description:'File-based routing, runes, and SSR patterns.' },
    { name:'CSS Architecture', author:'Andy Bell', rank:'B', installs:'19K', stars:'244', platforms:['Claude','Multi'], description:'CUBE CSS, modern layout primitives, container queries.' },
    { name:'Vue Idioms', author:'Vue Labs', rank:'B', installs:'24K', stars:'312', platforms:['Claude','Cursor'], description:'Composition API, Pinia, and Nuxt patterns done right.' }
  ],
  mcpFeatured: [
    { ic:'GH', name:'GitHub', author:'GitHub · Official', rank:'S', installs:'412K', stars:'8.2K', description:'Read repos, manage issues, review PRs, and run Actions from any MCP-aware agent.' },
    { ic:'ST', name:'Stripe', author:'Stripe · Official', rank:'S', installs:'218K', stars:'4.6K', description:'Query customers, refund charges, manage subscriptions, read financial reports.' },
    { ic:'AW', name:'AWS', author:'Anthropic · Official', rank:'S', installs:'184K', stars:'3.8K', description:'S3, Lambda, RDS and CloudWatch surfaces, scoped via IAM. Read-only by default.' }
  ],
  mcpServers: [
    { ic:'LN', name:'Linear', author:'Linear', installs:'96K', stars:'1.4K', d:'Issues, projects, and cycles. Read-write surface.' },
    { ic:'NT', name:'Notion', author:'Notion Labs', installs:'82K', stars:'1.2K', d:'Databases, pages, and blocks for knowledge work.' },
    { ic:'SL', name:'Slack', author:'Slack', installs:'71K', stars:'980', d:'Channels, threads, and DMs. Posts behind explicit consent.' },
    { ic:'PG', name:'PostgreSQL', author:'Anthropic', installs:'68K', stars:'920', d:'Schema-aware querying with safe write modes.' },
    { ic:'SY', name:'Sentry', author:'Sentry', installs:'54K', stars:'760', d:'Issues, releases, and event triage from the agent.' },
    { ic:'VC', name:'Vercel', author:'Vercel', installs:'48K', stars:'680', d:'Deployments, env vars, logs, project management.' }
  ],
  platforms: [
    { n:'Claude Code', p:'~/.claude/skills/' }, { n:'OpenAI Codex', p:'~/.codex/skills/' },
    { n:'Cursor', p:'.cursor/rules/' }, { n:'Gemini CLI', p:'~/.gemini/skills/' },
    { n:'GitHub Copilot', p:'.github/copilot/' }, { n:'Windsurf', p:'.windsurfrules' }
  ]
};
