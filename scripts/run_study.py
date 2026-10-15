"""Parameterised paired study, reusing the audited pilot job/aggregation code.

Every declared (scenario, seed, method) record is retained with its validity
flag; incomplete or invalid matrices produce no scores or intervals. Seeds that
overlap training or previously used experiment seeds are refused unless the run
is explicitly labelled a development check.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluate import VARIANTS
from scripts.run_experiments import CODE_SHA256
from graphvoi.analysis import paired_intervals
from scripts.run_pilot import aggregate, job

USED_SEEDS = set(range(62001, 62011)) | {63004} | set(range(64001, 64021))


def seed_list(text):
    if '-' in text:
        lo, hi = map(int, text.split('-'))
        return list(range(lo, hi + 1))
    return [int(s) for s in text.split(',')]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', required=True, help='lo-hi inclusive or comma list')
    p.add_argument('--methods', default='graphvoi,degree_first,uncertainty_first,greedy,no_asks,random')
    p.add_argument('--variants', default='all')
    p.add_argument('--workers', type=int, default=6)
    p.add_argument('--purpose', choices=['development', 'confirmatory'], required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--no-traces', action='store_true')
    args = p.parse_args()
    seeds, methods = seed_list(args.seeds), tuple(args.methods.split(','))
    variants = tuple(VARIANTS) if args.variants == 'all' else tuple(args.variants.split(','))
    training = set(json.loads(Path('assets/training_summary.json').read_text())['training_seeds'])
    if set(seeds) & training:
        p.error('Seeds overlap training seeds')
    if args.purpose == 'confirmatory' and set(seeds) & USED_SEEDS:
        p.error('Confirmatory seeds must be untouched by pilot/development runs')
    output = Path(args.output)
    if output.exists():
        p.error('Output exists; preserve prior experiment instead of overwriting')
    output.parent.mkdir(parents=True, exist_ok=True)
    root = output.parent / (output.stem + '_traces')
    metadata = dict(purpose=args.purpose, mode='trusted_research_inprocess', startup_included=False,
        workers=args.workers, python_version=sys.version, code_sha256=CODE_SHA256,
        asset_sha256={n: hashlib.sha256(Path('assets', n).read_bytes()).hexdigest()
                      for n in ('pair_model.json', 'answer_model.json')},
        decision_days=60, follow_up_days=40, members_per_episode=200,
        acquisition=dict(frontier=16, paired_actions=8, world_limit=8, evaluation_limit=256,
                         lambda_cost=0, shared_hard_budget_fill=True),
        note='Parallel host timings do not certify official Docker resource limits.')
    order = lambda r: (variants.index(r['variant']), r['seed'], methods.index(r['method']))
    rows, started = [], time.perf_counter()
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(job, s, v, m, None if args.no_traces else str(root / f'{v}_{s}_{m}.json'))
                   for s in seeds for v in variants for m in methods]
        for n, future in enumerate(as_completed(futures), 1):
            row = future.result()
            rows.append(row)
            if n % 25 == 0 or n == len(futures):
                result = aggregate(sorted(rows, key=order), methods, seeds, variants, bootstrap=False)
                result.update(metadata, elapsed_seconds=time.perf_counter() - started)
                output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
            print(json.dumps(dict(done=n, total=len(futures), method=row['method'], variant=row['variant'],
                                  seed=row['seed'], valid=row['valid'], error=row.get('error'))), flush=True)
    ordered = sorted(rows, key=order)
    result = aggregate(ordered, methods, seeds, variants)
    if result['paired_intervals'] is not None and 'graphvoi_nofill' in methods:
        # Ablation reference: fill versus no fill under the identical v3 selector.
        result['paired_intervals']['graphvoi_nofill'] = paired_intervals(
            ordered, reference='graphvoi_nofill', expected_methods=methods,
            expected_pairs={(v, s) for v in variants for s in seeds})
    result.update(metadata, elapsed_seconds=time.perf_counter() - started)
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    return 0 if all(r['valid'] for r in rows) else 2


if __name__ == '__main__':
    raise SystemExit(main())
