#!/usr/bin/env node
'use strict';

// Dependencies resolve from the skill package, never a fixture's node_modules.
const fs = require('node:fs');
const path = require('node:path');

async function main(argv) {
  const help = 'Usage: node validate-glb.cjs --out-dir NEW_DIRECTORY [--allow-warnings] FILE.glb [FILE.glb ...]\n'
    + 'Uses gltf-validator pinned in the skill package. Outputs are separate from inputs.\n'
    + 'Exit: 0 = valid, 1 = validation failure, 2 = usage/I/O/dependency failure.\n';
  if (argv.length === 1 && ['--help', '-h'].includes(argv[0])) {
    process.stdout.write(help);
    return 0;
  }
  let output;
  let allowWarnings = false;
  const inputs = [];
  let positional = false;
  for (let i = 0; i < argv.length; i++) {
    const value = argv[i];
    if (positional) inputs.push(value);
    else if (value === '--') positional = true;
    else if (value === '--allow-warnings') allowWarnings = true;
    else if (value === '--out-dir' && !output && argv[i + 1] && !argv[i + 1].startsWith('--')) output = argv[++i];
    else if (value.startsWith('-')) throw new Error(`Unknown or incomplete argument: ${value}\n${help}`);
    else inputs.push(value);
  }
  if (!output || !inputs.length) throw new Error(help);
  const files = inputs.map(file => fs.realpathSync(file));
  if (new Set(files).size !== files.length) throw new Error('Duplicate input files are not allowed');
  for (const file of files) {
    if (path.extname(file).toLowerCase() !== '.glb' || !fs.statSync(file).isFile()) {
      throw new Error(`Expected an existing .glb file: ${file}`);
    }
  }
  const requested = path.resolve(output);
  // Resolve existing ancestors too, protecting inputs behind directory symlinks.
  function canonical(file) {
    if (fs.existsSync(file)) return fs.realpathSync(file);
    const parent = path.dirname(file);
    if (parent === file) return file;
    return path.join(canonical(parent), path.basename(file));
  }
  const out = canonical(requested);
  const inside = (file, directory) => {
    const relative = path.relative(directory, file);
    return relative === '' || (!relative.startsWith(`..${path.sep}`) && relative !== '..' && !path.isAbsolute(relative));
  };
  if (files.some(file => inside(file, out))) throw new Error('Output directory must not contain input files');
  if (fs.existsSync(out) && (!fs.statSync(out).isDirectory() || fs.readdirSync(out).length)) {
    throw new Error('--out-dir must be a new or empty directory');
  }
  let validator;
  try { validator = require('gltf-validator'); }
  catch (error) {
    throw new Error(`Cannot load gltf-validator; run npm ci --prefix "${path.resolve(__dirname, '..')}". ${error.message}`);
  }
  fs.mkdirSync(out, { recursive: true });
  const summary = { validatorVersion: validator.version(), strictWarnings: !allowWarnings, passed: true, files: [] };
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    const reportName = `${i + 1}-${path.basename(file)}.validator.json`;
    const bytes = new Uint8Array(fs.readFileSync(file));
    let result;
    try {
      result = await validator.validateBytes(bytes, {
        uri: path.basename(file),
        // A self-contained GLB must not depend on unread external resource files.
        externalResourceFunction: async () => { throw new Error('External resources are unsupported; embed them in the GLB'); },
      });
    } catch (error) {
      // The validator rejects (sometimes without a value) for unreadable GLB
      // containers. This is an invalid asset, not a usage or dependency error.
      result = { issues: { numErrors: 1, numWarnings: 0, numInfos: 0, messages: [
        { code: 'VALIDATOR_REJECTED_INPUT', severity: 0,
          message: error?.message || String(error ?? 'Validator rejected malformed input') },
      ] } };
    }
    fs.writeFileSync(path.join(out, reportName), JSON.stringify(result, null, 2) + '\n', { flag: 'wx' });
    const passed = result.issues.numErrors === 0 && (allowWarnings || result.issues.numWarnings === 0);
    summary.passed = summary.passed && passed;
    summary.files.push({ input: file, report: reportName, passed, issues: result.issues });
    console.log(path.basename(file), passed ? 'PASS' : 'FAIL', JSON.stringify(result.issues));
  }
  fs.writeFileSync(path.join(out, 'summary.json'), JSON.stringify(summary, null, 2) + '\n', { flag: 'wx' });
  return summary.passed ? 0 : 1;
}

if (require.main === module) {
  main(process.argv.slice(2)).then(code => { process.exitCode = code; }).catch(error => {
    console.error(error.message);
    process.exitCode = 2;
  });
}
