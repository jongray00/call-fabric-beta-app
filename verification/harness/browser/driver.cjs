// Playwright device driver. HTTP control API on 127.0.0.1:8100:
//   POST /devices {id, backend, wav}          -> open a new browser context + device page
//   POST /devices/:id/call {fn, args}          -> page.evaluate(window.harness[fn](...args))
//   DELETE /devices/:id                        -> close the context
const http = require('http');
const { chromium } = require('playwright');

const devices = {};
let browser;

async function launch(wav) {
  if (browser) return browser;
  const args = ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream', '--autoplay-policy=no-user-gesture-required'];
  if (wav) args.push(`--use-file-for-fake-audio-capture=${wav}`);
  browser = await chromium.launch({ headless: true, args });
  return browser;
}

function body(req) { return new Promise(r => { let d = ''; req.on('data', c => d += c); req.on('end', () => r(d ? JSON.parse(d) : {})); }); }

http.createServer(async (req, res) => {
  const send = (code, obj) => { res.writeHead(code, { 'content-type': 'application/json' }); res.end(JSON.stringify(obj)); };
  try {
    const m = req.url.match(/^\/devices(?:\/([^/]+))?(\/call)?$/);
    if (!m) return send(404, { error: 'no route' });
    if (req.method === 'POST' && !m[1]) {
      const { id, backend, wav } = await body(req);
      const b = await launch(wav);
      const ctx = await b.newContext({ permissions: ['microphone', 'camera'] });
      const page = await ctx.newPage();
      page.on('console', msg => process.stdout.write(`[${id}] ${msg.type()}: ${msg.text()}\n`));
      await page.goto(`${backend}/static/device.html?device=${encodeURIComponent(id)}`);
      await page.waitForFunction(() => !!window.harness);
      devices[id] = { ctx, page };
      return send(200, { ok: true, shape: await page.evaluate(() => window.harness.sdkShape()) });
    }
    if (req.method === 'POST' && m[2]) {
      const { fn, args = [] } = await body(req);
      const d = devices[m[1]]; if (!d) return send(404, { error: 'no device' });
      const result = await d.page.evaluate(([f, a]) => window.harness[f](...a), [fn, args]);
      return send(200, { ok: true, result });
    }
    if (req.method === 'DELETE' && m[1]) {
      const d = devices[m[1]]; if (d) { try { await d.page.evaluate(() => window.harness.destroy()); } catch (e) {} await d.ctx.close(); delete devices[m[1]]; }
      return send(200, { ok: true });
    }
    send(405, { error: 'method' });
  } catch (e) { send(500, { ok: false, error: String(e && e.message || e) }); }
}).listen(Number(process.env.DRIVER_PORT || 8100), '127.0.0.1', () => console.log('driver ready'));
