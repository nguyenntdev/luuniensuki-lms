/** Independent decoder for the Tate development wires. */
import assert from 'node:assert/strict'
import fs from 'node:fs'
import {execFileSync} from 'node:child_process'

const [basePath, wirePath, targetPath] = process.argv.slice(2)
const lines = path => fs.readFileSync(path,'utf8').trimEnd().split('\n').map(row => JSON.parse(row))
const [schema,...base] = lines(basePath)

const originals = new Map(base.map(([id,...values]) => [id, values]))
const data = new Map([...originals].map(([id,row]) => [id,[...row]]))
const [removed, inserted, columns] = JSON.parse(execFileSync('xz',['-dc',wirePath],{maxBuffer:512<<20}))
for (const id of removed) assert(data.delete(id))
const keys = [...data.keys()] // canonical file already in Python lexical order
const slug = s => s.normalize('NFKD').replace(/[^\x00-\x7F]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'')
const apply = (src, ops) => ops === null ? src : ops.map(op => typeof op === 'string' ? op : [...src].slice(op[0], op[0]+op[1]).join('')).join('')
const ungap = values => {
  let n=0
  return values.map((d,i) => {assert(Number.isSafeInteger(d) && d >= (i===0?0:1)); n+=d; return n})
}
function reference(key,j,selector) {
  const old = originals.get(key), row = data.get(key)
  if (selector===0) return ''
  if (selector===1) return old[j]
  const [mode, field, transform] = selector
  assert(Number.isInteger(field) && field>=0 && field<old.length)
  if (mode==='o') return old[field]
  assert(field<j)
  if (mode==='n') return row[field]
  assert.equal(mode,'r')
  const normalize = transform ? slug : x=>x
  return old[j].split(normalize(old[field])).join(normalize(row[field]))
}

function charClass(ch) {
  if (ch===undefined) return 0
  if (ch>='0' && ch<='9') return 1
  if (ch>='A' && ch<='Z') return 2
  if (ch>='a' && ch<='z') return 3
  return ch===' ' ? 4 : 5
}

function bucket(mode, chars, p) {
  if (mode==='row') return 0
  if (mode==='start') return p
  if (mode==='end') return chars.length-p
  const ch = p===chars.length ? 0 : chars[p].codePointAt(0)+1
  if (mode==='character') return ch
  assert.equal(mode,'context')
  return (ch*6+charClass(chars[p-1]))*6+charClass(chars[p+1])
}

function decodeEvents(j,op,explicitKeys) {
  const [,mask,selectors,mode,ranks,lengths,strings] = op
  const selected = explicitKeys??ungap(mask).map(i=>keys[i])
  assert.equal(selected.length,selectors.length)
  const sources = selected.map((key,n)=>[...reference(key,j,selectors[n])])
  const counts = new Map()
  for (const chars of sources) {
    for (let p=0;p<=chars.length;p++) {
      const key=bucket(mode,chars,p)
      counts.set(key,(counts.get(key)??0)+1)
    }
  }
  const cursor = new Map()
  let offset = 0
  for (const group of [...counts.keys()].sort((a,b)=>a-b)) {
    cursor.set(group,offset)
    offset+=counts.get(group)
  }
  assert.equal(ranks.length,lengths.length)
  assert.equal(ranks.length,strings.length)
  const changes=new Map(ungap(ranks).map((pos,i)=>[pos,i]))
  let used=0
  for (const [n,chars] of sources.entries()) {
    const parts=[]
    let copied=0
    for (let p=0;p<=chars.length;p++) {
      const group=bucket(mode,chars,p), index=cursor.get(group)
      cursor.set(group,index+1)
      if (!changes.has(index)) continue
      const i=changes.get(index)
      assert(p>=copied && Number.isInteger(lengths[i]) && lengths[i]>=0 && p+lengths[i]<=chars.length)
      parts.push(chars.slice(copied,p).join(''),strings[i])
      copied=p+lengths[i]
      used++
    }
    parts.push(chars.slice(copied).join(''))
    data.get(selected[n])[j]=parts.join('')
  }
  assert.equal(used,changes.size)
}

function legacyValue(key,j,code) {
  if (typeof code === 'string') return code
  const selector = code[0]==='e' ? 1 : code.slice(0,-1)
  return apply(reference(key,j,selector),code.at(-1))
}

function transfer(x, a, b) {
  const before=[...a], after=[...b]
  const end=Math.min(before.length,after.length)
  let lo=0, tail=0
  while (lo<end && before[lo]===after[lo]) lo++
  while (tail<end-lo && before.at(-1-tail)===after.at(-1-tail)) tail++
  const src=before.slice(lo,before.length-tail).join('')
  const dst=after.slice(lo,after.length-tail).join('')
  if (src && x.includes(src)) return x.split(src).join(dst)
  if (!src && !lo) return dst+x
  if (!src && !tail) return x+dst
  throw Error('inapplicable donor')
}

function batch(j,op) {
  const [,ordering,mask,marks,detail]=op
  const ranked=keys.map(key=>[key,ordering===-1?null:Buffer.from(originals.get(key)[ordering])])
  if (ordering!==-1) ranked.sort((a,b)=>Buffer.compare(a[1],b[1]))
  const chosen=ungap(mask).map(i=>ranked[i][0])
  if (marks!==0) assert.equal(marks.length,chosen.length)
  const anchors=chosen.filter((key,i)=>marks===0 || !marks[i])
  if (detail[0]==='codes') {
    assert.equal(anchors.length,detail[1].length)
    anchors.forEach((key,i)=>{data.get(key)[j]=legacyValue(key,j,detail[1][i])})
  } else {
    assert.equal(detail[0],'events')
    decodeEvents(j,['events',[],...detail.slice(1)],anchors)
  }
  const history=new Map()
  let previous
  for (const [i,key] of chosen.entries()) {
    const x=originals.get(key)[j], row=data.get(key)
    switch (marks===0?0:marks[i]) {
      case 0: break
      case 1: row[j]=previous[1];break
      case 2: assert(history.has(x));row[j]=history.get(x);break
      case 3: row[j]=transfer(x,...previous);break
      default: throw Error('bad donor')
    }
    previous=[x,row[j]]
    history.set(x,row[j])
  }
}

for (const [j,op] of columns) {
  if (op[0]==='batch') {batch(j,op);continue}
  if (op[0]==='events') {decodeEvents(j,op);continue}
  assert(['legacy','plain'].includes(op[0]))
  const [rules, deltas, instructions] = op[0]==='legacy' ? op.slice(1) : [[], ...op.slice(1)]
  const claimed=new Set()
  for (const [kind,src,dst,mode,positions] of rules) {
    const eligible=[]
    for (const [index,key] of keys.entries()) {
      if (claimed.has(index)) continue
      const x=originals.get(key)[j]
      let value
      if (kind==='whole' && x===src) value=dst
      else if (kind==='start' && x.startsWith(src)) value=dst+x.slice(src.length)
      else if (kind==='end' && x.endsWith(src)) value=x.slice(0,x.length-src.length)+dst
      else if (kind==='sub' && src && x.includes(src)) value=x.split(src).join(dst)
      if (value!==undefined && x!==value) eligible.push([index,value])
    }
    const selector=new Set(ungap(positions))
    let used=0
    for (const [rank,[index,value]] of eligible.entries()) {
      assert(['a','i','x'].includes(mode))
      const hit=selector.has(mode==='a'?index:rank)
      if (hit) used++
      if (mode==='x' ? hit : !hit) continue
      data.get(keys[index])[j]=value
      claimed.add(index)
    }
    assert.equal(used,selector.size)
  }
  let i=0
  assert.equal(deltas.length, instructions.length)
  for (let w=0; w<deltas.length; w++) {
    i+=deltas[w]
    assert(!claimed.has(i))
    const k=keys[i], old=originals.get(k), row=data.get(k), code=instructions[w]
    row[j]=legacyValue(k,j,code)
  }
}
for (const [id,row] of inserted) {assert(!data.has(id)); data.set(id,row)}
const [nextSchema,...target] = lines(targetPath)
assert.deepEqual(schema,nextSchema)
assert.equal(data.size,target.length)
for (const [id,...row] of target) assert.deepEqual(data.get(id),row)
console.log('Verified',target.length,'rows')
