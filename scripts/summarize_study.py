"""Render report tables from a run_study.py result; numbers are never hand-typed."""
import argparse
import json
import statistics
import sys


def fmt(x, digits=3):
    return 'n/a' if x is None else f'{x:+.{digits}f}' if digits and x < 0 else f'{x:.{digits}f}'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('result')
    args = p.parse_args()
    d = json.load(open(args.result))
    design = d['expected_design']
    methods, variants = design['methods'], design['variants']
    episodes = d['episodes']
    out = [f"Design: {len(design['seeds'])} seeds x {len(variants)} families x {len(methods)} methods; "
           f"complete={d['complete']}; recorded={len(episodes)}; "
           f"invalid={sum(not r.get('valid') for r in episodes)}; wall={d.get('elapsed_seconds', 0)/3600:.2f} h", '']
    out += ['| Method | MSMI/100 | Mutual accepts/ep | Dates/ep | Coverage | Ask cost/ep | Missing feedback/ep '
            '| Unserved/ep | Served wait median/p90 | Invalid |', '|---|' + '---:|' * 9]
    for m in methods:
        s, rs = d['summaries'][m], [r for r in episodes if r['method'] == m and r.get('valid')]
        sec = d['secondary'].get(m, {})
        mean = lambda k: statistics.mean(r[k] for r in rs) if rs else None
        out.append(f"| {m} | {fmt(s.get('primary_score'))} | {fmt(mean('mutual_acceptances'), 2)} | "
                   f"{fmt(mean('dates'), 2)} | {fmt(100 * mean('coverage'), 1)}% | {fmt(mean('ask_cost'), 1)} | "
                   f"{fmt(mean('missing_feedback'), 1)} | {fmt(mean('unserved_members'), 1)} | "
                   f"{fmt(sec.get('served_wait_median'), 1)}/{fmt(sec.get('served_wait_p90'), 1)} | {s.get('invalid_count')} |")
    out += ['', '| Scenario | ' + ' | '.join(methods) + ' |', '|---|' + '---:|' * len(methods)]
    for v in variants:
        cells = [fmt(d['summaries'][m].get('scenario_means', {}).get(v, {}).get('msmi_per_100_arrived_members'))
                 for m in methods]
        out.append(f'| {v} | ' + ' | '.join(cells) + ' |')
    out += ['', '| Comparison (A − B) | Metric | Delta | 95% CI | 97.5% CI (Bonferroni, 2 primary) |',
            '|---|---|---:|---:|---:|']
    pi = d.get('paired_intervals') or {}
    for ref, block in pi.items():
        for m, metrics in block.items():
            if not m.startswith('graphvoi'):
                continue
            for metric in ('msmi_per_100_arrived_members', 'mutual_acceptances', 'dates', 'coverage', 'ask_cost'):
                r = metrics.get(metric)
                if not r:
                    continue
                if r['status'] != 'complete':
                    out.append(f"| {m} − {ref} | {metric} | {r['status']} | — | — |")
                    continue
                ci, cb = r['ci95'], r.get('ci97_5_bonferroni2')
                out.append(f"| {m} − {ref} | {metric} | {fmt(r['delta'])} | [{fmt(ci[0])}, {fmt(ci[1])}] | "
                           + (f"[{fmt(cb[0])}, {fmt(cb[1])}]" if cb else '—') + ' |')
    rt = {}
    for r in episodes:
        if r.get('valid') and 'phase_runtime' in r:
            x = rt.setdefault(r['method'], dict(ask=0, match=0, total=[]))
            x['ask'] = max(x['ask'], r['phase_runtime']['ask']['maximum'])
            x['match'] = max(x['match'], r['phase_runtime']['match']['maximum'])
            x['total'].append(r['inference_seconds'])
    out += ['', '| Method | Mean inference s/episode | Max ask s | Max match s |', '|---|---:|---:|---:|']
    for m in methods:
        if m in rt:
            out.append(f"| {m} | {statistics.mean(rt[m]['total']):.1f} | {rt[m]['ask']:.3f} | {rt[m]['match']:.3f} |")
    print('\n'.join(out))


if __name__ == '__main__':
    sys.exit(main())
