const { chromium } = require('playwright-core');
(async () => {
  const b = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox'] });
  const pages = [['home', '/'], ['costco', '/companies/costco/'], ['gold', '/commodities/gold/']];
  const views = [['desktop', { width: 1440, height: 900 }, 1], ['mobile', { width: 390, height: 844 }, 2]];
  const errs = [];
  for (const [vn, vp, dpr] of views) {
    const ctx = await b.newContext({ viewport: vp, deviceScaleFactor: dpr, isMobile: vn === 'mobile', hasTouch: vn === 'mobile' });
    for (const [n, u] of pages) {
      const p = await ctx.newPage();
      p.on('console', m => { if (['error', 'warning'].includes(m.type())) errs.push(`${vn} ${u} console.${m.type()}: ${m.text()}`) });
      p.on('pageerror', e => errs.push(`${vn} ${u} pageerror: ${e.message}`));
      p.on('requestfailed', r => errs.push(`${vn} ${u} requestfailed: ${r.url()}`));
      p.on('response', r => { if (r.status() >= 400) errs.push(`${vn} ${u} HTTP ${r.status()}: ${r.url()}`) });
      await p.goto('http://127.0.0.1:8765' + u, { waitUntil: 'networkidle' });
      await p.waitForTimeout(1500);
      const ow = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      if (ow > 0) errs.push(`${vn} ${u} horizontal overflow ${ow}px`);
      await p.screenshot({ path: `/workspace/ventures/moneyflow/screenshots/${n}-${vn}.png`, fullPage: true });
      await p.close();
    }
    await ctx.close();
  }
  await b.close();
  console.log(errs.length ? errs.join('\n') : 'NO CONSOLE ERRORS');
})();
