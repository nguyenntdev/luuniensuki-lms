import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {readFileSync} from 'node:fs';
import {join} from 'node:path';
import {gunzipSync} from 'node:zlib';

const [archive, run] = process.argv.slice(2);
function source(name) {
    return execFileSync('unzip',['-p',archive,name+'.csv'],{encoding:'utf8',maxBuffer:32<<20})
        .trimEnd().split(/\r?\n/).slice(1).map(line => [...line.matchAll(/"([^"]*)"/g)].map(x => x[1]));
}
const key = r => r.slice(0,3).join('/');
const registration = new Map(source('studentRegistration').map(row => [key(row),row]));
const info = source('studentInfo').filter(r => {
    const start = registration.get(key(r))[3];
    return start !== '?' && Number(start) <= 60;
});
const future = new Set(info.filter(r => r[1]==='2014J').map(r => r[2]));
const all = info.filter(r => {
    const end = registration.get(key(r))[4];
    return (end==='?' || Number(end)>60) && (r[1]==='2014J' || !future.has(r[2]));
});
const people = new Map([...new Set(all.map(r => +r[2]))].sort((a,b)=>a-b).map((x,i)=>[x,i]));
const lines = gunzipSync(readFileSync(join(run,'predictions.csv.gz'))).toString().trimEnd().split('\n');
const methods = lines.shift().split(',').slice(5);
const groups = new Map();
for(const line of lines) {
    const [row,learner,course,term,target,...values] = line.split(',');
    const ref = all[+row];
    assert.equal(ref[0],course); assert.equal(ref[1],term); assert.equal(term,'2014J');
    assert.equal(people.get(+ref[2]),+learner); assert.equal(Number(ref.at(-1)==='Withdrawn'),+target);
    assert.equal(values.length,methods.length);
    if(!groups.has(course)) groups.set(course,[]);
    const p = values.map(Number); assert.ok(p.every(x=>x>0&&x<1));
    groups.get(course).push({y:+target,p,row:+row});
}
assert.equal(lines.length, all.filter(r=>r[1]==='2014J').length);
assert.equal(new Set([...groups.values()].flat().map(r=>r.row)).size,lines.length);
const stats = JSON.parse(readFileSync(join(run,'summary.json')));
for(const [j,name] of methods.entries()) {
    let total = 0;
    for(const rows of groups.values()) {
        const p = rows.filter(r=>r.y).map(r=>r.p[j]), n = rows.filter(r=>!r.y).map(r=>r.p[j]);
        let wins = 0;
        for(const x of p) for(const y of n) wins += x>y ? 1 : x===y ? .5 : 0;
        total += wins/(p.length*n.length);
    }
    assert.ok(Math.abs(total/groups.size-stats.macro_auc[name])<1e-12);
}
const expectedCounts = new Map();
for(const r of all) {
    const k = r.slice(0,2).join(',');
    if(!expectedCounts.has(k)) expectedCounts.set(k,[0,new Set(),0]);
    const v=expectedCounts.get(k);v[0]++;v[1].add(r[2]);v[2]+=Number(r.at(-1)==='Withdrawn');
}
const counts=readFileSync(join(run,'counts.csv'),'utf8').trimEnd().split('\n').slice(1);
assert.equal(counts.length,expectedCounts.size);
for(const line of counts) {
    const [course,term,split,n,learners,positive]=line.split(',');
    const [size,ids,cases]=expectedCounts.get(course+','+term);
    assert.deepEqual([size,ids.size,cases],[+n,+learners,+positive]);
    assert.equal(split,term==='2014J'?'dev':'train');
}
console.log(JSON.stringify({registrations:lines.length,forecasts:lines.length*methods.length,
    verified_course_periods:counts.length,verified_macro_auc:methods.length}));
