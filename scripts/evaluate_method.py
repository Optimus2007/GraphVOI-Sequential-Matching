"""Run the unchanged official episode evaluator against an Orbit policy command."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluate import VARIANTS, episode, summarise
from kit import generate


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--method', default='safe_core')
    p.add_argument('--seeds', default='101')
    p.add_argument('--variants', default='development')
    p.add_argument('--output', default='results/safe_core.json')
    args = p.parse_args()
    variants = list(VARIANTS) if args.variants == 'all' else args.variants.split(',')
    if any(v not in VARIANTS for v in variants):
        p.error('Unknown variant')
    rows = []
    for variant in variants:
        for seed in map(int, args.seeds.split(',')):
            try:
                row = episode(generate(seed, 200, 'evaluation', variant),
                              [sys.executable, 'policy.py', '--method', args.method])
            except (ValueError, TypeError, KeyError, OSError) as error:
                row = {'valid': False, 'error': str(error)}
            row.update(seed=seed, variant=variant)
            rows.append(row)
            print(json.dumps(row), flush=True)
    result = dict(release='1.0.0', method=args.method, mode='trusted_local',
                  decision_days=60, follow_up_days=40, members_per_episode=200,
                  episodes=rows, summary=summarise(rows))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    return 0 if result['summary']['eligible'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
