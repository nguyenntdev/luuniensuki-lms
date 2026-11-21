/** Independent decoder for the Tate development wires. */
import assert from 'node:assert/strict'
import fs from 'node:fs'
import {execFileSync} from 'node:child_process'

const [basePath, wirePath, targetPath] = process.argv.slice(2)
const lines = path => fs.readFileSync(path,'utf8').trimEnd().split('\n').map(row => JSON.parse(row))
const [schema,...base] = lines(basePath)
const [nextSchema,...target] = lines(targetPath)
assert.deepEqual(schema, nextSchema)
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
for (const [j, rules, deltas, instructions] of columns) {
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
    if (typeof code === 'string') {row[j]=code; continue}
    const [mode, field, transform] = code
    let ref
    switch (mode) {
      case 'e': ref=old[j]; break
      case 'o': ref=old[field]; break
      case 'n': assert(field < j); ref=row[field]; break
      case 'r': {
        assert(field < j)
        const normalize = transform ? slug : s => s
        ref=old[j].split(normalize(old[field])).join(normalize(row[field])); break
      }
      default: throw Error(mode)
    }
    row[j]=apply(ref, code.at(-1))
  }
}
for (const [id,row] of inserted) {assert(!data.has(id)); data.set(id,row)}
assert.equal(data.size,target.length)
for (const [id,...row] of target) assert.deepEqual(data.get(id),row)
console.log('Verified',target.length,'rows')
