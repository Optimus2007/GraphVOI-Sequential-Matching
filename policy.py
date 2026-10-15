"""Team Orbit JSON adapter. Official baselines remain explicitly selectable."""
import argparse
import itertools
import json
import random
import sys
from kit import baseline_asks, baseline_match, eligibility


def decide(request, mode='greedy'):
    state = request['state']
    memory = request.get('memory') or {}
    if request['phase'] == 'ask':
        return {'asks': [] if mode == 'no_asks' else baseline_asks(state), 'memory': memory}
    if mode != 'random':
        pairs = baseline_match(state)
    else:
        candidates = [m for m in state['members'] if m['available']]
        past = {tuple(sorted((i['user_a'], i['user_b']))) for i in state['introductions']}
        edges = [tuple(sorted((a['member_id'], b['member_id'])))
                 for a, b in itertools.combinations(candidates, 2)
                 if eligibility(a, b)['status'] == 'feasible'
                 and tuple(sorted((a['member_id'], b['member_id']))) not in past]
        random.Random(17 + state['day']).shuffle(edges)
        pairs, used = [], set()
        for pair in edges:
            if not used.intersection(pair):
                pairs.append(list(pair))
                used.update(pair)
    return {'pairs': pairs, 'memory': memory}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', choices=['greedy', 'no_asks', 'random'], default=None)
    parser.add_argument('--method', choices=['safe_core', 'learned_greedy', 'learned_maxweight',
                                            'uncertainty_first', 'degree_first', 'graphvoi',
                                            'graphvoi_no_pairs', 'graphvoi_wait', 'graphvoi_nofill'], default='graphvoi')
    parser.add_argument('--answer-perturbation', choices=['none', 'biased', 'overconfident',
                        'underconfident', 'refusal', 'subgroup_refusal', 'temporal_drift'], default='none')
    args = parser.parse_args()
    request = json.load(sys.stdin)
    if args.baseline is not None:
        response = decide(request, args.baseline)
    else:
        from graphvoi.policy import decide as orbit_decide
        response = orbit_decide(request, method=args.method, perturbation=args.answer_perturbation)
    print(json.dumps(response, allow_nan=False))
