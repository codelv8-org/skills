'use strict';
const { test, after } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const root = fs.mkdtempSync(path.join(os.tmpdir(), 'krathong-validator-'));
const script = path.resolve(__dirname, '../scripts/validate-glb.cjs');
// Only the temporary directory created by this suite is removed, never inputs.
after(() => fs.rmSync(root, { recursive: true, force: true }));
const run = (...args) => spawnSync(process.execPath, [script, ...args], { cwd: root, encoding: 'utf8' });
function glb(file, external = false) {
  const data = { asset: { version: '2.0' }, scene: 0, scenes: [{ nodes: [0] }], nodes: [{}] };
  if (external) data.buffers = [{ uri: 'missing.bin', byteLength: 4 }];
  let json = JSON.stringify(data);
  json = json.padEnd(Math.ceil(Buffer.byteLength(json) / 4) * 4, ' ');
  const chunk = Buffer.from(json);
  const header = Buffer.alloc(20);
  header.writeUInt32LE(0x46546c67, 0);
  header.writeUInt32LE(2, 4);
  header.writeUInt32LE(20 + chunk.length, 8);
  header.writeUInt32LE(chunk.length, 12);
  header.writeUInt32LE(0x4e4f534a, 16);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, Buffer.concat([header, chunk]));
  return file;
}

test('help works without cwd dependency', () => {
  const result = run('--help');
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Usage:/);
});
test('valid GLBs with identical basenames get distinct reports; inputs unchanged', () => {
  const a = glb(path.join(root, 'space one/model.glb'));
  const b = glb(path.join(root, 'space two/model.glb'));
  const before = fs.readFileSync(a);
  const output = path.join(root, 'valid reports');
  const result = run('--out-dir', output, a, b);
  assert.equal(result.status, 0, result.stderr + result.stdout);
  const summary = JSON.parse(fs.readFileSync(path.join(output, 'summary.json')));
  assert.equal(summary.files.length, 2);
  assert.notEqual(summary.files[0].report, summary.files[1].report);
  assert.ok(summary.passed);
  assert.deepEqual(fs.readFileSync(a), before);
});
test('malformed GLB fails actual independent validation', () => {
  const file = path.join(root, 'broken.glb');
  fs.writeFileSync(file, 'not a GLB');
  const result = run('--out-dir', path.join(root, 'invalid report'), file);
  assert.equal(result.status, 1, result.stderr + result.stdout);
});
test('warnings fail by default; explicit allow-warnings leaves warnings visible', () => {
  const file = glb(path.join(root, 'warning.glb'));
  // BUFFER_DATA_URI is a warning for an embedded data URI in a GLB.
  const bytes = fs.readFileSync(file);
  const data = JSON.parse(bytes.subarray(20).toString());
  data.buffers = [{ uri: 'data:application/octet-stream;base64,AAAAAA==', byteLength: 4 }];
  let text = JSON.stringify(data);
  text = text.padEnd(Math.ceil(Buffer.byteLength(text) / 4) * 4, ' ');
  const header = Buffer.from(bytes.subarray(0, 20));
  header.writeUInt32LE(20 + Buffer.byteLength(text), 8);
  header.writeUInt32LE(Buffer.byteLength(text), 12);
  fs.writeFileSync(file, Buffer.concat([header, Buffer.from(text)]));
  const strict = run('--out-dir', path.join(root, 'warning strict'), file);
  assert.equal(strict.status, 1, strict.stderr + strict.stdout);
  const loose = run('--allow-warnings', '--out-dir', path.join(root, 'warning allowed'), file);
  assert.equal(loose.status, 0, loose.stderr + loose.stdout);
  const summary = JSON.parse(fs.readFileSync(path.join(root, 'warning allowed/summary.json')));
  assert.ok(summary.files[0].issues.numWarnings > 0);
});
test('nonempty output is refused without altering sentinel', () => {
  const out = path.join(root, 'occupied');
  fs.mkdirSync(out);
  fs.writeFileSync(path.join(out, 'sentinel'), 'keep');
  const file = glb(path.join(root, 'occupied-input.glb'));
  assert.equal(run('--out-dir', out, file).status, 2);
  assert.deepEqual(fs.readdirSync(out), ['sentinel']);
  assert.equal(fs.readFileSync(path.join(out, 'sentinel'), 'utf8'), 'keep');
});
test('missing, duplicate and incomplete inputs fail before output creation', () => {
  const file = glb(path.join(root, 'usage-input.glb'));
  for (const args of [[file, file], ['missing.glb'], ['--unknown'], []]) {
    const out = path.join(root, 'must not exist');
    assert.equal(run('--out-dir', out, ...args).status, 2);
    assert.ok(!fs.existsSync(out));
  }
});
test('external resources cannot silently pass without being validated', () => {
  const file = glb(path.join(root, 'external.glb'), true);
  const result = run('--out-dir', path.join(root, 'external report'), file);
  assert.equal(result.status, 1, result.stderr + result.stdout);
});
