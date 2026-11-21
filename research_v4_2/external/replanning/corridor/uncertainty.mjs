// Simultaneous one-sided basic bootstrap bounds in log-latency ratio units.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const [latencyPath,setupPath]=process.argv.slice(2);
function rows(path) {
  return readFileSync(path,'utf8').trim().split('\n').slice(1).map(row=>row.split(','));
}
const setup=new Map(rows(setupPath).map(([method,ns])=>[method,Number(ns)]));
const cells=new Map();
for(const [scenario,,repeat,method,ns] of rows(latencyPath)) {
  const key=method+'/'+scenario;
  if(!cells.has(key)) cells.set(key,[]);
  cells.get(key)[Number(repeat)]=Number(ns);
}
const n=48, draws=3000, methods=[...setup.keys()];
const scenarios=Array.from({length:n},(_,i)=>i);
const times=methods.map(m=>scenarios.map(s=>{
  const v=cells.get(m+'/'+s);
  assert.equal(v.length,5);
  return v.sort((a,b)=>a-b)[2];
}));
function summaries(index, sample) {
  const v=sample.map(i=>times[index][i]).sort((a,b)=>a-b);
  const p95=v[Math.ceil(.95*n)-1];
  const cost=setup.get(methods[index])/n;
  const gmLog=add=>v.reduce((s,x)=>s+Math.log(x+add),0)/n;
  return [Math.log(p95),gmLog(0),Math.log(p95+cost),gmLog(cost)];
}
function contrasts(sample) {
  const scores=methods.map((_,i)=>summaries(i,sample));
  const candidate=scores.pop();
  return scores.flatMap(s=>s.map((x,i)=>x-candidate[i]));
}
const point=contrasts(scenarios), maxima=[];
let state=4202;
function next(){state=(Math.imul(state,1664525)+1013904223)>>>0;return Math.floor(state/4294967296*n);}
for(let r=0;r<draws;r++) {
  const ratios=contrasts(Array.from({length:n},next));
  maxima.push(Math.max(...ratios.map((x,i)=>x-point[i])));
}
const critical=maxima.sort((a,b)=>a-b)[Math.ceil(.95*draws)-1];
const bounds=Object.fromEntries(methods.slice(0,-1).map((m,i)=>[m,point.slice(i*4,i*4+4).map(x=>1-Math.exp(critical-x))]));
console.log(JSON.stringify({draws,unit:"simulated trip cancellation",family:point.length,
 endpoints:["p95","geometric","amortized_p95","amortized_geometric"],lower_fractional_gain:bounds},null,2));
