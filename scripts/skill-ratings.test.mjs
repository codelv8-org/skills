import test from 'node:test';
import assert from 'node:assert/strict';
import {parseReview,approvalFor,buildOutputs} from './build-skill-ratings.mjs';
const known=new Set(['demo']);
const approvedAt='2026-11-24T08:00:00Z';
const body=['<!-- codelv8-skill-review:v1 -->','Skill: demo','Version: 1.0.0','Agent: codex','Output Quality: 5','Accuracy: 4','Ease of Use: 3','Efficiency: 2','Consistency: 1','---','<img src=x onerror=alert(1)> รีวิว'].join('\n');
const issue={number:1,title:'[Skill Review] demo v1.0.0',body,user:{id:123,login:'test-user',type:'User'}};
const node={lastEditedAt:null,labels:{nodes:[{name:'skill-review-approved'}]},timelineItems:{nodes:[{label:{name:'skill-review-approved'},createdAt:approvedAt}]}};
test('approval is required and edits after or at approval invalidate it',()=>{assert.deepEqual(approvalFor(node),{approvedAt});assert.equal(approvalFor({...node,lastEditedAt:approvedAt}),null);assert.equal(approvalFor({...node,lastEditedAt:'2026-11-24T08:01:00Z'}),null);assert.equal(approvalFor({...node,labels:{nodes:[]}}),null);assert.equal(approvalFor({...node,timelineItems:{nodes:[]}}),null);});
test('strict structured review and safe bounded content',()=>{const r=parseReview(issue,known,{approvedAt});assert.equal(r.overall,3);assert.equal(r.comment,'<img src=x onerror=alert(1)> รีวิว');assert.equal(parseReview(issue,known,null),null);assert.equal(parseReview({...issue,body:body.replace('Quality: 5','Quality: 6')},known,{approvedAt}),null);assert.equal(parseReview({...issue,user:{...issue.user,type:'Bot'}},known,{approvedAt}),null);assert.equal(parseReview({...issue,title:'wrong'},known,{approvedAt}),null);assert.equal(parseReview({...issue,body:body+'x'.repeat(501)},known,{approvedAt}),null);assert.equal(parseReview(issue,new Set(),{approvedAt}),null);});
test('deduplicate by account ID, skill and version; keep history',()=>{const r=parseReview(issue,known,{approvedAt}),newer={...r,issueNumber:2,overall:5,approvedAt:'2026-11-24T09:00:00Z'},oldVersion={...r,version:'0.9.0'},other={...r,authorId:456,author:'other-user',issueNumber:3,overall:1};const o=buildOutputs({skills:[{id:'demo'},{id:'empty'}]},[r,newer,oldVersion,other],{},approvedAt);assert.equal(o.reviews.reviews.length,3);assert.equal(o.ratings.skills.demo.versions['1.0.0'].count,2);assert.equal(o.ratings.skills.demo.versions['1.0.0'].average,3);assert.equal(o.ratings.skills.demo.versions['0.9.0'].count,1);assert.deepEqual(o.ratings.skills.empty.versions,{});assert.ok(o.reviews.reviews.every(x=>!('authorId' in x)));});

test('only GitHub attachment URLs become images; count and helpful votes are bounded',()=>{
 const url='https://github.com/user-attachments/assets/12345678-abcd-abcd-abcd-123456789abc';
 const r=parseReview({...issue,body:body+'\n![result]('+url+')',reactions:{'+1':7}},known,{approvedAt});
 assert.equal(r.helpful,7);assert.deepEqual(r.images,[url]);assert.equal(r.comment,'<img src=x onerror=alert(1)> รีวิว');
 const external=parseReview({...issue,body:body+'\n![tracker](https://example.com/pixel)'},known,{approvedAt});assert.deepEqual(external.images,[]);
 const html=parseReview({...issue,body:body+'\n<img width="100" alt="result" src="'+url+'" />'},known,{approvedAt});assert.deepEqual(html.images,[url]);
 const four=Array.from({length:4},(_,i)=>'![x]('+url.slice(0,-1)+i+')').join('\n');
 assert.equal(parseReview({...issue,body:body+'\n'+four},known,{approvedAt}),null);
});
