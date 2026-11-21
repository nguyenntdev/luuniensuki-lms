// Independent station-based time-dependent Dijkstra oracle and journey verifier.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { gunzipSync } from 'node:zlib';
const [network, witnesses, timings, startup, inventory] = process.argv.slice(2);
const bytes = readFileSync(network);
assert.equal(createHash('sha256').update(bytes).digest('hex'),JSON.parse(readFileSync(inventory)).projection_sha256);
const lines = bytes.toString().trimEnd().split('\n').map(s=>s.split(' ').map(Number));
const [stations, trips, nLeg, nQuery, nScenarios] = lines[0];
const legs = lines.slice(1,nLeg+1);
const queries = lines.slice(nLeg+1,nLeg+nQuery+1);
const bans = lines.at(-1);
assert.equal(bans.length,nScenarios);
assert.equal(new Set(bans).size,nScenarios);
assert(bans.every(t=>t>=0 && t<trips));
const departures = Array.from({length:stations},()=>[]);
for(const l of legs) departures[l[1]].push(l);
const INF=1e9;
function optimal([origin,start,destination],ban) {
  const times = new Int32Array(stations).fill(INF);
  const settled = new Uint8Array(stations);
  times[origin]=start;
  for(;;) {
    let v=-1, t=INF;
    for(let s=0;s<stations;s++) if(!settled[s] && times[s]<t) {v=s;t=times[s];}
    if(v<0 || v===destination) return times[destination];
    settled[v]=1;
    for(const [dep,,arr,to,trip] of departures[v]) {
      if(trip!==ban && dep>=t && arr<times[to]) times[to]=arr;
    }
  }
}
const answers=bans.map(b=>queries.map(q=>optimal(q,b)));
const base=queries.map(q=>optimal(q,-1));
let affected=0, unreach=0, finite=0, becameUnreachable=0;
for(const rows of answers) rows.forEach((t,i)=>{
  assert(t>=base[i]);
  if(t>base[i]) affected++;
  if(t===INF) {unreach++; if(t>base[i]) becameUnreachable++;}
  else finite++;
});
const methods=['csa','full_profile','path_cache','all_predecessors','eager','indexed_csa','lazy_unpruned','candidate'];
const visited = new Uint8Array(nScenarios*nQuery*methods.length);
let numberOfRides=0;
for(const row of gunzipSync(readFileSync(witnesses)).toString().trimEnd().split('\n')) {
  const [s,m,q,arrival,...route]=row.split(' ').map(Number);
  assert(s>=0 && s<nScenarios && m>=0 && m<methods.length && q>=0 && q<nQuery);
  const k=(s*methods.length+m)*nQuery+q;
  assert.equal(visited[k],0);visited[k]=1;
  assert.equal(arrival,answers[s][q],row);
  let [at,time,dest]=queries[q];
  if(arrival===INF) assert.equal(route.length,0);
  else {
    for(const i of route) {
      assert(i>=0 && i<nLeg);
      const [dep,from,arr,to,trip]=legs[i];
      assert.equal(at,from);assert(time<=dep && dep<arr && trip!==bans[s]);
      at=to;time=arr;numberOfRides++;
    }
    assert.equal(at,dest);assert.equal(time,arrival);
  }
}
assert(visited.every(v=>v===1));
function csv(path) {
  const rows=readFileSync(path,'utf8').trimEnd().split('\n');
  const fields=rows.shift().split(',');
  return rows.map(row=>Object.fromEntries(row.split(',').map((v,i)=>[fields[i],v])));
}
const data=csv(timings);
const setup=Object.fromEntries(csv(startup).map(r=>[r.method,Number(r.ns)]));
const results={};
function gmean(a) {return Math.exp(a.reduce((sum,v)=>sum+Math.log(v),0)/a.length);}
for(const m of methods) {
  const values=[];
  for(let s=0; s<nScenarios;s++) {
    const rs=data.filter(r=>r.method===m && +r.scenario===s);
    assert.equal(rs.length,5);
    assert.deepEqual(rs.map(r=>+r.repeat).sort(),[0,1,2,3,4]);
    assert(rs.every(r=>+r.trip===bans[s] && +r.ns>0));
    values.push(rs.map(r=>+r.ns).sort((a,b)=>a-b)[2]);
  }
  const p95=values.toSorted((a,b)=>a-b)[Math.ceil(values.length*.95)-1];
  const amortized=values.map(x=>x+setup[m]/nScenarios);
  results[m]={setup_ms:setup[m]/1e6, p95_ms:p95/1e6, geometric_ms:gmean(values)/1e6,
              amortized_p95_ms:(p95+setup[m]/nScenarios)/1e6, amortized_geometric_ms:gmean(amortized)/1e6};
}
assert.equal(data.length,nScenarios*methods.length*5);
const gains={};
for(const m of methods.slice(0,-1)) {
  gains[m]={p95:1-results.candidate.p95_ms/results[m].p95_ms,geometric:1-results.candidate.geometric_ms/results[m].geometric_ms, amortized_p95:1-results.candidate.amortized_p95_ms/results[m].amortized_p95_ms, amortized_geometric:1-results.candidate.amortized_geometric_ms/results[m].amortized_geometric_ms};
}
console.log(JSON.stringify({queries:nQuery,scenarios:nScenarios,verified:visited.length,witness_legs:numberOfRides,
 finite,unreachable:unreach,affected,became_unreachable:becameUnreachable,results,gains,
 advance:Object.values(gains).every(g=>g.p95>=.1 && g.geometric>=.1 && g.amortized_p95>=.1 && g.amortized_geometric>=.1)},null,2));
