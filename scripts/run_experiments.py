"""Complete paired research episodes; public observations serialized at boundary.

In-process mode is a fast trusted scientific runner, not official Docker validation.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import random
import statistics
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluate import VARIANTS, LIMIT, strict_json, summarise, validate_response
from kit import HARD, SOFT, Simulator, generate
from official_policy import decide as baseline_decide
from graphvoi.analysis import OpportunityTracker, calibration, paired_intervals, comparison_design
from graphvoi.models import PairModel
from graphvoi.policy import METHODS, decide, pair_model

CODE_SHA256 = {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
               for path in sorted(list(Path('graphvoi').glob('*.py')) + list(Path('scripts').glob('*.py')))}


def complete_summaries(rows, methods, expected_pairs):
    """Do not score a recorded prefix as the declared experiment."""
    result = {}
    for method in methods:
        records = [r for r in rows if r['method'] == method]
        design = comparison_design(records, method, method, expected_pairs)
        result[method] = (summarise(records) if design['status'] == 'complete' else
                          dict(eligible=False, primary_score=None,
                               reason=design['status'], validation=design))
        result[method].update(recorded_count=len(records),
                              invalid_count=sum(not r.get('valid', False) for r in records))
    return result


class DisclosureSimulator(Simulator):
    """Independent experimental wrapper. Changes disclosure, never preferences.

    The evaluated policy gets only ordinary observable JSON; no rate, RNG, seed,
    simulator or world object. This is NOT an official leaderboard environment.
    """
    rate = .35
    subgroup = None
    drift = False

    def __init__(self, world):
        super().__init__(world)
        self.disclosure_rng = random.Random(world['seed'] + 730000)

    def resolve_asks(self, asks):
        before = {q['member_id']: copy.deepcopy(self.members[q['member_id']]) for q in asks}
        result = super().resolve_asks(asks)
        for q, answer in zip(asks, result):
            m, old = self.members[q['member_id']], before[q['member_id']]
            rate = self.rate * (min(1, self.day / 35) if self.drift else 1)
            if self.subgroup and m['gender'] != self.subgroup:
                rate = 0
            keys = HARD if q['field'] == 'constraints' else [q['field']]
            # Bundle-level disclosure refusal, keeping earlier observations intact.
            if self.disclosure_rng.random() < rate:
                for key in keys:
                    if old['field_status'][key] == 'not_asked':
                        m['fields'][key] = None
                        m['field_status'][key] = 'declined'
                        m['field_observed_day'][key] = None
                        answer['values'][key] = None
                        answer['statuses'][key] = 'declined'
        if asks:
            self.ask_log[-len(asks):] = copy.deepcopy(result)
        return result


def research_episode(seed, variant, method, belief='none', actual='none', trace_path=None):
    world = generate(seed, 200, 'evaluation', variant)
    if actual != 'none':
        class ExperimentSimulator(DisclosureSimulator):
            subgroup = 'non_binary' if actual == 'subgroup' else None
            drift = actual == 'drift'
        sim = ExperimentSimulator(world)
    else:
        sim = Simulator(world)
    memory, timings, predictions, trace = None, {'ask': [], 'match': []}, [], []
    digest, tracker = hashlib.sha256(), OpportunityTracker()
    for _ in range(60):
        day_asks, match_state, pairs = [], None, []
        for phase in ('ask', 'match'):
            request = dict(schema_version='1.0.0', phase=phase, state=sim.observe(), memory=memory)
            raw = json.dumps(request, allow_nan=False)
            if len(raw.encode()) > LIMIT:
                raise ValueError('Request exceeds 1 MiB')
            # Explicit JSON boundary: no privileged Python objects cross it.
            public_request = strict_json(raw)
            started = time.perf_counter()
            response = (baseline_decide(public_request, method) if method in ('greedy', 'no_asks', 'random')
                        else decide(public_request, method=method, perturbation=belief))
            elapsed = time.perf_counter() - started
            if elapsed > 10:
                raise ValueError('Research invocation exceeded 10 seconds (startup excluded)')
            timings[phase].append(elapsed)
            encoded = json.dumps(response, allow_nan=False)
            if len(encoded.encode()) > LIMIT:
                raise ValueError('Response exceeds 1 MiB')
            response = validate_response(strict_json(encoded), phase)
            memory = response['memory']
            action = response['asks' if phase == 'ask' else 'pairs']
            digest.update(json.dumps([phase, sim.day, action], sort_keys=True).encode())
            trace.append(dict(day=sim.day, phase=phase, action=action, seconds=elapsed))
            if phase == 'ask':
                day_asks = action
                sim.resolve_asks(action)
            else:
                match_state, pairs = public_request['state'], action
                members = {m['member_id']: m for m in match_state['members']}
                before = len(sim.introductions)
                # Record predictions BEFORE outcomes, using only public inputs.
                pending = [(p, pair_model().stages(members[p[0]], members[p[1]], sim.day),
                            {i: {'gender': members[i]['gender'], 'age': members[i]['age'],
                                 'zone': members[i]['zone']} for i in p}) for p in pairs]
                tracker.observe(match_state, day_asks, pairs)
                sim.advance(action)
                new = {tuple(sorted((i['user_a'], i['user_b']))): i for i in sim.introductions[before:]}
                predictions.extend(dict(introduction=new[tuple(sorted(p))], prediction=prediction,
                                        groups=groups) for p, prediction, groups in pending)
    arrived = {m['member_id']: m['arrived_day'] for m in sim.observe()['members'] if m['arrived_day'] <= 59}
    for _ in range(40):
        sim.advance([])
    metrics = sim.metrics()
    opportunity = tracker.results()
    served = sum(r['introductions'] > 0 for r in opportunity['members'])
    metrics.update(valid=True, arrived_members=len(arrived), served_members=served,
        unserved_members=len(arrived) - served, coverage=served / max(1, len(arrived)),
        msmi_per_100_arrived_members=100 * metrics['mutual_second_meeting_intention'] / max(1, len(arrived)),
        mutual_acceptances_per_100=100 * metrics['mutual_acceptances'] / max(1, len(arrived)),
        first_introduction_wait_days=sorted(r['wait_days'] for r in opportunity['members'] if r['wait_days'] is not None),
        inference_seconds=sum(sum(x) for x in timings.values()),
        phase_runtime={k: dict(total=sum(x), maximum=max(x), p90=sorted(x)[53]) for k, x in timings.items()},
        action_sha256=digest.hexdigest(), seed=seed, variant=variant, method=method,
        belief=belief, actual_disclosure=actual,
        fallback_count=memory.get('orbit_fallback_count', 0) if isinstance(memory, dict) else 0,
        deadline_count=memory.get('orbit_deadline_count', 0) if isinstance(memory, dict) else 0)
    labels, by_intro = [], {}
    for event in sim.receive_feedback():
        by_intro.setdefault(event['introduction_id'], []).append(event)
    for record in predictions:
        intro = record['introduction']
        for i, key in [(intro['user_a'], 'a_accepts_b'), (intro['user_b'], 'b_accepts_a')]:
            events = [e for e in by_intro.get(intro['introduction_id'], [])
                      if e['event'] == 'introduction_response' and e['member_id'] == i]
            if events:
                e = events[0]
                labels.append(dict(p=record['prediction'][key],
                    y=int(e['value'] == 'yes' and e['observed_day'] <= intro['response_deadline_day']),
                    observed_preference=e['value'] if e['value'] in ('yes', 'no') else None,
                    direction=key, groups=record['groups'][i], introduction_id=intro['introduction_id']))
    calibration_result = dict(recorded_yes=calibration(labels),
        by_direction={k: calibration([r for r in labels if r['direction'] == k])
                      for k in ('a_accepts_b', 'b_accepts_a')},
        by_gender={g: dict(calibration([r for r in labels if r['groups']['gender'] == g]),
                          sufficient_sample=sum(r['groups']['gender'] == g for r in labels) >= 50)
                   for g in ('woman', 'man', 'non_binary')},
        target='Recorded Yes by seven-day deadline; no response is not dislike.',
        limitation='No posthoc calibration fitted to these evaluation labels. Directions share parameters with swapped features.')
    if trace_path:
        path = Path(trace_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(dict(metrics=metrics, actions=trace, opportunity=opportunity,
            predictions=predictions, calibration_labels=labels,
            feedback=sim.receive_feedback()), separators=(',', ':'), allow_nan=False) + '\n')
    return dict(metrics, opportunity={k: v for k, v in opportunity.items() if k != 'members'},
                calibration=calibration_result)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--methods', default='greedy,no_asks,random,learned_greedy,learned_maxweight,uncertainty_first,degree_first,graphvoi,graphvoi_no_pairs,graphvoi_wait')
    p.add_argument('--seeds', default='41001,41002,41003')
    p.add_argument('--variants', default='all')
    p.add_argument('--belief', choices=['none', 'biased', 'overconfident', 'underconfident',
                   'refusal', 'subgroup_refusal', 'temporal_drift'], default='none')
    p.add_argument('--actual-disclosure', choices=['none', 'refusal', 'subgroup', 'drift'], default='none')
    p.add_argument('--output', default='results/research_smoke.json')
    args = p.parse_args()
    seeds, methods = list(map(int, args.seeds.split(','))), args.methods.split(',')
    variants = list(VARIANTS) if args.variants == 'all' else args.variants.split(',')
    if len(set(seeds))!=len(seeds) or len(set(methods))!=len(methods) or len(set(variants))!=len(variants):
        p.error('Duplicate seed, method or scenario')
    if any(v not in VARIANTS for v in variants) or any(m not in METHODS + ('greedy', 'no_asks', 'random') for m in methods):
        p.error('Unknown scenario or method')
    train_seeds = set(json.loads(Path('assets/training_summary.json').read_text())['training_seeds'])
    if set(seeds) & train_seeds:
        p.error('Evaluation seeds overlap training seeds')
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    trace_root = output.parent / (output.stem + '_traces')
    rows = []
    for variant in variants:
        for seed in seeds:
            for method in methods:
                try:
                    row = research_episode(seed, variant, method, args.belief, args.actual_disclosure,
                        trace_root / f'{variant}_{seed}_{method}.json')
                except (ValueError, TypeError, KeyError, OSError) as error:
                    row = dict(valid=False, error=str(error), variant=variant, seed=seed, method=method)
                rows.append(row)
                result = dict(mode='trusted_research_inprocess', startup_included=False,
                    python_version=sys.version, code_sha256=CODE_SHA256,
                    decision_days=60, follow_up_days=40, members_per_episode=200,
                    experimental_disclosure=args.actual_disclosure != 'none', episodes=rows,
                    complete=len(rows) == len(variants) * len(seeds) * len(methods),
                    summaries=complete_summaries(rows,methods,{(v,s) for v in variants for s in seeds}),
                    expected_design=dict(seeds=seeds,variants=variants,methods=methods),
                    paired_intervals=paired_intervals(rows,expected_pairs={(v,s) for v in variants for s in seeds},expected_methods=methods),
                    asset_sha256={name: hashlib.sha256(Path('assets', name).read_bytes()).hexdigest()
                                  for name in ('pair_model.json', 'answer_model.json')})
                output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
                print(json.dumps({k: row.get(k) for k in ('method', 'seed', 'variant', 'valid',
                      'msmi_per_100_arrived_members', 'inference_seconds', 'error')}), flush=True)
    return 0 if all(r['valid'] for r in rows) else 2


if __name__ == '__main__':
    raise SystemExit(main())
