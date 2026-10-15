"""How much do GraphVOI's chosen asks change under answer-model errors?

Every belief sees the identical public state, so differences are caused only by
the answer model. States come from unperturbed GraphVOI trajectories.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluate import VARIANTS, VERSION
from kit import Simulator, generate
from graphvoi.policy import decide

BELIEFS = ('none', 'biased', 'overconfident', 'underconfident', 'refusal', 'subgroup_refusal', 'temporal_drift')


def world(args):
    seed, variant, days = args
    sim, memory, out = Simulator(generate(seed, 200, 'evaluation', variant)), None, []
    for _ in range(max(days) + 1):
        request = {'schema_version': VERSION, 'phase': 'ask', 'state': sim.observe(), 'memory': memory}
        if sim.day in days:
            choices = {b: decide(json.loads(json.dumps(request)), method='graphvoi', perturbation=b)['asks']
                       for b in BELIEFS}
            ref = {(q['member_id'], q['field']) for q in choices['none']}
            for b in BELIEFS[1:]:
                got = {(q['member_id'], q['field']) for q in choices[b]}
                out.append(dict(seed=seed, variant=variant, day=sim.day, belief=b,
                                jaccard=len(ref & got) / len(ref | got) if ref | got else 1.0,
                                identical=ref == got,
                                first_changed=(choices[b][:1] != choices['none'][:1]),
                                units_none=sum(3 if f == 'constraints' else 1 for _, f in ref),
                                units_belief=sum(3 if f == 'constraints' else 1 for _, f in got)))
        response = decide(request, method='graphvoi')
        memory = response['memory']
        sim.resolve_asks(response['asks'])
        sim.advance(decide({'schema_version': VERSION, 'phase': 'match', 'state': sim.observe(),
                            'memory': memory}, method='graphvoi')['pairs'])
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--workers', type=int, default=1)
    p.add_argument('--output', default='results/decision_sensitivity/states.json')
    args = p.parse_args()
    jobs = [(s, v, {0, 5, 10, 20}) for s in range(71001, 71011) for v in VARIANTS]
    with ProcessPoolExecutor(args.workers) as ex:
        rows = [r for part in ex.map(world, jobs) for r in part]
    summary = {}
    for b in BELIEFS[1:]:
        rs = [r for r in rows if r['belief'] == b]
        summary[b] = dict(states=len(rs), mean_jaccard=sum(r['jaccard'] for r in rs) / len(rs),
                          identical_share=sum(r['identical'] for r in rs) / len(rs),
                          first_ask_changed_share=sum(r['first_changed'] for r in rs) / len(rs),
                          by_day={d: sum(r['jaccard'] for r in rs if r['day'] == d) /
                                  max(1, sum(r['day'] == d for r in rs)) for d in (0, 5, 10, 20)})
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dict(summary=summary, rows=rows), indent=1) + '\n')
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
