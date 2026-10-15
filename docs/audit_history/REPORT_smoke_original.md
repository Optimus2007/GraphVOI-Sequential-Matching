# GraphVOI: allocation-aware clarification

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
the chain rule. Training yields 7392 directed
response labels and 382 completed-date
examples, with only 33 positive
timely mutual-second outcomes. The answer model has 6285
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

| Method | MSMI/100 | Coverage | Mutual accepts/100 | Ask cost |
|---|---:|---:|---:|---:|
| greedy | 0.333 | 0.366 | 5.250 | 235.0 |
| no_asks | 0.250 | 0.084 | 1.833 | 0.0 |
| random | 0.500 | 0.370 | 6.750 | 235.0 |
| learned_greedy | 0.500 | 0.367 | 7.000 | 235.0 |
| learned_maxweight | 0.500 | 0.367 | 6.333 | 235.0 |
| uncertainty_first | 0.000 | 0.350 | 5.667 | 443.2 |
| degree_first | 0.000 | 0.329 | 4.917 | 187.0 |
| graphvoi | 0.500 | 0.328 | 5.833 | 188.5 |
| graphvoi_no_pairs | 0.083 | 0.241 | 4.667 | 110.0 |
| graphvoi_wait | 0.167 | 0.307 | 3.750 | 191.7 |

Scenario-level MSMI per 100 arrivals:

| Scenario | Greedy | No asks | Random | Uncertainty | Degree | GraphVOI |
|---|---:|---:|---:|---:|---:|---:|
| development | 0.50 | 0.50 | 1.00 | 0.00 | 0.00 | 1.00 |
| sparse | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| cold_start | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| delayed | 0.50 | 0.00 | 0.50 | 0.00 | 0.00 | 0.50 |
| shift | 0.50 | 0.50 | 0.50 | 0.00 | 0.00 | 0.50 |
| drift | 0.50 | 0.50 | 1.00 | 0.00 | 0.00 | 1.00 |

One seed per family cannot establish superiority. Paired seed-bootstrap intervals
are saved but flagged as unreliable for this smoke sample. The final proposed
study uses seeds 51001..51100, with no test-set tuning. Zero-MSMI episodes remain
in every average, and invalid episodes would disqualify a method.

## Directional calibration and opportunities

GraphVOI's held-out recorded-Yes calibration has n=956,
Brier=0.2330, log loss=0.6585. Results include each
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

| Method / observed gender | Member-scenarios | Unserved | Served median / p90 wait | Mean introductions | Mean eligible partners |
|---|---:|---:|---:|---:|---:|
| uncertainty_first / woman | 595 | 368 | 3.0 / 15.0 | 0.93 | 1.08 |
| uncertainty_first / man | 546 | 369 | 4.0 / 16.0 | 0.84 | 0.91 |
| uncertainty_first / non_binary | 59 | 43 | 5.0 / 8.0 | 0.56 | 0.68 |
| degree_first / woman | 595 | 377 | 3.0 / 18.6 | 0.86 | 1.01 |
| degree_first / man | 546 | 388 | 3.0 / 19.0 | 0.69 | 0.76 |
| degree_first / non_binary | 59 | 40 | 2.0 / 16.0 | 0.76 | 0.78 |
| graphvoi / woman | 595 | 378 | 4.0 / 20.0 | 0.86 | 1.01 |
| graphvoi / man | 546 | 387 | 3.0 / 21.0 | 0.73 | 0.79 |
| graphvoi / non_binary | 59 | 42 | 0.0 / 13.0 | 0.73 | 0.76 |

These are descriptive member-scenario records, with the same seed populations
reused across families, not independent participants. Waiting summaries condition
on introduction and must be read alongside unserved counts. Detailed observed
blocking classifications and clarification allocations are retained in traces.
GraphVOI's unserved records include
377 with a recorded
hard refusal, 350
with unresolved observations,
7 that had at least
one feasible opportunity but were never introduced, and
73 with no
observed feasible opportunity. These categories are not interchangeable allocation
failures.

## Answer-model misspecification

Static question stability is tested on identical day-0/20/40 observations in every
scenario, comparing biased, tempered, refusal, subgroup-refusal and drift beliefs.
Mean nonreference question-set Jaccard is 0.907; both-empty
question sets count as identical. Full standard-scenario sensitivity uses seed
41002. Independent actual-disclosure changes act only on whether new answers are
disclosed; they preserve underlying hard preferences and never reveal parameters
to the evaluated policy. These modified environments are not official scenarios.

| Answer belief / actual disclosure | MSMI/100 | Coverage | Ask cost |
|---|---:|---:|---:|
| none / none | 0.00 | 0.380 | 156 |
| biased / none | 0.00 | 0.385 | 156 |
| overconfident / none | 0.00 | 0.380 | 156 |
| underconfident / none | 0.00 | 0.380 | 156 |
| refusal / none | 0.00 | 0.380 | 156 |
| subgroup_refusal / none | 0.00 | 0.380 | 156 |
| temporal_drift / none | 0.00 | 0.380 | 156 |
| none / refusal | 0.00 | 0.315 | 168 |
| none / subgroup | 0.00 | 0.405 | 172 |
| none / drift | 0.00 | 0.375 | 168 |

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
2.546 s, excluding process startup. Separate official subprocess episodes,
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
