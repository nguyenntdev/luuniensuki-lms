// Recompute paired point estimates and verify that each source component is assigned once.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {join} from 'node:path';
const [out] = process.argv.slice(2);
const result = JSON.parse(readFileSync(join(out, 'result.json')));
const [header, ...lines] = readFileSync(join(out, 'metrics.csv'), 'utf8').trim().split(/\r?\n/);
const fields = header.split(',');
const groups = new Map();
const ids = new Set();
const sums = Object.fromEntries(Object.keys(result.mean).map(name => [name, 0]));
let n = 0;
for (const row of lines) {
  const cells = row.match(/("[^"]*"|[^,]+)(?=,|$)/g).map(v => v.replaceAll('"',''));
  assert.equal(cells.length, fields.length);
  const r = Object.fromEntries(fields.map((key, i) => [key, cells[i]]));
  assert(!ids.has(r.claim));
  ids.add(r.claim);
  for (const source of r.component.split(',')) {
    if (groups.has(source)) assert.equal(groups.get(source), r.screen);
    groups.set(source, r.screen);
  }
  if (r.screen === 'True') {
    n++;
    for (const k of Object.keys(sums)) {
      assert(Number(r[k]) >= 0 && Number(r[k]) <= 1.0000001);
      sums[k] += Number(r[k]);
    }
  }
}
assert.equal(n, result.screen);
assert.equal(ids.size, result.queries);
let advance = true;
for (const k of Object.keys(sums)) {
  assert(Math.abs(sums[k] / n - result.mean[k]) < 1e-10);
  if (k === 'candidate') continue;
  const gain = (sums.candidate - sums[k]) / n;
  assert(Math.abs(gain - result.contrasts[k].gain) < 1e-10);
  advance &&= gain >= .02 && result.contrasts[k].ci[0] > 0;
}
assert.equal(advance, result.advance);
console.log(JSON.stringify({queries: ids.size, screen: n, advance}));
