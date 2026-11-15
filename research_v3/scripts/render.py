"""V3-G10: render tables/figures ONLY from numeric JSON artifacts.

Rule: nothing in the output may come from hand-pasted constants. The renderer
reads one or more numeric artifact JSON files (metrics.json style: any dict of
numbers / nested dicts of numbers), checks the source file SHA-256s, and emits
a Markdown table plus an SVG bar chart derived strictly from those values.

Any non-numeric leaf is rejected (fail-closed) — a renderer that accepted
strings would eventually accept pasted claims.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from research_v3.scripts._paths import FIGURES_DIR

EXIT_OK = 0
EXIT_RENDER_FAILED = 14


class RenderError(ValueError):
    """Raised when an artifact is not purely numeric or cannot be read."""


def _flatten_numeric(obj, path: str = "") -> dict[str, float]:
    """Collect numeric leaves; raise on any bool/str/None leaf (fail-closed)."""
    out: dict[str, float] = {}
    if isinstance(obj, bool):
        raise RenderError(f"{path}: boolean leaf is not a numeric metric")
    if isinstance(obj, (int, float)):
        if obj != obj or obj in (float("inf"), float("-inf")):
            raise RenderError(f"{path}: non-finite number")
        return {path: float(obj)}
    if isinstance(obj, dict):
        if not obj:
            raise RenderError(f"{path}: empty object carries no numeric value")
        for key, value in obj.items():
            out.update(_flatten_numeric(value, f"{path}.{key}" if path else str(key)))
        return out
    raise RenderError(f"{path}: non-numeric leaf of type {type(obj).__name__}")


def load_artifacts(paths: list[Path]) -> tuple[dict[str, float], list[dict[str, str]]]:
    values: dict[str, float] = {}
    sources: list[dict[str, str]] = []
    for path in paths:
        if not path.is_file():
            raise RenderError(f"artifact not found: {path}")
        raw = path.read_text(encoding="utf-8")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RenderError(f"{path}: invalid JSON: {exc}") from exc
        values.update(_flatten_numeric(payload, path.stem))
        sources.append(
            {
                "path": str(path),
                "sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
            }
        )
    if not values:
        raise RenderError("no numeric values found in the given artifacts")
    return values, sources


def render_markdown_table(values: dict[str, float]) -> str:
    lines = ["| metric | value |", "|---|---|"]
    for key in sorted(values):
        lines.append(f"| {key} | {values[key]:.6f} |")
    return "\n".join(lines)


def render_svg_bars(values: dict[str, float], *, width: int = 720, bar_h: int = 22) -> str:
    """Dependency-free SVG bar chart derived from the numeric values only."""
    items = sorted(values.items())
    label_w = max((len(k) for k, _ in items), default=10) * 7 + 12
    vmax = max(abs(v) for v in values.values()) or 1.0
    plot_w = width - label_w - 60
    height = len(items) * (bar_h + 6) + 30
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        'viewBox="0 0 '
        f'{width} {height}">',
        f'<rect width="{width}" height="{height}" fill="white"/>',
    ]
    y = 20
    for key, v in items:
        w = max(1.0, abs(v) / vmax * plot_w)
        parts.append(f"<text x=\"8\" y=\"{y + bar_h - 6}\" font-size=\"12\" font-family=\"monospace\">{key}</text>")
        parts.append(
            f"<rect x=\"{label_w}\" y=\"{y}\" width=\"{w:.1f}\" height=\"{bar_h - 4}\" "
            'fill="#3b6ea5"/>'
        )
        parts.append(
            f"<text x=\"{label_w + w + 6}\" y=\"{y + bar_h - 6}\" font-size=\"11\" "
            f"font-family=\"monospace\">{v:.4f}</text>"
        )
        y += bar_h + 6
    parts.append("</svg>")
    return "\n".join(parts)


def build_render(values: dict[str, float], sources: list[dict[str, str]], *, title: str) -> dict:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "schema": "research_v3.render/v1",
        "task_id": "V3-G10",
        "title": title,
        "generated_at_utc": now,
        "sources": sources,
        "n_metrics": len(values),
        "markdown": render_markdown_table(values),
        "svg": render_svg_bars(values),
        "provenance_note": "Every value above is derived from the listed SHA-pinned numeric artifacts.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m research_v3.scripts.render",
        description=(
            "Build tables/figures ONLY from numeric JSON artifacts — no pasted "
            "constants (V3-G10). Outputs Markdown + SVG under "
            "research_artifacts_v3/figures/."
        ),
    )
    parser.add_argument("--artifacts", type=Path, nargs="+", required=True, help="Numeric JSON artifact files")
    parser.add_argument("--title", default="V3 numeric render")
    parser.add_argument("--output-dir", type=Path, default=FIGURES_DIR)
    parser.add_argument("--stdout", action="store_true", help="Print the render instead of writing files")
    args = parser.parse_args(argv)

    try:
        values, sources = load_artifacts(args.artifacts)
    except RenderError as exc:
        print(f"FAIL render: {exc}", file=sys.stderr)
        return EXIT_RENDER_FAILED

    render = build_render(values, sources, title=args.title)
    if args.stdout:
        print(render["markdown"])
        return EXIT_OK

    args.output_dir.mkdir(parents=True, exist_ok=True)
    slug = "".join(c if c.isalnum() else "-" for c in args.title.lower()).strip("-")[:48] or "render"
    md_path = args.output_dir / f"{slug}.md"
    svg_path = args.output_dir / f"{slug}.svg"
    json_path = args.output_dir / f"{slug}.json"
    md_path.write_text(render["markdown"] + "\n", encoding="utf-8")
    svg_path.write_text(render["svg"] + "\n", encoding="utf-8")
    json_path.write_text(json.dumps(render, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"OK render: {render['n_metrics']} metrics from {len(sources)} source(s) "
        f"-> {md_path.name}, {svg_path.name}"
    )
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
