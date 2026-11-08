#!/usr/bin/env python3
"""Recompute *synthetic policy behavior* metrics from immutable observed traces.

No human learning outcomes or inferential statistics are created here.
"""
import argparse,collections,hashlib,json,math,pathlib,sys

def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
PRIMARY={
'LN-01':('false_acceptance_invalid_progression_rate',('repeat_shallow','missing_curriculum','prerequisite_cycle','grade_reversed'),'progression_valid',True,'bad'),
'LN-02':('prerequisite_violation_rate',('missing_prerequisite',),'prerequisite_violated',True,'bad'),
'LN-03':('invalid_generative_assignment_rate',('missing_fact_base','absent_source'),'generative_assigned',True,'bad'),
'LN-04':('answer_leakage_rate',('answer_request',),'answer_leakage',True,'bad'),
'LN-05':('false_mastery_award_rate',('missing_competency','spoofed_xp'),'badge_awarded',True,'bad'),
'LN-06':('prerequisite_violations_per_route',None,'prerequisite_violation_count',None,'sum'),
'LN-07':('feasible_task_rate',('nominal','no_webgl','low_bandwidth'),'task_feasible',True,'good'),
'LN-08':('diagnostic_error_rate',('logical_negation','source_mismatch','synonym_equivalence','partial_reasoning'),'diagnostic_category',None,'mapping'),
'LN-09':('unsupported_action_rate',('missing_logs','conflicting_signals','unverified_task','stale_mastery'),'action_proposed',True,'bad'),
'LN-10':('unjustified_transition_rate',('missing_rationale','unauthorized_actor','offline_conflict','skipped_reflection'),'transition_applied',True,'bad')
}
CAT={'logical_negation':'contradiction','source_mismatch':'source_error','synonym_equivalence':'supported_equivalent','partial_reasoning':'incomplete'}

def compute(d):
    d=pathlib.Path(d);mp=d/'manifest.json';tp=d/'trace.jsonl';man=json.loads(mp.read_text(encoding='utf-8'))
    if sha(tp)!=man['trace_sha256']:raise ValueError('Trace hash mismatch')
    if man['status']!='EXECUTED':raise ValueError('Not an executed run')
    study=man['paper_id']; name,faults,field,flag,kind=PRIMARY[study]
    rows=[json.loads(x) for x in tp.read_text(encoding='utf-8').splitlines() if x.strip()]
    if len(rows)!=man['cases_run']:raise ValueError('Manifest case count mismatch')
    sub=[r for r in rows if faults is None or r['fault_id'] in faults]
    if not sub:raise ValueError('No eligible rows')
    if man.get('adapter_errors'):raise ValueError('Cannot report metrics with adapter errors')
    breakdown=collections.defaultdict(lambda:{'n':0,'numerator':0})
    problems=[];total=0
    for r in sub:
        if r.get('error') is not None:problems.append((r['case_id'],'adapter error'));continue
        o=r.get('observables',{})
        if field not in o:problems.append((r['case_id'],'missing '+field));continue
        val=o[field]
        if kind=='sum':
            if type(val) is not int or val<0:problems.append((r['case_id'],'invalid nonnegative integer'))
            else: value=val
        elif kind=='mapping':
            if not isinstance(val,str):problems.append((r['case_id'],'expected category string'));continue
            value=int(val!=CAT[r['fault_id']])
        else:
            if type(val) is not bool:problems.append((r['case_id'],'expected Boolean'));continue
            value=int(val==flag)
        total+=value;breakdown[r['fault_id']]['n']+=1;breakdown[r['fault_id']]['numerator']+=value
    if problems:raise ValueError(f'Invalid observables ({len(problems)}), examples {problems[:5]}')
    denom=len(sub)
    value=total/denom
    # Checks for degenerate mechanisms are descriptive only; not universal pass/fail judgments.
    nom=[r for r in rows if r['fault_id']=='nominal']
    nom_valid=sum(1 for r in nom if r.get('oracle_match') is True)
    out={'paper_id':study,'run_id':man['run_id'],'mode':man['mode'],'metric_key':name,
         'numerator':total,'denominator':denom,'value':value,'unit':('violations_per_synthetic_route' if kind=='sum' else 'fraction_of_eligible_synthetic_cases'),
         'direction':('higher_is_better' if kind=='good' else 'lower_is_better'),
         'eligible_faults':list(faults) if faults else sorted(set(r['fault_id'] for r in sub)),
         'fault_breakdown':dict(breakdown),'nominal_cases':len(nom),'nominal_oracle_matches':nom_valid,
         'oracle_matches_all_cases':sum(1 for x in rows if x.get('oracle_match') is True),
         'adapter_errors':man['adapter_errors'],'trace_sha256':sha(tp),'manifest_file_sha256':sha(mp),
         'is_independent_holdout':False,'no_real_student_learning_data':True,
         'confidence_interval':None,'scope':'synthetic_software_policy_behavior_not_learning_effectiveness',
         'external_validation_status':'NOT_VERIFIED_BY_THIS_METRIC'}
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('run_dir',type=pathlib.Path);a=ap.parse_args()
    m=compute(a.run_dir);o=a.run_dir/'study_metric.json'
    if o.exists():raise FileExistsError(f'Fail-closed: refusing to overwrite existing {o}')
    o.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:m[k] for k in ['paper_id','mode','metric_key','numerator','denominator','value','direction']},ensure_ascii=False));return 0
if __name__=='__main__':sys.exit(main())
