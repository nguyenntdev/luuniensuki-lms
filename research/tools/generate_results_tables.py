#!/usr/bin/env python3
"""Generate manuscript TABLE FRAGMENTS only from 50 validated observed runs.

Does not inject results into authors' manuscripts. Software-only claims only.
"""
import argparse,csv,json,pathlib,sys
from verify_release import check
ROOT=pathlib.Path(__file__).resolve().parents[1]
MATRIX=json.loads((ROOT/'configs'/'experiments.json').read_text(encoding='utf-8'))

def esc(x):return str(x).replace('_',r'\_').replace('%',r'\%').replace('&',r'\&')
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
    report,_=check(a.output)
    if report['status']!='SOFTWARE_EVIDENCE_TECHNICALLY_COMPLETE':
        print(json.dumps({'status':'BLOCKED','reasons':report['blockers'][:20]},ensure_ascii=False,indent=2));return 1
    target=a.output/'manuscript_tables'
    if target.exists() and any(target.iterdir()):raise FileExistsError('Refusing overwrite manuscript_tables; use clean output root')
    target.mkdir(parents=True,exist_ok=True)
    for study,entry in MATRIX['studies'].items():
        rows=[]
        for condition in entry['runs']:
            mode=condition['id']
            metric=json.loads((a.output/study/mode/'study_metric.json').read_text(encoding='utf-8'))
            manifest=json.loads((a.output/study/mode/'manifest.json').read_text(encoding='utf-8'))
            rows.append({'condition':mode,'variant':condition['label'],'numerator':metric['numerator'],'denominator':metric['denominator'],
                         'value':metric['value'],'metric':metric['metric_key'],'unit':metric['unit'],'run_id':manifest['run_id'],
                         'source_sha':manifest['source_commit_at_runtime'],'trace_sha256':manifest['trace_sha256']})
        with (target/f'{study}_results.csv').open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
        name=rows[0]['metric'];unit=rows[0]['unit']
        result=[]
        result += [r'\begin{table}[htbp]',r'\centering',r'\small',
                  r'\caption{Comparison on frozen synthetic software-policy scenarios (not student outcomes).}',
                  r'\label{tab:'+study.lower()+'-policy-benchmark}',r'\begin{tabular}{lrrr}',r'\toprule',
                  r'Condition & Numerator & Eligible $N$ & Metric \\',r'\midrule']
        for row in rows:
            if unit=='violations_per_synthetic_route':show=f"{row['value']:.4f} / route"
            else:show=f"{row['value']*100:.2f}\\%"
            result.append(f"{esc(row['condition']+' '+row['variant'])} & {row['numerator']} & {row['denominator']} & {show} \\\\")
        result += [r'\bottomrule',r'\end{tabular}',r'\par\smallskip',
          r'\begin{minipage}{0.98\linewidth}\footnotesize',
          'Primary measure: '+esc(name)+'. All conditions are executed on the same frozen synthetic policy inputs; the eligible denominator depends on the declared fault strata. These are software-policy decisions, not measured changes in learning. Read exact run IDs and SHA-256 fingerprints in the accompanying evidence registry. Source commit: '+r'\texttt{'+rows[0]['source_sha'][:12]+'}.',
          r'\end{minipage}',r'\end{table}']
        (target/f'{study}_results.tex').write_text('\n'.join(result)+'\n',encoding='utf-8')
    print('Generated 10 verified policy-only .tex table fragments and 10 .csv tables:',target)
    return 0
if __name__=='__main__':sys.exit(main())
