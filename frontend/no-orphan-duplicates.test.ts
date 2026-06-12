import { describe, it, expect } from "vitest";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

// Duplicate-scan guard (frontend-consolidation-typing — Property 3 / Req 3.1,
// 3.2): no repository-root component file may duplicate a component maintained
// under `frontend/src/`, whether divergent or identical.
//
// The scan compares by basename WITHOUT extension so that, e.g., a root
// `MediaPlayer.tsx` is flagged as a duplicate of `frontend/src/components/
// MediaPlayer.jsx`.

const FRONTEND_DIR = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(FRONTEND_DIR, "..");
const SRC_DIR = path.join(FRONTEND_DIR, "src");

// Extensions that denote a (React) component / module file we care about.
const COMPONENT_EXTS = new Set([".jsx", ".tsx", ".js", ".ts"]);

function collectSrcComponentNames(dir: string, acc: Set<string>): Set<string> {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === "node_modules" || entry.name === ".next") continue;
      collectSrcComponentNames(full, acc);
    } else if (entry.isFile()) {
      const ext = path.extname(entry.name);
      if (COMPONENT_EXTS.has(ext) && !entry.name.endsWith(".test" + ext)) {
        acc.add(path.basename(entry.name, ext));
      }
    }
  }
  return acc;
}

function rootComponentFiles(): string[] {
  return fs
    .readdirSync(REPO_ROOT, { withFileTypes: true })
    .filter((e) => e.isFile())
    .map((e) => e.name)
    .filter((name) => COMPONENT_EXTS.has(path.extname(name)));
}

describe("no orphaned root-level component duplicates", () => {
  it("contains no repository-root file that duplicates a maintained frontend/src component", () => {
    const maintained = collectSrcComponentNames(SRC_DIR, new Set<string>());

    const duplicates = rootComponentFiles().filter((name) =>
      maintained.has(path.basename(name, path.extname(name))),
    );

    expect(duplicates).toEqual([]);
  });
});
