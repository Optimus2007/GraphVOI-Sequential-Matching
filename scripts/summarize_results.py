"""Summarize actual runs; calibration uncertainty is clustered by episode."""
import argparse
import json
from pathlib import Path
import random
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from graphvoi.analysis import calibration, paired_intervals, percentile


def clustered_calibration(episodes):
    rows = [r for episode in episodes for r in episode]
    result = calibration(rows)
    result['episode_count'] = len(episodes)
    result['uncertainty_supported'] = len(episodes) >= 20
    if episodes and rows:
        if len(episodes) == 1:
            for metric in ('brier', 'log_loss'):
                result[metric + '_ci95'] = [result[metric], result[metric]]
            result['ci_note'] = 'A single independent world seed gives a degenerate cluster bootstrap; no inferential uncertainty estimate is supported.'
            return result
        rng = random.Random(882)
        draws = [calibration([r for episode in rng.choices(episodes, k=len(episodes)) for r in episode])
                 for _ in range(1000)]
        for metric in ('brier', 'log_loss'):
            values = [d[metric] for d in draws if d[metric] is not None]
            result[metric + '_ci95'] = [percentile(values, .025), percentile(values, .975)]
    return result


def stage_labels(trace):
    by_intro = {}
    for e in trace['feedback']:
        by_intro.setdefault(e['introduction_id'], []).append(e)
    rows = {k: [] for k in ('mutual_acceptance', 'date_given_mutual', 'timely_seconds_given_date')}
    for record in trace['predictions']:
        intro, prediction = record['introduction'], record['prediction']
        events = by_intro.get(intro['introduction_id'], [])
        responses = [e for e in events if e['event'] == 'introduction_response']
        if len(responses) != 2:
            continue
        mutual = all(e['value'] == 'yes' and e['observed_day'] <= intro['response_deadline_day'] for e in responses)
        rows['mutual_acceptance'].append(dict(p=prediction['mutual_acceptance'], y=int(mutual)))
        if not mutual:
            continue
        dates = [e for e in events if e['event'] == 'date_happened']
        if not dates:
            continue
        date = dates[0]
        completed = date['value'] is True and date['occurred_day'] - intro['assigned_day'] <= 30
        rows['date_given_mutual'].append(dict(p=prediction['date_given_mutual'], y=int(completed)))
        if not completed:
            continue
        seconds = [e for e in events if e['event'] == 'second_meeting_intention']
        if len(seconds) == 2:
            positive = all(e['value'] == 'yes' and e['occurred_day'] is not None
                           and e['occurred_day'] - date['occurred_day'] <= 3 for e in seconds)
            rows['timely_seconds_given_date'].append(dict(p=prediction['timely_seconds_given_date'], y=int(positive)))
    return rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', default='results/paired_smoke.json')
    p.add_argument('--output', default='results/analysis_summary.json')
    args = p.parse_args()
    source = Path(args.input)
    data = json.loads(source.read_text())
    methods = sorted({r['method'] for r in data['episodes']})
    root = source.parent / (source.stem + '_traces')
    out = dict(source=str(source), complete=data['complete'], calibration={},
               outcome_summaries=data['summaries'], paired_intervals=paired_intervals(data['episodes']),
               caveat='Bootstrap clusters are entire world seeds, including all paired directions and scenarios. Few worlds do not support reliable CIs.')
    for method in methods:
        by_seed = {}
        stages_by_seed = {k: {} for k in ('mutual_acceptance', 'date_given_mutual', 'timely_seconds_given_date')}
        for path in sorted(root.glob(f'*_{method}.json')):
            trace = json.loads(path.read_text())
            by_seed.setdefault(trace['metrics']['seed'], []).extend(trace['calibration_labels'])
            for key, values in stage_labels(trace).items():
                stages_by_seed[key].setdefault(trace['metrics']['seed'], []).extend(values)
        episodes = list(by_seed.values())
        out['calibration'][method] = dict(overall=clustered_calibration(episodes),
            directions={d: clustered_calibration([[r for r in ep if r['direction'] == d] for ep in episodes])
                        for d in ('a_accepts_b', 'b_accepts_a')},
            genders={g: clustered_calibration([[r for r in ep if r['groups']['gender'] == g] for ep in episodes])
                     for g in ('woman', 'man', 'non_binary')},
            conditional_stages={k: clustered_calibration(list(values.values())) for k, values in stages_by_seed.items()})
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
