// Check held-out membership and feasible binary nDCG values from original relevance sets.
import {readFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {join} from 'node:path';

const [raw, out] = process.argv.slice(2);
const claims = execFileSync('tar',['-xzOf',join(raw,'data.tar.gz'),'data/claims_train.jsonl'],
  {encoding:'utf8',maxBuffer:8e6}).trim().split('\n').map(JSON.parse);
const eligible = new Map(claims.filter(c => Object.keys(c.evidence).length).map(c => [c.id,c]));
const adjacency = new Map();
for (const claim of claims) {
  const cited = [...new Set([...claim.cited_doc_ids,...Object.keys(claim.evidence).map(Number)])];
  for (const x of cited) {
    if (!adjacency.has(x)) adjacency.set(x,new Set());
    for (const y of cited) adjacency.get(x).add(y);
  }
}
const component = new Map();
for (const source of adjacency.keys()) {
  if (component.has(source)) continue;
  const queue = [source];
  const visited = new Set(queue);
  for (let i=0; i<queue.length; i++) {
    for (const next of adjacency.get(queue[i])) {
      if (visited.has(next)) continue;
      visited.add(next);
      queue.push(next);
    }
  }
  const label = queue.sort((a,b)=>a-b).join(',');
  for (const node of visited) component.set(node,label);
}
const [header,...lines] = readFileSync(join(out,'metrics.csv'),'utf8').trim().split(/\r?\n/);
assert.equal(lines.length,eligible.size);
const seen = new Set();
for (const line of lines) {
  const cells = line.match(/("[^"]*"|[^,]+)(?=,|$)/g).map(v=>v.replaceAll('"',''));
  const row = Object.fromEntries(header.split(',').map((k,i)=>[k,cells[i]]));
  const c = eligible.get(Number(row.claim));
  assert(c && !seen.has(c.id));
  seen.add(c.id);
  const group = component.get(c.cited_doc_ids[0]);
  assert.equal(row.component,group);
  assert.equal(row.screen==='True',createHash('sha256').update(group).digest().readBigUInt64BE()%3n===0n);
  // For one relevant document there are only eleven possible nDCG@10 values.
  if (Object.keys(c.evidence).length===1) {
    const attainable=[0,...Array.from({length:10},(_,i)=>1/Math.log2(2+i))];
    for (const n of cells.slice(3)) assert(attainable.some(v=>Math.abs(v-Number(n))<1e-11));
  }
}
console.log(JSON.stringify({source_claims:claims.length,eligible_checked:seen.size}));
