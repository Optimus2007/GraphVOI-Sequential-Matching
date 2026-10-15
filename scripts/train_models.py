"""Train from public simulator rollouts, retaining only pre-action observations."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kit import HARD, SOFT, Simulator, baseline_asks, baseline_match, generate
from evaluate import VARIANTS
from graphvoi.core import pair_features
from graphvoi.models import fit_logistic, symmetric_features


def collect(seed, variant):
    sim = Simulator(generate(seed, 200, f'train_{seed}', variant))
    examples = []
    for _ in range(60):
        sim.resolve_asks(baseline_asks(sim.observe()))
        state = sim.observe()
        members = {m['member_id']: m for m in state['members']}
        pairs = baseline_match(state)
        before = len(sim.introductions)
        sim.advance(pairs)
        for intro in sim.introductions[before:]:
            a, b = members[intro['user_a']], members[intro['user_b']]
            examples.append((copy.deepcopy(intro), pair_features(a, b, state['day']),
                             pair_features(b, a, state['day']), symmetric_features(a, b, state['day'])))
    for _ in range(40):
        sim.advance([])
    # Only observed feedback, including legitimate maturation follow-up.
    events = {}
    for event in sim.receive_feedback():
        events.setdefault(event['introduction_id'], []).append(event)
    return examples, events, sim.observe()['members']


def labelled_rows(examples, events):
    rows = {k: [] for k in ('directional_acceptance', 'mutual_acceptance',
                            'date_given_mutual', 'timely_seconds_given_date')}
    censored = 0
    for intro, xa, xb, xs in examples:
        es = events.get(intro['introduction_id'], [])
        responses = {e['member_id']: e for e in es if e['event'] == 'introduction_response'}
        if len(responses) != 2:
            censored += 1
            continue
        labels = []
        for ident, features in ((intro['user_a'], xa), (intro['user_b'], xb)):
            event = responses[ident]
            y = int(event['value'] == 'yes' and event['observed_day'] <= intro['response_deadline_day'])
            rows['directional_acceptance'].append((features, y))
            labels.append(y)
        mutual = int(all(labels))
        rows['mutual_acceptance'].append((xs, mutual))
        if not mutual:
            continue
        dates = [e for e in es if e['event'] == 'date_happened']
        if not dates:
            censored += 1
            continue
        date = dates[0]
        completed = date['value'] is True and date['occurred_day'] - intro['assigned_day'] <= 30
        rows['date_given_mutual'].append((xs, int(completed)))
        if not completed:
            continue
        seconds = [e for e in es if e['event'] == 'second_meeting_intention']
        if len(seconds) != 2:
            censored += 1
            continue
        y = int(all(e['value'] == 'yes' and e['occurred_day'] is not None and
                    e['occurred_day'] - date['occurred_day'] <= 3 for e in seconds))
        rows['timely_seconds_given_date'].append((xs, y))
    return rows, censored


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', default='31001,31002,31003,31004,31005,31006,31007,31008')
    parser.add_argument('--output', default='assets')
    args = parser.parse_args()
    seeds = list(map(int, args.seeds.split(',')))
    all_rows = {k: [] for k in ('directional_acceptance', 'mutual_acceptance',
                               'date_given_mutual', 'timely_seconds_given_date')}
    donors, soft_counts, censor_count = [], {k: {} for k in SOFT}, 0
    for variant in VARIANTS:
        for seed in seeds:
            examples, events, members = collect(seed, variant)
            rows, censored = labelled_rows(examples, events)
            censor_count += censored
            for k, values in rows.items():
                all_rows[k].extend(values)
            for m in members:
                if all(m['fields'][k] is not None and m['field_status'][k] == 'observed' for k in HARD):
                    donors.append({k: copy.deepcopy(m[k]) for k in ('age', 'gender', 'zone')} |
                                  {'fields': {k: copy.deepcopy(m['fields'][k]) for k in HARD}})
                for k in SOFT:
                    value = m['fields'][k]
                    if value is not None and m['field_status'][k] == 'observed':
                        soft_counts[k][value] = soft_counts[k].get(value, 0) + 1
            print(json.dumps(dict(seed=seed, variant=variant, introductions=len(examples))), flush=True)
    dimensions = len(next(x for values in all_rows.values() for x, _ in values))
    models = {k: fit_logistic(values, dimensions) for k, values in all_rows.items()}
    meta = dict(schema_version='1.0.0', source='public simulator observed rollouts',
                training_seeds=seeds, variants=list(VARIANTS), censor_count=censor_count,
                feature_version=1, iterations=100, l2_penalty=.05,
                logging_policy='official greedy', inference_random_seed='none; deterministic',
                limitations=['selective labels', 'baseline-conditional training distribution',
                             'joint-stage model has limited rare-outcome support',
                             'conditional donor selection and bounded support approximation'])
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    (out / 'pair_model.json').write_text(json.dumps(dict(meta, models=models), indent=2) + '\n')
    (out / 'answer_model.json').write_text(json.dumps(dict(meta, hard_donors=donors,
                                                        soft_counts=soft_counts), separators=(',', ':')) + '\n')
    (out / 'training_summary.json').write_text(json.dumps(dict(meta, stages={k: {
        field: m[field] for field in ('count', 'positives', 'fitted_features')} for k, m in models.items()},
        donor_count=len(donors), asset_sha256={name: hashlib.sha256((out / name).read_bytes()).hexdigest()
                                               for name in ('pair_model.json', 'answer_model.json')}), indent=2) + '\n')


if __name__ == '__main__':
    main()
