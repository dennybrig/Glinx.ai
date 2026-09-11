import {validateReport} from './model.js';

export const escapeHtml = value => String(value ?? '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');
const text = (v,n=600) => typeof v === 'string' && v.length <= n;
const nonempty = (v,n=100) => text(v,n) && v.trim().length > 0;
const list = (v,n) => Array.isArray(v) && v.length <= n;
const validTime = v => text(v,60) && Number.isFinite(Date.parse(v));
const fail = message => {throw new Error(message);};

export function validateMemory(data) {
  if (!data || data.company_memory_version !== '1.0') fail('Open a Glinx company memory export, version 1.0.');
  if (!data.company || !nonempty(data.company.id) || !nonempty(data.company.name,200) || !text(data.company.purpose,1000) || !['demo','live'].includes(data.company.mode)) fail('The history needs a valid company profile.');
  if (!data.scope || !nonempty(data.scope.id) || !Number.isInteger(data.scope.revision) || data.scope.revision < 1 || !text(data.scope.description,1000)) fail('The collection scope is invalid.');
  if (!list(data.runs,20) || !data.runs.length || !list(data.views,20) || data.views.length !== data.runs.length || !list(data.comparisons,190)) fail('The history must contain 1–20 saved snapshots and their views.');
  const indexes = new Map();
  for (const [i,run] of data.runs.entries()) {
    if (!run || !nonempty(run.run_id) || indexes.has(run.run_id) || !validTime(run.generated_at) || !validTime(run.imported_at) || !text(run.legacy_scan_id,100)) fail('Snapshot metadata is invalid.');
    validateReport(run.report);
    if (run.report.company !== data.company.name || run.report.mode !== data.company.mode) fail('A history cannot mix companies or demo and live evidence.');
    if (Date.parse(run.generated_at) !== Date.parse(run.report.generated_at) || (i && Date.parse(run.generated_at) < Date.parse(data.runs[i-1].generated_at))) fail('Snapshots must be ordered by collection time.');
    if (run.label !== undefined && !text(run.label,200)) fail('Invalid snapshot label.');
    if (run.narrative !== undefined && !text(run.narrative,600)) fail('Invalid snapshot description.');
    indexes.set(run.run_id,i);
  }
  const known = new Map();
  for (const [i,view] of data.views.entries()) {
    const run = data.runs[i];
    for (const system of run.report.systems) known.set(system.id,system);
    if (!view || view.run_id !== run.run_id || !list(view.systems,100000) || view.systems.length !== known.size || !list(view.relationships,200000)) fail('A saved company view is invalid.');
    const seen = new Set(run.report.systems.map(s=>s.id)), ids = new Set(), counts = {remembered:known.size,seen:seen.size,unavailable:0,not_seen:0};
    for (const s of view.systems) {
      if (!s?.record || !known.has(s.record.id) || ids.has(s.record.id) || !['seen','unavailable','not_seen'].includes(s.visibility) || (s.visibility==='seen') !== seen.has(s.record.id)) fail('A remembered system has invalid visibility.');
      validateReport({...run.report,systems:[s.record],relationships:[]});
      if (!validTime(s.first_seen) || !validTime(s.last_seen) || !indexes.has(s.first_run_id) || !indexes.has(s.last_run_id) || indexes.get(s.last_run_id)>i || indexes.get(s.first_run_id)>indexes.get(s.last_run_id) || !list(s.history,20) || !s.history.length || s.history.some(id=>!indexes.has(id)||indexes.get(id)>i) || !list(s.owner_claims,20) || !list(s.unavailable_sources,1000) || s.unavailable_sources.some(id=>!text(id,100))) fail('System history references are invalid.');
      if (s.owner_claims.some(c=>!text(c.owner,200)||!indexes.has(c.run_id)||indexes.get(c.run_id)>i||c.status!=='reported')) fail('Owner claim history is invalid.');
      if (s.history.some(id=>!data.runs[indexes.get(id)].report.systems.some(r=>r.id===s.record.id)) || s.history[0]!==s.first_run_id || s.history.at(-1)!==s.last_run_id || Date.parse(s.first_seen)!==Date.parse(data.runs[indexes.get(s.first_run_id)].generated_at) || Date.parse(s.last_seen)!==Date.parse(data.runs[indexes.get(s.last_run_id)].generated_at)) fail('System history does not match its source snapshots.');
      ids.add(s.record.id);
      if (s.visibility !== 'seen') counts[s.visibility]++;
    }
    validateReport({...run.report,systems:view.systems.map(s=>s.record),relationships:view.relationships.map(r=>r.record)});
    for (const r of view.relationships) if (!['seen','not_seen'].includes(r.visibility) || !indexes.has(r.last_run_id) || indexes.get(r.last_run_id)>i) fail('Connection history is invalid.');
    if (!view.counts || Object.keys(counts).some(k=>counts[k]!==view.counts[k])) fail('Company counts disagree with the saved evidence.');
  }
  const pairs = new Set();
  for (const c of data.comparisons) {
    const a=indexes.get(c?.before_run_id),b=indexes.get(c?.after_run_id),key=`${a}:${b}`;
    if (a===undefined || b===undefined || a>=b || pairs.has(key) || !list(c.system_changes,200000) || !list(c.relationship_changes,200000) || !list(c.source_changes,200)) fail('A comparison crosses invalid snapshot boundaries.');
    pairs.add(key);
    const systems=new Set(data.views[b].systems.map(s=>s.record.id)), links=new Set(data.views[b].relationships.map(r=>r.record.id));
    for (const change of c.system_changes) {
      if (!systems.has(change?.id) || !text(change.name,200) || !['added','changed','evidence_changed','seen_again','not_seen','unavailable'].includes(change.kind) || !list(change.fields,6) || !indexes.has(change.after_run_id) || indexes.get(change.after_run_id)>b || (change.before_run_id!==null&&(!indexes.has(change.before_run_id)||indexes.get(change.before_run_id)>a))) fail('System change references are invalid.');
      if (change.fields.some(f=>!['name','category','owner','status','confidence','attributes'].includes(f.field)||!Object.hasOwn(f,'before')||!Object.hasOwn(f,'after'))) fail('A changed field is invalid.');
    }
    for (const change of c.relationship_changes) if (!links.has(change?.id) || !['added','changed','not_seen','seen_again'].includes(change.kind) || !indexes.has(change.after_run_id) || indexes.get(change.after_run_id)>b) fail('A connection change is invalid.');
    for (const source of c.source_changes) if (!text(source.id,100)||!text(source.name,500)||!['complete','error','not_configured','absent'].includes(source.before)||!['complete','error','not_configured','absent'].includes(source.after)) fail('A source change is invalid.');
  }
  if (pairs.size !== data.runs.length*(data.runs.length-1)/2) fail('The history is missing comparisons.');
  return data;
}

export function comparisonFor(data,before,after) {
  if (!Number.isInteger(before)||!Number.isInteger(after)||before<0||after>=data.runs.length||before>=after) return null;
  return data.comparisons.find(c=>c.before_run_id===data.runs[before].run_id && c.after_run_id===data.runs[after].run_id) || null;
}

export function filterMemory(view,query='') {
  const q=query.trim().toLowerCase();
  return view.systems.filter(s=>[s.record.name,s.record.owner,s.record.category,s.visibility].join(' ').toLowerCase().includes(q));
}
