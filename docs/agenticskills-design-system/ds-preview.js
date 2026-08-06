/* ds-preview.js — renders component cards and UI kits WITHOUT the compiled
   _ds_bundle.js. Fetches each component source, strips the ESM keywords,
   transpiles with the already-loaded Babel, and exposes them on
   window.__DS_NS__ so the standard namespace resolver finds them.

   Load AFTER Babel and AFTER the _ds_bundle.js <script> tag. If the real
   bundle is present this is a no-op. Synchronous by design so the
   type="text/babel" blocks that follow can destructure immediately. */
(function () {
  if (typeof Babel === 'undefined' || typeof React === 'undefined') return;

  // Real bundle already loaded? Leave it alone.
  var skip = { top: 1, parent: 1, self: 1, window: 1, frames: 1, opener: 1 };
  for (var k in window) {
    if (skip[k]) continue;
    try {
      var v = window[k];
      if (v && typeof v === 'object' && !Array.isArray(v) && v.Button && v.Tag && v.HairlineGrid) return;
    } catch (e) { /* cross-origin */ }
  }

  var FILES = [
    'components/core/Button.jsx',
    'components/core/Tag.jsx',
    'components/core/Rank.jsx',
    'components/core/MicroLabel.jsx',
    'components/core/Monogram.jsx',
    'components/core/Breadcrumbs.jsx',
    'components/core/Icon.jsx',
    'components/layout/HairlineGrid.jsx',
    'components/layout/SectionHead.jsx',
    'components/layout/PageHead.jsx',
    'components/layout/StatRow.jsx',
    'components/navigation/Ticker.jsx',
    'components/navigation/Navbar.jsx',
    'components/navigation/Footer.jsx',
    'components/navigation/TableOfContents.jsx',
    'components/forms/Input.jsx',
    'components/forms/FormField.jsx',
    'components/forms/SegmentedControl.jsx',
    'components/forms/SearchInput.jsx',
    'components/forms/NewsletterForm.jsx',
    'components/content/SkillCard.jsx',
    'components/content/FeatureCard.jsx',
    'components/content/CategoryCard.jsx',
    'components/content/ArticleCard.jsx',
    'components/content/StepCard.jsx',
    'components/code/Terminal.jsx',
    'components/code/InstallPanel.jsx'
  ];

  var me = document.currentScript && document.currentScript.src;
  if (!me) return;
  var base = me.replace(/ds-preview\.js.*$/, '');

  var parts = [];
  for (var i = 0; i < FILES.length; i++) {
    var xhr = new XMLHttpRequest();
    try {
      xhr.open('GET', base + FILES[i], false);
      xhr.send();
    } catch (e) { return; }
    if (xhr.status && (xhr.status < 200 || xhr.status >= 400)) return;
    if (!xhr.responseText) return;
    parts.push(xhr.responseText);
  }

  var body = parts.join('\n\n')
    .replace(/^[ \t]*import[^\n]*\n/gm, '')
    .replace(/\bexport\s+(function|const|let|var)\b/g, '$1');

  var names = FILES.map(function (f) {
    return f.split('/').pop().replace('.jsx', '');
  });
  names.push('ICONS');

  try {
    var code = Babel.transform(body, { presets: ['react'] }).code;
    window.__DS_NS__ = new Function('React', code + '\nreturn {' + names.join(',') + '};')(React);
  } catch (e) {
    console.error('[ds-preview] failed to build namespace:', e);
  }
})();
