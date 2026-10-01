// Reads the animation-synced SFX event list (window.SFX) from index.html → sfx-events.json
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('pageerror', e => console.error('PAGEERR', e.message));
  await p.goto('file://' + path.resolve(__dirname, '../index.html'));
  await p.waitForFunction(() => window.READY === true);
  fs.writeFileSync(path.resolve(__dirname, '../sfx-events.json'), JSON.stringify(await p.evaluate(() => window.SFX)));
  await b.close();
})();
