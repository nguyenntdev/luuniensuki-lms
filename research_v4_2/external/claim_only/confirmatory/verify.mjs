// Independently score saved decisions against the released rows and audit checkpoint decoders.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync, writeFileSync} from 'node:fs';
import {join} from 'node:path';

const [source, scoreDir, resultDir] = process.argv.slice(2);
if (!resultDir) throw Error('Usage: node verify.mjs RAW_ROOT SCORE_DIR RESULT_DIR');

const labels = ['SUPPORTS', 'REFUTES', 'NOT ENOUGH INFO'];
const checkpoints = [
  'albert-base-vitaminc', 'albert-base-vitaminc-mnli', 'albert-base-vitaminc-fever',
  'albert-xlarge-vitaminc', 'albert-xlarge-vitaminc-mnli', 'albert-xlarge-vitaminc-fever',
  'bart-original', 'roberta-large-mnli',
];
const candidate = 'context_stack_paired';

function csv(path) {
  // All fields in these model-output files are ASCII numeric values, release IDs or method names.
  const lines = readFileSync(path, 'utf8').trimEnd().split(/\r?\n/);
  assert(!lines.some(line => line.includes('"')));
  const cols = lines.shift().split(',');
  const rows = lines.map(line => {
    const values = line.split(',');
    assert.equal(values.length, cols.length);
    return Object.fromEntries(cols.map((name, i) => [name, values[i]]));
  });
  return {cols, rows};
}

const release = readFileSync(join(source, 'vitaminc/test.jsonl'), 'utf8').trimEnd().split('\n')
  .map(line => JSON.parse(line)).filter(row => row.revision_type === 'real');
const pageSet = [...new Set(release.map(row => row.page))].map(page => ({
  name: page, key: createHash('sha256').update(page).digest(),
})).sort((a, b) => a.key.compare(b.key)).slice(128, 256).map(entry => entry.name);
const titles = new Set(pageSet);
const indexed = [...titles].sort((a, b) => Buffer.from(a).compare(Buffer.from(b)));
const records = release.filter(row => titles.has(row.page));
const {cols, rows} = csv(join(resultDir, 'predictions.csv'));
const summary = JSON.parse(readFileSync(join(resultDir, 'result.json'), 'utf8'));
assert.equal(summary.candidate, candidate);
assert.equal(summary.rows.test, records.length);
assert.equal(summary.pages.test, titles.size);
assert.equal(rows.length, 1335);
assert.equal(titles.size, 128);
const methods = cols.slice(3);
const comparators = methods.filter(name => name !== candidate);
assert.deepEqual(cols.slice(0, 3), ['id', 'page', 'gold']);
assert.deepEqual([...methods].sort(), Object.keys(summary.correct).sort());
assert.deepEqual(comparators.slice().sort(), Object.keys(summary.contrasts).sort());
assert.equal(comparators.length, 21);
const sets = new Map();
for (const [i, r] of records.entries()) {
  const key = JSON.stringify([r.case_id, r.claim]);
  if (!sets.has(key)) sets.set(key, []);
  sets.get(key).push(i);
  assert.equal(rows[i].id, r.unique_id);
  assert.equal(Number(rows[i].gold), labels.indexOf(r.label));
  assert.equal(indexed[Number(rows[i].page)], r.page);
  for (const m of methods) assert(['0','1','2'].includes(rows[i][m]));
}
assert.equal([...sets.values()].filter(s => s.length === 2).length, 666);

const counts = new Map(methods.map(method => [method, rows.filter(r => r[method] === r.gold).length]));
for (const m of methods) assert.equal(summary.correct[m], counts.get(m));
const matrices = {};
for (const name of checkpoints) {
  const scores = csv(join(scoreDir, 'test', name + '.csv'));
  assert.deepEqual(scores.cols, ['id', ...labels]);
  assert.equal(scores.rows.length, rows.length);
  matrices[name] = scores.rows.map((row, i) => {
    assert.equal(row.id, records[i].unique_id);
    return labels.map(l => {
      const v = Number(row[l]);
      assert(Number.isFinite(v));
      return v;
    });
  });
}
matrices.uniform_ensemble = records.map((_, i) => labels.map((_, l) =>
  checkpoints.slice(0, 6).reduce((sum, name) => sum + matrices[name][i][l], 0) / 6));

for (const [name, matrix] of Object.entries(matrices)) {
  const expected = matrix.map(v => v.indexOf(Math.max(...v)));
  for (const [i, y] of expected.entries()) assert.equal(Number(rows[i][name]), y);
  // Enumerate all allowed assignments, resolving an exact orientation tie by release ID.
  for (const group of sets.values()) {
    if (group.length !== 2) continue;
    const [i, j] = group;
    const options = [];
    for (const [a, b] of [[0,1], [0,2], [1,0], [2,0]]) {
      options.push({a, b, s:matrix[i][a] + matrix[j][b], id:rows[a === 0 ? i : j].id});
    }
    options.sort((x, y) => (y.s - x.s) || Buffer.from(x.id).compare(Buffer.from(y.id)) || x.a - y.a || x.b - y.b);
    expected[i] = options[0].a;
    expected[j] = options[0].b;
  }
  for (const [i, y] of expected.entries()) assert.equal(Number(rows[i][name + '_paired']), y);
}

const output = ['page_index,rows,comparator,candidate_correct,comparator_correct,rescued,regressed'];
for (const [idx, title] of indexed.entries()) {
  const group = rows.filter(r => Number(r.page) === idx);
  assert(group.length > 0);
  for (const method of comparators) {
    const won = r => r[candidate] === r.gold;
    const otherWon = r => r[method] === r.gold;
    output.push([idx, group.length, method, group.filter(won).length, group.filter(otherWon).length,
      group.filter(r => won(r) && !otherWon(r)).length, group.filter(r => !won(r) && otherWon(r)).length].join(','));
  }
}
let latest = 0;
const ascending = Object.entries(summary.contrasts).sort((a, b) => a[1].p - b[1].p);
for (const [k, [method, stats]] of ascending.entries()) {
  latest = Math.max(latest, Math.min(1, (ascending.length - k) * stats.p));
  assert(Math.abs(stats.holm_p - latest) < 1e-12);
  const gain = (counts.get(candidate) - counts.get(method)) / rows.length;
  assert(Math.abs(stats.gain - gain) < 1e-12);
  assert.equal(stats.pass, gain >= .01 && stats.ci95[0] > 0 && latest < .05);
}
assert.equal(summary.all_pass, Object.values(summary.contrasts).every(s => s.pass));
writeFileSync(join(resultDir, 'page-results.csv'), output.join('\n') + '\n');
console.log(`Verified ${rows.length} release labels, ${methods.length} method counts, 18 decoded decisions per row and ${output.length - 1} page contrasts.`);
