#!/usr/bin/env node
// Render source-backed workflow diagrams using pinned Archify 3.3.0.
// No skill code, project inputs, or live user data are executed/read by this build.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import assert from 'node:assert/strict';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const folder = 'assets/skill-workflows';
const expectedArchify = '3ca198d867ce4b616332f846ff66e5c8e5e60f95';
const read = p => fs.readFileSync(path.join(root,p),'utf8');
const catalog = JSON.parse(read('data/skills.json'));
const html = read('index.html');
const embedded = JSON.parse(html.split('    const EMBEDDED_DATA = ')[1].split('\n    let appData = EMBEDDED_DATA;')[0].trim().replace(/;$/,''));
const checkOnly = process.argv.includes('--check');
const arg = process.argv.find(x=>x.startsWith('--archify='));
const ids = new Set();
const candidates = [];
const sha = bytes=>createHash('sha256').update(bytes).digest('hex');
const run = (cmd,args,cwd=root,env=process.env) => {
  const r=spawnSync(cmd,args,{cwd,env,encoding:'utf8',maxBuffer:32*1024*1024,timeout:180000});
  if(r.status!==0 || r.error) {
    process.stderr.write((r.stdout||'')+'\n'+(r.stderr||'')+'\n');
    throw new Error('Command failed: '+cmd+' '+args.slice(0,3).join(' ')+' '+(r.error?.message||r.status));
  }
  return r.stdout;
};
for(const s of catalog.skills) {
  assert.match(s.id,/^[a-z0-9]+(?:-[a-z0-9]+)*$/);
  assert(!ids.has(s.id),'duplicate skill');ids.add(s.id);
  const w=s.workflow;
  assert(w && w.steps.length,'Missing workflow for '+s.id);
  assert.deepEqual(embedded.skills.find(x=>x.id===s.id)?.workflow,w,'Embedded catalog drift: '+s.id);
  const base=folder+'/'+s.id;
  assert.equal(w.sourcePath,base+'.workflow.json');
  assert.equal(w.htmlPath,base+'.html');
  const g=JSON.parse(read(w.sourcePath));
  assert.equal(g.schema_version,2);
  assert.equal(g.diagram_type,'workflow');
  assert.equal(g.meta.output,w.htmlPath);
  assert.equal(g.meta.repository.revision,w.revision);
  assert.deepEqual(g.mainPath,w.steps.map(x=>x.id));
  const nodes=new Map(g.nodes.map(n=>[n.id,n]));
  assert.equal(nodes.size,g.nodes.length);
  assert.equal(g.nodes.length,w.steps.length+w.branches.length);
  const source=run('git',['show',w.revision+':'+s.entryFile]).split('\n');
  for(const n of [...w.steps,...w.branches]){
    const actual=nodes.get(n.id);
    assert(actual,'node missing '+n.id);
    assert.equal(actual.label,n.title);
    assert.equal(actual.sublabel,n.subtitle);
    assert.equal(actual.explanation,n.description);
    assert(Number.isInteger(n.line)&&Number.isInteger(n.endLine)&&n.line>0&&n.endLine>=n.line&&n.endLine<=source.length);
    assert.deepEqual(actual.sources,[{path:s.entryFile,line:n.line,end_line:n.endLine,label:'SKILL.md'}]);
  }
  for(let i=1;i<w.steps.length;i++)assert(g.edges.some(e=>e.from===w.steps[i-1].id&&e.to===w.steps[i].id&&e.role==='main'),'main path edge missing');
  for(const b of w.branches){
    assert(g.edges.some(e=>e.from===b.from&&e.to===b.id&&e.label===b.condition),'branch edge missing');
    if(b.returnTo)assert(g.edges.some(e=>e.from===b.id&&e.to===b.returnTo),'return missing');
  }
  for(const e of g.edges)assert(nodes.has(e.from)&&nodes.has(e.to),'dangling edge');
  assert.deepEqual(g.cards[0].items,w.notes);
  candidates.push({id:s.id,graph:g,source:w.sourcePath,output:w.htmlPath});
}
assert.equal(embedded.skills.length,catalog.skills.length);
const script=html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
assert(script,'Catalog JS not found');
const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'codelv8-archify-'));
try{
  const syntaxFile=path.join(tmp,'catalog.js');
  fs.writeFileSync(syntaxFile,script);
  run(process.execPath,['--check',syntaxFile]);
  console.log('PASS: catalog coverage, embedded parity, source line bounds, graph edges and JavaScript syntax ('+candidates.length+' skills)');
  if(!checkOnly){
    if(!arg)throw new Error('Usage: node scripts/build-skill-workflows.mjs --archify=/path/to/archify-repo');
    const checkout=path.resolve(arg.slice('--archify='.length));
    assert.equal(run('git',['rev-parse','HEAD'],checkout).trim(),expectedArchify,'Unexpected Archify revision');
    const cli=path.join(checkout,'archify/bin/archify.mjs');
    fs.accessSync(cli,fs.constants.R_OK);
    fs.mkdirSync(path.join(tmp,folder),{recursive:true});
    const results=[];
    const failures=[];
    for(const c of candidates){
      try{
      const evidence=path.join(tmp,'qa',c.id);
      fs.mkdirSync(evidence,{recursive:true});
      console.log('Archify finalize: '+c.id);
      const stdout=run(process.execPath,[cli,'finalize','workflow',path.join(root,c.source),c.output,'--repo-root',root,'--quality',c.graph.meta.quality_profile,'--out-dir',evidence,'--json'],tmp);
      // Fail-closed: only actual Archify finalize success is published.
      const file=path.join(tmp,c.output);
      const bytes=fs.readFileSync(file);
      assert(bytes.length>10000&&bytes.toString('utf8',0,256).toLowerCase().includes('<!doctype html'),'Missing native HTML');
      console.log(stdout.slice(0,1800));
      results.push({id:c.id,source:c.source,source_sha256:sha(fs.readFileSync(path.join(root,c.source))),html:c.output,html_sha256:sha(bytes),bytes:bytes.length,validation:'archify-finalize-pass'});
      }catch(error){failures.push(c.id);console.error('ARCHIFY FAILED: '+c.id+' — '+error.message);}
    }
    if(failures.length)throw new Error('Archify finalize failed: '+failures.join(', '));
    // Publish only after every diagram is successfully finalized.
    for(const r of results)fs.copyFileSync(path.join(tmp,r.html),path.join(root,r.html));
    fs.writeFileSync(path.join(root,folder,'archify-build.json'),JSON.stringify({archify:{url:'https://github.com/tt-a1i/archify',revision:expectedArchify,version:'3.3.0',license:'Apache-2.0'},diagrams:results},null,2)+'\n');
    for(const p of ['LICENSE','NOTICE'])if(fs.existsSync(path.join(checkout,p)))fs.copyFileSync(path.join(checkout,p),path.join(root,folder,'ARCHIFY-'+p+'.txt'));
    console.log('PASS: '+results.length+' native Archify workflow diagrams');
  }
} finally {fs.rmSync(tmp,{recursive:true,force:true});}
