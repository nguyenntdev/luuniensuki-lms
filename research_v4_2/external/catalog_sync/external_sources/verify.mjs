// Independently audit source pins, LFS pointers, content digests and the inventory shape.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {createReadStream} from 'node:fs';
import {readFile, stat} from 'node:fs/promises';
import {join} from 'node:path';
import {fileURLToPath} from 'node:url';

const root = fileURLToPath(new URL('.', import.meta.url));
const [cache] = process.argv.slice(2);
assert(cache, 'Pass the raw release cache');
const pins = JSON.parse(await readFile(join(root, 'revisions.json')));
const results = JSON.parse(await readFile(join(root, 'inventory.json')));
assert.equal(results.length, 12);
assert.equal(pins.length, results.length);
const keys = new Set();
const providers = new Map();
for (const [i, entry] of pins.entries()) {
  const row = results[i];
  const name = entry.provider + '/' + entry.cutoff;
  assert(!keys.has(name));
  keys.add(name);
  assert.equal(row.provider, entry.provider);
  assert.equal(row.cutoff, entry.cutoff);
  assert.match(entry.commit, /^[0-9a-f]{40}$/);
  assert(new Date(entry.date) <= new Date(entry.cutoff + 'T00:00:00Z'));
  const dates = providers.get(entry.provider) || [];
  dates.push(entry.cutoff);
  providers.set(entry.provider, dates);
  const path = join(cache, name+'.csv');
  const size = (await stat(path)).size;
  assert.equal(size, row.bytes);
  const sha256 = createHash('sha256');
  const git = createHash('sha1').update('blob ' + size + '\0');
  for await (const chunk of createReadStream(path)) {
    sha256.update(chunk);
    git.update(chunk);
  }
  assert.equal(sha256.digest('hex'), row.sha256);
  if (row.git_lfs) {
    const pointer = await readFile(join(cache, name+'.pointer'));
    const expected = 'version https://git-lfs.github.com/spec/v1\noid sha256:' + row.sha256 + '\nsize ' + size;
    assert.equal(pointer.toString().trimEnd(), expected);
    assert.equal(createHash('sha1').update('blob ' + pointer.length + '\0').update(pointer).digest('hex'), entry.blob);
  } else {
    assert.equal(git.digest('hex'), entry.blob);
  }
  assert.equal(new Set(row.header).size, row.header.length);
  assert(row.header.includes(entry.key));
  assert.equal(row.unique_ids, row.records);
  assert(row.records > 0);
}
assert.deepEqual([...providers.keys()].sort(), ['cleveland', 'moma', 'nga']);
for (const dates of providers.values()) assert.deepEqual(dates, ['2026-01-01','2026-04-01','2026-07-01','2026-10-01']);
console.log('Verified 12 complete source digests, Git pins, and four cutoffs per publisher.');
