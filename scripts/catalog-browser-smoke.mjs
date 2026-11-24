import assert from 'node:assert/strict';
import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import {chromium} from 'playwright-core';

const catalog=JSON.parse(await fs.readFile('data/skills.json','utf8')),skill=catalog.skills[0],stamp='2026-01-01T00:00:00Z';
const reviews=[{skillId:skill.id,version:skill.version,agent:'codex',ratings:{quality:5,accuracy:4,ease:4,efficiency:4,consistency:3},overall:4,comment:'synthetic browser fixture',author:'fixture-user',issueNumber:1,approvedAt:stamp,helpful:7,images:[]}];
const current={count:1,average:4,helpful:7,dimensions:reviews[0].ratings,agents:{codex:{count:1,average:4}}};
const fixtures={
 '/data/reviews.json':{schemaVersion:1,generatedAt:stamp,reviews},
 '/data/ratings.json':{schemaVersion:1,generatedAt:stamp,skills:{[skill.id]:{versions:{[skill.version]:{count:1,average:4}}}}},
 '/data/skill-insights.json':{schemaVersion:1,generatedAt:stamp,sourceCommit:'fixture',skills:{[skill.id]:{currentVersion:skill.version,versions:{[skill.version]:current},summary:{mode:'statistics',status:'insufficient_reviews',count:1,strongest:'quality',weakest:'consistency'}}},benchmarks:{[skill.id]:{passed:1,total:1,score:100,checks:[{label:'Fixture check',pass:true,detail:'Synthetic browser test only'}],toolTests:{status:'pass',suites:[{suite:'fixture',status:'pass',tests:1,durationMs:1}]}}}}
};
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.webp':'image/webp','.svg':'image/svg+xml'};
const server=http.createServer(async(req,res)=>{
 try{
  const url=new URL(req.url,'http://127.0.0.1'),pathname=url.pathname;
  if(Object.hasOwn(fixtures,pathname)){res.setHeader('Content-Type',mime['.json']);res.end(JSON.stringify(fixtures[pathname]));return;}
  const file=path.resolve('.'+(pathname==='/'?'/index.html':pathname));
  if(!file.startsWith(process.cwd()+path.sep))throw Error('bad path');
  const body=await fs.readFile(file);res.setHeader('Content-Type',mime[path.extname(file)]||'application/octet-stream');res.end(body);
 }catch{res.statusCode=404;res.end('not found');}
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
let browser;
try{
 browser=await chromium.launch({executablePath:process.env.CHROME_BIN||'/usr/bin/google-chrome',headless:true,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1280,height:900}});
 const origin='http://127.0.0.1:'+server.address().port;
 await page.route('**/*',route=>route.request().url().startsWith(origin)?route.continue():route.abort());
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(origin,{waitUntil:'domcontentloaded'});
 await page.waitForSelector('#viewContainer .sr-badge');
 assert.match(await page.locator('#viewContainer .sr-badge').first().textContent(),/4\.0/);
 for(const view of ['card','list','table','bento']){
  await page.locator('.view-btn[data-view="'+view+'"]').click();
  assert.equal(await page.locator('#viewContainer .sr-badge').count(),catalog.skills.length);
 }
 await page.locator('#skillInsightsDashboard summary').click();
 await page.waitForSelector('#skillInsightsDashboard .si-table');
 assert.match(await page.locator('#skillInsightsDashboard').textContent(),/Skill Comparison/);
 const selects=page.locator('#skillInsightsDashboard select');await selects.nth(1).selectOption(skill.id);
 assert.match(await page.locator('#skillInsightsDashboard .si-result').textContent(),/ไม่ซ้ำ/);
 await selects.nth(1).selectOption(catalog.skills[1].id);
 assert.match(await page.locator('#skillInsightsDashboard .si-result').textContent(),/Community rating/);
 await page.evaluate(id=>window.openDetailModal(id),skill.id);
 await page.waitForSelector('#modalReviews .sr-review');
 assert.match(await page.locator('#modalReviews .sr-review').textContent(),/synthetic browser fixture/);
 assert.match(await page.locator('#modalReviews .sr-vote').textContent(),/7/);
 assert.match(await page.locator('#modalInsights').textContent(),/Functional tool regression/);
 await page.locator('#modalReviews .sr-write summary').click();
 await page.locator('#modalReviews select[name="agent"]').selectOption('codex');
 for(const k of ['quality','accuracy','ease','efficiency','consistency'])await page.locator('#modalReviews input[name="'+k+'"][value="5"]').check({force:true});
 assert.match(await page.locator('#modalReviews .sr-live').textContent(),/5\.0/);
 assert.equal(errors.length,0,errors.join('\n'));
 console.log('PASS: Chrome catalog layouts, comparison, review and benchmark modal, rating form; synthetic fixtures were served in memory only.');
}finally{if(browser)await browser.close();await new Promise(r=>server.close(r));}
