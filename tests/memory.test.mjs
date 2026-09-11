import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {spawnSync} from 'node:child_process';
import {validateMemory,comparisonFor,filterMemory,escapeHtml} from '../dist/memory-model.js';

const data=JSON.parse(fs.readFileSync(new URL('../dist/memory-demo.json',import.meta.url),'utf8'));

test('Alder Forge history displays the actual engine projections and comparisons',()=>{
  validateMemory(data);
  assert.equal(data.runs.length,3);
  const result=spawnSync(process.env.PYTHON||'python',['-c',"import json,sys; from glinx_company.projection import project,compare; d=json.load(sys.stdin); rs=d['runs']; print(json.dumps({'views':[project(rs[:i+1]) for i in range(len(rs))], 'comparisons':[compare(rs,rs[a]['run_id'],rs[b]['run_id']) for b in range(len(rs)) for a in range(b)]}))"],{input:JSON.stringify(data),encoding:'utf8',maxBuffer:3_000_000});
  assert.equal(result.status,0,result.stderr);
  const actual=JSON.parse(result.stdout);
  assert.deepEqual(data.views,actual.views);
  assert.deepEqual(data.comparisons,actual.comparisons);
  assert.deepEqual(data.views[2].counts,{remembered:13,seen:10,unavailable:2,not_seen:1});
  assert.equal(comparisonFor(data,1,2).system_changes.length,3);
  assert.equal(comparisonFor(data,2,1),null);
});

test('missing evidence stays inspectable and the baseline contains no future systems',()=>{
  assert.equal(filterMemory(data.views[0],'Fiix').length,0);
  const found=filterMemory(data.views[2],'Salesforce');
  assert.equal(found.length,1);
  assert.equal(found[0].visibility,'unavailable');
  assert.equal(found[0].history.length,2);
  assert.equal(filterMemory(data.views[2],'Maya Chen').length,1);
});

test('import rejects mixed evidence, incomplete comparisons, invalid counts, and false history references',()=>{
  for(const mutate of [
    d=>d.runs[1].report.mode='live',
    d=>d.runs[1].report.company='Another company',
    d=>d.comparisons.pop(),
    d=>d.views[2].counts.remembered=10,
    d=>d.views[0].systems[0].last_run_id=d.runs[2].run_id,
    d=>d.views[0].systems[0].history=[d.runs[2].run_id],
    d=>d.comparisons[0].after_run_id=d.comparisons[0].before_run_id
  ]) {const invalid=structuredClone(data);mutate(invalid);assert.throws(()=>validateMemory(invalid));}
});

test('imported claims render as text instead of executable markup',()=>{
  const attack='<img src=x onerror="alert(1)"> & \'quoted\'';
  assert.equal(escapeHtml(attack),'&lt;img src=x onerror=&quot;alert(1)&quot;&gt; &amp; &#39;quoted&#39;');
});
