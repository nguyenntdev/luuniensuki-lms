import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { createReadStream, readFileSync } from 'node:fs';
import { createGunzip } from 'node:zlib';
import { createInterface } from 'node:readline';
import { join } from 'node:path';

const [archive,out]=process.argv.slice(2);
const lines = path => createInterface({input:createReadStream(path).pipe(createGunzip()),crlfDelay:Infinity});
let header;
const keep=new Map(), gold=[], users=[];
for await (const line of lines(archive)) {
  const row=line.split(',');
  if (!header) {header=row;continue;}
  const id=row[header.indexOf('user_id')];
  if (!keep.has(id)) keep.set(id,createHash('sha256').update(id).digest().readUInt32BE()%100===13);
  if (!keep.get(id)) continue;
  const target=Number(row.at(-1))/Number(row.at(-2));
  assert(Number.isFinite(target));
  users.push(id); gold.push(target);
}
const study=JSON.parse(readFileSync(join(out,'result.json'),'utf8'));
const sorted=[...new Set(users)].sort();
assert.equal(sorted.length,study.learners);
const names=Object.keys(study.mean_learner_loss);
const groups=Array.from({length:sorted.length},()=>({n:0,sums:new Float64Array(names.length)}));
header=null;
let i=0;
for await (const line of lines(join(out,'forecasts.csv.gz'))) {
  const row=line.split(',');
  if (!header) {header=row;continue;}
  const learner=Number(row[0]), y=Number(row[1]);
  assert.equal(users[i],sorted[learner]);assert(Math.abs(y-gold[i])<1e-14);
  groups[learner].n++;
  for (const [j,k] of names.entries()) {
    const raw=Number(row[header.indexOf(k)]);
    assert(raw>=0 && raw<=1);
    const p=Math.min(1-1e-8,Math.max(raw,1e-8));
    groups[learner].sums[j]+=-y*Math.log(p)-(1-y)*Math.log1p(-p);
  }
  i++;
}
assert.equal(i,gold.length);assert.equal(i,study.rows);
for (const [j,k] of names.entries()) {
  const l=groups.reduce((s,g)=>s+g.sums[j]/g.n,0)/groups.length;
  assert(Math.abs(l-study.mean_learner_loss[k])<1e-10);
  if(k!=='reconciled')assert(Math.abs(l-study.mean_learner_loss.reconciled-study.gains[k])<1e-10);
}
console.log(JSON.stringify({rows:i,learners:groups.length,forecasts:names.length*i,source_labels_verified:true}));
