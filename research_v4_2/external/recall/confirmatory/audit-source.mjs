import assert from 'node:assert/strict'
import { createHash } from 'node:crypto'
import { createReadStream } from 'node:fs'
import { readFile } from 'node:fs/promises'
import { join } from 'node:path'
import { createInterface } from 'node:readline'
import { createGunzip } from 'node:zlib'

const [archive, run] = process.argv.slice(2)
if (!archive || !run) throw new Error('Usage: node audit-source.mjs traces.csv.gz output_directory')
const load = async name => JSON.parse(await readFile(join(run, name), 'utf8'))
const lines = path => createInterface({ input: createReadStream(path).pipe(createGunzip()), crlfDelay: Infinity })
const freeze = await load('freeze.json')
const result = await load('result.json')
const additional = process.argv.includes('--reference') ? await load('reference_freeze.json') : null
const checks = ['leitner', 'pimsleur', 'smoothed_history']
const clip = (p, lo, hi) => Math.max(lo, Math.min(hi, p))
const calibrate = (p, [a, b]) => 1 / (1 + Math.exp(-(a + b * Math.log(p / (1 - p)))))
const users = new Map()
const counts = Array(100).fill(0)
let header = true
for await (const line of lines(archive)) {
  if (header) {
    assert.equal(line, 'p_recall,timestamp,delta,user_id,learning_language,ui_language,lexeme_id,lexeme_string,history_seen,history_correct,session_seen,session_correct')
    header = false
    continue
  }
  // The ID precedes all lexeme columns. Read the two integer counts from the row end.
  const fields = line.split(',')
  const id = fields[3]
  let user = users.get(id)
  if (!user) {
    assert.match(id, /^u:[a-zA-Z0-9_-]+$/)
    const bucket = createHash('sha256').update(id).digest().readUInt32BE(0) % 100
    user = { bucket, rows: 0, correctFraction: 0 }
    users.set(id, user)
  }
  if (user.bucket < 10 || user.bucket > 17) continue
  const correct = Number(fields.at(-1))
  const seen = Number(fields.at(-2))
  assert.ok(Number.isInteger(seen) && Number.isInteger(correct) && seen > 0 && correct >= 0 && correct <= seen)
  user.rows++
  const outcome = correct / seen
  user.correctFraction += outcome
  if (additional && user.bucket >= 14) {
    const elapsed = Number(fields[2]) / 86400
    const right = Number(fields.at(-3))
    const total = Number(fields.at(-4))
    const forget = logHalfLife => clip(2 ** (-elapsed / clip(2 ** logHalfLife, 15 / 1440, 274)), .0001, .9999)
    const raw = [forget(2 * right - total), forget(2.35 * total - 16.46), (right + 2) / (total + 4)]
    user.losses ??= Array(3).fill(0)
    for (const [i, name] of checks.entries()) {
      const pred = clip(calibrate(clip(raw[i], 1e-8, 1 - 1e-8), additional.selected[name].coefs), 1e-8, 1 - 1e-8)
      user.losses[i] -= outcome * Math.log(pred) + (1 - outcome) * Math.log1p(-pred)
    }
  }
  counts[user.bucket]++
}

const selected = (lo, hi) => [...users.values()].filter(u => u.bucket >= lo && u.bucket <= hi)
const stages = [[10, 11, freeze.partitions.train], [12, 12, freeze.partitions.calibration],
  [13, 13, freeze.partitions.development], [14, 17, result.partition]]
for (const [lo, hi, summary] of stages) {
  assert.equal(selected(lo, hi).length, summary.learners)
  assert.equal(counts.slice(lo, hi + 1).reduce((a, b) => a + b, 0), summary.rows)
}
const train = selected(10, 11)
const raw = train.reduce((total, u) => total + u.correctFraction / u.rows, 0) / train.length
const [intercept, slope] = freeze.selected.constant.calibration
const p = 1 / (1 + Math.exp(-(intercept + slope * Math.log(raw / (1 - raw)))))
const test = [...users.entries()].filter(([, u]) => u.bucket >= 14 && u.bucket <= 17)
  .sort(([a, x], [b, y]) => x.bucket - y.bucket || (a < b ? -1 : 1))
const ordinals = new Map()
let index = 0
let cols
for await (const line of lines(join(run, 'learner_losses.csv.gz'))) {
  if (!cols) {
    cols = line.split(',')
    continue
  }
  const fields = line.split(',')
  const value = name => Number(fields[cols.indexOf(name)])
  const [, user] = test[index++]
  const ordinal = ordinals.get(user.bucket) ?? 0
  assert.equal(value('bucket'), user.bucket)
  assert.equal(value('learner_ordinal'), ordinal)
  ordinals.set(user.bucket, ordinal + 1)
  const fraction = user.correctFraction / user.rows
  const nll = -fraction * Math.log(p) - (1 - fraction) * Math.log1p(-p)
  assert.ok(Math.abs(nll - value('constant')) < 1e-10, 'Reference forecast or learner target differs')
}
assert.equal(index, test.length)
console.log(`Source audit passed for ${index} held-out learners across ${result.partition.rows} practice rows.`)

if (additional) {
  let header
  let index = 0
  const artifact = 'reference_learner_losses.csv.gz'
  for await (const line of lines(join(run, artifact))) {
    if (!header) {
      header = line.split(',')
      continue
    }
    const fields = line.split(',')
    const [, user] = test[index++]
    assert.equal(Number(fields[header.indexOf('bucket')]), user.bucket)
    checks.forEach((name, i) => {
      const expected = user.losses[i] / user.rows
      assert.ok(Math.abs(expected - Number(fields[header.indexOf(name)])) < 1e-10, name)
    })
  }
  assert.equal(index, test.length)
  console.log(`Reference equations agree for all ${index} learners.`)
}
