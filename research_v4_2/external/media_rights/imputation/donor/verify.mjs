// Independently reconstruct source membership and rescore the frozen development ledger.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { createReadStream, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { gunzipSync } from 'node:zlib';

const [raw, dir, previous, cpu] = process.argv.slice(2);
const hash = createHash('sha256');
for await (const chunk of createReadStream(raw)) hash.update(chunk);
assert.equal(hash.digest('hex'), 'f53eb3bd6e321a051ce11ad40bd7f5ee204c6c534cb07508f0f617d03bea0d3a');
const source = execFileSync('python3', ['-c', `import csv, hashlib, sys
with open(sys.argv[1],encoding='utf-8-sig',newline='') as f:
 for row in csv.DictReader(f):
  k=row['Object ID']
  h=int.from_bytes(hashlib.sha256(k.encode()).digest()[:6],'big')%100
  if 60<=h<80: print(k,{'False':0,'True':1}[row['Is Public Domain']],sep=',')`, raw],
  { encoding:'utf8',maxBuffer:5e6 });
const truth = new Map(source.trimEnd().split('\n').map(row => row.split(',')));
function read(path) {
  const [first,...rows] = gunzipSync(readFileSync(path)).toString().trimEnd().split('\n');
  return [first.split(','),rows.map(line=>line.split(','))];
}
const [fields, rows] = read(join(dir,'dev.csv.gz'));
const refs = [[previous,'global','previous_global'],[cpu,'neighbor','cpu_neighbor']].map(([file,p,c])=>{
  const [k, r] = read(file);
  return [new Map(r.map(v=>[v[0],Number(v[k.indexOf(p)])])),fields.indexOf(c)];
});
assert.deepEqual(fields.slice(0,2), ['oid','y']);
const losses = Array(fields.length-2).fill(0);
for (const r of rows) {
  assert.equal(truth.get(r[0]),r[1]);
  truth.delete(r[0]);
  for (const [control,col] of refs) assert.ok(Math.abs(Number(r[col])-control.get(r[0]))<1e-14);
  for (let j=2;j<fields.length;j++) {
    const p=Number(r[j]);
    assert.ok(p>0 && p<1);
    losses[j-2] -= r[1]==='1'?Math.log(p):Math.log1p(-p);
  }
}
assert.equal(truth.size,0);
const report=JSON.parse(readFileSync(join(dir,'summary.json')));
assert.equal(report.development,rows.length);
const means=Object.fromEntries(fields.slice(2).map((c,i)=>[c,losses[i]/rows.length]));
for (const [name,score] of Object.entries(means)) {
  assert.ok(Math.abs(report.loss[name]-score)<1e-11);
  if(name!=='compatible') assert.ok(Math.abs(score-means.compatible-report.gain[name])<1e-11);
}
assert.equal(report.pass_screen,Object.values(report.gain).every(v=>v>=.005));
console.log(JSON.stringify({rows:rows.length,models:losses.length,source_hash_verified:true,
 previous_predictions_checked:rows.length*2,pass_screen:report.pass_screen}));
