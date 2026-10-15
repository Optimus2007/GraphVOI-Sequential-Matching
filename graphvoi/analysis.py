"""Observed trajectory diagnostics, calibration and paired uncertainty."""
import collections
import math
import random
import statistics

from kit import HARD, eligibility
from .core import available_members, past_pairs


def percentile(values, p):
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * p
    lo, hi = math.floor(index), math.ceil(index)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (index - lo)


class OpportunityTracker:
    def __init__(self):
        self.members = {}

    def observe(self, state, asks, pairs):
        served = {i for pair in pairs for i in pair}
        active = available_members(state)
        past = past_pairs(state)
        for m in state['members']:
            ident = m['member_id']
            self.members.setdefault(ident, dict(arrived_day=m['arrived_day'], gender=m['gender'],
                age_band='21-29' if m['age'] < 30 else '30-39' if m['age'] < 40 else '40+',
                zone=m['zone'], first_introduction_day=None, introductions=0,
                available_days=0, feasible_days=0, unresolved_days=0,
                known_infeasible_days=0, no_other_available_days=0,
                hard_declined_days=0, feasible_wait_days=0,
                opportunity_partners=set(), ask_cost=0, asks=0))
        for m in active:
            record = self.members[m['member_id']]
            record['available_days'] += 1
            feasible, unresolved, tested = [], 0, 0
            for other in active:
                if other['member_id'] == m['member_id'] or tuple(sorted((m['member_id'], other['member_id']))) in past:
                    continue
                tested += 1
                status = eligibility(m, other)['status']
                if status == 'feasible':
                    feasible.append(other['member_id'])
                elif status == 'needs_clarification':
                    unresolved += 1
            if any(m['field_status'][k] == 'declined' for k in HARD):
                record['hard_declined_days'] += 1
            if feasible:
                record['feasible_days'] += 1
                record['opportunity_partners'].update(feasible)
                record['feasible_wait_days'] += m['member_id'] not in served
            elif unresolved:
                record['unresolved_days'] += 1
            elif tested:
                record['known_infeasible_days'] += 1
            else:
                record['no_other_available_days'] += 1
        for ask in asks:
            r = self.members[ask['member_id']]
            r['asks'] += 1
            r['ask_cost'] += 3 if ask['field'] == 'constraints' else 1
        for pair in pairs:
            for ident in pair:
                r = self.members[ident]
                r['introductions'] += 1
                if r['first_introduction_day'] is None:
                    r['first_introduction_day'] = state['day']

    def results(self):
        rows = []
        for ident, record in sorted(self.members.items()):
            r = dict(record, member_id=ident)
            r['eligible_opportunities'] = len(r.pop('opportunity_partners'))
            first = r['first_introduction_day']
            r['wait_days'] = None if first is None else first - r['arrived_day']
            r['classification'] = ('served' if first is not None else
                'feasible_but_never_introduced' if r['feasible_days'] else
                'blocked_by_declined_hard_field' if r['hard_declined_days'] else
                'unresolved_observed_constraints' if r['unresolved_days'] else
                'no_observed_feasible_opportunity')
            rows.append(r)
        groups = {}
        for dimension in ('gender', 'age_band', 'zone'):
            groups[dimension] = {}
            for name in sorted({r[dimension] for r in rows}):
                rs = [r for r in rows if r[dimension] == name]
                waits = [r['wait_days'] for r in rs if r['wait_days'] is not None]
                groups[dimension][name] = dict(count=len(rs), served=len(waits),
                    unserved=len(rs) - len(waits), median_wait=percentile(waits, .5),
                    p90_wait=percentile(waits, .9),
                    mean_exposure=statistics.mean(r['introductions'] for r in rs),
                    mean_eligible_opportunities=statistics.mean(r['eligible_opportunities'] for r in rs),
                    clarification_cost=sum(r['ask_cost'] for r in rs),
                    classification_counts=dict(collections.Counter(r['classification'] for r in rs)))
        waits = [r['wait_days'] for r in rows if r['wait_days'] is not None]
        return dict(members=rows, groups=groups, median_wait=percentile(waits, .5),
                    p90_wait=percentile(waits, .9), unserved=len(rows) - len(waits),
                    limitation='Eligibility/opportunities are observable and time-varying, not hidden truth; wait summaries condition on served members.')


def calibration(rows):
    """Rows contain p,y, direction and group; labels must be mature recorded events."""
    if not rows:
        return dict(count=0, brier=None, log_loss=None, reliability=[])
    brier = statistics.mean((r['p'] - r['y']) ** 2 for r in rows)
    logloss = statistics.mean(-(r['y'] * math.log(max(1e-12, r['p'])) +
                                (1 - r['y']) * math.log(max(1e-12, 1 - r['p']))) for r in rows)
    bins = []
    for i in range(10):
        rs = [r for r in rows if min(9, int(r['p'] * 10)) == i]
        bins.append(dict(lower=i / 10, upper=(i + 1) / 10, count=len(rs),
                         predicted=statistics.mean(r['p'] for r in rs) if rs else None,
                         observed=statistics.mean(r['y'] for r in rs) if rs else None))
    return dict(count=len(rows), positives=sum(r['y'] for r in rows), brier=brier,
                log_loss=logloss, reliability=bins)


def comparison_design(rows, method, reference, expected_pairs=None):
    """Validate complete paired records without discarding failures or duplicates."""
    relevant = [r for r in rows if r['method'] in (method, reference)]
    expected = set(expected_pairs) if expected_pairs is not None else {(r['variant'], r['seed']) for r in rows}
    counts = collections.Counter((r['method'], r['variant'], r['seed']) for r in relevant)
    invalid = {m: sum(not r.get('valid', False) for r in relevant if r['method'] == m)
               for m in (method, reference)}
    missing = {m: sorted(expected - {(r['variant'], r['seed']) for r in relevant if r['method'] == m})
               for m in (method, reference)}
    duplicate = sorted(k for k, n in counts.items() if n != 1)
    unexpected = sorted({(r['variant'], r['seed']) for r in relevant} - expected)
    status = ('invalid' if any(invalid.values()) else 'duplicate' if duplicate else
              'incomplete' if not expected or any(missing.values()) or unexpected else 'complete')
    return dict(status=status, invalid_counts=invalid, missing_pairs=missing,
                duplicate_keys=duplicate, unexpected_pairs=unexpected,
                expected_pairs=len(expected), recorded_counts={m: sum(r['method']==m for r in relevant)
                                                             for m in (method, reference)})


def paired_intervals(rows, reference='uncertainty_first', replicates=2000,
                     expected_pairs=None, expected_methods=None):
    """Official failures block inference; stratified paired seed-cluster bootstrap.

    Strata are the set of scenarios containing a seed. Sampling an entire seed
    within that stratum preserves cross-scenario covariance and every original
    family denominator, even for partially overlapping or imbalanced seed sets.
    """
    methods = sorted(({r['method'] for r in rows} | set(expected_methods or [])) - {reference})
    indexed = {(r['method'], r['variant'], r['seed']): r for r in rows}
    expected = set(expected_pairs) if expected_pairs is not None else {(r['variant'],r['seed']) for r in rows}
    core_metrics = ('msmi_per_100_arrived_members','mutual_acceptances_per_100','coverage','ask_cost')
    out = {}
    for method in methods:
        relevant=[r for r in rows if r['method'] in (method,reference)]
        metrics=core_metrics+tuple(k for k in ('dates','mutual_acceptances','unserved_members','inference_seconds')
                                  if relevant and all(k in r for r in relevant))
        design = comparison_design(rows, method, reference, expected)
        out[method] = {'validation': design}
        families = {v: sorted(s for w,s in expected if w==v) for v in sorted({v for v,_ in expected})}
        if design['status'] != 'complete':
            for metric in metrics:
                out[method][metric] = dict(status=design['status'], delta=None, ci95=None,
                    invalid_counts=design['invalid_counts'], paired_counts={v:0 for v in families},
                    reliable_sample_size=False, note='No performance inference: invalid, missing or duplicate expected episodes.')
            continue
        # An official valid flag is necessary but not sufficient for usable numeric metrics.
        for r in rows:
            if r['method'] in (method,reference):
                if any(not isinstance(r.get(k),(int,float)) or not math.isfinite(r[k]) for k in metrics):
                    raise ValueError('Valid episode has missing/nonfinite metric')
        membership = {}
        for seed in sorted({s for _,s in expected}):
            signature=tuple(v for v,seeds in families.items() if seed in seeds)
            membership.setdefault(signature,[]).append(seed)
        for metric in metrics:
            differences = {(v,s): indexed[method,v,s][metric]-indexed[reference,v,s][metric]
                           for v,s in expected}
            rng=random.Random(771); draws=[]
            for _ in range(replicates):
                totals={v:0.0 for v in families}
                for signature,seeds in membership.items():
                    for seed in rng.choices(seeds,k=len(seeds)):
                        for v in signature: totals[v]+=differences[v,seed]
                draws.append(statistics.mean(totals[v]/len(families[v]) for v in families))
            family_deltas={v:statistics.mean(differences[v,s] for s in seeds) for v,seeds in families.items()}
            out[method][metric]=dict(status='complete',delta=statistics.mean(family_deltas.values()),
                scenario_deltas=family_deltas,ci95=[percentile(draws,.025),percentile(draws,.975)],
                ci97_5_bonferroni2=[percentile(draws,.0125),percentile(draws,.9875)],
                paired_counts={v:len(seeds) for v,seeds in families.items()},invalid_counts=design['invalid_counts'],
                reliable_sample_size=min(map(len,membership.values()))>=20,
                bootstrap='paired seed clusters stratified by scenario membership, equal scenario weights',
                cluster_counts={','.join(k):len(v) for k,v in membership.items()},
                note='Retain all records; failures block inference. Small pilot bootstrap intervals have limited support.')
    return out
