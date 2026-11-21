import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {join} from 'node:path';

const [raw,out] = process.argv.slice(2);
const fields = ['title','authors','venue','year'];
const hash = s => createHash('sha256').update(s).digest('hex');
const tokens = s => new Set(s.normalize('NFKD').toLowerCase().match(/[\p{L}\p{N}]+/gu) || []);
function record(s) {
  const markers=[...s.matchAll(/\bCOL (title|authors|venue|year) VAL\b/g)];
  if (markers.length !== 4 || !markers.every((m,i)=>m[1]===fields[i])) throw Error('Unexpected field markers');
  const sets=markers.map((m,i)=>tokens(s.slice(m.index+m[0].length,markers[i+1]?.index ?? s.length)));
  return {sets, all:new Set(sets.flatMap(t=>[...t]))};
}
for (const dataset of ['DBLP-ACM','DBLP-GoogleScholar']) {
  const rows=[];
  const docs=new Map();
  for (const split of ['train','valid']) {
    const lines=readFileSync(join(raw,dataset+'-'+split+'.txt'),'utf8').trimEnd().split(/\r?\n/);
    for (const [i,line] of lines.entries()) {
      const [a,b,gold]=line.split('\t');
      if (!['0','1'].includes(gold.trim())) throw Error('Invalid label');
      const role=split==='valid'?'validation':parseInt(hash(a+'\t'+b).slice(0,8),16)%5===0?'calibration':'fit';
      for (const text of [a,b]) if (!docs.has(text)) docs.set(text,record(text));
      rows.push({a,b,y:Number(gold),role,id:split+'-'+i});
    }
  }
  const texts=new Set(rows.filter(r=>r.role==='fit').flatMap(r=>[r.a,r.b]));
  const df=new Map();
  for (const text of texts) for (const t of docs.get(text).all) df.set(t,(df.get(t)||0)+1);
  const maxWeight=1+Math.log(1+texts.size);
  const weight=t=>maxWeight-Math.log(1+(df.get(t)||0));
  function similarity(a,b) {
    let overlap=0,wa=0,wb=0;
    for (const t of a) {const w=weight(t);wa+=w;if (b.has(t)) overlap+=w;}
    for (const t of b) wb+=weight(t);
    return [overlap/(wa||1),overlap/(wb||1),overlap/(wa+wb-overlap||1),Math.log1p(wa),Math.log1p(wb)];
  }
  const packed=rows.map(({a,b,y,role,id})=>{
    const left=docs.get(a),right=docs.get(b);
    const flat=similarity(left.all,right.all), same=[],cross=[],pooled=[];
    for (let i=0;i<4;++i) {
      same.push(...similarity(left.sets[i],right.sets[i]));
      pooled.push(...similarity(left.sets[i],right.all),...similarity(left.all,right.sets[i]));
      for (let j=0;j<4;++j) if (i!==j) cross.push(...similarity(left.sets[i],right.sets[j]));
    }
    return [id,role,y,hash(a),hash(b),...flat,...same,...cross,...pooled].join(',');
  });
  writeFileSync(join(out,dataset+'.csv'),packed.join('\n')+'\n');
}
