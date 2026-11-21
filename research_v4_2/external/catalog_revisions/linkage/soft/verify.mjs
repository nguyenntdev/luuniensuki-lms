import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {join} from 'node:path';

const [raw, run] = process.argv.slice(2);
const summary = JSON.parse(readFileSync(join(run, 'summary.json')));
const hash = text => createHash('sha256').update(text).digest('hex');
const lines = file => readFileSync(file, 'utf8').trimEnd().split(/\r?\n/);
for (const [name, result] of Object.entries(summary)) {
  const source = lines(join(raw, name + '-valid.txt')).map(line => line.split('\t'));
  const [header,...data] = lines(join(run, name + '.csv'));
  const names = header.split(',');
  const rows = data.map(line => Object.fromEntries(line.split(',').map((v, i) => [names[i], v])));
  assert.equal(source.length, result.validation);
  assert.equal(rows.length, source.length);
  for (const [i,row] of rows.entries()) {
    const [left,right,target] = source[i];
    assert.deepEqual([row.id,row.left_hash,row.right_hash,row.label],
                     ['valid-'+i,hash(left),hash(right),target.trim()]);
  }
  for (const [method,metric] of Object.entries(result.models)) {
    let tp=0, fp=0, fn=0, tn=0, fixed=0, lost=0;
    for (const row of rows) {
      assert(['0','1'].includes(row[method]));
      const actual = row.label==='1', prediction = row[method]==='1';
      if (prediction && actual) tp++;
      else if (prediction) fp++;
      else if (actual) fn++;
      else tn++;
      if ('p_'+method in row) {
        const score = Number(row['p_'+method]);
        assert(Number.isFinite(score));
        assert.equal(prediction, score >= metric.threshold);
      }
      if (row.candidate!==row[method]) {
        if (row.candidate===row.label) fixed++; else lost++;
      }
    }
    assert.deepEqual([tp,fp,fn,tn], [metric.tp,metric.fp,metric.fn,metric.tn]);
    assert(Math.abs(metric.f1-2*tp/(2*tp+fp+fn))<1e-12);
    if (method!=='candidate') {
      const contrast = result.contrasts[method];
      assert.deepEqual([fixed,lost], [contrast.fixed,contrast.lost]);
      assert(Math.abs(result.models.candidate.f1-metric.f1-contrast.gain)<1e-12);
    }
  }
  const worst = Math.min(...Object.values(result.contrasts).map(v => v.gain));
  assert.equal(worst,result.smallest_gain);
  assert.equal(worst>=.01,result.passes_one_point);
  console.log(name, rows.length, 'pairs verified across', Object.keys(result.models).length, 'methods');
}
