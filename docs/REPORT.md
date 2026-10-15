# GraphVOI: corrected allocation-aware clarification

Team Orbit, The Sequential Matching Problem, Round2. This report concerns the
frozen conditional-acquisition v2 implementation and a prespecified10-seed pilot.
The original smoke report is preserved in `audit_history/REPORT_smoke_original.md`;
its results concern superseded cache/batch/statistics code, not this corrected build.
No full100-seed study has run. This is not certified submission-ready: Docker and
an immutable public release remain unverified.

## Method and correctness

Research question: does allocation-aware asking improve official MSMI/100 relative
to degree-first and uncertainty-first? For action q, GraphVOI evaluates
E[V(G after q)]−V(G)−lambda cost(q), where V is exact maximum-weight general-graph
matching on observable, reciprocally eligible pairs. Lambda0 in the frozen pilot.
Joint constraint bundles cost3/member, soft asks1; daily cap12.

After selecting asks, remaining candidates are evaluated against their joint
counterfactual world distribution, with allocation recomputed under each updated
state. Duplicate asks are removed from residual actions and charged once. Paired
questions capture zero-singleton-gain complements, including soft/nonpartner
questions that change an alternating allocation. No additive independent-VOI
subtraction is used. Actual match responses always use refreshed observed answers,
never hypothetical values.

Approximations: myopic pool value, nearest-four donor support,16-single/8-pair
restricted frontier (up to4 reserved hard pairs), greedy conditional acquisition,
8-world deterministic probability quadrature,256 coalesced candidate-outcome
work cap. Larger joint distributions can have biased compressed expectations;
this is not global optimal batch VOI. Common >600-edge fallback remains. Tests
compare exact uncapped small supports and brute-force matching, not merely renamed
heuristics. The three selectors share pair model/assets/solver/waiting/candidates,
budget and world seeds; only entropy/degree/allocation selection criteria differ.

Answer-cache identity now includes all current calculation dependencies. An
uncached reference,400 randomized exact comparisons, mutation isolation and
per-invocation clearing establish cached calculation equivalence. They do not
prove answer-model fidelity. Refused hard fields remain unavailable, known hard
violations dominate missingness, explicit preferences are never overridden.
Policy inference has no generator, simulator, seed or privileged-state access.
Official eligibility/evaluator/simulator/baselines and model weights are unchanged.

## Training and model limitations

Fixed assets use48 lawful observed training rollouts: seeds31001..31008 across
six public variants,60 decision plus40 follow-up days. Pre-introduction public
features and matured recorded events only; evaluation/pilot seeds are disjoint.
Static public train/validation/development-test pools remain separate.
Regularized logistic models estimate directional recorded Yes with reversed
features, joint mutual acceptance directly, timely completed date conditional on
mutual acceptance, then timely mutual second intention conditional on a date.
7392 directed labels,382 completed-date examples,33 positive timely-second
outcomes. Answer support uses6285 disclosed donors and soft frequencies.

Pending events are censored; absence of recorded Yes is not a dislike label.
Undated pairs have no invented second-meeting label. Greedy-logged selective
training and reused scenario populations limit interpretation. Prior one-seed
Brier/log-loss/reliability records remain historical; no new fitted calibration or
held-out answer-model validation is claimed. H5 remains UNVERIFIED. A larger
held-out disclosure/support/refusal study remains necessary before asserting that
beliefs are accurate or robust to actual disclosure changes.

## Frozen pilot design and inference

`CORRECTED_PILOT_PROTOCOL.md` was declared before execution. Seeds62001..62010,
six official families, six methods,360 expected complete200-member episodes,
60/method. Three independent host workers; inference receives ordinary JSON.
All rows/validity flags and120 daily action records per valid episode are saved.
No fitting, frontier tuning or threshold tuning uses pilot outcomes.

Official scoring: any invalid episode makes a method ineligible. Missing/duplicate
expected scenario/seed/method records also suppress scores and paired inference.
Zero outcomes are retained. Each family mean has equal weight in the aggregate.
Paired bootstrap resamples whole world-seed clusters across families,2,000 draws,
seed771; scenario-membership strata preserve denominators if seed lists differ.
The balanced pilot has10 clusters, not60 independent worlds. Its intervals are
explicitly flagged as limited support. An implemented runner is not completed
experimental evidence; the measured complete result matrix is authoritative.

## Completed corrected pilot results

`results/corrected_pilot.json`:360 completed valid episodes,60 per method,10 paired seeds per family. Invalid episodes:0. Independent aggregate/trace/bootstrap/source checks passed in `results/corrected_pilot_verification.json`. No full100-seed study was run.

Counts are recorded events across60 simulated episodes per method; families share seed populations. Cost and unserved are episode means. Waiting quantiles pool served members only.

| Method | MSMI/100 | Mutual accepts (total) | Dates (total) | Coverage | Cost/episode | Unserved/episode | Served median/p90 days | Invalid |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| graphvoi | 0.308 | 530 | 421 | 28.0% | 136.4 | 144.0 | 3.5/24.0 | 0 |
| degree_first | 0.317 | 576 | 444 | 28.4% | 135.5 | 143.2 | 4.0/24.0 | 0 |
| uncertainty_first | 0.333 | 630 | 470 | 30.5% | 245.6 | 139.0 | 5.0/25.0 | 0 |
| greedy | 0.350 | 670 | 500 | 33.0% | 197.6 | 134.0 | 4.0/16.0 | 0 |
| no_asks | 0.117 | 148 | 127 | 12.8% | 0.0 | 174.5 | 0.0/14.9 | 0 |
| random | 0.233 | 674 | 515 | 32.9% | 197.6 | 134.2 | 4.0/16.0 | 0 |

Equal-family MSMI/100 means:

| Scenario | GraphVOI | Degree | Uncertainty | Greedy | No asks | Random |
|---|---:|---:|---:|---:|---:|---:|
| development | 0.400 | 0.450 | 0.500 | 0.500 | 0.150 | 0.350 |
| sparse | 0.050 | 0.050 | 0.100 | 0.050 | 0.050 | 0.050 |
| cold_start | 0.200 | 0.200 | 0.250 | 0.400 | 0.150 | 0.250 |
| delayed | 0.400 | 0.500 | 0.500 | 0.500 | 0.100 | 0.450 |
| shift | 0.400 | 0.200 | 0.200 | 0.200 | 0.100 | 0.050 |
| drift | 0.400 | 0.500 | 0.450 | 0.450 | 0.150 | 0.250 |

Paired differences are GraphVOI minus comparator, official MSMI/100. Bootstrap2,000 whole-seed draws; each draw retains all six scenarios with equal family weights. All comparisons have10 pairs/family and10 independent seed clusters; all intervals are flagged limited support.

| Comparator | Difference | Paired95% interval |
|---|---:|---:|
| degree_first | -0.008 | [-0.108, +0.092] |
| uncertainty_first | -0.025 | [-0.142, +0.117] |
| greedy | -0.042 | [-0.200, +0.100] |
| no_asks | +0.192 | [+0.042, +0.342] |
| random | +0.075 | [-0.092, +0.233] |

These are pilot estimates, not proof of superiority. No parameters were tuned from this run. CIs for acceptance, dates, coverage, cost, unserved counts and inference time are also retained in the JSON. Waiting quantiles remain descriptive and conditional, not population censor-aware estimates.

Runtime under three parallel host workers (in-process; excludes startup):

| Method | Mean inference seconds/episode | Max ask seconds | Max match seconds |
|---|---:|---:|---:|
| graphvoi | 43.01 | 1.289 | 0.199 |
| degree_first | 41.97 | 1.305 | 0.123 |
| uncertainty_first | 31.50 | 1.012 | 0.116 |
| greedy | 2.98 | 0.019 | 0.124 |
| no_asks | 3.79 | 0.000 | 0.133 |
| random | 2.84 | 0.001 | 0.087 |

Pilot wall time: 58.0 minutes. Measured worker peakRSS: 75.0MiB (cumulative trusted-process high-water mark, including simulator/traces). Isolated policy fresh-process profile:61.14MiB; maxask1.4344s/maxmatch0.7580s. Neither measurement certifies Docker's enforced resources.

All360 metric rows and43,200 phase actions were checked against trace digests, per-member waiting/coverage records, equal-family summaries, frozen source/assets and an independently recomputed paired MSMI bootstrap. Six fresh official subprocess families plus a complete repeated episode provide7 separate validity episodes; the balanced pilot count excludes those and intermediate repair-build runs.

## Waiting, opportunities and disclosure scope

First-introduction median/p90 condition on served members. Unserved counts and
coverage retain all arrivals; never impute unserved waits as0. Traces distinguish
feasible-but-unserved, hard-refusal blocked, unresolved constraints and no observed
opportunity; the latter is not proof of true hidden ineligibility. Population
censor-aware waiting and independently supported subgroup differences remain unrun.
No preference relaxation or fairness claim is made.

Historical10-episode single-seed disclosure smoke and126 snapshot comparisons
were not rerun in this pilot. Belief perturbations and independent actual-disclosure
wrapper remain separate mechanisms; neither exposes disclosure parameters to the
policy. The corrected pilot is official-environment validity/comparison evidence,
not a new disclosure degradation or robustness experiment.

## Verification, runtime and release limitations

85 unit/integration tests actually executed/pass,71 checksums verified. Six
fresh official subprocess scenarios at seed63004 are valid, and a second full
development episode has identical action hash. Manual A–F,30 random small graphs,
probabilistic redundancy, paired hard/soft complements and failure-aware
statistics tests pass. Profiles:20 fresh-process calls with two hash seeds,
maxask1.4344s/maxmatch0.7580s, peakRSS61.14MiB.750,000-byte memory roundtrip
succeeds; unsupported schema rejects without stdout JSON. Model assets load.
These are measured local cases, not worst-case guarantees or Docker certification.
Pilot phase timing excludes startup and includes parallel host scheduling.

NetworkX3.5 is vendored/pinned, offline inference assets included, starter/data/
dependency notices retained. Source/script/asset/test hashes are frozen in
`CORRECTED_BUILD_MANIFEST.json`; results carry runner and model hashes. Docker
resource compliance, public immutable release/pin, owner-selected contribution
licence, fresh corrected archive and some packaging hygiene remain outstanding.
The existing candidate archive contains superseded code and must not be submitted.
No implementation of new architectures or full100-seed study was performed.

Research limitations remain rare outcomes, answer-model bias, restricted
acquisition/support/quadrature, selective labels, missing population waiting
analysis, insufficient subgroup/disclosure evidence, and synthetic-only outcomes.
No GraphVOI superiority or real-product effectiveness is claimed from smoke or
pilot alone. See the audit follow-up and release checklist for unresolved gates.

Explicit quadrature counterexample: two independent four-outcome hard questions
produce16 worlds; each unlocks a disjoint weight10 pair with probability.75, so
exact expectation15. Eight systematic midpoint worlds miss every second-member
failure, yielding17.5. Regression asserts both results and measured bias2.5.
This is a runtime-bounded approximation, with no small universal error bound or
global-batch exactness guarantee. Cap sensitivity remains a research limitation.
The static additive-credit bug is fixed; arbitrary joint expectation is not exact
after compression. No policy change was made after the pilot freeze.
