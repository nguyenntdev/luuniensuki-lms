/** Decode a sparse column patch before looking at the expected target. */
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import assert from 'node:assert/strict';

const [baseFile, wire, expectedFile, xdelta] = process.argv.slice(2);
const readTable = file => fs.readFileSync(file,'utf8').trimEnd().split('\n').map(JSON.parse);
const [baseHeader, ...base] = readTable(baseFile);
const [newLayout, removed, inserted, columns] = JSON.parse(execFileSync('xz',['-dc',wire],{maxBuffer:512<<20}));
const values = new Map(base.map(([id,...row])=>[id,row]));
for (const id of removed) assert(values.delete(id));
for (const id of inserted) {assert(!values.has(id)); values.set(id,[]);}
const compare = (a,b)=>Buffer.compare(Buffer.from(a),Buffer.from(b));
const keys=[...values.keys()].sort(compare);
const schema=newLayout ?? baseHeader;
assert.equal(schema[0],baseHeader[0]);
const remap=schema.slice(1).map(name=>baseHeader.indexOf(name)-1);
const old=keys.map(id=>remap.map(j=>values.get(id)[j] ?? ''));
const next=old.map(row=>row.slice());
const orders=new Map();
function order(j){
  if(!orders.has(j)){
    const indices=Array.from(keys.keys());
    if(j!==-1){
      assert(j>=0 && j<schema.length-1);
      const tokens=old.map(row=>Buffer.from(row[j]));
      indices.sort((a,b)=>Buffer.compare(tokens[a],tokens[b]));
    }
    orders.set(j,indices);
  }
  return orders.get(j);
}
function binary(input){
  const chunks=[];
  for(const word of input){
    const data=Buffer.from(word);
    for(let i=0;i<data.length;i++) if(data[i]===0) data[i]=255;
    chunks.push(data,Buffer.from([0]));
  }
  return Buffer.concat(chunks);
}
function substitutions(base,b,a){
  if(b===a) return [];
  const x=Array.from(b), y=Array.from(a);
  let i=0,t=0;
  while(i<Math.min(x.length,y.length) && x[i]===y[i]) i++;
  while(t<Math.min(x.length,y.length)-i && x.at(-t-1)===y.at(-t-1)) t++;
  const output=[];
  for(const k of [0,2]){
    const start=Math.max(0,i-k), trim=Math.max(0,t-k);
    const src=x.slice(start,x.length-trim).join('');
    if(src && base.includes(src)) output.push(base.split(src).join(y.slice(start,y.length-trim).join('')));
  }
  return output;
}
function source(kind,rs,j){
  if(kind==='own') return binary(rs.map(i=>old[i][j]));
  if(kind==='all') return binary([...new Set(old.map(r=>r[j]))].sort(compare));
  assert.equal(kind,'relation');
  const entries=[];
  for(const i of rs){
    const context=[old[i][j]];
    for(let k=0;k<j;k++){
      if(old[i][k]!==next[i][k]) context.push(...substitutions(old[i][j],old[i][k],next[i][k]),next[i][k]);
    }
    entries.push(...new Set(context.concat(old[i])));
  }
  return binary(entries);
}
const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'catalog-conditional-'));
try{
  const masks=new Map();
  for(const [j,[maskOrder,previous,packed],[valueOrder,kind,body]] of columns){
    const current=new Set(masks.get(previous) ?? []);
    const positions=order(maskOrder);
    let rank=0,n=0,factor=1;
    for(const b of Buffer.from(packed,'base64')){
      n+=(b & 127)*factor;
      if(b>=128) {factor*=128;continue;}
      rank+=n;
      assert(rank<positions.length);
      const row=positions[rank];
      if(current.has(row)) current.delete(row);else current.add(row);
      n=0;factor=1;
    }
    assert.equal(factor,1);
    masks.set(j,current);
    const rs=order(valueOrder).filter(i=>current.has(i));
    let decoded=body;
    if(kind!=='literal'){
      const p=path.join(tmp,'source');
      fs.writeFileSync(p,source(kind,rs,j));
      const bytes=execFileSync(xdelta,['-d','-c','-s',p],{input:Buffer.from(body,'base64'),maxBuffer:512<<20});
      decoded=[];
      let start=0;
      for(let k=0;k<bytes.length;k++){
        if(bytes[k]===255) {bytes[k]=0;continue;}
        if(bytes[k]===0){decoded.push(bytes.toString('utf8',start,k));start=k+1;}
      }
      assert.equal(start,bytes.length);
    }
    assert.equal(decoded.length,rs.length);
    for(let k=0;k<rs.length;k++) next[rs[k]][j]=decoded[k];
  }
  const [targetHeader,...target]=readTable(expectedFile);
  assert.deepEqual(schema,targetHeader);
  assert.equal(target.length,next.length);
  for(let i=0;i<keys.length;i++) assert.deepEqual([keys[i],...next[i]],target[i]);
  console.log('Decoded and checked',keys.length,'rows');
}finally{fs.rmSync(tmp,{recursive:true,force:true});}
