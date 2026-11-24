// Exercise the generated public example, including actual WebGL texture swaps.
// Run after build-photoreal-example.py --strict; never serve synthetic success data.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright-core';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const example = path.join(root, 'assets/examples/photoreal-head');
const evidence = process.env.PHOTOREAL_SMOKE_ARTIFACTS || path.join(os.tmpdir(), 'codelv8-photoreal-smoke');
const report = JSON.parse(await fs.readFile(path.join(example, 'reports/projection_lab.json'), 'utf8'));
const ids = ['front_only', 'multiview', 'tinted_mean', 'tinted_robust', 'reviewed_quarantine', 'coverage', 'ambiguity', 'uv_anisotropy', 'uv_density'];
const digest = data => createHash('sha256').update(data).digest('hex');
assert.equal(report.status, 'B1_DIAGNOSTIC_COMPLETE', 'Build the real public projection example before browser QA');
assert.equal(report.uv.status, 'PASS_UV_ONLY', 'Projection candidate must pass the exact UV gate');
assert.deepEqual(report.uv.errors, []);
for (const key of ['degenerate', 'out_of_bounds', 'wrong_winding', 'overlap_pairs_found']) {
  assert.equal(report.uv.metrics[key], 0, `UV gate failed: ${key}`);
}
assert.equal(report.projectionMesh, 'model/projection-head.glb');
assert.equal(digest(await fs.readFile(path.join(example, report.projectionMesh))), report.sourceSha256, 'Stale projection geometry');
assert.equal(digest(await fs.readFile(path.join(example, 'model/head.glb'))), report.baselineSha256, 'Stale baseline geometry');
assert.deepEqual(report.modes.map(mode => mode.id), ids);
for (const mode of report.modes) {
  assert.equal(mode.path, `projection-lab/${mode.id}.webp`);
  assert.equal(digest(await fs.readFile(path.join(example, mode.path))), mode.sha256, `Stale texture: ${mode.id}`);
}
await fs.mkdir(evidence, {recursive:true});
const mime = {'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.webp':'image/webp','.jpg':'image/jpeg','.png':'image/png','.svg':'image/svg+xml','.glb':'model/gltf-binary','.woff2':'font/woff2'};
const server = http.createServer(async (req, res) => {
  try {
    const pathname = decodeURIComponent(new URL(req.url, 'http://127.0.0.1').pathname);
    const file = path.resolve(root, '.' + pathname);
    if (!file.startsWith(root + path.sep)) throw Error('Path outside catalog');
    const body = await fs.readFile(file);
    res.setHeader('Content-Type', mime[path.extname(file)] || 'application/octet-stream');
    res.end(body);
  } catch {res.statusCode = 404; res.end('not found');}
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const url = `${origin}/assets/examples/photoreal-head/preview.html`;
const failures = [];
const captures = [];
let browser;
let page;
const canvasShot = () => page.locator('#viewer').screenshot({animations:'disabled', style:'.stage > :not(canvas) { visibility: hidden !important; }'});
const waitLabel = label => page.waitForFunction(expected => document.querySelector('#mode-label').textContent === expected, label);
try {
  browser = await chromium.launch({
    executablePath:process.env.CHROME_BIN || '/usr/bin/google-chrome',
    headless:true,
    args:['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
  });
  page = await browser.newPage({viewport:{width:1440,height:1000}, reducedMotion:'reduce'});
  page.on('pageerror', error => failures.push(error.message));
  page.on('response', response => {
    if (response.url().startsWith(origin) && response.status() >= 400 && !response.url().endsWith('/favicon.ico')) {
      failures.push(`${response.status()}: ${response.url()}`);
    }
  });
  await page.route('**/*', route => route.request().url().startsWith(origin) ? route.continue() : route.abort());
  await page.goto(url, {waitUntil:'networkidle'});
  await page.waitForSelector('#projection-mode:not([disabled])', {timeout:30000});
  assert.equal(await page.locator('#error').isVisible(), false);
  assert.match(await page.locator('#lab-status').textContent(), /B1 diagnostic complete/);
  assert.equal(await page.locator('#projection-mode option').count(), ids.length + 1);
  for (const selector of ['#lab-front', '#lab-multi', '#lab-robust', '#lab-mean', '#lab-quarantine']) {
    assert.notEqual((await page.locator(selector).textContent()).trim(), '—', `Missing generated metric ${selector}`);
  }

  await page.locator('[data-view="front"]').click();
  const baseline = await canvasShot();
  for (const mode of report.modes) {
    await page.locator('#projection-mode').selectOption(mode.id);
    await waitLabel(mode.label);
    const screenshot = await canvasShot();
    assert.notEqual(digest(screenshot), digest(baseline), `Texture mode did not change canvas: ${mode.id}`);
    const file = `${mode.id}.png`;
    await fs.writeFile(path.join(evidence, file), screenshot);
    captures.push({mode:mode.id, file, sha256:digest(screenshot)});
  }
  await page.locator('#projection-mode').selectOption('');
  await waitLabel('พื้นผิวสแกน');
  assert.equal(digest(await canvasShot()), digest(baseline), 'Baseline material was not restored');

  // Reset must cancel a pending diagnostic mode as well as an already-loaded one.
  await page.locator('#projection-mode').selectOption('tinted_robust');
  await page.locator('[data-mode="clay"]').click();
  await waitLabel('Clay · ปิดแผนที่พื้นผิว');
  assert.equal(await page.locator('#projection-mode').inputValue(), '');
  const clayFront = digest(await canvasShot());
  for (const view of ['left', 'right', 'threequarter']) {
    await page.locator(`[data-view="${view}"]`).click();
    assert.equal(await page.locator(`[data-view="${view}"]`).getAttribute('aria-pressed'), 'true');
    assert.notEqual(digest(await canvasShot()), clayFront, `Camera did not change: ${view}`);
  }
  await page.locator('[data-mode="wire"]').click();
  await waitLabel('Wireframe · โครงสร้างสามเหลี่ยม');
  await page.locator('[data-mode="skin"]').click();
  await waitLabel('พื้นผิวสแกน');
  await page.screenshot({path:path.join(evidence, 'desktop.png'), fullPage:true});

  await page.setViewportSize({width:390,height:844});
  await page.locator('#projection-mode').selectOption('multiview');
  await waitLabel(report.modes.find(mode => mode.id === 'multiview').label);
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), true, 'Mobile horizontal overflow');
  await page.screenshot({path:path.join(evidence, 'mobile.png'), fullPage:true});

  // A stale report may not authorize textures on a different projection mesh.
  await page.route('**/reports/projection_lab.json', route => route.fulfill({
    status:200, contentType:'application/json',
    body:JSON.stringify({...report, sourceSha256:'0'.repeat(64)}),
  }));
  await page.reload({waitUntil:'networkidle'});
  await page.waitForFunction(() => document.querySelector('#lab-status').textContent.includes('ไม่ตรงกับรายงาน'));
  assert.equal(await page.locator('#projection-mode').isDisabled(), true);
  await page.locator('[data-mode="clay"]').click();
  await waitLabel('Clay · ปิดแผนที่พื้นผิว');
  assert.equal(await page.locator('#error').isVisible(), false);

  // A genuinely blocked report must leave the baseline usable and hide results.
  await page.route('**/reports/projection_lab.json', route => route.fulfill({
    status:200, contentType:'application/json',
    body:JSON.stringify({schemaVersion:1, skillVersion:report.skillVersion, status:'BLOCKED', modes:[]}),
  }));
  await page.reload({waitUntil:'networkidle'});
  await page.waitForSelector('[data-mode="skin"]:not([disabled])');
  assert.equal(await page.locator('#projection-mode').isDisabled(), true);
  assert.match(await page.locator('#lab-status').textContent(), /BLOCKED/);
  assert.equal(await page.locator('#lab-comparison').isVisible(), false);
  assert.equal(await page.locator('#lab-robust').textContent(), '—');
  await page.locator('[data-mode="clay"]').click();
  await waitLabel('Clay · ปิดแผนที่พื้นผิว');
  assert.equal(await page.locator('#error').isVisible(), false);
  assert.deepEqual(failures, [], failures.join('\n'));
  await fs.writeFile(path.join(evidence, 'browser_qa.json'), JSON.stringify({
    status:'PASS', browser:await browser.version(), sourceSha256:report.sourceSha256,
    atlasSize:report.atlasSize, desktop:[1440,1000], mobile:[390,844], modes:captures,
    checks:['exact UV gate', 'projection and baseline mesh hashes', 'real generated texture hashes', 'nine canvas texture swaps', 'baseline restoration', 'material reset', 'camera views', 'mobile layout', 'mismatched model rejection', 'blocked report fallback', 'no page errors or missing assets'],
  }, null, 2) + '\n');
  console.log('PASS: public head — nine real projection modes, baseline restore, camera views, 390px mobile layout, mismatched-model rejection, blocked-report fallback, no page errors.');
} catch (error) {
  if (page) await page.screenshot({path:path.join(evidence, 'failure.png'), fullPage:true}).catch(() => {});
  await fs.writeFile(path.join(evidence, 'failure.json'), JSON.stringify({error:String(error), failures}, null, 2) + '\n');
  throw error;
} finally {
  if (browser) await browser.close();
  await new Promise(resolve => server.close(resolve));
}
