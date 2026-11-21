// Independent held-out row and log-loss verification against the released sequence archive.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {join} from 'node:path';
import {gunzipSync} from 'node:zlib';
const [raw, out] = process.argv.slice(2);
const text = file => readFileSync(file,'utf8').trimEnd().split(/\r?\n/);
const users = new Set();
const train = text(join(raw,'train_valid.csv'));
for (const row of train.slice(1)) {
  const uid = row.split(',',2)[1];
  assert(!users.has(uid));
  users.add(uid);
}
const predictions = gunzipSync(readFileSync(join(out,'predictions.csv.gz'))).toString().trimEnd().split('\n');
const header = predictions[0].split(',');
const result = JSON.parse(readFileSync(join(out,'result.json')));
const fit = JSON.parse(readFileSync(join(out,'development.json')));
const methods = Object.keys(result.nll);
const nll = Object.fromEntries(methods.map(k=>[k,0]));
let n = 0, positives = 0, people = 0;
for(const line of text(join(raw,'test.csv')).slice(1)) {
  const cells = [...line.matchAll(/(?:^|,)(?:"([^"]*)"|([^,]*))/g)].map(m => m[1]??m[2]);
  const [,uid,concepts,responses] = cells;
  assert(!users.has(uid));
  users.add(uid);
  people++;
  const labels = responses.split(',');
  assert.equal(labels.length, concepts.split(',').length);
  for (let i=1;i<labels.length;i++) {
    const values = predictions[++n].split(',');
    const p = Object.fromEntries(header.map((key,k)=>[key,Number(values[k])]));
    const gold = Number(labels[i]);
    assert.equal(p.uid,Number(uid));
    assert.equal(p.step,i);
    assert.equal(p.y,gold);
    positives+=gold;
    for(const name of ['full','short']) {
      const w = fit.weights[name];
      assert(Math.abs(p[name+'_blend'] - (w*p.dkt+(1-w)*p[name])) < 3e-7);
    }
    for(const k of methods) {
      assert(Number.isFinite(p[k]) && p[k]>=0 && p[k]<=1);
      const prob = Math.min(1-1e-7,Math.max(1e-7,p[k]));
      nll[k]-=gold ? Math.log(prob) : Math.log1p(-prob);
    }
  }
}
assert.equal(predictions.length,n+1);
assert.equal(result.events,n);
assert.equal(result.correct,positives);
assert.equal(result.learners,people);
for(const k of methods) assert(Math.abs(nll[k]/n - result.nll[k]) < 1e-7,k);
console.log(JSON.stringify({learners:people,events:n,correct:positives,forecasts:n*methods.length}));
