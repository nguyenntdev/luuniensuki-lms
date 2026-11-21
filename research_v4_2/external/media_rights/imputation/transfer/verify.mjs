/** Independently check training IDs, observed declarations and temporal transitions. */
import assert from "node:assert/strict";
import {createHash} from "node:crypto";
import {readFileSync, writeFileSync} from "node:fs";
import {join} from "node:path";
import {gunzipSync} from "node:zlib";

const [raw, receiptPath, pendingPath, aliasOutput] = process.argv.slice(2);
const aliases = new Map();
const receipt = JSON.parse(readFileSync(receiptPath));
const sha = (bytes) => createHash("sha256").update(bytes).digest("hex");
const snapshots = [];
for (const [commit, expected] of Object.entries(receipt.archives)) {
  const bytes = readFileSync(join(raw, commit + ".tar.gz"));
  assert.equal(sha(bytes), expected);
  const archive = gunzipSync(bytes);
  const labels = new Map();
  let invalid = 0;
  for (let off = 0; off + 512 <= archive.length;) {
    const hdr = archive.subarray(off, off + 512);
    if (!hdr[0]) break;
    const name = hdr.toString("utf8", 0, 100).split("\0")[0];
    const size = parseInt(hdr.toString("ascii", 124, 136).replace(/\0/g,"").trim(), 8);
    assert(Number.isSafeInteger(size));
    const data = off + 512;
    off = data + 512 * Math.ceil(size / 512);
    const m = name.match(/^collection-([a-f0-9]{40})\/objects\/(\d+)\/(\d+)\.json$/);
    if (!m) continue;
    assert.equal(m[1], commit);
    const id = Number(m[3]);
    if ([1, 17].includes(id) || parseInt(sha(String(id)).slice(0, 12),16) % 100 >= 60) continue;
    if (Number(m[2]) !== Math.floor(id / 1000)) {
      invalid++;
      if (snapshots.length === 1) {
        let alias;
        try { alias = JSON.parse(archive.toString("utf8",data,data+size)); } catch { continue; }
        if (String(alias?.id).split("/").pop() === String(id)) {
          if (!aliases.has(id)) aliases.set(id,new Set());
          aliases.get(id).add((alias.rights_type || "").trim());
        }
      }
      continue;
    }
    let obj;
    try {
      obj = JSON.parse(archive.toString("utf8",data,data+size));
    } catch {
      invalid++;
      continue;
    }
    if (!obj || typeof obj !== "object" || !("id" in obj)) {
      invalid++;
      continue;
    }
    if (String(obj.id).split("/").pop() !== String(id)) { invalid++; continue; }
    assert(!labels.has(id));
    labels.set(id,(obj.rights_type || "").trim());
  }
  assert.equal(invalid, Object.values(receipt.excluded_training_files[commit]).reduce((a,b)=>a+b,0));
  snapshots.push(labels);
}
const [old, later] = snapshots;
const r = receipt.training;
assert.equal(old.size,r.early_train_objects);
assert.equal(later.size,r.late_train_objects);
const transitions = {}, filled = {}, classes = {};
function incr(counter, key) {counter[key] = (counter[key] ?? 0) + 1;}
for (const [id,l] of old) {
  const n = later.get(id);
  incr(classes,l);
  if (!l && n) incr(filled,n);
  const k = n === undefined ? "no_valid_later_record" : l === "" ? (n ? "filled" : "still_blank") :
    n === "" ? "lost_label" : n === l ? "same" : "revised";
  incr(transitions,k);
}
assert.deepEqual(classes,r.early_label_counts);
assert.deepEqual(filled,r.later_labels_of_early_blank);
assert.deepEqual(transitions,r.transitions);
console.log("Verified both archive hashes, ID splits, class counts, and transition counts.");

if (pendingPath) {
  const pending = JSON.parse(readFileSync(pendingPath));
  const statuses = new Set(["Copyright Not Evaluated","Copyright Undetermined"]);
  const destinations = {}, outcomes = {}, resolvedDifferences = {};
  for (const [id, early] of old) {
    const canonical = later.get(id);
    const aliased = aliases.get(id);
    if ((!early || statuses.has(early)) && aliased && [...aliased].some(a => a !== canonical)) {
      incr(resolvedDifferences,early || "(blank)");
    }
    if (!statuses.has(early)) continue;
    if (canonical === undefined) incr(outcomes,"no_valid_later_record");
    else if (!canonical) incr(outcomes,"blank");
    else if (statuses.has(canonical)) incr(outcomes,"still_pending");
    else {
      incr(outcomes,canonical === "Public Domain" ? "public_domain" : "other_substantive");
      incr(destinations,canonical);
    }
  }
  assert.deepEqual(outcomes,pending.outcomes);
  assert.deepEqual(destinations,pending.final_declarations);
  if (aliasOutput) {
    let duplicates = 0, disagree = 0, substantiveConflict = 0;
    const earlyPendingDifferentNonblank = {};
    const unambiguousLaterPendingOutcomes = {};
    for (const [id, early] of old) {
      if (!statuses.has(early)) continue;
      const n = later.get(id);
      if (!n) { incr(unambiguousLaterPendingOutcomes,"no_canonical_label"); continue; }
      if (aliases.has(id) && [...aliases.get(id)].some(a => a && a !== n)) {
        incr(unambiguousLaterPendingOutcomes,"ambiguous"); continue;
      }
      incr(unambiguousLaterPendingOutcomes,statuses.has(n) ? "still_pending" :
        n === "Public Domain" ? "public_domain" : "other_substantive");
    }
    for (const [id,values] of aliases) {
      if (later.has(id)) {
        duplicates++;
        if ([...values].some(a => a !== later.get(id))) disagree++;
        if (later.get(id) && [...values].some(a => a && a !== later.get(id))) {
          substantiveConflict++;
          if (statuses.has(old.get(id))) incr(earlyPendingDifferentNonblank,old.get(id));
        }
      }
    }
    writeFileSync(aliasOutput,JSON.stringify({noncanonical_ids_with_matching_internal_id:aliases.size,
      also_in_canonical_export:duplicates, noncanonical_labels_conflict_with_canonical:disagree,
      conflicting_among_early_blank_or_pending:resolvedDifferences,
      different_nonblank_labels_on_both_paths:substantiveConflict,
      different_nonblank_labels_on_both_paths_among_early_pending:earlyPendingDifferentNonblank,
      early_pending_under_unambiguous_later_labels:unambiguousLaterPendingOutcomes},null,2)+"\n");
  }
  console.log("Verified explicit pending transition labels.");
}
