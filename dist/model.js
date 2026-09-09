export const categories = ['ERP','Email','Finance','CRM','People','Collaboration','Data','Infrastructure','Unclassified'];
const states = ['observed','reported','inferred'];
const text = (v, max=600) => typeof v === 'string' && v.length <= max;
const array = (v, max=5000) => Array.isArray(v) && v.length <= max;
export function validateReport(data) {
  const fail = message => { throw new Error(message); };
  if (!data || data.schema_version !== '1.0') fail('This file must be a Glinx report with schema_version 1.0.');
  if (!['demo','live'].includes(data.mode) || !text(data.company,200) || !data.company.trim()) fail('The report needs a company and a valid demo/live mode.');
  if (!text(data.generated_at,60) || !Number.isFinite(Date.parse(data.generated_at))) fail('The report timestamp is invalid.');
  if (!array(data.systems) || !array(data.relationships,10000) || !array(data.collectors,100)) fail('The report contains invalid or oversized collections.');
  const ids = new Set();
  for (const a of data.systems) {
    if (!a || !text(a.id,100) || !a.id || ids.has(a.id)) fail('System IDs must be unique, nonempty strings.');
    ids.add(a.id);
    if (!text(a.name,200) || !a.name || !categories.includes(a.category) || !states.includes(a.status) || !Number.isFinite(a.confidence) || a.confidence<0 || a.confidence>100 || !text(a.owner,200)) fail('A system has invalid metadata.');
    if (!array(a.evidence,1000) || !a.evidence.length) fail('Each system must include its discovery evidence.');
    for (const e of a.evidence) {
      if (!e || !text(e.id,100) || !text(e.summary) || !text(e.source,100) || !text(e.locator,500) || !text(e.observed_at,60) || !Number.isFinite(Date.parse(e.observed_at)) || !states.includes(e.status) || !Number.isFinite(e.confidence) || e.confidence<0 || e.confidence>100) fail('A discovery evidence record is invalid.');
    }
  }
  const links=new Set();
  for (const r of data.relationships) {
    if (!r || !text(r.id,100) || links.has(r.id) || !ids.has(r.source) || !ids.has(r.target) || r.source===r.target || !text(r.label,200) || !states.includes(r.status) || !text(r.evidence)) fail('A relationship is invalid or refers to a missing system.');
    links.add(r.id);
  }
  for (const c of data.collectors) {
    if (!c || !text(c.id,100) || !text(c.name,500) || !['complete','error','not_configured'].includes(c.status) || !Number.isInteger(c.count) || c.count<0 || !text(c.detail)) fail('A discovery source is invalid.');
  }
  if (data.limitations !== undefined && (!array(data.limitations,20) || data.limitations.some(v=>!text(v)))) fail('Report limitations are invalid.');
  return data;
}
export function metrics(data) {
  return { systems:data.systems.length, functions:new Set(data.systems.map(s=>s.category).filter(c=>!['Unclassified','Infrastructure'].includes(c))).size, links:data.relationships.length, complete:data.collectors.filter(c=>c.status==='complete').length, configured:data.collectors.filter(c=>c.status!=='not_configured').length, evidence:data.systems.reduce((n,s)=>n+s.evidence.length,0) };
}
export function insights(data) {
  const result=[];
  const unknownOwners=data.systems.filter(s=>!s.owner);
  const clues=data.systems.filter(s=>s.status==='inferred');
  const unclassified=data.systems.filter(s=>s.category==='Unclassified');
  const unavailable=data.collectors.filter(c=>c.status!=='complete');
  if(unknownOwners.length) result.push({kind:'Ownership',title:`${unknownOwners.length} systems need an owner`,body:'Assign a person or team to confirm business purpose, criticality, and access.',ids:unknownOwners.map(s=>s.id)});
  if(clues.length) result.push({kind:'Verification',title:`${clues.length} discoveries are still clues`,body:'Confirm these provider and product fingerprints before treating them as company systems.',ids:clues.map(s=>s.id)});
  if(unavailable.length) result.push({kind:'Visibility',title:`${unavailable.length} discovery sources need attention`,body:'These sources failed or were not configured. Their systems may be missing from this map.',ids:[]});
  if(unclassified.length) result.push({kind:'Classification',title:`${unclassified.length} systems need business context`,body:'Review these applications with a process owner to identify the function they support.',ids:unclassified.map(s=>s.id)});
  if(data.relationships.some(r=>r.status==='reported')) result.push({kind:'Connections',title:'Validate the reported connections',body:'Ask system owners to confirm the direction, frequency, and mechanism of each integration.',ids:[...new Set(data.relationships.filter(r=>r.status==='reported').flatMap(r=>[r.source,r.target]))]});
  if(!data.systems.some(s=>s.category==='ERP')) result.push({kind:'Visibility',title:'No ERP identified in this scan',body:'Ask how orders, purchasing, inventory, and production are managed. Absence from this scan is not proof of absence.',ids:[]});
  return result;
}
export function filterSystems(data, query='', category='all', state='all') {
  const q=query.trim().toLowerCase();
  return data.systems.filter(s=>(category==='all'||s.category===category)&&(state==='all'||s.status===state)&&[s.name,s.category,s.owner,...s.evidence.map(e=>e.source)].join(' ').toLowerCase().includes(q));
}
export function inventoryCsv(data) {
  const cell=v=>{let s=String(v??'');if(/^[\s]*[=+\-@]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"';};
  const rows=[['name','category','owner','status','confidence','evidence_sources'],...data.systems.map(s=>[s.name,s.category,s.owner,s.status,s.confidence,[...new Set(s.evidence.map(e=>e.source))].join('; ')])];
  return rows.map(row=>row.map(cell).join(',')).join('\r\n');
}
