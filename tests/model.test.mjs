import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {validateReport,metrics,insights,filterSystems,inventoryCsv} from '../dist/model.js';
const fixture=JSON.parse(fs.readFileSync(new URL('../dist/demo.json',import.meta.url),'utf8'));
test('fixture has traceable evidence and consistent discovery counts',()=>{
  validateReport(fixture);const m=metrics(fixture);assert.equal(m.systems,12);assert.equal(m.functions,7);assert.equal(m.links,3);
  assert.equal(fixture.mode,'demo');
  for(const c of fixture.collectors)assert.equal(c.count,fixture.systems.reduce((n,s)=>n+s.evidence.filter(e=>e.source===c.id).length,0));
});
test('invalid and dangling relationships cannot enter the map',()=>{
  const bad=structuredClone(fixture);bad.relationships[0].source='missing';assert.throws(()=>validateReport(bad));
});
test('duplicate identities, missing evidence, invalid confidence are rejected',()=>{
  for(const mutate of [d=>d.systems.push(d.systems[0]),d=>d.systems[0].evidence=[],d=>d.systems[0].confidence=NaN,d=>d.mode='verified']){const d=structuredClone(fixture);mutate(d);assert.throws(()=>validateReport(d));}
});
test('rules expose exact supporting systems without a fictional savings claim',()=>{
  const issues=insights(fixture);const owners=issues.find(i=>i.kind==='Ownership');assert.equal(owners.ids.length,3);assert(owners.ids.every(id=>!fixture.systems.find(s=>s.id===id).owner));assert(!JSON.stringify(issues).includes('$'));
});
test('function, owner, source and evidence filters combine',()=>{
  assert.equal(filterSystems(fixture,'operations','ERP','observed').length,1);assert.equal(filterSystems(fixture,'','ERP').length,2);assert.equal(filterSystems(fixture,'unlikely').length,0);
});
test('CSV preserves commas and quotes and neutralizes spreadsheet formulas',()=>{
  const data=structuredClone(fixture);data.systems[0].name=' =HYPERLINK("bad", "x")';const csv=inventoryCsv(data);assert(csv.includes('"\' =HYPERLINK(""bad"", ""x"")"'));
});
test('empty or failed scans do not become successful discovery',()=>{
  const d={...fixture,mode:'live',systems:[],relationships:[],collectors:[{id:'m365',name:'Microsoft 365',status:'error',count:0,detail:'No token'}]};validateReport(d);assert.equal(metrics(d).systems,0);assert.equal(metrics(d).complete,0);assert(insights(d).some(i=>i.kind==='Visibility'));
});
