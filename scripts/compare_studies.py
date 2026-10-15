"""Paired comparisons across separately run studies on the same seeds.

Rows are only paired when both studies ran the identical policy and runner code
(same SHA-256 for graphvoi/*.py and the runner modules) and the same assets.
Writes results/ablations/paired.json and results/disclosure/paired.json.
"""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluate import VARIANTS
from graphvoi.analysis import paired_intervals

SHARED = [k for k in ('graphvoi/__init__.py', 'graphvoi/analysis.py', 'graphvoi/answers.py',
                      'graphvoi/clarification.py', 'graphvoi/core.py', 'graphvoi/models.py',
                      'graphvoi/policy.py', 'scripts/run_experiments.py', 'scripts/run_pilot.py')]
METRICS = ('msmi_per_100_arrived_members', 'mutual_acceptances', 'dates', 'coverage', 'ask_cost')


def same_code(a, b):
    bad = [k for k in SHARED if a['code_sha256'].get(k) != b['code_sha256'].get(k)]
    if bad:
        raise SystemExit(f'Refusing to pair: code differs in {bad}')
    if 'asset_sha256' in a and 'asset_sha256' in b and a['asset_sha256'] != b['asset_sha256']:
        raise SystemExit('Refusing to pair: model assets differ')


def compact(result):
    return {m: {k: {x: v.get(x) for x in ('status', 'delta', 'ci95', 'scenario_deltas')}
                for k, v in block.items() if k in METRICS}
            for m, block in result.items()}


def ablations(confirm):
    path = Path('results/v3_ablations.json')
    if not path.exists():
        return print('skip ablations: missing', path)
    abl = json.loads(path.read_text())
    same_code(confirm, abl)
    seeds = abl['expected_design']['seeds']
    rows = [r for r in confirm['episodes'] + abl['episodes'] if r['seed'] in seeds]
    expected = {(v, s) for v in VARIANTS for s in seeds}
    methods = sorted({r['method'] for r in rows})
    out = {ref: compact(paired_intervals(rows, reference=ref, expected_pairs=expected, expected_methods=methods))
           for ref in ('graphvoi', 'learned_maxweight', 'learned_greedy')}
    Path('results/ablations').mkdir(parents=True, exist_ok=True)
    Path('results/ablations/paired.json').write_text(json.dumps(out, indent=1) + '\n')
    print('wrote results/ablations/paired.json')


def disclosure(confirm):
    path = Path('results/v3_disclosure.json')
    if not path.exists():
        return print('skip disclosure: missing', path)
    dis = json.loads(path.read_text())
    if not dis.get('complete'):
        raise SystemExit('Disclosure study incomplete')
    same_code(confirm, dis)
    lo, hi = dis['seeds']
    seeds = set(range(lo, hi + 1))
    expected = {(v, s) for v in VARIANTS for s in seeds}
    base = {(r['method'], r['variant'], r['seed']): r for r in confirm['episodes'] if r['seed'] in seeds}
    out = {}
    for method, belief, actual in dis['conditions']:
        cond = [r for r in dis['episodes']
                if (r['method'], r.get('belief'), r.get('actual_disclosure')) == (method, belief, actual)]
        tag = f'{method}|belief={belief}|actual={actual}'
        # Degradation: condition versus the same method's unperturbed confirmatory rows.
        rows = [dict(r, method='perturbed') for r in cond] + \
               [dict(base[(method, v, s)], method='reference') for v, s in sorted(expected)]
        out[tag] = compact(paired_intervals(rows, reference='reference', expected_pairs=expected,
                                            expected_methods=['perturbed', 'reference']))['perturbed']
    # Within a shifted environment: GraphVOI against each comparator.
    for actual in sorted({c[2] for c in dis['conditions'] if c[2] != 'none'}):
        rows = [r for r in dis['episodes'] if r.get('actual_disclosure') == actual]
        methods = sorted({r['method'] for r in rows})
        for ref in methods:
            if ref != 'graphvoi':
                res = paired_intervals(rows, reference=ref, expected_pairs=expected, expected_methods=methods)
                out[f'graphvoi_minus_{ref}|actual={actual}'] = compact(res)['graphvoi']
    Path('results/disclosure').mkdir(parents=True, exist_ok=True)
    Path('results/disclosure/paired.json').write_text(json.dumps(out, indent=1) + '\n')
    print('wrote results/disclosure/paired.json')


def matched(confirm):
    """Belief that matches the changed environment versus the unaware ('none') belief."""
    m_path, d_path = Path('results/v3_disclosure_matched.json'), Path('results/v3_disclosure.json')
    if not (m_path.exists() and d_path.exists()):
        return print('skip matched beliefs: missing input')
    mat, dis = json.loads(m_path.read_text()), json.loads(d_path.read_text())
    if not mat.get('complete'):
        raise SystemExit('Matched-belief study incomplete')
    same_code(confirm, mat)
    lo, hi = mat['seeds']
    expected = {(v, s) for v in VARIANTS for s in range(lo, hi + 1)}
    out = {}
    for _, belief, actual in mat['conditions']:
        rows = [dict(r, method='matched') for r in mat['episodes']
                if r.get('belief') == belief and r.get('actual_disclosure') == actual] + \
               [dict(r, method='unaware') for r in dis['episodes'] if r['method'] == 'graphvoi'
                and r.get('belief') == 'none' and r.get('actual_disclosure') == actual]
        res = paired_intervals(rows, reference='unaware', expected_pairs=expected,
                               expected_methods=['matched', 'unaware'])
        out[f'graphvoi|belief={belief}_minus_none|actual={actual}'] = compact(res)['matched']
    path = Path('results/disclosure/matched_beliefs.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=1) + '\n')
    print('wrote', path)


def main():
    confirm = json.loads(Path('results/v3_confirmatory.json').read_text())
    if not confirm.get('complete'):
        raise SystemExit('Confirmatory study incomplete')
    ablations(confirm)
    disclosure(confirm)
    matched(confirm)


if __name__ == '__main__':
    main()
