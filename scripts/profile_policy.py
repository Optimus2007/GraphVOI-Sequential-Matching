"""Profile ask and match separately on public observations and save actual timings."""
import argparse
import cProfile
import json
from pathlib import Path
import pstats
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluate import invoke
from kit import Simulator, generate
from graphvoi.policy import decide


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seed', type=int, default=41003)
    p.add_argument('--output', default='results/profile.json')
    args = p.parse_args()
    sim, rows = Simulator(generate(args.seed, 200, 'profile')), []
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    for day in (0, 20, 40, 59):
        while sim.day < day:
            sim.advance([])
        for phase in ('ask', 'match'):
            request = dict(schema_version='1.0.0', phase=phase, state=sim.observe(), memory=None)
            profiler = cProfile.Profile()
            started = time.perf_counter()
            response = profiler.runcall(decide, request, method='graphvoi')
            elapsed = time.perf_counter() - started
            with out.with_name(f'profile_{day}_{phase}.txt').open('w') as stream:
                pstats.Stats(profiler, stream=stream).sort_stats('cumulative').print_stats(25)
            actual, process_elapsed = invoke([sys.executable, 'policy.py', '--method', 'graphvoi'], request)
            if actual != response:
                raise ValueError('Profiled and subprocess actions differ')
            rows.append(dict(day=day, phase=phase, instrumented_seconds=elapsed,
                             subprocess_seconds=process_elapsed, actions_equal=True))
    out.write_text(json.dumps(dict(seed=args.seed, python_version=sys.version, profiles=rows,
        note='Snapshots wait without introductions; instrumented runtime has profiler overhead. Subprocess includes startup, but Docker resource limits are not enforced.'), indent=2) + '\n')


if __name__ == '__main__':
    main()
