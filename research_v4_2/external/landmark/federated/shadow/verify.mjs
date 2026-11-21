import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {join} from 'node:path';
import {gunzipSync} from 'node:zlib';

const [prepared, run]=process.argv.slice(2);
function table(path){
  const data = readFileSync(path);
  const lines = (path.endsWith('.gz') ? gunzipSync(data) : data).toString().trimEnd().split(/\r?\n/);
  const names = lines.shift().split(',');
  return lines.map(line=>Object.fromEntries(line.split(',').map((v,i)=>[names[i],v])));
}
function offset(p,d){
  return 1/(1+Math.exp(-Math.log(p/(1-p))-d));
}
function quantile(vals,q){
  const sorted=vals.slice().sort((a,b)=>a-b);
  const j=(sorted.length-1)*q;
  return sorted[Math.floor(j)]+(j%1)*(sorted[Math.ceil(j)]-sorted[Math.floor(j)]);
}
const input=table(prepared);
const expected=input.filter(r=>r.split==='train' && createHash('sha256').update('shadow-v1:'+r.learner).digest().readUInt32BE()%5<2);
const ids=new Set(expected.map(r=>r.row));
const cal=table(join(run,'calibration.csv.gz'));
const dev=table(join(run,'predictions.csv.gz'));
const config=JSON.parse(readFileSync(join(run,'gate.json')));
const expectedDev=input.filter(r=>r.split==='dev');
assert.deepEqual(dev.map(r=>r.row),expectedDev.map(r=>r.row));
const rosterNames=['mixed','lr','mlp'];
const courses=[...new Set(dev.map(r=>r.code_module))];
let decisions=0;
for(const name of rosterNames){
  const thisCal=cal.filter(r=>r.roster===name);
  assert.deepEqual(new Set(thisCal.map(r=>r.row)),ids);
  assert.equal(thisCal.length,ids.size);
  for(const course of courses){
    const fitted=config.gate[name+'/'+course];
    const rows=thisCal.filter(r=>r.code_module===course);
    const p=rows.map(r=>offset(+r.raw_local,fitted.offsets[0]));
    const t=rows.map(r=>offset(+r.raw_transfer,fitted.offsets[1]));
    const yy=rows.map(r=>+r.y);
    for(let i=0;i<rows.length;i++){
      assert.equal(input[rows[i].row].code_module,course);
      assert.equal(input[rows[i].row].y,rows[i].y);
    }
    for (const probs of [p,t]){
      const score=probs.reduce((acc,v,i)=>acc+v-yy[i],0)/probs.length;
      assert.ok(Math.abs(score)<1e-10);
    }
    const cut=[quantile(p,1/3),quantile(p,2/3)];
    for (let i=0;i<2;i++) assert.ok(Math.abs(cut[i]-fitted.cuts[i])<1e-10);
    const bin=v=>v<=cut[0]?0:v<=cut[1]?1:2;
    const overall=Array(5).fill(0),parts=Array.from({length:3},()=>Array(5).fill(0));
    for(let i=0;i<p.length;i++)for(let j=0;j<5;j++){
      const z=p[i]+j*(t[i]-p[i])/4;
      const l=yy[i]?-Math.log(z):-Math.log1p(-z);
      overall[j]+=l;parts[bin(p[i])][j]+=l;
    }
    const argmin=a=>a.indexOf(Math.min(...a))/4;
    const ws=parts.map(a=>argmin(a.map((v,j)=>v+64*overall[j]/p.length)));
    assert.deepEqual(ws,fitted.weights);
    assert.equal(argmin(overall),fitted.global_weight);
    for(const r of dev.filter(r=>r.code_module===course)){
      const a=+r[name+'_local'], b=+r[name+'_transfer'];
      const chosen=ws[bin(a)], target=name==='mixed'?'adapted':name+'_strata';
      assert.ok(Math.abs(+r[target]-(a+chosen*(b-a)))<1e-12);
      assert.ok(Math.abs(+r[name+'_single']-(a+fitted.global_weight*(b-a)))<1e-12);
      decisions+=2;
    }
  }
}
console.log(JSON.stringify({calibration_registrations:expected.length,rosters:rosterNames.length,courses:courses.length,verified_gate_predictions:decisions}));
