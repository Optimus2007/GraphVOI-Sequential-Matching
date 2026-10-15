"""Compact, reviewable exports of a study: per-episode CSV plus a summary JSON.

The raw study JSON and per-episode traces are large; they are archived with a
SHA-256 instead of committed. Everything here is recomputed from them.

Waiting is censor-aware: an unserved member is censored at the last decision
day (59) instead of being dropped, so policies that serve fewer people cannot
look faster just because only their easy cases are measured.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

FIELDS = ('method', 'variant', 'seed', 'valid', 'msmi_per_100_arrived_members', 'mutual_second_meeting_intention',
          'mutual_acceptances', 'dates', 'assignments', 'coverage', 'served_members', 'unserved_members',
          'arrived_members', 'ask_cost', 'missing_feedback', 'inference_seconds', 'max_ask_seconds',
          'max_match_seconds', 'deadline_count', 'fallback_count', 'belief', 'actual_disclosure',
          'action_sha256', 'error')


def kaplan_meier(times, events, horizon=14):
    """Return (median, P(first introduction within `horizon` days))."""
    at_risk, survival, median, within = len(times), 1.0, None, None
    for t in sorted(set(times)):
        d = sum(1 for x, e in zip(times, events) if x == t and e)
        if t > horizon and within is None:
            within = 1 - survival
        if d and at_risk:
            survival *= 1 - d / at_risk
        if median is None and survival <= .5:
            median = t
        at_risk -= sum(1 for x in times if x == t)
    return median, (1 - survival if within is None else within)


def pooled_calibration(rows, key):
    bins = [dict(count=0, predicted=0.0, observed=0.0) for _ in range(10)]
    brier = count = 0.0
    for r in rows:
        c = r.get('calibration', {}).get('by_direction', {}).get(key) if key else r.get('calibration', {}).get('recorded_yes')
        if not c or not c.get('count'):
            continue
        brier += c['brier'] * c['count']
        count += c['count']
        for b, x in zip(bins, c['reliability']):
            if x['count']:
                b['count'] += x['count']
                b['predicted'] += x['predicted'] * x['count']
                b['observed'] += x['observed'] * x['count']
    return dict(labels=int(count), brier=brier / count if count else None,
                reliability=[dict(bin=i, count=b['count'],
                                  predicted=b['predicted'] / b['count'] if b['count'] else None,
                                  observed=b['observed'] / b['count'] if b['count'] else None)
                             for i, b in enumerate(bins)])


def opportunity(trace_root, rows):
    """Per method and subgroup: served share, exposure, censor-aware waiting."""
    groups = {}
    for r in rows:
        path = trace_root / f"{r['variant']}_{r['seed']}_{r['method']}.json"
        if not path.exists():
            return None
        members = json.loads(path.read_text())['opportunity']['members']
        for m in members:
            if m['arrived_day'] > 59:
                continue
            for dim in ('all', 'gender', 'age_band'):
                name = 'all' if dim == 'all' else m[dim]
                g = groups.setdefault(r['method'], {}).setdefault(dim, {}).setdefault(
                    name, dict(times=[], events=[], open_times=[], open_events=[], intros=0, eligible=0,
                         ask_cost=0, blocked=0))
                served = m['first_introduction_day'] is not None
                g['times'].append(m['wait_days'] if served else 59 - m['arrived_day'])
                g['events'].append(served)
                g['intros'] += m['introductions']
                g['eligible'] += m['eligible_opportunities']
                g['ask_cost'] += m['ask_cost']
                blocked = m['classification'] == 'blocked_by_declined_hard_field'
                g['blocked'] += blocked
                if not blocked:
                    g['open_times'].append(g['times'][-1])
                    g['open_events'].append(served)
    out = {}
    for method, dims in groups.items():
        for dim, names in dims.items():
            for name, g in names.items():
                n = len(g['times'])
                median, within14 = kaplan_meier(g['times'], g['events'])
                open_median, open_within14 = kaplan_meier(g['open_times'], g['open_events'])
                out.setdefault(method, {}).setdefault(dim, {})[name] = dict(
                    members=n, served_share=sum(g['events']) / n, km_median_wait_days=median,
                    km_served_within_14_days=within14, introductions_per_member=g['intros'] / n,
                    eligible_partners_per_member=g['eligible'] / n, ask_units_per_member=g['ask_cost'] / n,
                    declined_hard_field_share=g['blocked'] / n,
                    servable_members=len(g['open_times']),
                    servable_served_share=sum(g['open_events']) / max(1, len(g['open_times'])),
                    servable_km_median_wait_days=open_median,
                    servable_km_served_within_14_days=open_within14)
    return out


def daily_spend(trace_root, rows):
    """Mean ask units spent on each decision day, per method."""
    totals, counts = {}, {}
    for r in rows:
        path = trace_root / f"{r['variant']}_{r['seed']}_{r['method']}.json"
        if not path.exists():
            return None
        spend = totals.setdefault(r['method'], [0.0] * 60)
        counts[r['method']] = counts.get(r['method'], 0) + 1
        for a in json.loads(path.read_text())['actions']:
            if a['phase'] == 'ask':
                spend[a['day']] += sum(3 if q['field'] == 'constraints' else 1 for q in a['action'])
    return {m: [x / counts[m] for x in v] for m, v in totals.items()}


def preference_audit(trace_root, rows):
    """Re-check every introduction against members' TRUE stated hard preferences.

    Evaluation-side only: worlds are regenerated here to read truth; the policy
    never sees it. Returns introductions checked and violations, per method.
    """
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from kit import HARD, eligibility, generate
    worlds, out = {}, {}
    for r in rows:
        path = trace_root / f"{r['variant']}_{r['seed']}_{r['method']}.json"
        if not path.exists():
            return None
        key = (r['seed'], r['variant'])
        if key not in worlds:
            members = generate(r['seed'], 200, 'evaluation', r['variant'])['members']
            worlds[key] = {m['member_id']: dict(m, fields=m['truth']) for m in members}
        truth = worlds[key]
        o = out.setdefault(r['method'], dict(introductions=0, violations=0, declined_member_introduced=0))
        for a in json.loads(path.read_text())['actions']:
            if a['phase'] != 'match':
                continue
            for x, y in a['action']:
                o['introductions'] += 1
                o['violations'] += eligibility(truth[x], truth[y])['status'] == 'infeasible'
                o['declined_member_introduced'] += any(truth[i]['field_status'][k] == 'declined'
                                                       for i in (x, y) for k in HARD)
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument('raw')
    p.add_argument('--name', required=True)
    args = p.parse_args()
    raw = Path(args.raw)
    d = json.loads(raw.read_text())
    out = Path('results') / args.name
    out.mkdir(parents=True, exist_ok=True)
    rows = d['episodes']
    with open(out / 'episodes.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction='ignore')
        w.writeheader()
        for r in rows:
            rt = r.get('phase_runtime', {})
            w.writerow({**r, 'max_ask_seconds': rt.get('ask', {}).get('maximum'),
                        'max_match_seconds': rt.get('match', {}).get('maximum')})
    methods = sorted({r['method'] for r in rows})
    valid = [r for r in rows if r.get('valid')]
    summary = {k: d.get(k) for k in ('complete', 'expected_design', 'purpose', 'summaries', 'secondary',
                                     'paired_intervals', 'code_sha256', 'asset_sha256', 'acquisition',
                                     'python_version', 'workers', 'elapsed_seconds', 'conditions', 'seeds')
               if k in d}
    summary['raw_sha256'] = hashlib.sha256(raw.read_bytes()).hexdigest()
    summary['raw_file'] = raw.name
    summary['calibration'] = {m: {k: pooled_calibration([r for r in valid if r['method'] == m], k)
                                  for k in ('a_accepts_b', 'b_accepts_a', None)} for m in methods}
    for m in summary['calibration']:
        summary['calibration'][m]['both_directions'] = summary['calibration'][m].pop(None)
    summary['opportunity'] = opportunity(raw.parent / (raw.stem + '_traces'), valid)
    summary['daily_ask_units'] = daily_spend(raw.parent / (raw.stem + '_traces'), valid)
    summary['true_preference_audit'] = preference_audit(raw.parent / (raw.stem + '_traces'), valid)
    summary['calibration_by_gender'] = {m: {g: {k: [r['calibration']['by_gender'][g][k]
                                                   for r in valid if r['method'] == m
                                                   and r.get('calibration', {}).get('by_gender', {}).get(g, {}).get('count')]
                                               for k in ('count', 'brier')}
                                           for g in ('woman', 'man', 'non_binary')} for m in methods}
    for m, gs in summary['calibration_by_gender'].items():
        for g, v in gs.items():
            n = sum(v['count'])
            gs[g] = dict(labels=n, brier=sum(c * b for c, b in zip(v['count'], v['brier'])) / n if n else None)
    (out / 'summary.json').write_text(json.dumps(summary, indent=1, allow_nan=False) + '\n')
    print(out, len(rows), 'episodes', round((out / 'summary.json').stat().st_size / 1e6, 2), 'MB summary')


if __name__ == '__main__':
    raise SystemExit(main())
