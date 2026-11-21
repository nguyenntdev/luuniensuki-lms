// Reconstruct every expected item loss by ordered sequential draws without replacement.
import {readFileSync} from "node:fs";
import {createHash} from "node:crypto";
import {join} from "node:path";
import assert from "node:assert/strict";

const [raw, out] = process.argv.slice(2);
const hash = text => createHash("sha256").update(text).digest("hex");
const group = row => hash(row.example.premise.toLowerCase().trim().split(/\s+/u).join(" "));
const corpora = ["snli", "mnli_m"];
const rows = corpora.map(name => readFileSync(join(raw, "chaosNLI_"+name+".jsonl"), "utf8").trim().split("\n").map(s=>JSON.parse(s)));
const groups = rows.map(items=>new Set(items.map(group)));
const classes=["entailment","neutral","contradiction"];
function index(counts) {
  let idx = 0;
  const n=counts.reduce((a,b)=>a+b);
  for(let i=0;i<counts[0];i++) idx += n-i+1;
  return idx+counts[1];
}
for(const [c,name] of corpora.entries()){
  const dir=join(out,name), forecasts=JSON.parse(readFileSync(join(dir,"forecasts.json")));
  const [header,...lines]=readFileSync(join(dir,"items.csv"),"utf8").trim().split("\n");
  const models=header.split(",").slice(2);
  const scored=new Map(lines.map(line=>{const [uid,g,...n]=line.split(",");return [uid,[g,n.map(Number)]];}));
  let checked=0;
  for(const row of rows[c]){
    const g=group(row);
    if(BigInt("0x"+g)%5n!==0n || groups[1-c].has(g) || row.old_labels.length!==5 || row.old_labels.some(v=>!classes.includes(v))) continue;
    const [savedGroup,saved]=scored.get(row.uid);
    assert.equal(savedGroup,g);
    const old=index(classes.map(k=>row.old_labels.filter(v=>v===k).length));
    const losses=models.map(()=>0);
    const counts=[0,0,0];
    function draw(depth,weight){
      if(depth===4){
        const visible=index(counts);
        for(const [j,m] of models.entries()) for(let k=0;k<3;k++)
          losses[j]-=weight*(row.label_count[k]-counts[k])/96*Math.log(forecasts[m][old][visible][k]);
        return;
      }
      for(let k=0;k<3;k++){
        const left=row.label_count[k]-counts[k];
        if(left===0)continue;
        counts[k]++;draw(depth+1,weight*left/(100-depth));counts[k]--;
      }
    }
    draw(0,1);
    for(let j=0;j<models.length;j++) assert.ok(Math.abs(saved[j]-losses[j])<1e-11);
    checked++;
  }
  assert.equal(checked,scored.size);
  console.log(name,checked,"test items and all forecast losses verified");
}
