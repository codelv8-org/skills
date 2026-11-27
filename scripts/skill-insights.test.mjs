import test from 'node:test';
import assert from 'node:assert/strict';
import {benchmarkChecks,metrics,fallbackSummary,validateAiSummary} from './build-skill-insights.mjs';
const skill={id:'demo',version:'1.0.0',entryFile:'skills/demo/SKILL.md',supportedAgents:['codex'],assets:[{path:'skills/demo/references/a.md'}],workflow:{steps:[{id:'one'}],sourcePath:'assets/demo.json'}};
const source='---\nname: demo\nversion: 1.0.0\ndescription: A sufficiently long activation description for tests\nagents: [codex]\n---\nRead [a](references/a.md)';
test('static benchmark reports real pass/fail and version mismatch separately from output quality',()=>{
 const ok=benchmarkChecks(skill,source,()=>true,true);assert.equal(ok.score,100);assert.equal(ok.outputEvaluation,'not_run');
 const fail=benchmarkChecks(skill,source.replace('1.0.0','2.0.0'),p=>!p.endsWith('/a.md'),false);assert.equal(fail.sourceVersion,'2.0.0');assert.equal(fail.passed,5);assert.equal(fail.checks.find(x=>x.id==='version').pass,false);
});
test('analytics never fills absent ratings with zero',()=>{
 assert.equal(metrics([]).average,null);assert.equal(metrics([]).dimensions.quality,null);
 const review={overall:4,ratings:{quality:5,accuracy:4,ease:4,efficiency:3,consistency:4},agent:'codex',helpful:3,comment:'ok'};
 const m=metrics([review]);assert.equal(m.average,4);assert.equal(m.helpful,3);assert.equal(m.agents.codex.count,1);assert.equal(fallbackSummary([review],true).status,'insufficient_reviews');assert.equal(fallbackSummary([review,review,review],false).status,'not_configured');
});
test('AI output requires grounded issue IDs and bounded plain text',()=>{
 const allowed=new Set([1,2]);assert.deepEqual(validateAiSummary({points:[{text:'ดี',issues:[1,1,2]}]},allowed),[{text:'ดี',issues:[1,2]}]);
 assert.equal(validateAiSummary({points:[{text:'invented',issues:[3]}]},allowed),null);assert.equal(validateAiSummary({points:[{text:'x'.repeat(351),issues:[1]}]},allowed),null);
});
