// Full-page screenshot with true device emulation through the Chrome DevTools Protocol.
// Usage: node preview_cdp.mjs <index.html> <out.png> <width> <height> [mobile]
// No dependencies: Node's built-in fetch and WebSocket. Copyright (c) 2025 Intelligent Cloud Lab Inc.
import { spawn } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const [, , file, out, widthArg, heightArg, mode] = process.argv;
const width = Number(widthArg), height = Number(heightArg), mobile = mode === 'mobile';
const chrome = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const port = 9300 + Math.floor(Math.random() * 500);
const profile = mkdtempSync(join(tmpdir(), 'preview-'));
const proc = spawn(chrome, [
  '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
  `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, 'about:blank',
], { stdio: 'ignore' });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function ready() {
  for (let i = 0; i < 100; i++) {
    try { const r = await fetch(`http://127.0.0.1:${port}/json/version`); if (r.ok) return; } catch {}
    await sleep(100);
  }
  throw new Error('chrome did not start');
}

try {
  await ready();
  const target = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: 'PUT' })).json();
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((r) => (ws.onopen = r));
  let seq = 0;
  const waiting = new Map();
  let loaded;
  const loadedPromise = new Promise((r) => (loaded = r));
  ws.onmessage = (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id && waiting.has(m.id)) { waiting.get(m.id)(m); waiting.delete(m.id); }
    if (m.method === 'Page.loadEventFired') loaded();
  };
  const send = (method, params = {}) => new Promise((res) => {
    const id = ++seq; waiting.set(id, res); ws.send(JSON.stringify({ id, method, params }));
  });
  const metrics = (h) => send('Emulation.setDeviceMetricsOverride', { width, height: h, deviceScaleFactor: 1, mobile });

  await send('Page.enable');
  await metrics(height);
  await send('Page.navigate', { url: 'file://' + file });
  await loadedPromise;
  await sleep(200);
  const { result } = await send('Runtime.evaluate', { expression: 'document.documentElement.scrollHeight', returnByValue: true });
  const full = Math.max(height, result.result.value);
  await metrics(full);
  const shot = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true });
  writeFileSync(out, Buffer.from(shot.result.data, 'base64'));
  const over = await send('Runtime.evaluate', { expression: 'document.documentElement.scrollWidth', returnByValue: true });
  process.stdout.write(JSON.stringify({ width, height: full, scrollWidth: over.result.result.value }));
  ws.close();
} finally {
  const exited = new Promise((r) => proc.once('exit', r));
  proc.kill();
  await exited;
  rmSync(profile, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 });
}
