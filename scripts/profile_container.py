"""Time individual official-flag container invocations on real mid-episode states.

The official evaluator records only per-episode totals; eligibility depends on
every single call (including startup) finishing inside 10 seconds.
"""
import argparse
import json
from pathlib import Path
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluate import VERSION, docker_command, invoke
from kit import Simulator, generate
from graphvoi.policy import decide


def requests(seed, variant, days):
    """Drive the episode with the in-process policy; keep requests on chosen days."""
    sim, memory, out = Simulator(generate(seed, 200, 'evaluation', variant)), None, []
    for _ in range(max(days) + 1):
        for phase in ('ask', 'match'):
            request = {'schema_version': VERSION, 'phase': phase, 'state': sim.observe(), 'memory': memory}
            if sim.day in days:
                out.append((sim.day, phase, json.loads(json.dumps(request))))
            response = decide(request, method='graphvoi')
            memory = response['memory']
            if phase == 'ask':
                sim.resolve_asks(response['asks'])
            else:
                sim.advance(response['pairs'])
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--image', required=True)
    p.add_argument('--seeds', default='101,102')
    p.add_argument('--variants', default='development,cold_start,sparse')
    p.add_argument('--days', default='0,3,8,15,30,59')
    p.add_argument('--repeats', type=int, default=3)
    p.add_argument('--output', required=True)
    args = p.parse_args()
    days = set(map(int, args.days.split(',')))
    rows = []
    for variant in args.variants.split(','):
        for seed in map(int, args.seeds.split(',')):
            for day, phase, request in requests(seed, variant, days):
                times, actions = [], set()
                for _ in range(args.repeats):
                    response, elapsed = invoke(docker_command(args.image), request)
                    times.append(elapsed)
                    actions.add(json.dumps(response['asks' if phase == 'ask' else 'pairs'], sort_keys=True))
                rows.append(dict(seed=seed, variant=variant, day=day, phase=phase,
                                 request_bytes=len(json.dumps(request).encode()),
                                 seconds=times, deterministic=len(actions) == 1))
                print(json.dumps(rows[-1]), flush=True)
    summary = {phase: dict(calls=sum(len(r['seconds']) for r in rows if r['phase'] == phase),
                           max_seconds=max(t for r in rows if r['phase'] == phase for t in r['seconds']),
                           median_seconds=statistics.median(t for r in rows if r['phase'] == phase
                                                            for t in r['seconds']))
               for phase in ('ask', 'match')}
    summary['all_deterministic'] = all(r['deterministic'] for r in rows)
    result = dict(image=args.image, flags=docker_command(args.image)[:-1], rows=rows, summary=summary,
                  note='Wall time per docker run including container and Python startup, host-specific.')
    Path(args.output).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    raise SystemExit(main())
