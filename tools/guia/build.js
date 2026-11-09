// Genera assets/guia-10-pasos-invertir-dubai.pdf a partir de tools/guia/guia.html
// Uso: node tools/guia/build.js   (necesita Playwright con Chromium)
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const html = path.join(__dirname, 'guia.html');
  const out = path.join(__dirname, '..', '..', 'assets', 'guia-10-pasos-invertir-dubai.pdf');
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto('file://' + html, { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  // Comprueba que ninguna página se desborda
  const over = await p.$$eval('.page', ps => ps.map((el, i) => el.scrollHeight > el.clientHeight + 1 ? i + 1 : 0).filter(Boolean));
  if (over.length) console.warn('Páginas con texto que no cabe:', over.join(', '));
  await p.pdf({ path: out, format: 'A4', printBackground: true, preferCSSPageSize: true });
  await b.close();
  console.log('PDF creado:', out);
})();
