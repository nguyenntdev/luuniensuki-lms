import assert from "node:assert/strict";
import {execFileSync} from "node:child_process";
import {createHash} from "node:crypto";
import {readFileSync} from "node:fs";
import {join} from "node:path";
import {gunzipSync,inflateRawSync} from "node:zlib";

const [raw,out] = process.argv.slice(2);
const result = JSON.parse(readFileSync(join(out,"result.json")));
const blob = readFileSync(join(raw,"KT1.prefix"));
const questions = execFileSync("unzip",["-p",join(raw,"contents.zip"),"contents/questions.csv"],{encoding:"utf8"}).trim().split(/\r?\n/);
const key = new Map(questions.slice(1).map(line => {const r=line.split(",");return [r[0],r[3]];}));
const expected = new Map();
const users = new Set();
let members=0;
for (let pos=0;pos+30<blob.length && members<2500;) {
  assert.equal(blob.readUInt32LE(pos),0x04034b50);
  const size=blob.readUInt32LE(pos+18), n=blob.readUInt16LE(pos+26), m=blob.readUInt16LE(pos+28);
  const name=blob.toString("utf8",pos+30,pos+30+n);
  const start=pos+30+n+m; pos=start+size;
  if (pos>blob.length) break;
  if (!name.endsWith(".csv")) continue;
  members++;
  const uid=name.split("/").at(-1).slice(0,-4);
  const bucket=createHash("sha256").update(uid).digest().readUInt32BE(0)%100;
  if (bucket<70 || bucket>=80) continue;
  const [header,...lines]=inflateRawSync(blob.subarray(start,pos)).toString("utf8").trim().split(/\r?\n/);
  const fields=header.split(",");
  const rows=lines.map((line,id)=> {
    const r=Object.fromEntries(line.split(",").map((v,i)=>[fields[i],v]));
    return {id,ts:Number(r.timestamp),end:Number(r.timestamp)+Number(r.elapsed_time),bundle:r.solving_id,
            y:Number(r.user_answer===key.get(r.question_id))};
  }).sort((a,b)=>a.ts-b.ts || a.id-b.id);
  const incomplete=new Set(rows.slice(160).map(r=>r.bundle));
  const groups=new Map();
  for (const row of rows.slice(0,160)) {
    if (incomplete.has(row.bundle)) continue;
    if (!groups.has(row.bundle)) groups.set(row.bundle,[]);
    groups.get(row.bundle).push(row);
  }
  for (const [bundle,group] of groups) {
    const now=Math.min(...group.map(r=>r.ts));
    const available=[...groups].filter(([b,g])=>b!==bundle && g.every(r=>r.end<now)).flatMap(([,g])=>g);
    if (!available.length) continue;
    const gap=(now-Math.max(...available.map(r=>r.ts)))/1000;
    for (const row of group) expected.set(uid+"_"+row.id,{y:row.y,start:now,gap});
    users.add(uid);
  }
}
assert.equal(members,2500);
const [header,...lines]=gunzipSync(readFileSync(join(out,"screen.csv.gz"))).toString("utf8").trim().split(/\r?\n/);
const fields=header.split(",");
const sums=Object.fromEntries(Object.keys(result.loss).map(n=>[n,0]));
for (const line of lines) {
  const values=line.split(","), r=Object.fromEntries(fields.map((n,i)=>[n,values[i]]));
  const id=r.uid+"_"+r.row;
  const truth=expected.get(id);
  assert(truth);
  assert.deepEqual([+r.y,+r.start,+r.gap_s],[truth.y,truth.start,truth.gap]);
  expected.delete(id);
  for (const n in sums) {
    const p=+r[n]; assert(p>=0 && p<=1);
    const prob=Math.max(1e-7,Math.min(1-1e-7,p));
    sums[n]-=truth.y?Math.log(prob):Math.log1p(-prob);
  }
  for (const [n,w] of Object.entries(result.weights)) {
    assert(Math.abs(+r["blend_"+n]-(w*r.sakt+(1-w)*r[n]))<1e-12);
  }
}
assert.equal(expected.size,0);
assert.equal(result.screen.learners,users.size);
assert.equal(result.screen.events,lines.length);
for (const n in sums) assert(Math.abs(sums[n]/lines.length-result.loss[n])<1e-10);
const flags=Object.entries(result.contrasts).map(([n,c])=>{
  assert(Math.abs((sums[n]-sums.blend_joint)/lines.length-c.gain)<1e-10);
  return c.gain>.015 && c.ci[0]>0;
});
assert.equal(flags.every(Boolean),result.advance);
console.log(JSON.stringify({archive_members:members,screen_learners:users.size,source_labels:lines.length,
  event_forecasts:lines.length*Object.keys(sums).length,passing:flags.filter(Boolean).length,comparisons:flags.length}));
