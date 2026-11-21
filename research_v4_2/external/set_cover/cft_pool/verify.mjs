// Independent OR-Library parser and witness, scope, and paired-statistics audit.
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const [data, runs, output] = process.argv.slice(2);
if (!output) throw Error('usage: node verify.mjs DATA RUNS OUTPUT');
const here = path.dirname(fileURLToPath(import.meta.url));
const hashes = new Map(fs.readFileSync(path.join(here, '../equal_budget/matrices.sha256'), 'utf8')
  .trim().split('\n').map(line => {
    const [hash, name] = line.split(/\s+/);
    return [path.basename(name), hash];
  }));
const methods = ['cft', 'prefix', 'random', 'full'];
const names = [...'efgh'].flatMap(f => [1, 2, 3, 4, 5].map(i => 'scpnr' + f + i));
assert.deepEqual(fs.readdirSync(runs).sort(), names.map(n => n + '.json'));
const records = [];
let checked = 0;
const branchStats = Object.fromEntries(['pool', 'random', 'full'].map(name =>
  [name, {reported_optimal_by_deadline: 0, late_returns: 0, max_return_cpu: 0, strict_improvements: 0}]));
let maxPrefixCpu = 0;
let prefixesOverBudget = 0;
for (const name of names) {
  const saved = JSON.parse(fs.readFileSync(path.join(runs, name + '.json')));
  const raw = fs.readFileSync(path.join(data, name + '.txt'));
  assert.equal(saved.instance, name);
  assert.equal(saved.sha256, crypto.createHash('sha256').update(raw).digest('hex'));
  assert.equal(saved.sha256, hashes.get(name + '.txt'));
  const ints = raw.toString().trim().split(/\s+/).map(Number);
  let pos = 0;
  const m = ints[pos++], n = ints[pos++];
  const cost = [0, ...ints.slice(pos, pos + n)];
  pos += n;
  const covered = Array.from({length: n + 1}, () => []);
  for (let row = 0; row < m; row++) {
    const count = ints[pos++];
    for (let k = 0; k < count; k++) covered[ints[pos++]].push(row);
  }
  assert.equal(pos, ints.length);

  function uniqueCols(cols) {
    assert.deepEqual(cols, [...new Set(cols)].sort((a, b) => a - b));
    assert(cols.every(j => Number.isInteger(j) && j >= 1 && j <= n));
  }
  function check(w) {
    uniqueCols(w.cols);
    assert.equal(w.cost, w.cols.reduce((t, j) => t + cost[j], 0));
    const rows = new Set();
    for (const j of w.cols) for (const i of covered[j]) rows.add(i);
    assert.equal(rows.size, m);
    checked++;
  }
  check(saved.warm);
  assert.equal(saved.warm.cpu, 0);
  assert.deepEqual(saved.runs.map(r => r.seed), [11, 29, 47]);
  for (const run of saved.runs) {
    function trace(entries, deadline, returned, global) {
      let stamp = 0, score = saved.warm.cost;
      for (const w of entries) {
        check(w);
        assert(w.cpu >= stamp && w.cpu <= deadline && w.cpu <= returned);
        if (global) assert(w.cost < score);
        stamp = w.cpu;
        score = w.cost;
      }
    }
    trace(run.baseline_trace, 5, run.baseline_cpu, true);
    trace(run.prefix_trace, 2, run.prefix_native_cpu, false);
    assert(run.prefix_cpu >= run.prefix_native_cpu);
    maxPrefixCpu = Math.max(maxPrefixCpu, run.prefix_cpu);
    if (run.prefix_cpu > 5) prefixesOverBudget++;
    const distinct = new Map();
    for (const w of run.prefix_trace) if (!distinct.has(String(w.cols))) distinct.set(String(w.cols), w);
    const elite = [...distinct.values()].sort((a, b) => a.cost - b.cost).slice(0, 12);
    const best = [saved.warm, ...elite].sort((a, b) => a.cost - b.cost)[0];
    assert.deepEqual(best, run.prefix_best);
    const expected = [...new Set([best, ...elite].flatMap(w => w.cols))].sort((a, b) => a - b);
    const scores = {
      instance: name, seed: run.seed, cft: (run.baseline_trace.at(-1) ?? saved.warm).cost,
      prefix: best.cost, observed: run.prefix_trace.length, distinct: distinct.size, pool_size: expected.length
    };
    assert.deepEqual(Object.keys(run.branches).sort(), ['full', 'pool', 'random']);
    for (const [method, b] of Object.entries(run.branches)) {
      check(b);
      const stats = branchStats[method];
      assert(b.return_cpu >= run.prefix_cpu);
      if (method === 'full') {
        assert.equal(b.pool, null);
        assert.equal(b.size, n);
      } else {
        uniqueCols(b.pool);
        assert.equal(b.pool.length, expected.length);
        assert.equal(b.size, expected.length);
        if (method === 'pool') assert.deepEqual(b.pool, expected);
        const allowed = new Set(b.pool);
        assert(best.cols.every(j => allowed.has(j)));
        assert(b.cols.every(j => allowed.has(j)));
      }
      if (b.cost < best.cost) {
        assert(b.improved_cpu >= run.prefix_cpu && b.improved_cpu <= Math.min(5, b.return_cpu));
        stats.strict_improvements++;
      } else {
        assert.equal(b.improved_cpu, null);
        assert.equal(b.cost, best.cost);
        assert.deepEqual(b.cols, best.cols);
      }
      if (b.certified) {
        assert.equal(b.status, 'Optimal');
        assert(b.return_cpu <= 5.001);
        stats.reported_optimal_by_deadline++;
      }
      if (b.return_cpu > 5) stats.late_returns++;
      stats.max_return_cpu = Math.max(stats.max_return_cpu, b.return_cpu);
      scores[method] = b.cost;
    }
    records.push(scores);
  }
}
const median = x => [...x].sort((a, b) => a - b)[Math.floor(x.length / 2)];
const instanceMedians = names.map(instance => {
  const group = records.filter(r => r.instance === instance);
  return {instance, ...Object.fromEntries(['pool', ...methods].map(method =>
    [method, median(group.map(r => r[method]))]))};
});
function effects(rows) {
  return Object.fromEntries(methods.map(method => {
    const savings = rows.map(r => (r[method] - r.pool) / r[method]);
    const count = predicate => savings.filter(predicate).length;
    return [method, {wins: count(x => x > 0), ties: count(x => x === 0), losses: count(x => x < 0),
      mean_relative_saving: savings.reduce((a, b) => a + b, 0) / rows.length}];
  }));
}
const summary = {
  scope: 'development only', instances: names.length, paired_seeds: records.length,
  witness_records_checked: checked, max_prefix_cpu: maxPrefixCpu, prefixes_over_five_seconds: prefixesOverBudget,
  branches: branchStats, instance_median_comparisons: effects(instanceMedians),
  family_median_comparisons: Object.fromEntries([...'efgh'].map(f =>
    [f, effects(instanceMedians.filter(r => r.instance.startsWith('scpnr' + f)))])),
  paired_seed_comparisons: effects(records), instance_medians: instanceMedians, seed_costs: records
};
fs.writeFileSync(output, JSON.stringify(summary, null, 2) + '\n');
console.log(JSON.stringify({instances: names.length, checked, instance_effects: effects(instanceMedians)}));
