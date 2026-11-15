"""V3-G01: build the claim-ID ledger from manuscripts_v5 (read-only).

Scans every ``*.tex`` manuscript and extracts numbered claim anchors
(``\\claim{...}`` or ``\\label{claim:...}``), plus paper-level metadata, into
``research_v3/governance/claims/claims_ledger.csv`` with overlap columns:

``claim_id, paper_id, source_file, claim_kind, claim_text, overlap_paper_ids,
overlap_note, evidence_status``

manuscripts_v5 is NEVER written to. Papers that carry no explicit claim
anchors still get one paper-level row (``PAPER_LEVEL``) so every paper is
represented in the ledger; ``overlap_paper_ids`` is derived from the audited
LN->P reuse map (02_AUDIT/LN_TO_P_MAPPING.md) which is vendored in the spec
directory and copied here as configuration.

Exit codes: 0 ok, 4 when manuscripts root is missing, 5 on ledger write error.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

from research_v3.scripts._paths import REPO_ROOT

CLAIMS_CSV = Path(__file__).resolve().parents[1] / "governance" / "claims" / "claims_ledger.csv"

# Vendored reuse map from LUU_NIEN_RESEARCH_V3_14_PAPERS_SPEC_20261115/
# 01_AUDIT/LN_TO_P_MAPPING.md (paper -> reused LN assets). Two papers that
# reuse the same LN asset are flagged as overlap candidates in the ledger.
PAPER_TO_LN_ASSETS: dict[str, tuple[str, ...]] = {
    "P01": ("LN-02",),
    "P02": ("LN-01", "LN-06", "LN-02"),
    "P03": ("LN-04", "LN-08"),
    "P04": ("LN-02",),
    "P05": ("LN-03",),
    "P06": ("LN-09",),
    "P07": ("LN-07",),
    "P08": ("LN-05",),
    "P09": ("LN-04", "LN-08"),
    "P10": ("LN-01",),
    "P11": ("LN-08",),
    "P12": ("LN-04", "LN-08"),
    "P13": ("LN-10",),
    "P14": ("LN-07",),
}

CLAIM_PATTERN = re.compile(r"\\claim\{(?P<text>[^}]*)\}|\\label\{claim:(?P<label>[^}]*)\}")
SECTION_PATTERN = re.compile(r"\\(?:section|subsection)\{([^}]*)\}")

# Reverse reuse map: LN study -> the V3 papers reusing it. manuscripts_v5 holds
# LN-01..LN-10 manuscripts (plus byte-identical alias files named
# LN-XX_<slug>.tex, which are skipped so each study registers exactly once).
LN_TO_PAPERS: dict[str, tuple[str, ...]] = {}
for _p, _assets in PAPER_TO_LN_ASSETS.items():
    for _ln in _assets:
        LN_TO_PAPERS.setdefault(_ln, []).append(_p)  # type: ignore[union-attr]
LN_TO_PAPERS = {k: tuple(v) for k, v in LN_TO_PAPERS.items()}  # type: ignore[assignment]

LEDGER_COLUMNS = (
    "claim_id",
    "paper_id",
    "source_file",
    "claim_kind",
    "claim_text",
    "overlap_paper_ids",
    "overlap_note",
    "evidence_status",
)


class ClaimsLedgerError(RuntimeError):
    """Raised when the claim ledger cannot be built or written."""


def _paper_id_of(tex_path: Path) -> str:
    """Map the manuscript file name to its canonical paper/study id.

    ``LN-01.tex`` (canonical) -> ``LN-01``; ``LN-01_spiral_curriculum.tex``
    (alias) is reported as ``LN-01_ALIAS`` and skipped by the caller.
    """
    match = re.match(r"(LN-\d{2}|P\d{2})", tex_path.name)
    if not match:
        return tex_path.stem.upper()
    study = match.group(1)
    if tex_path.name != f"{study}.tex":
        return f"{study}_ALIAS"
    return study


def _overlap_for(paper_id: str) -> tuple[list[str], str]:
    """Manuscript ids sharing at least one reused LN asset with ``paper_id``."""
    if paper_id in PAPER_TO_LN_ASSETS:
        mine = set(PAPER_TO_LN_ASSETS[paper_id])
    elif paper_id in LN_TO_PAPERS:
        mine = {paper_id}
    else:
        return [], "no reuse map entry"
    shared: set[str] = set()
    for other, assets in PAPER_TO_LN_ASSETS.items():
        if other != paper_id and mine & set(assets):
            shared.add(other)
    for other, papers in LN_TO_PAPERS.items():
        if other != paper_id and mine & {other}:
            shared.update(papers)
    shared.discard(paper_id)
    note = (
        "shares reused LN asset(s): "
        + ",".join(sorted(mine))
        + " with "
        + ",".join(sorted(shared))
        if shared
        else "no overlap candidate via reuse map"
    )
    return sorted(shared), note


def extract_claims(tex_path: Path) -> list[dict[str, str]]:
    """Extract claim anchors from one manuscript file (read-only)."""
    text = tex_path.read_text(encoding="utf-8", errors="replace")
    paper_id = _paper_id_of(tex_path)
    rel = tex_path.relative_to(REPO_ROOT).as_posix()
    overlap_ids, overlap_note = _overlap_for(paper_id)

    rows: list[dict[str, str]] = []
    counter = 0
    section = ""
    for line in text.splitlines():
        sec = SECTION_PATTERN.search(line)
        if sec:
            section = sec.group(1).strip()
        for m in CLAIM_PATTERN.finditer(line):
            counter += 1
            label = (m.group("label") or "").strip()
            inline = (m.group("text") or "").strip()
            claim_id = label or f"{paper_id}-C{counter:03d}"
            rows.append(
                {
                    "claim_id": claim_id,
                    "paper_id": paper_id,
                    "source_file": rel,
                    "claim_kind": "labeled_claim" if label else "inline_claim",
                    "claim_text": inline or section or "(anchor only; text lives in manuscript)",
                    "overlap_paper_ids": ";".join(overlap_ids),
                    "overlap_note": overlap_note,
                    "evidence_status": "UNVERIFIED",
                }
            )

    if not rows:
        rows.append(
            {
                "claim_id": f"{paper_id}-PAPER",
                "paper_id": paper_id,
                "source_file": rel,
                "claim_kind": "PAPER_LEVEL",
                "claim_text": "paper registered in ledger; no explicit \\claim anchors found",
                "overlap_paper_ids": ";".join(overlap_ids),
                "overlap_note": overlap_note,
                "evidence_status": "UNVERIFIED",
            }
        )
    return rows


def build_ledger(manuscripts_root: Path) -> list[dict[str, str]]:
    if not manuscripts_root.is_dir():
        raise ClaimsLedgerError(f"manuscripts root not found: {manuscripts_root}")
    tex_files = sorted(p for p in manuscripts_root.glob("*.tex") if not p.stem.endswith("_ALIAS"))
    tex_files = [p for p in tex_files if _paper_id_of(p) != f"{p.stem.split('_')[0]}_ALIAS"]
    tex_files = [p for p in tex_files if not _paper_id_of(p).endswith("_ALIAS")]
    if not tex_files:
        raise ClaimsLedgerError(f"no .tex manuscripts under {manuscripts_root}")
    rows: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for tex in tex_files:
        for row in extract_claims(tex):
            if row["claim_id"] in seen_ids:
                raise ClaimsLedgerError(
                    f"duplicate claim_id {row['claim_id']!r} across manuscripts "
                    f"(collision in {row['source_file']})"
                )
            seen_ids.add(row["claim_id"])
            rows.append(row)
    return rows


def write_ledger(rows: list[dict[str, str]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(LEDGER_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m research_v3.scripts.claims",
        description=(
            "Build the claim-ID ledger from manuscripts_v5 (read-only) with "
            "paper-overlap columns (V3-G01)."
        ),
    )
    parser.add_argument(
        "--manuscripts-root",
        type=Path,
        default=REPO_ROOT / "manuscripts_v5",
        help="Directory holding the LN/P .tex manuscripts (read-only)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=CLAIMS_CSV,
        help="Output CSV (default: research_v3/governance/claims/claims_ledger.csv)",
    )
    parser.add_argument("--json-summary", action="store_true", help="Also print a JSON summary")
    args = parser.parse_args(argv)

    try:
        rows = build_ledger(args.manuscripts_root)
        write_ledger(rows, args.output)
    except ClaimsLedgerError as exc:
        print(f"FAIL claims: {exc}", file=sys.stderr)
        return 4

    papers = sorted({r["paper_id"] for r in rows})
    overlap_pairs = sum(1 for r in rows if r["overlap_paper_ids"])
    summary = {
        "claims_total": len(rows),
        "papers": papers,
        "rows_with_overlap_flag": overlap_pairs,
        "output": str(args.output),
        "manuscripts_root_read_only": str(args.manuscripts_root),
    }
    print(
        f"OK claims: {len(rows)} claim rows across {len(papers)} papers -> {args.output}"
    )
    if args.json_summary:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
