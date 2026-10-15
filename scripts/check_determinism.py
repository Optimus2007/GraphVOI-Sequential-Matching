"""Re-run study episodes with the current code and compare action hashes.

The policy is deterministic, so the same episode must produce the same actions
on any machine and after any change that is meant not to alter decisions.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluate import VARIANTS
from scripts.run_experiments import research_episode
from graphvoi.policy import ASK_DEADLINE_SECONDS


def run(args):
    seed, variant, method = args
    r = research_episode(seed, variant, method)
    return seed, variant, method, r['action_sha256'], r['deadline_count']


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--study', default='results/v3_confirmatory.json')
    p.add_argument('--seeds', default='71001,71002,71003,71004')
    p.add_argument('--methods', default='graphvoi')
    p.add_argument('--workers', type=int, default=6)
    p.add_argument('--output', default='results/validation/final_guard_determinism.json')
    args = p.parse_args()
    ref = {(r['seed'], r['variant'], r['method']): r['action_sha256']
           for r in json.loads(Path(args.study).read_text())['episodes']}
    jobs = [(int(s), v, m) for s in args.seeds.split(',') for v in VARIANTS for m in args.methods.split(',')]
    with ProcessPoolExecutor(args.workers) as ex:
        res = list(ex.map(run, jobs))
    cells = [dict(seed=s, variant=v, method=m, action_sha256=h, deadline_count=d, matches=h == ref[(s, v, m)])
             for s, v, m, h, d in res]
    out = dict(ask_deadline_seconds=ASK_DEADLINE_SECONDS, reference=Path(args.study).name, episodes=len(cells),
               identical_to_reference=sum(c['matches'] for c in cells),
               deadline_hits=sum(c['deadline_count'] for c in cells), cells=cells)
    Path(args.output).write_text(json.dumps(out, indent=1) + '\n')
    print(f"{out['episodes']} episodes; identical action hashes: {out['identical_to_reference']}; "
          f"guard hits: {out['deadline_hits']}")
    return 0 if out['identical_to_reference'] == out['episodes'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
