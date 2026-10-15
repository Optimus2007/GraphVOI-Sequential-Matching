"""Belief errors and independent disclosure changes; static decision stability."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluate import VARIANTS
from kit import Simulator, generate
from graphvoi.policy import decide
from scripts.run_experiments import research_episode

BELIEFS = ('none', 'biased', 'overconfident', 'underconfident', 'refusal',
           'subgroup_refusal', 'temporal_drift')


def ask_set(response):
    return {(q['member_id'], q['field']) for q in response['asks']}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seed', type=int, default=41002)
    p.add_argument('--output', default='results/robustness_smoke.json')
    args = p.parse_args()
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    results = dict(seed=args.seed, complete=False, belief_snapshot_stability=[], full_episodes=[],
        note='Smoke sensitivity only. Independent disclosure wrapper differs from official worlds; no hidden parameters enter policy JSON.')
    for variant in VARIANTS:
        sim = Simulator(generate(args.seed, 200, 'robustness', variant))
        for day in (0, 20, 40):
            while sim.day < day:
                sim.advance([])
            state = sim.observe()
            request = dict(schema_version='1.0.0', phase='ask', state=state, memory=None)
            reference = ask_set(decide(request, method='graphvoi'))
            for belief in BELIEFS:
                selected = ask_set(decide(request, method='graphvoi', perturbation=belief))
                results['belief_snapshot_stability'].append(dict(variant=variant, day=day,
                    belief=belief, reference_cost=sum(3 if f == 'constraints' else 1 for _, f in reference),
                    selected_cost=sum(3 if f == 'constraints' else 1 for _, f in selected),
                    jaccard=(len(reference & selected) / len(reference | selected)
                             if reference | selected else 1.0),
                    both_empty=not reference and not selected,
                    reference=sorted(reference), selected=sorted(selected),
                    observation_sha256=hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()))
            print(json.dumps(dict(variant=variant, day=day, stability_complete=True)), flush=True)
            out.write_text(json.dumps(results, indent=2, allow_nan=False) + '\n')
    # Full-episode sensitivity in standard scenario, with fixed independent seed.
    for belief, actual in [(b, 'none') for b in BELIEFS] + [('none', a) for a in ('refusal', 'subgroup', 'drift')]:
        row = research_episode(args.seed, 'development', 'graphvoi', belief, actual,
            out.parent / (out.stem + '_traces') / f'{belief}_{actual}.json')
        results['full_episodes'].append(row)
        reference = results['full_episodes'][0]
        row['delta_vs_original'] = {k: row[k] - reference[k] for k in
            ('msmi_per_100_arrived_members', 'mutual_acceptances_per_100', 'ask_cost', 'coverage')}
        out.write_text(json.dumps(results, indent=2, allow_nan=False) + '\n')
        print(json.dumps(dict(belief=belief, actual=actual, valid=row['valid'],
                             msmi=row['msmi_per_100_arrived_members'])), flush=True)
    results['complete'] = True
    out.write_text(json.dumps(results, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
