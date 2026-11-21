"""Build the unchanged five-second comparator and a two-second local-witness observer."""
import argparse
from pathlib import Path
import subprocess
import sys

old = Path(__file__).resolve().parents[1] / 'equal_budget'
cli = argparse.ArgumentParser()
for key in ('cft', 'fmt', 'out'):
    cli.add_argument(key, type=Path)
args = cli.parse_args()
subprocess.run([sys.executable, old / 'build.py', args.cft, args.fmt, args.out], check=True)
source = (old / 'native.cpp').read_text()
for before, after in [
    ('constexpr double budget = 5;', 'constexpr double budget = 2;'),
    ('stamp > budget || cost >= incumbent_cost', 'stamp > budget'),
    ('    if (cost >= incumbent_cost) return;', '    if (elapsed() > budget) return;'),
]:
    if source.count(before) != 1:
        raise ValueError('unexpected native observer revision')
    source = source.replace(before, after)
# In CFT mode incumbent_cost only feeds reporting after the warm start is supplied.
adapter = args.out / 'pool.cpp'
adapter.write_text(source)
subprocess.run(['g++', '-std=c++17', '-O3', '-DNDEBUG', '-DFMT_HEADER_ONLY',
                '-I', args.out / 'include', '-I', args.cft / 'src', '-I', args.fmt / 'include',
                adapter, '-o', args.out / 'pool'], check=True)
