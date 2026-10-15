"""Write a concise report from completed machine-readable runs only."""
import json
from pathlib import Path
import statistics
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from graphvoi.analysis import percentile


def main():
    root = Path(__file__).resolve().parents[1]
    data = json.loads((root / 'results/paired_smoke.json').read_text())
    if not data['complete']:
        raise ValueError('Smoke comparison is incomplete; do not write a finished report')
    training = json.loads((root / 'assets/training_summary.json').read_text())
    analysis = json.loads((root / 'results/analysis_summary.json').read_text())
    robustness = json.loads((root / 'results/robustness_smoke.json').read_text())
    if not robustness.get('complete'):
        raise ValueError('Robustness run is incomplete')
    table = ['| Method | MSMI/100 | Coverage | Mutual accepts/100 | Ask cost |',
             '|---|---:|---:|---:|---:|']
    for name, summary in data['summaries'].items():
        if not summary['eligible']:
            table.append(f'| {name} | INVALID | | | |')
            continue
        r = summary['overall']
        table.append(f"| {name} | {r['msmi_per_100_arrived_members']:.3f} | {r['coverage']:.3f} | {r['mutual_acceptances_per_100']:.3f} | {r['ask_cost']:.1f} |")
    graph = analysis['calibration']['graphvoi']['overall']
    scenario_table = ['| Scenario | Greedy | No asks | Random | Uncertainty | Degree | GraphVOI |',
                      '|---|---:|---:|---:|---:|---:|---:|']
    for variant in ('development', 'sparse', 'cold_start', 'delayed', 'shift', 'drift'):
        values = [data['summaries'][method]['scenario_means'][variant]['msmi_per_100_arrived_members']
                  for method in ('greedy', 'no_asks', 'random', 'uncertainty_first', 'degree_first', 'graphvoi')]
        scenario_table.append('| ' + variant + ' | ' + ' | '.join(f'{v:.2f}' for v in values) + ' |')
    opportunity_table = ['| Method / observed gender | Member-scenarios | Unserved | Served median / p90 wait | Mean introductions | Mean eligible partners |',
                         '|---|---:|---:|---:|---:|---:|']
    classification = {}
    for method in ('uncertainty_first', 'degree_first', 'graphvoi'):
        records = []
        for path in sorted((root / 'results/paired_smoke_traces').glob(f'*_{method}.json')):
            records.extend(json.loads(path.read_text())['opportunity']['members'])
        classification[method] = {name: sum(r['classification'] == name for r in records)
                                  for name in sorted({r['classification'] for r in records})}
        for gender in ('woman', 'man', 'non_binary'):
            rs = [r for r in records if r['gender'] == gender]
            waits = [r['wait_days'] for r in rs if r['wait_days'] is not None]
            med, p90 = percentile(waits, .5), percentile(waits, .9)
            wait_text = 'NA' if med is None else f'{med:.1f} / {p90:.1f}'
            opportunity_table.append(f"| {method} / {gender} | {len(rs)} | {len(rs)-len(waits)} | {wait_text} | {statistics.mean(r['introductions'] for r in rs):.2f} | {statistics.mean(r['eligible_opportunities'] for r in rs):.2f} |")
    sensitivity = ['| Answer belief / actual disclosure | MSMI/100 | Coverage | Ask cost |',
                   '|---|---:|---:|---:|']
    for row in robustness['full_episodes']:
        sensitivity.append(f"| {row['belief']} / {row['actual_disclosure']} | {row['msmi_per_100_arrived_members']:.2f} | {row['coverage']:.3f} | {row['ask_cost']} |")
    stability = [1.0 if r['both_empty'] else r['jaccard']
                 for r in robustness['belief_snapshot_stability'] if r['belief'] != 'none']
    stages = training['stages']
    runtime = max(r['phase_runtime']['ask']['maximum'] for r in data['episodes'] if r.get('valid'))
    text = f'''# GraphVOI: allocation-aware clarification

Team Orbit, The Sequential Matching Problem, Round 2 research implementation.
This report describes actual public smoke experiments, not a validated competition
win. The proposed 100 paired episodes per family remain unrun. Docker checks are
blocked by the environment; this build is not yet certified submission-ready.

## Question and method

Does allocation-aware clarification improve eventual mutual second-meeting
intention relative to degree-first and uncertainty-first asking? GraphVOI ranks
legal actions by E[V(G after answer)] - V(G) - lambda*cost, with V an exact
maximum-weight general-graph matching. Lambda is zero in these initial experiments.
We enumerate four empirical constraint donor outcomes or all observed soft
categories, and evaluate their actual matching optima. Two blocked endpoints can
be queried together as a six-unit action, even when singleton gains are zero.

All three clarification methods share the trained scorer, exact solver, waiting
rule, legal candidates, 16-single/8-pair frontier, support size, budget and worlds.
Uncertainty sums conditional answer entropy, adjusted for disclosure probability;
degree counts expected added feasible edges. Static VOI/unit batch packing does
not optimize joint question redundancy. The frontier and small answer support
approximate the full acquisition problem and can miss useful questions. A common
deterministic dense-graph fallback is explicitly counted in memory and result JSON.

We import the official public eligibility helper. Known failures dominate missing
information; refused or unresolved hard fields never permit an introduction.
Counterfactual values are confined to copied member records. Only actual refreshed
observations determine the match phase. Availability, previous introductions,
pool membership and disjoint batches are rechecked before output. There is no
policy access to hidden truth, generator seeds, private coefficients or future
outcomes, and no online model updates across these controlled policies.

## Prediction and training

Eight declared training seeds, 31001..31008 across six public variants, generated
48 complete 60-day rollouts with 40 follow-up days. All features were recorded
before introduction from public JSON; final questionnaires were not attached to
earlier decisions. The static train/validation/development-test split is retained;
development-test pools were not used for model selection.

Regularized logistic models estimate each directional recorded Yes separately,
joint mutual acceptance directly, timely completed date given mutual acceptance,
and two timely second-meeting Yes answers given a completed date. Joint acceptance
does not multiply directional marginals. The remaining conditional stages use
the chain rule. Training yields {stages['directional_acceptance']['count']} directed
response labels and {stages['timely_seconds_given_date']['count']} completed-date
examples, with only {stages['timely_seconds_given_date']['positives']} positive
timely mutual-second outcomes. The answer model has {training['donor_count']}
disclosed constraint donors and observed soft frequencies, without member IDs.

Pending responses are censored, not negatives. For recorded Yes by deadline,
nonresponse means absence of that recorded event, not dislike. Undated pairs have
no second-meeting label. Training is selective under the official greedy logging
policy; no logging propensity or unbiased counterfactual evaluation is claimed.
Pool reuse across scenario variants means counts are not independent population
counts. Sparse donors, selection bias and scenario shifts can miscalibrate scores.

## Controlled smoke results

All six official scenario families use the same independent validation seed 41001
for every method. Each episode has 200 members, 60 decision days and 40 follow-up
days. Table values weight families equally. Full episode JSON and traces are in
results/paired_smoke.json and results/paired_smoke_traces/.

{chr(10).join(table)}

Scenario-level MSMI per 100 arrivals:

{chr(10).join(scenario_table)}

One seed per family cannot establish superiority. Paired seed-bootstrap intervals
are saved but flagged as unreliable for this smoke sample. The final proposed
study uses seeds 51001..51100, with no test-set tuning. Zero-MSMI episodes remain
in every average, and invalid episodes would disqualify a method.

## Directional calibration and opportunities

GraphVOI's held-out recorded-Yes calibration has n={graph['count']},
Brier={graph['brier']:.4f}, log loss={graph['log_loss']:.4f}. Results include each
direction, observed gender groups, ten reliability bins and separate conditional
stages. These smoke populations supply only one independent seed cluster; the
bootstrap cannot support inferential confidence. No calibrator is fitted to these
evaluation labels. A larger validation study is needed before recalibration.

![Directional reliability curves with sample counts](../results/calibration.png)

Per-member traces record first introduction, introductions, available member-days,
feasible member-days, distinct currently eligible partners, feasible waiting,
clarification cost and observed group membership. Served-only median/p90 waits
are reported with unserved counts. Classification separates known hard refusal,
unresolved observations, feasible-but-unserved members and no observed opportunity.
The last category is not a claim of hidden true ineligibility. Preferences are
never relaxed to equalize opportunity. Small subgroups require caution.

{chr(10).join(opportunity_table)}

These are descriptive member-scenario records, with the same seed populations
reused across families, not independent participants. Waiting summaries condition
on introduction and must be read alongside unserved counts. Detailed observed
blocking classifications and clarification allocations are retained in traces.
GraphVOI's unserved records include
{classification['graphvoi'].get('blocked_by_declined_hard_field', 0)} with a recorded
hard refusal, {classification['graphvoi'].get('unresolved_observed_constraints', 0)}
with unresolved observations,
{classification['graphvoi'].get('feasible_but_never_introduced', 0)} that had at least
one feasible opportunity but were never introduced, and
{classification['graphvoi'].get('no_observed_feasible_opportunity', 0)} with no
observed feasible opportunity. These categories are not interchangeable allocation
failures.

## Answer-model misspecification

Static question stability is tested on identical day-0/20/40 observations in every
scenario, comparing biased, tempered, refusal, subgroup-refusal and drift beliefs.
Mean nonreference question-set Jaccard is {sum(stability)/len(stability):.3f}; both-empty
question sets count as identical. Full standard-scenario sensitivity uses seed
41002. Independent actual-disclosure changes act only on whether new answers are
disclosed; they preserve underlying hard preferences and never reveal parameters
to the evaluated policy. These modified environments are not official scenarios.

{chr(10).join(sensitivity)}

These are sensitivity smoke runs, not robust performance estimates. Complete
belief/actual-disclosure traces and performance/cost deltas are retained in
results/robustness_smoke.json. Subgroup and temporal changes can produce very small
effective samples; the static stability results complement full episode outcomes.
Uniform refusal beliefs with zero cost penalty often rescale single-question
gains without changing ranks; stable decisions do not prove that beliefs are
correct. When all conditions have zero MSMI, the run cannot establish MSMI
degradation; coverage, exposure, costs and decision stability remain observable.

## Runtime, reproducibility and limitations

The largest measured research ask invocation in the controlled smoke was
{runtime:.3f} s, excluding process startup. Separate official subprocess episodes,
profiles at days 0/20/40/59 and a fully eligible dense 200-member test include
startup and passed their tested ten-second invocation limits. This does not verify
Docker's two-CPU/one-GiB resource envelope. Exact solver output is canonical for
fixed inputs; inference has no random seed and reads no persistent filesystem state.

The official simulator/evaluator/data remain unchanged. NetworkX 3.5 is vendored,
pinned and BSD-licensed; the Dockerfile copies only inference code/assets/notices.
Research inputs, static worlds and credentials are excluded. See README.md,
docs/EVALUATION_PROTOCOL.md and docs/PROVENANCE.md for exact commands, source commit,
asset hashes, training settings, tooling and permissions. Team Orbit's original
code licence must be chosen before publishing; starter permissions are retained.

Open limitations: myopic pool-level VOI, truncated donor support, static batch
redundancy, baseline-selective training, weak rare-outcome evidence, unverified
container resources, and the unrun larger paired study. Synthetic simulation
cannot establish product effectiveness or infer real people's preferences.
'''
    (root / 'docs/REPORT.md').write_text(text)


if __name__ == '__main__':
    main()
