"""Build a timing/witness observer against pinned CFT and fmt source checkouts."""
import argparse
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
cli = argparse.ArgumentParser()
cli.add_argument('cft', type=Path)
cli.add_argument('fmt', type=Path)
cli.add_argument('out', type=Path)
args = cli.parse_args()
for path, pin in [(args.cft, '6cb63d0036223b8be9c4d01f95b296d641209f95'),
                  (args.fmt, '40626af88bd7df9a5fb80be7b25ac85b122d6c21')]:
    sha = subprocess.check_output(['git','-C',path,'rev-parse','HEAD'],text=True).strip()
    if sha != pin:
        raise ValueError(f'wrong revision for {path}')
    subprocess.run(['git','-C',path,'diff','--exit-code','HEAD'],check=True)
override = args.out / 'include/algorithms'
override.mkdir(exist_ok=True,parents=True)
edits = {
    'ThreePhase.hpp': [
        ('_three_phase_setup(inst, greedy, sol, best_sol, core, lagr_mult, fixing);',
         '::observe_cft(best_sol);'),
        ('_from_core_to_unfixed_sol(sol, core, fixing, best_sol);\n                CFT_IF_DEBUG',
         None)],
    'Refinement.hpp': [
        ('auto result_3p = three_phase(env, inst);', None)]
}
for filename, patches in edits.items():
    src = (args.cft / 'src/algorithms' / filename).read_text()
    for old, suffix in patches:
        if src.count(old) != 1:
            raise ValueError(f'unexpected {filename} revision')
        if suffix:
            new = old + '\n' + suffix
        elif filename == 'ThreePhase.hpp':
            new = old.replace('CFT_IF_DEBUG', '::observe_cft(best_sol);\n                CFT_IF_DEBUG')
        else:
            new = 'if (::elapsed() >= ::budget) break;\n        ::outer_fixing = &fixing;\n        '+old
        src = src.replace(old,new)
    (override/filename).write_text(src)
subprocess.run(['g++','-std=c++17','-O3','-DNDEBUG','-DFMT_HEADER_ONLY',
                '-I',args.out/'include','-I',args.cft/'src','-I',args.fmt/'include',
                HERE/'native.cpp','-o',args.out/'solve'],check=True)
