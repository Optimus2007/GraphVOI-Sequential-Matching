"""Frozen 10-seed paired pilot, including unchanged official baselines.

Parallel independent episodes have separate process caches. Checkpoints retain
failures and declare the entire expected matrix; incomplete matrices have no CIs.
No hyperparameter selection or full 100-seed study is performed here.
"""
import argparse
import collections
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import resource
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evaluate import VARIANTS, summarise
from graphvoi.analysis import comparison_design, paired_intervals, percentile
from scripts.run_experiments import research_episode, CODE_SHA256

METHODS=('graphvoi','degree_first','uncertainty_first','greedy','no_asks','random')
SEEDS=tuple(range(62001,62011))


def job(seed,variant,method,trace):
    try:
        row=research_episode(seed,variant,method,trace_path=trace)
        rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        row['worker_peak_rss_bytes']=rss if sys.platform=='darwin' else rss*1024
        return row
    except (ValueError,TypeError,KeyError,OSError) as error:
        return dict(valid=False,seed=seed,variant=variant,method=method,error=str(error))


def aggregate(rows,methods=METHODS,seeds=SEEDS,variants=VARIANTS,bootstrap=True):
    expected={(v,s) for v in variants for s in seeds}
    summaries={}; secondary={}
    for m in methods:
        rs=[r for r in rows if r['method']==m]
        design=comparison_design(rs,m,m,expected)
        summaries[m]=summarise(rs) if design['status']=='complete' else dict(
            eligible=False,primary_score=None,reason=design['status'],validation=design)
        summaries[m]['invalid_count']=sum(not r.get('valid') for r in rs)
        summaries[m]['recorded_count']=len(rs)
        if summaries[m]['eligible']:
            waits=[w for r in rs for w in r['first_introduction_wait_days']]
            secondary[m]=dict(mean_mutual_acceptances=sum(r['mutual_acceptances'] for r in rs)/len(rs),
                mean_completed_dates=sum(r['dates'] for r in rs)/len(rs),
                mean_unserved=sum(r['unserved_members'] for r in rs)/len(rs),
                served_wait_median=percentile(waits,.5),served_wait_p90=percentile(waits,.9),
                max_ask_seconds=max(r['phase_runtime']['ask']['maximum'] for r in rs),
                max_match_seconds=max(r['phase_runtime']['match']['maximum'] for r in rs),
                note='Waiting quantiles condition on served members; unserved remain in scoring/coverage denominator.')
    counts=collections.Counter((r['method'],r['variant'],r['seed']) for r in rows)
    complete=counts==collections.Counter({(m,v,s):1 for m in methods for v,s in expected})
    out=dict(complete=complete,expected_design=dict(methods=list(methods),seeds=list(seeds),variants=list(variants)),
             episodes=rows,summaries=summaries,secondary=secondary)
    # Progress checkpoints explicitly suppress inference before the full matrix finishes.
    if bootstrap and complete:
        out['paired_intervals']={ref:paired_intervals(rows,reference=ref,expected_pairs=expected,expected_methods=methods)
                                 for ref in ('uncertainty_first','degree_first','greedy','no_asks','random') if ref in methods}
    else:out['paired_intervals']=None
    return out


def main():
    p=argparse.ArgumentParser();p.add_argument('--workers',type=int,default=3)
    p.add_argument('--output',default='results/corrected_pilot.json');args=p.parse_args()
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists():p.error('Output exists; preserve prior experiment instead of overwriting')
    training=json.loads(Path('assets/training_summary.json').read_text())
    assert not set(SEEDS)&set(training['training_seeds'])
    root=output.parent/(output.stem+'_traces');rows=[];started=time.perf_counter()
    metadata=dict(mode='trusted_research_inprocess',startup_included=False,workers=args.workers,
        python_version=sys.version,code_sha256=CODE_SHA256,
        asset_sha256={n:hashlib.sha256(Path('assets',n).read_bytes()).hexdigest() for n in ('pair_model.json','answer_model.json')},
        decision_days=60,follow_up_days=40,members_per_episode=200,
        acquisition=dict(frontier=16,paired_actions=8,world_limit=8,evaluation_limit=256,lambda_cost=0),
        note='Pilot only. Parallel host timings do not certify official Docker resource limits.')
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures=[executor.submit(job,s,v,m,str(root/f'{v}_{s}_{m}.json'))
                 for v in VARIANTS for s in SEEDS for m in METHODS]
        for future in as_completed(futures):
            row=future.result();rows.append(row)
            ordered=sorted(rows,key=lambda r:(VARIANTS.index(r['variant']),r['seed'],METHODS.index(r['method'])))
            result=aggregate(ordered,bootstrap=False);result.update(metadata,elapsed_seconds=time.perf_counter()-started)
            output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
            print(json.dumps(dict(done=len(rows),total=len(futures),method=row['method'],variant=row['variant'],
                seed=row['seed'],valid=row['valid'],error=row.get('error'))),flush=True)
    result=aggregate(ordered);result.update(metadata,elapsed_seconds=time.perf_counter()-started)
    output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return 0 if all(r['valid'] for r in rows) else 2


if __name__=='__main__':raise SystemExit(main())
