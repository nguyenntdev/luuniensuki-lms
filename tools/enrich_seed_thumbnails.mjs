#!/usr/bin/env node
/**
 * Enriches seed JSON files with `thumbnail_url` by scanning the `ban-duc-noi/` photo folder.
 *
 * Output URLs match what Nginx serves in production:
 *   /assets/ban-duc-noi/<URN_DIR>/<FILE>
 *
 * Usage:
 *   node tools/enrich_seed_thumbnails.mjs --seed-path data --image-path ban-duc-noi
 */

import fs from "node:fs/promises";
import path from "node:path";

const IMAGE_SLUG_ALIASES = new Map([
  [["chuong-dinh", "ngu-tinh"].join("|"), "moc-tinh-hoa-tinh-tho-tinh-kim-tinh-thuy-tinh"],
  // ban-duc-noi/NHAN DINH contains "HUƠU GIANG.jpg" but seed uses "Hương Giang".
  [["nhan-dinh", "huong-giang"].join("|"), "huou-giang"],
]);

const IMAGE_EXTENSIONS = new Set([".jpg", ".jpeg", ".png", ".webp", ".gif"]);
const COMPOSITE_NAME_SPLIT_RE = /\s*(?:,|;|\s+[\-–—]\s+)\s*/g;

function parseArgs(argv) {
  const args = {
    seedPath: "data",
    imagePath: "ban-duc-noi",
    dryRun: false,
  };

  for (let i = 2; i < argv.length; i += 1) {
    const raw = argv[i];
    if (!raw.startsWith("--")) continue;
    const [key, maybeValue] = raw.split("=", 2);
    const readValue = () => (maybeValue !== undefined ? maybeValue : argv[i + 1]);

    if (key === "--seed-path") {
      args.seedPath = readValue();
      if (maybeValue === undefined) i += 1;
    } else if (key === "--image-path") {
      args.imagePath = readValue();
      if (maybeValue === undefined) i += 1;
    } else if (key === "--dry-run") {
      args.dryRun = true;
    }
  }

  return args;
}

function slugify(value) {
  const normalized = value
    .trim()
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/g, "d");

  return normalized.replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}

function slugVariants(value) {
  const variants = [];
  const base = slugify(value);
  if (base) variants.push(base);

  const parts = value
    .split(COMPOSITE_NAME_SPLIT_RE)
    .map((p) => p.trim())
    .filter(Boolean);

  if (parts.length > 1) {
    const partSlugs = parts.map(slugify).filter(Boolean).sort();
    if (partSlugs.length > 1) variants.push(partSlugs.join("-"));
  }

  return [...new Set(variants)];
}

function encodeUrlPath(posixPath) {
  return posixPath
    .split("/")
    .map((seg) => encodeURIComponent(seg))
    .join("/");
}

async function walkFiles(rootDir) {
  const out = [];
  async function walk(current) {
    const entries = await fs.readdir(current, { withFileTypes: true });
    for (const entry of entries) {
      const full = path.join(current, entry.name);
      if (entry.isDirectory()) {
        await walk(full);
        continue;
      }
      if (!entry.isFile()) continue;
      out.push(full);
    }
  }
  await walk(rootDir);
  return out;
}

async function scanImages(imagePath) {
  const absImagePath = path.resolve(imagePath);
  const baseDirName = path.basename(absImagePath);
  const baseUrl = `/assets/${baseDirName}`.replace(/\/+$/g, "");

  let files;
  try {
    files = await walkFiles(absImagePath);
  } catch (err) {
    throw new Error(`Image path not found: ${imagePath}`);
  }

  /** @type {Map<string, string[]>} key -> urls[] */
  const candidates = new Map();

  for (const full of files.sort()) {
    const ext = path.extname(full).toLowerCase();
    if (!IMAGE_EXTENSIONS.has(ext)) continue;
    const rel = path.relative(absImagePath, full);
    const parts = rel.split(path.sep).filter(Boolean);
    if (parts.length < 2) continue;

    const urnDirName = parts[0];
    const urnSlug = slugify(urnDirName);
    const motifSlug = slugify(path.parse(full).name);
    const key = `${urnSlug}|${motifSlug}`;

    const relPosix = parts.join("/");
    const url = `${baseUrl}/${encodeUrlPath(relPosix)}`;
    if (!candidates.has(key)) candidates.set(key, []);
    candidates.get(key).push(url);
  }

  /** @type {Map<string, string>} */
  const imageMap = new Map();
  let duplicates = 0;
  for (const [key, urls] of candidates.entries()) {
    imageMap.set(key, urls[0]);
    if (urls.length > 1) duplicates += urls.length - 1;
  }

  return { imageMap, duplicates };
}

function levenshtein(a, b) {
  if (a === b) return 0;
  if (!a.length) return b.length;
  if (!b.length) return a.length;

  const v0 = new Array(b.length + 1).fill(0);
  const v1 = new Array(b.length + 1).fill(0);
  for (let i = 0; i <= b.length; i += 1) v0[i] = i;

  for (let i = 0; i < a.length; i += 1) {
    v1[0] = i + 1;
    for (let j = 0; j < b.length; j += 1) {
      const cost = a[i] === b[j] ? 0 : 1;
      v1[j + 1] = Math.min(v1[j] + 1, v0[j + 1] + 1, v0[j] + cost);
    }
    for (let j = 0; j <= b.length; j += 1) v0[j] = v1[j];
  }
  return v1[b.length];
}

function similarity(a, b) {
  const maxLen = Math.max(a.length, b.length);
  if (maxLen === 0) return 1;
  return 1 - levenshtein(a, b) / maxLen;
}

function resolveThumbnailUrl(imageMap, { urnSlug, nameVi }) {
  const targetSlug = slugify(nameVi);

  const aliasKey = `${urnSlug}|${targetSlug}`;
  const alias = IMAGE_SLUG_ALIASES.get(aliasKey);
  if (alias) {
    const url = imageMap.get(`${urnSlug}|${alias}`);
    if (url) return url;
  }

  for (const candidate of slugVariants(nameVi)) {
    const url = imageMap.get(`${urnSlug}|${candidate}`);
    if (url) return url;
  }

  // Fuzzy fallback: pick the closest match within this urn.
  const candidates = [];
  for (const key of imageMap.keys()) {
    const [u, motifSlug] = key.split("|");
    if (u === urnSlug) candidates.push(motifSlug);
  }

  let best = null;
  let bestScore = 0;
  let second = null;
  let secondScore = 0;
  for (const c of candidates) {
    const s = similarity(targetSlug, c);
    if (s > bestScore) {
      second = best;
      secondScore = bestScore;
      best = c;
      bestScore = s;
      continue;
    }
    if (s > secondScore) {
      second = c;
      secondScore = s;
    }
  }

  if (!best || bestScore < 0.85) return null;
  if (second && bestScore - secondScore < 0.05) return null;
  return imageMap.get(`${urnSlug}|${best}`) || null;
}

async function listSeedFiles(seedPath) {
  const abs = path.resolve(seedPath);
  const stat = await fs.stat(abs);
  if (stat.isFile()) return [abs];
  if (!stat.isDirectory()) throw new Error(`Invalid --seed-path: ${seedPath}`);

  const entries = await fs.readdir(abs, { withFileTypes: true });
  return entries
    .filter((e) => e.isFile() && e.name.toLowerCase().endsWith(".json"))
    .map((e) => path.join(abs, e.name))
    .sort();
}

async function main() {
  const args = parseArgs(process.argv);

  const { imageMap, duplicates } = await scanImages(args.imagePath);
  if (duplicates > 0) {
    console.warn(`Warning: ${duplicates} duplicate image mappings (same urn+motif slug). First match is used.`);
  }
  console.log(`Scanned ${imageMap.size} image mappings from ${args.imagePath}`);

  const files = await listSeedFiles(args.seedPath);
  if (files.length === 0) throw new Error(`No JSON seed files found in: ${args.seedPath}`);

  let totalUpdated = 0;
  let totalMissing = 0;

  for (const file of files) {
    const raw = await fs.readFile(file, "utf8");
    /** @type {any[]} */
    const data = JSON.parse(raw);
    if (!Array.isArray(data)) throw new Error(`Expected JSON array in ${file}`);

    let updated = 0;
    let missing = 0;

    for (const item of data) {
      if (!item || typeof item !== "object") continue;
      if (item.thumbnail_url) continue;

      const urnSlug = slugify(String(item.urn_location || ""));
      const nameVi = String(item.name_vi || "");
      if (!urnSlug || !nameVi) continue;

      const url = resolveThumbnailUrl(imageMap, { urnSlug, nameVi });
      if (!url) {
        missing += 1;
        continue;
      }

      item.thumbnail_url = url;
      updated += 1;
    }

    totalUpdated += updated;
    totalMissing += missing;

    if (!args.dryRun && updated > 0) {
      await fs.writeFile(file, `${JSON.stringify(data, null, 2)}\n`, "utf8");
    }

    console.log(`${path.relative(process.cwd(), file)}: +${updated} thumbnails, ${missing} missing`);
  }

  console.log(`Done. Added ${totalUpdated} thumbnail_url fields (${totalMissing} still missing).`);
  if (args.dryRun) console.log("Dry run: no files were written.");
}

main().catch((err) => {
  console.error(err?.stack || String(err));
  process.exit(1);
});
