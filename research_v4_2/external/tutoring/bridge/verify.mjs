import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';

const [run, indoml, dev, held] = process.argv.slice(2);
const json = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const text = value => value.toLowerCase().trim().replace(/\s+/gu, ' ');
const devCases = json(dev);
const testCases = json(held);
for (const [name, reference, expected] of [
  ['trainset', devCases, 300], ['dev_testset', testCases, 41], ['testset', testCases, 150],
]) {
  const data = json(path.join(indoml, name + '.json'));
  const histories = new Set(reference.map(r => text(r.conversation_history)));
  assert.equal(data.length, expected);
  assert(data.every(r => histories.has(text(r.conversation_history))));
  const annotated = data.filter(r => Object.values(r.tutor_responses).some(v => v.annotation)).length;
  assert.equal(annotated, name === 'trainset' ? 300 : 0);
}
const result = json(path.join(run, 'result.json'));
assert.equal(Object.values(result.exclusions_in_priority_order).reduce((a,b) => a+b, 0), 482);
if (result.correct) {
  const [header,...body] = fs.readFileSync(path.join(run, 'decisions.csv'), 'utf8').trimEnd().split('\n');
  const keys = header.split(',');
  const rows = body.map(row => Object.fromEntries(row.split(',').map((v,i) => [keys[i],v])));
  assert.equal(new Set(rows.map(r=>r.group)).size, result.groups);
  assert.equal(new Set(rows.map(r=>r.archive_index)).size, rows.length);
  for (const [name,n] of Object.entries(result.correct)) {
    assert.equal(rows.reduce((sum,r)=>sum+Number(r[name]),0), n);
    if (name !== 'joint') assert(Math.abs((result.correct.joint-n)/rows.length-result.comparisons[name].gain)<1e-12);
  }
}
console.log('Verified source overlap, scoring denominator, counts and paired point differences.');
