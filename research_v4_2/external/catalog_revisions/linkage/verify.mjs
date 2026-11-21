import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {join} from 'node:path';
const [raw,run]=process.argv.slice(2);
const result=JSON.parse(readFileSync(join(run,'summary.json')));
for (const [name,study] of Object.entries(result)) {
  const source=readFileSync(join(raw,name+'-valid.txt'),'utf8').trimEnd().split(/\r?\n/);
  const [header,...rows]=readFileSync(join(run,name+'.csv'),'utf8').trimEnd().split(/\r?\n/);
  assert.equal(rows.length,source.length);
  const params=header.split(',');
  for (const [method,saved] of Object.entries(study.models)) {
    let tp=0,fp=0,fn=0;
    for(const [i,row] of rows.entries()) {
      const values=row.split(',');
      const actual=Number(source[i].split('\t')[2]);
      assert.equal(Number(values[1]),actual);
      assert.equal(values[0],'valid-'+i);
      const predicted=Number(values[params.indexOf(method)]);
      assert([0,1].includes(predicted));
      if(actual&&predicted) tp++; else if(predicted) fp++; else if(actual) fn++;
    }
    assert(Math.abs(saved.f1-2*tp/(2*tp+fp+fn))<1e-12);
  }
  console.log(name, source.length, 'all F1 scores verified');
}
