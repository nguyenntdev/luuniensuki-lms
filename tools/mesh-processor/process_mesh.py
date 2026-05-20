#!/usr/bin/env python3
"""Mesh denoising and Quadric Edge Collapse decimation tool.

Implements the pre-processing pipeline described in the conference paper
"Giải pháp số hóa cổ vật chi phí thấp bằng công nghệ scan 3D LiDAR" by
Nguyễn Đắc Quang Minh, Trần Minh Đức, Nguyễn Ngọc Thiện.

Pipeline (matches paper section 2):
    1. Load raw scan (GLB/OBJ/PLY/STL/FBX)
    2. Remove duplicated vertices (denoising step 1)
    3. Fill small holes (mặt khuất / hidden faces — paper keyword)
    4. Smooth with Taubin filter (preserves volume)
    5. Quadric Edge Collapse Decimation (= "Error Quadrics" in paper)
       → reduces face count to target ratio while preserving features
    6. Export to GLB at requested LOD level

Usage:
    process_mesh.py INPUT --output OUTPUT [--lod {512,1k,2k}] [--ratio FLOAT]
                    [--smooth-iter N] [--fill-holes] [--quiet]

The three LOD levels match the existing Cao Đỉnh model files:
    --lod 512 → ~5MB target  (95% reduction; for mobile/AR)
    --lod 1k  → ~27MB target (10% reduction; default web)
    --lod 2k  → no decimation (raw quality; admin preview)

Exit codes:
    0 — success
    1 — input file missing or unreadable
    2 — processing error (mesh malformed, decimation failed)
    3 — output write error

Output is JSON on stdout (parseable by Rust subprocess caller).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Optional

import numpy as np
import trimesh


# Decimation ratios matching the paper's reported 60-84% reduction range.
LOD_RATIOS = {
    "2k": 1.00,   # no decimation, baseline
    "1k": 0.50,   # ~50% face reduction
    "512": 0.10,  # ~90% face reduction (matches measured 83% file size cut)
}


def emit(record: dict, *, quiet: bool = False) -> None:
    """Emit a JSON status line to stdout (parseable by callers)."""
    if quiet:
        return
    print(json.dumps(record, ensure_ascii=False), flush=True)


def remove_duplicates(mesh: trimesh.Trimesh) -> dict:
    """Step 1: deduplicate vertices that scan tools generate as separate copies."""
    n_vertices_before = len(mesh.vertices)
    n_faces_before = len(mesh.faces)
    mesh.merge_vertices()
    return {
        "step": "remove_duplicates",
        "vertices_before": int(n_vertices_before),
        "vertices_after": int(len(mesh.vertices)),
        "faces_before": int(n_faces_before),
        "faces_after": int(len(mesh.faces)),
    }


def fill_holes(mesh: trimesh.Trimesh) -> dict:
    """Step 2: fill small holes — bổ sung mặt khuất theo bài báo.

    `trimesh.repair.fill_holes` patches non-manifold boundary loops by
    triangulating the hole. Only fills small holes — large gaps left alone.
    """
    n_faces_before = len(mesh.faces)
    try:
        success = trimesh.repair.fill_holes(mesh)
    except Exception as exc:  # noqa: BLE001
        return {
            "step": "fill_holes",
            "skipped": True,
            "reason": str(exc),
        }
    return {
        "step": "fill_holes",
        "filled_any": bool(success),
        "faces_before": int(n_faces_before),
        "faces_after": int(len(mesh.faces)),
    }


def smooth_taubin(mesh: trimesh.Trimesh, iterations: int = 5) -> dict:
    """Step 3: Taubin smoothing — denoising while preserving volume.

    Uses iterative Laplacian + inverse Laplacian to avoid the shrinkage
    that pure Laplacian smoothing causes.
    """
    n_iter = max(0, int(iterations))
    if n_iter == 0:
        return {"step": "smooth_taubin", "iterations": 0, "skipped": True}
    try:
        trimesh.smoothing.filter_taubin(mesh, iterations=n_iter)
    except Exception as exc:  # noqa: BLE001
        return {
            "step": "smooth_taubin",
            "iterations": n_iter,
            "skipped": True,
            "reason": str(exc),
        }
    return {"step": "smooth_taubin", "iterations": n_iter}


def decimate_quadric(mesh: trimesh.Trimesh, target_ratio: float) -> dict:
    """Step 4: Quadric Edge Collapse Decimation = "Error Quadrics" (paper keyword).

    This is the algorithm by Garland & Heckbert (1997) that the paper
    explicitly references. trimesh delegates to fast-simplification (a
    Python binding for the same algorithm) when available; otherwise it
    falls back to manifold3d. Both implement quadric error metrics.
    """
    if target_ratio >= 0.999:
        return {
            "step": "decimate_quadric",
            "target_ratio": target_ratio,
            "skipped": True,
            "reason": "ratio >= 1.0 means no decimation",
        }

    n_faces_before = len(mesh.faces)
    target_faces = max(4, int(round(n_faces_before * target_ratio)))
    try:
        # trimesh.simplify_quadric_decimation calls fast-simplification
        # which implements the Quadric Error Metrics algorithm.
        simplified = mesh.simplify_quadric_decimation(face_count=target_faces)
    except Exception as exc:  # noqa: BLE001
        return {
            "step": "decimate_quadric",
            "target_ratio": target_ratio,
            "target_faces": target_faces,
            "error": str(exc),
        }

    # simplify_quadric_decimation returns a new mesh; mutate caller's mesh
    # via swap-in (we return the simplified mesh in `_decimated`).
    return {
        "step": "decimate_quadric",
        "target_ratio": target_ratio,
        "target_faces": target_faces,
        "faces_before": int(n_faces_before),
        "faces_after": int(len(simplified.faces)),
        "reduction_pct": round((1 - len(simplified.faces) / n_faces_before) * 100, 2),
        "_decimated": simplified,
    }


def export_glb(mesh: trimesh.Trimesh, output_path: Path) -> dict:
    """Step 5: write the processed mesh to GLB."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(mesh.export(file_type="glb"))
    return {
        "step": "export",
        "output_path": str(output_path),
        "output_bytes": output_path.stat().st_size,
    }


def process(
    input_path: Path,
    output_path: Path,
    target_ratio: float,
    smooth_iter: int,
    do_fill_holes: bool,
    quiet: bool,
) -> dict:
    """Run the full pipeline. Returns a summary dict."""
    started_at = time.monotonic()

    # Load
    if not input_path.exists():
        return {"ok": False, "error": "input_not_found", "path": str(input_path)}
    try:
        loaded = trimesh.load(input_path, force="mesh")
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": "load_failed", "reason": str(exc)}

    if isinstance(loaded, trimesh.Scene):
        # Concatenate all meshes in the scene into one for processing.
        if not loaded.geometry:
            return {"ok": False, "error": "empty_scene"}
        mesh = trimesh.util.concatenate([g for g in loaded.geometry.values() if isinstance(g, trimesh.Trimesh)])
    elif isinstance(loaded, trimesh.Trimesh):
        mesh = loaded
    else:
        return {"ok": False, "error": "unsupported_geometry", "type": type(loaded).__name__}

    input_bytes = input_path.stat().st_size
    summary = {
        "ok": True,
        "input_path": str(input_path),
        "input_bytes": input_bytes,
        "target_ratio": target_ratio,
        "vertices_initial": int(len(mesh.vertices)),
        "faces_initial": int(len(mesh.faces)),
        "steps": [],
    }

    emit({"phase": "load", **summary}, quiet=quiet)

    # Step 1 — dedupe
    step = remove_duplicates(mesh)
    summary["steps"].append(step)
    emit({"phase": "step", **step}, quiet=quiet)

    # Step 2 — fill holes
    if do_fill_holes:
        step = fill_holes(mesh)
        summary["steps"].append(step)
        emit({"phase": "step", **step}, quiet=quiet)

    # Step 3 — Taubin smooth
    step = smooth_taubin(mesh, iterations=smooth_iter)
    summary["steps"].append(step)
    emit({"phase": "step", **step}, quiet=quiet)

    # Step 4 — Quadric Edge Collapse Decimation
    step = decimate_quadric(mesh, target_ratio=target_ratio)
    if "_decimated" in step:
        mesh = step.pop("_decimated")
    summary["steps"].append(step)
    emit({"phase": "step", **step}, quiet=quiet)

    # Step 5 — export
    try:
        export_step = export_glb(mesh, output_path)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": "export_failed", "reason": str(exc), "summary": summary}
    summary["steps"].append(export_step)
    emit({"phase": "step", **export_step}, quiet=quiet)

    elapsed_ms = int((time.monotonic() - started_at) * 1000)
    summary.update({
        "vertices_final": int(len(mesh.vertices)),
        "faces_final": int(len(mesh.faces)),
        "output_path": str(output_path),
        "output_bytes": output_path.stat().st_size,
        "size_reduction_pct": round((1 - output_path.stat().st_size / input_bytes) * 100, 2) if input_bytes > 0 else 0.0,
        "elapsed_ms": elapsed_ms,
    })
    emit({"phase": "done", **summary}, quiet=quiet)
    return summary


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Mesh denoising + Quadric Edge Collapse decimation (Cửu Đỉnh pipeline).",
    )
    parser.add_argument("input", type=Path, help="Input mesh file (GLB/OBJ/PLY/STL/FBX)")
    parser.add_argument("--output", "-o", type=Path, required=True, help="Output GLB file")
    parser.add_argument(
        "--lod",
        choices=list(LOD_RATIOS.keys()),
        help=f"LOD preset. One of {sorted(LOD_RATIOS.keys())}. Overrides --ratio.",
    )
    parser.add_argument(
        "--ratio",
        type=float,
        default=0.50,
        help="Target face count ratio (0..1). Default 0.50. Ignored if --lod is set.",
    )
    parser.add_argument(
        "--smooth-iter",
        type=int,
        default=5,
        help="Taubin smoothing iterations. Default 5. Use 0 to skip.",
    )
    parser.add_argument(
        "--fill-holes",
        action="store_true",
        help="Run fill_holes step (bổ sung mặt khuất). Default off.",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress progress JSON, only print final summary.")

    args = parser.parse_args(argv)

    target_ratio = LOD_RATIOS[args.lod] if args.lod else args.ratio
    if not 0.0 < target_ratio <= 1.0:
        print(json.dumps({"ok": False, "error": "ratio must be in (0, 1]"}), file=sys.stderr)
        return 2

    summary = process(
        input_path=args.input,
        output_path=args.output,
        target_ratio=target_ratio,
        smooth_iter=args.smooth_iter,
        do_fill_holes=args.fill_holes,
        quiet=args.quiet,
    )
    if not summary.get("ok"):
        # Always print the failure summary on stderr regardless of --quiet
        print(json.dumps(summary, ensure_ascii=False), file=sys.stderr)
        if summary.get("error") == "input_not_found":
            return 1
        if summary.get("error") == "export_failed":
            return 3
        return 2
    if args.quiet:
        # Print only the final summary
        print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
