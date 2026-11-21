"""Run equal CPU-budget comparisons on the 20 NRE-NRH test matrices."""
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor

for var in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[var] = '1'
import highspy
import numpy as np
from scipy.sparse import csr_matrix

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'multifamily'))
from study import parse_cover, fill_cover, trim_cover, union_masks

BUDGET = 5
SEEDS = (11,29,47)
NAMES = [f'scpnr{family}{i}' for family in 'efgh' for i in range(1,6)]


class Deadline(Exception):
    pass


def timeout(signum, frame):
    raise Deadline()


def solve_instance(task):
    path, solver, zhu_path, out, core = task
    os.sched_setaffinity(0,{core})
    sys.path.insert(0,str(zhu_path))
    from SetCoverPy.setcover import SetCover
    raw = path.read_bytes()
    matrix,masks,cost = parse_cover(raw)
    m,n=matrix.shape
    full=(1<<m)-1
    warm=trim_cover(fill_cover(full,masks,cost),masks,full)
    all_runs={}
    def cost_of(cols):
        return sum(cost[j] for j in cols)
    def check(cols):
        if len(cols)!=len(set(cols)) or any(j<0 or j>=n for j in cols) or union_masks(cols,masks)!=full:
            raise ValueError(f'invalid witness on {path.name}')
    check(warm)
    warm_cost=cost_of(warm)
    with tempfile.NamedTemporaryFile('w',suffix='.cols') as capsule:
        capsule.write(' '.join(map(str,warm))); capsule.flush()
        for method in ('greedy','exchange','adaptive','single','cft','zhu','highs'):
            runs=[]
            for seed in (SEEDS if method not in ('greedy','exchange') else [0]):
                best=warm.copy()
                best_cost=warm_cost
                reached=0.
                elapsed=0.
                updates=0
                def record(cols,stamp):
                    nonlocal best,best_cost,reached,updates
                    if stamp>BUDGET:
                        return
                    trial_cost=cost_of(cols)
                    if trial_cost<best_cost:
                        check(cols)
                        if time.process_time()-started>BUDGET and method not in ('adaptive','single','cft'):
                            return
                        best,best_cost,reached=list(cols),trial_cost,stamp
                        updates+=1
                started=time.process_time()
                if method in ('adaptive','single','cft'):
                    output=subprocess.check_output([solver,path,capsule.name,method,str(seed)],text=True)
                    for line in output.splitlines():
                        fields=line.split()
                        if fields[0]=='end':
                            elapsed=float(fields[1])
                        else:
                            stamp,value=float(fields[0]),int(fields[1])
                            cols=list(map(int,fields[2:]))
                            if value!=cost_of(cols) or stamp>BUDGET:
                                raise ValueError('native score mismatch')
                            record(cols,stamp)
                elif method=='highs':
                    engine=highspy.Highs()
                    def ok(value):
                        if value!=highspy.HighsStatus.kOk:
                            raise RuntimeError(f'HiGHS model setup returned {value}')
                    for key,value in [('output_flag',False),('threads',1),('random_seed',seed)]:
                        ok(engine.setOptionValue(key,value))
                    a=csr_matrix(matrix,dtype=np.float64)
                    columns=np.arange(n,dtype=np.int32)
                    ok(engine.addVars(n,np.zeros(n),np.ones(n)))
                    ok(engine.changeColsCost(n,columns,np.array(cost,dtype=float)))
                    ok(engine.changeColsIntegrality(n,columns,np.ones(n,dtype=np.uint8)))
                    ok(engine.addRows(m,np.ones(m),np.full(m,highspy.kHighsInf),a.nnz,a.indptr,a.indices,a.data))
                    x=np.zeros(n); x[warm]=1
                    ok(engine.setSolution(n,columns,x))
                    def improve(event):
                        record(np.flatnonzero(event.data_out.mip_solution>0.5).tolist(),time.process_time()-started)
                    def stop(event):
                        event.interrupt(time.process_time()-started>=BUDGET)
                    engine.cbMipImprovingSolution.subscribe(improve)
                    engine.cbMipInterrupt.subscribe(stop)
                    # Interrupts may be delivered after the cutoff. No late incumbent is eligible.
                    engine.run()
                    status=engine.getModelStatus()
                    if status not in (highspy.HighsModelStatus.kOptimal,highspy.HighsModelStatus.kInterrupt,
                                      highspy.HighsModelStatus.kHighsInterrupt):
                        raise RuntimeError(f'unexpected HiGHS stop: {status}')
                    if status == highspy.HighsModelStatus.kOptimal:
                        record(np.flatnonzero(np.array(engine.getSolution().col_value)>0.5).tolist(),time.process_time()-started)
                    elapsed=time.process_time()-started
                elif method in ('exchange','zhu'):
                    signal.signal(signal.SIGPROF,timeout)
                    signal.setitimer(signal.ITIMER_PROF,BUDGET)
                    try:
                        if method=='exchange':
                            current=warm.copy()
                            while True:
                                next_cover=current
                                value=cost_of(current)
                                for j in current:
                                    kept=[k for k in current if k!=j]
                                    added=fill_cover(full^union_masks(kept,masks),masks,cost,excluded=j)
                                    if added is None:
                                        continue
                                    trial=trim_cover(kept+added,masks,full)
                                    if cost_of(trial)<value:
                                        next_cover=trial; value=cost_of(trial)
                                        record(trial,time.process_time()-started)
                                if next_cover is current:
                                    break
                                current=next_cover
                        else:
                            active=np.flatnonzero(matrix.any(axis=0))
                            class ObservedSetCover(SetCover):
                                def greedy(self,*args,**kwargs):
                                    result=super().greedy(*args,**kwargs)
                                    if result<best_cost:
                                        record(active[self.s].tolist(),time.process_time()-started)
                                    return result
                            np.random.seed(seed)
                            with open(os.devnull,'w') as devnull, contextlib.redirect_stdout(devnull):
                                engine=ObservedSetCover(matrix[:,active],np.array(cost)[active])
                                engine.SolveSCP()
                    except Deadline:
                        pass
                    finally:
                        signal.setitimer(signal.ITIMER_PROF,0)
                    elapsed=time.process_time()-started
                check(best)
                runs.append(dict(seed=seed,cost=best_cost,columns_one_based=[j+1 for j in best],
                                 first_best_cpu_s=reached,observed_cpu_s=elapsed,improvements=updates))
            all_runs[method]=runs
    result=dict(instance=path.stem,sha256=hashlib.sha256(raw).hexdigest(),rows=m,columns=n,
                incidences=int(matrix.sum()),cpu=core,budget_cpu_s=BUDGET,runs=all_runs)
    (out/(path.stem+'.json')).write_text(json.dumps(result,separators=(',',':'))+'\n')
    return path.stem


if __name__=='__main__':
    cli=argparse.ArgumentParser()
    for arg in ('data','solver','zhu','out'):
        cli.add_argument(arg,type=Path)
    cli.add_argument('--jobs',type=int,default=10)
    cli.add_argument('--smoke',type=Path,help='Use one development matrix instead of the held-out collection')
    args=cli.parse_args()
    if subprocess.check_output(['git','-C',args.zhu,'rev-parse','HEAD'],text=True).strip()!='a1ff3c5cec45cc1b16541999a4adb593fa652363':
        raise ValueError('unexpected Zhu source revision')
    subprocess.run(['git','-C',args.zhu,'diff','--exit-code','HEAD','--','SetCoverPy'],check=True)
    args.out.mkdir(exist_ok=True,parents=True)
    paths=[args.smoke] if args.smoke else [args.data/(name+'.txt') for name in NAMES]
    cores=sorted(os.sched_getaffinity(0))
    if args.jobs>len(cores):
        raise ValueError('too many workers')
    def group(worker):
        tasks=[(p,args.solver.resolve(),args.zhu.resolve(),args.out,cores[worker]) for p in paths[worker::args.jobs]]
        return [solve_instance(t) for t in tasks]
    with ProcessPoolExecutor(max_workers=min(args.jobs,len(paths))) as pool:
        for done in pool.map(group,range(min(args.jobs,len(paths)))):
            print(*done,flush=True)
