import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {gunzipSync} from 'node:zlib';
import {join} from 'node:path';
const [study]=process.argv.slice(2);
function read(path) {
  const [header,...rows] = gunzipSync(readFileSync(path)).toString().trim().split('\n');
  const fields = header.split(',');
  return rows.map(row=>Object.fromEntries(row.split(',').map((x,i)=>[fields[i], x])));
}
const old=read(join(study,'../temporal/run/screen.csv.gz'));
const upstream=read(join(study,'../published_simplekt/run/screen.csv.gz'));
const extra=read(join(study,'run/estimates.csv.gz'));
const summary=JSON.parse(readFileSync(join(study,'run/result.json')));
const key=r=>[r.uid,r.row,r.start,r.y].join('/');
const maps=[old,upstream,extra].map(data=>new Map(data.map(r=>[key(r),r])));
for(const [i,m] of maps.entries()){
  assert.equal([old,upstream,extra][i].length,summary.rows);
  assert.equal(m.size,summary.rows);
}
const names=Object.keys(summary.loss);
const values=Object.fromEntries(names.map(k=>[k,0]));
const strata={};
for(const [k,r] of maps[0]){
  const a=maps[1].get(k),b=maps[2].get(k);
  assert(a && b);
  for(const same of ['clock','sakt','blend_joint']) assert(Math.abs(+r[same]- +a[same])<1e-12);
  const row={...r,...a,...b};
  const y=Number(r.y);
  const support=Number(b.question_support);
  const band=support===0?'unseen':support<6?'1_to_5':support<20?'6_to_19':'20_plus';
  strata[band]=(strata[band]||0)+1;
  for(const name of names){
    const p=Number(row[name]); assert(p>0 && p<1);
    values[name]+=y===1?-Math.log(p):-Math.log1p(-p);
  }
}
for(const [name,sum] of Object.entries(values)) assert(Math.abs(sum/old.length-summary.loss[name])<1e-12);
for(const [name,count] of Object.entries(strata)) assert.equal(summary.strata[name].rows,count);
for(const [name,c] of Object.entries(summary.contrasts)){
  const gain=(values[name]-values.ability)/old.length;
  assert(Math.abs(gain-c.gain)<1e-12);
  assert.equal(c.passed,gain>.015 && c.ci[0]>0);
}
assert.equal(new Set(old.map(r=>r.uid)).size,summary.learners);
console.log(JSON.stringify({rows:old.length,checked_forecasts:old.length*names.length,
  matched_prior_ledgers:2,contrasts:Object.keys(summary.contrasts).length}));
