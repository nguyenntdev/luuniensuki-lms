import assert from "node:assert/strict";
import {execFileSync} from "node:child_process";
import {readFileSync} from "node:fs";
import {join,resolve} from "node:path";
import {fileURLToPath} from "node:url";
import {gunzipSync} from "node:zlib";

const [raw,output] = process.argv.slice(2);
const temporal = fileURLToPath(new URL("../temporal/",import.meta.url));
const source = JSON.parse(execFileSync(process.execPath,[join(temporal,"verify.mjs"),raw,join(temporal,"run")]));
function rows(path){
    const bytes=readFileSync(path);
    const text=(path.endsWith(".gz")?gunzipSync(bytes):bytes).toString().trimEnd();
    const [header,...lines]=text.split(/\r?\n/);
    const keys=header.split(",");
    return lines.map(line=>Object.fromEntries(line.split(",").map((s,i)=>[keys[i],s])));
}
const old=rows(join(temporal,"run/screen.csv.gz"));
const screen=rows(resolve(output,"screen.csv.gz"));
const learnerSums=rows(resolve(output,"learner_sums.csv"));
const result=JSON.parse(readFileSync(resolve(output,"result.json")));
const names=Object.keys(result.loss);
const groups=new Map();
const correct=Object.fromEntries(names.map(n=>[n,0]));
assert.equal(screen.length,old.length);
for(const [i,r] of screen.entries()){
    for(const n of ["uid","row","start","gap_s","y","sakt","blend_joint","clock"]){
        if(n==="uid") assert.equal(r.uid,old[i].uid);
        else assert(Math.abs(Number(r[n])-Number(old[i][n]))<1e-12);
    }
    if(!groups.has(r.uid)) groups.set(r.uid,{rows:0,...Object.fromEntries(names.map(n=>[n,0]))});
    const g=groups.get(r.uid); g.rows++;
    for(const n of names){
        const p=Number(r[n]),y=Number(r.y);
        assert(p>0 && p<1);
        g[n]-=y?Math.log(Math.max(1e-7,p)):Math.log1p(-Math.min(1-1e-7,p));
        correct[n]+=Number((p>=.5)===Boolean(y));
    }
}
assert.equal(groups.size,result.learners);
assert.equal(groups.size,learnerSums.length);
for(const r of learnerSums){
    const g=groups.get(r.uid);
    assert(g);
    for(const n of ["rows",...names]) assert(Math.abs(g[n]-Number(r[n]))<1e-9);
    groups.delete(r.uid);
}
assert.equal(groups.size,0);
for(const n of names){
    const mean=learnerSums.reduce((v,r)=>v+Number(r[n]),0)/screen.length;
    assert(Math.abs(mean-result.loss[n])<1e-12);
    assert.equal(correct[n],result.correct[n]);
    if(n!=="blend_joint") assert(Math.abs((mean-result.loss.blend_joint)-result.contrasts[n].gain)<1e-12);
}
console.log(JSON.stringify({source_labels:source.source_labels,learner_groups:result.learners,forecasts:screen.length*names.length,checked_hard_decisions:screen.length*names.length}));
