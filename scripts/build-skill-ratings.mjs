import fs from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';

export function splitReviewContent(raw) {
  const images=[];const lines=raw.split('\n');
  const allowed=/^https:\/\/github\.com\/user-attachments\/assets\/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;
  const text=[];
  for(const line of lines){
    const v=line.trim();
    let m=v.match(/^!\[[^\]\r\n]{0,100}\]\((https:\/\/[^\s)]+)\)$/);
    if(!m && /^<img\s+[^<>]*\/?>$/i.test(v))m=v.match(/\bsrc="(https:\/\/[^"\s]+)"/i);
    if(m&&allowed.test(m[1])){if(!images.includes(m[1]))images.push(m[1]);continue;}
    text.push(line);
  }
  const comment=text.join('\n').trim();
  if(images.length>3||comment.length>500||/[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(comment))return null;
  return {comment,images};
}
export function parseReview(issue,knownSkills,approval) {
  if (!issue || issue.pull_request || issue.user?.type!=='User' || !Number.isSafeInteger(issue.user.id) || !Number.isSafeInteger(issue.number) || !approval || !approval.approvedAt) return null;
  if (typeof issue.body!=='string'||issue.body.length>4000||typeof issue.title!=='string')return null;
  const body=issue.body.replace(/\r\n/g,'\n');
  const match=body.match(/^<!-- codelv8-skill-review:v1 -->\nSkill: ([a-z0-9]+(?:-[a-z0-9]+)*)\nVersion: (\d{1,4}\.\d{1,4}\.\d{1,4}(?:-[0-9A-Za-z.-]{1,40})?)\nAgent: (codex|claude-code|antigravity|other)\nOutput Quality: ([1-5])\nAccuracy: ([1-5])\nEase of Use: ([1-5])\nEfficiency: ([1-5])\nConsistency: ([1-5])\n---(?:\n([\s\S]*))?$/);
  if(!match)return null;
  const [,skillId,version,agent,quality,accuracy,ease,efficiency,consistency,rawComment='']=match;
  if(!knownSkills.has(skillId)||issue.title.trim()!==`[Skill Review] ${skillId} v${version}`)return null;
  const content=splitReviewContent(rawComment);if(!content)return null;
  if(!/^[A-Za-z0-9-]{1,39}$/.test(issue.user.login))return null;
  const ratings={quality:+quality,accuracy:+accuracy,ease:+ease,efficiency:+efficiency,consistency:+consistency};
  const overall=Object.values(ratings).reduce((a,b)=>a+b,0)/5;
  return {skillId,version,agent,ratings,overall,...content,helpful:Number.isSafeInteger(issue.reactions?.['+1'])&&issue.reactions['+1']>=0?issue.reactions['+1']:0,author:issue.user.login,authorId:issue.user.id,issueNumber:issue.number,approvedAt:approval.approvedAt};
}
export function approvalFor(node) {
  if(!node || !node.labels?.nodes?.some(x=>x?.name==='skill-review-approved'))return null;
  const dates=(node.timelineItems?.nodes||[]).filter(x=>x?.label?.name==='skill-review-approved').map(x=>x.createdAt).filter(x=>typeof x==='string'&&Number.isFinite(Date.parse(x))).sort();
  const approvedAt=dates.at(-1);if(!approvedAt)return null;
  // Conservative fail-closed rule, including same-second edits.
  if(node.lastEditedAt&&(!Number.isFinite(Date.parse(node.lastEditedAt))||Date.parse(node.lastEditedAt)>=Date.parse(approvedAt)))return null;
  return {approvedAt};
}
export function buildOutputs(catalog,approved,updatedAt,generatedAt){
  const latest=new Map();
  for(const r of approved){
    const key=[r.skillId,r.version,r.authorId].join('|'),old=latest.get(key);
    if(!old||r.approvedAt>old.approvedAt||(r.approvedAt===old.approvedAt&&r.issueNumber>old.issueNumber))latest.set(key,r);
  }
  const reviews=[...latest.values()].sort((a,b)=>b.approvedAt.localeCompare(a.approvedAt)||b.issueNumber-a.issueNumber).map(({authorId,...r})=>r);
  const skills=Object.fromEntries(catalog.skills.map(s=>[s.id,{updatedAt:updatedAt[s.id]||null,versions:{}}]));
  for(const r of reviews){const versions=skills[r.skillId].versions;const s=versions[r.version]??={count:0,average:0};s.count++;s.average+=r.overall;}
  for(const s of Object.values(skills))for(const v of Object.values(s.versions))v.average/=v.count;
  return {ratings:{schemaVersion:1,generatedAt,skills},reviews:{schemaVersion:1,generatedAt,reviews}};
}

async function request(url,options={}){
  const response=await fetch(url,{...options,headers:{Accept:'application/vnd.github+json',Authorization:'Bearer '+process.env.GITHUB_TOKEN,'X-GitHub-Api-Version':'2022-11-28',...options.headers}});
  if(!response.ok)throw Error('GitHub request failed: '+response.status);
  return response.json();
}
async function loadApproved(repository,knownSkills){
  const results=[];
  const query='query($id: ID!){node(id:$id){... on Issue{title body lastEditedAt labels(first:100){nodes{name}} timelineItems(last:100,itemTypes:[LABELED_EVENT]){nodes{... on LabeledEvent{createdAt label{name}}}}}}}';
  for(let page=1;;page++){
    const batch=await request('https://api.github.com/repos/'+repository+'/issues?state=all&labels=skill-review-approved&per_page=100&page='+page);
    for(const issue of batch){
      if(issue.pull_request||!issue.node_id)continue;
      const response=await request('https://api.github.com/graphql',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query,variables:{id:issue.node_id}})});
      if(response.errors?.length)throw Error('GitHub GraphQL approval query failed');
      const node=response.data?.node;
      const approval=approvalFor(node);
      if(!approval)continue;
      const parsed=parseReview({...issue,title:node.title,body:node.body},knownSkills,approval);
      if(parsed)results.push(parsed);
    }
    if(batch.length<100)break;
  }
  return results;
}
async function main(){
  const repository=process.env.GITHUB_REPOSITORY||'codelv8-org/skills';
  if(repository!=='codelv8-org/skills')throw Error('Unexpected repository');
  if(!process.env.GITHUB_TOKEN)throw Error('GITHUB_TOKEN is required; no fabricated ratings will be generated.');
  const catalog=JSON.parse(await fs.readFile('data/skills.json','utf8'));
  const known=new Set(catalog.skills.map(s=>s.id));
  const approved=await loadApproved(repository,known);
  const updatedAt={};
  for(const id of known){
    if(!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(id))throw Error('Invalid catalog skill ID');
    updatedAt[id]=execFileSync('git',['log','-1','--format=%cI','--','skills/'+id],{encoding:'utf8'}).trim()||null;
  }
  const output=buildOutputs(catalog,approved,updatedAt,new Date().toISOString());
  for(const [file,payload] of Object.entries(output))await fs.writeFile('data/'+file+'.json',JSON.stringify(payload,null,2)+'\n');
  console.log('Generated '+output.reviews.reviews.length+' approved unique reviews');
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url))await main();
