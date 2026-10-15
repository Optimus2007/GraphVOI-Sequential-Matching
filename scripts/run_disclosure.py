"""Belief-misspecification and actual-disclosure-shift episodes (secondary study).

The policy only ever receives ordinary public JSON; perturbations act either on
its answer beliefs or on the research-only DisclosureSimulator environment.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluate import VARIANTS
from scripts.run_experiments import CODE_SHA256, research_episode

CONDITIONS = ([('graphvoi', b, 'none') for b in ('biased', 'overconfident', 'underconfident', 'refusal')] +
              [(m, 'none', a) for a in ('refusal', 'drift') for m in ('graphvoi', 'degree_first', 'greedy')])


def job(seed, variant, method, belief, actual):
    try:
        return research_episode(seed, variant, method, belief, actual)
    except (ValueError, TypeError, KeyError, OSError) as error:
        return dict(valid=False, seed=seed, variant=variant, method=method,
                    belief=belief, actual_disclosure=actual, error=str(error))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', default='71001-71010')
    p.add_argument('--workers', type=int, default=2)
    p.add_argument('--output', required=True)
    args = p.parse_args()
    lo, hi = map(int, args.seeds.split('-'))
    output = Path(args.output)
    if output.exists():
        p.error('Output exists; preserve prior experiment instead of overwriting')
    rows, started = [], time.perf_counter()
    expected = [(s, v, *c) for s in range(lo, hi + 1) for v in VARIANTS for c in CONDITIONS]
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(job, *e) for e in expected]
        for n, future in enumerate(as_completed(futures), 1):
            row = future.result()
            row.pop('opportunity', None)
            rows.append(row)
            print(json.dumps(dict(done=n, total=len(futures), method=row['method'], belief=row.get('belief'),
                                  actual=row.get('actual_disclosure'), valid=row['valid'])), flush=True)
            if n % 20 == 0 or n == len(futures):
                output.write_text(json.dumps(dict(complete=n == len(futures), expected=len(expected),
                    conditions=CONDITIONS, seeds=[lo, hi], code_sha256=CODE_SHA256, episodes=rows,
                    elapsed_seconds=time.perf_counter() - started), indent=1, allow_nan=False) + '\n')
    return 0 if all(r['valid'] for r in rows) else 2


if __name__ == '__main__':
    raise SystemExit(main())
