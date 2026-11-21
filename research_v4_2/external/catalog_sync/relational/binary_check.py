"""Replay the size-oriented HDiffPatch control on the originals' canonical tables."""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from screen import canonical, read

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("binaries", type=Path)
p.add_argument("snapshots", nargs=3, type=Path)
p.add_argument("out", type=Path)
args = p.parse_args()
checks = []
for a, b in zip(args.snapshots, args.snapshots[1:]):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        src, dst, patch, restored = [root / name for name in ("base", "target", "patch", "restored")]
        src.write_bytes(canonical(*read(a)))
        dst.write_bytes(canonical(*read(b)))
        subprocess.run([args.binaries/"hdiffz", "-p-1", "-m-6", "-c-lzma2-9", src, dst, patch], check=True)
        subprocess.run([args.binaries/"hpatchz", "-p-1", src, patch, restored], check=True)
        assert restored.read_bytes() == dst.read_bytes()
        checks.append(dict(canonical_target_sha256=hashlib.sha256(restored.read_bytes()).hexdigest(),
                           patch_sha256=hashlib.sha256(patch.read_bytes()).hexdigest(),
                           bytes=patch.stat().st_size))
args.out.write_text(json.dumps(checks,indent=2)+"\n")
