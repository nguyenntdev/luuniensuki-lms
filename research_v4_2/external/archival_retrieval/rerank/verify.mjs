import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const [raw, scores, out] = process.argv.slice(2);
const data = readFileSync(raw,'utf8').trim().split('\n').map(JSON.parse);
const pred = readFileSync(scores,'utf8').trim().split('\n').slice(1).map(s=>s.split(',').map(Number));
const result = JSON.parse(readFileSync(join(out,'result.json')));
const methods = Object.keys(result.mean), sums = Object.fromEntries(methods.map(k=>[k,0]));
let n = 0, hits = 0, gold = 0;
const ranks = values => {
  const order=values.map((_,i)=>i).sort((i,j)=>values[j]-values[i] || i-j);
  const out=[];
  order.forEach((i,r)=>out[i]=r+1);
  return out;
};
for (let i=0;i<data.length;i+=16) {
  const block=data.slice(i,i+16), ps=pred.slice(i,i+16);
  block.forEach((r,j)=>assert.deepEqual([r.query,r.doc],ps[j].slice(0,2)));
  if (!block[0].screen) continue;
  n++; hits+=block.filter(r=>r.hit).length; gold+=block[0].nrel;
  const base={document:block.map((_,j)=>j+1), sentence:ranks(block.map(r=>r.sentence)),
              abstract:ranks(ps.map(r=>r[2])),focus:ranks(ps.map(r=>r[3]))};
  for(const [k,[a,b,c]] of Object.entries(result.tuned_weights)) {
    base[k]=ranks(block.map((_,j)=>a/(10+base.document[j])+b/(10+base.abstract[j])+c/(10+base.focus[j])));
  }
  const ideal=Array.from({length:Math.min(10,block[0].nrel)},(_,j)=>1/Math.log2(2+j)).reduce((a,b)=>a+b);
  for (const k of methods) {
    sums[k]+=block.reduce((s,r,j)=>s+((r.hit && base[k][j]<=10)?1/Math.log2(1+base[k][j]):0),0)/ideal;
  }
}
assert.equal(n,result.screen); assert.equal(n,157);
assert(Math.abs(hits/gold-result.pool_recall)<1e-12);
for (const k of methods) assert(Math.abs(sums[k]/n-result.mean[k])<1e-12);
console.log(JSON.stringify({pairs:data.length,evaluated:n,metrics:methods.length}));
