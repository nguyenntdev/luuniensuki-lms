import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const dir = process.argv[2];
const reported = JSON.parse(fs.readFileSync(path.join(dir,'result.json'),'utf8'));
const [header,...lines] = fs.readFileSync(path.join(dir,'rankings.csv'),'utf8').trim().split(/\r?\n/);
const fields = header.split(',');
const records = lines.map(line => Object.fromEntries(line.split(',').map((v,i) => [fields[i],Number(v)])));
assert.equal(records.length, reported.training_sheet_rows);
assert.equal(new Set(records.map(r=>r.row)).size, records.length);
assert.equal(records.reduce((s,r)=>s+r.error,0), reported.errors);
const signs = {};
let floor = 0;
for (let f=0; f<5; ++f) {
  const rows = records.filter(r=>r.fold===f);
  const aurc = ordered => {
    let errors=0;
    return ordered.reduce((sum,r,i)=>sum+(errors+=r.error)/(i+1),0)/ordered.length;
  };
  floor += aurc(rows.toSorted((a,b)=>a.error-b.error))/5;
  for (const name of Object.keys(reported.mean_aurc)) {
    const value = aurc(rows.toSorted((a,b)=>b[name]-a[name] || a.row-b.row));
    assert.ok(Math.abs(value-reported.folds[f][name])<1e-12);
    if (name!=='blend') (signs[name]??=[]).push(Math.sign(value-reported.folds[f].blend));
  }
}
console.log(JSON.stringify({oracle_aurc:floor,fold_signs:signs},null,2));
