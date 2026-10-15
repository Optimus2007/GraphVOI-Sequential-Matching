# Independent adversarial audit — GraphVOI / Team Orbit

Audit date: 10 October 2026. Local directory: `/Users/adityakeshri/Documents/Romeo`.
This is a fresh source review and adversarial verification, not acceptance of the
previous progress claims. PASS means supported by inspected code and/or the named
execution, within its stated scope. UNVERIFIED is not a pass. Tests of a known
limitation deliberately confirm the defect; their passing does not certify that
defect as correct. No policy, simulator, baseline, evaluator or trained asset was
changed in this audit. New tests and evidence scripts were added.

## 1. Executive summary

**Verdict: not submission-ready.** There are **2 CRITICAL release blockers,
5 HIGH findings, 6 MEDIUM findings and 2 LOW findings**. No confirmed critical
rule-violating policy correctness bug was found; the two critical blockers are
unverified assessed-container execution and the missing accessible pinned release.
Neither can be fixed by claiming success in this environment.

GraphVOI is genuine **model-based counterfactual matching VOI for each candidate
action**, not renamed degree-first. It is a myopic surrogate for the eventual
sequential outcome, with truncated answer support, a restricted frontier, static
batch selection and a non-VOI dense fallback. It is not exact joint batch VOI.

The three main selectors share the same frozen model, solver, waiting rule,
frontier, daily budget cap and paired worlds. Their actual total spending differs.
The saved smoke comparison is balanced, but only one seed cluster underlies it.
No superiority conclusion is justified. The answer-cache defect below prevents
unqualified certification of arbitrary in-process comparisons.
The saved-run cache query probe found zero dependency collisions. Independent
replay also reproduced all saved pre-action predictions and recorded-Yes labels;
the defect is not evidence that these particular smoke scores were contaminated.

Fresh verification: **67 tests passed**, **71 data checksums passed**, the training
artifacts reproduced byte for byte, and **6 fresh official full episodes** passed
all six scenarios at seed 61001. One additional standard-scenario repeat matched
the entire action hash and outcome counts. Thus the audit ran **7 full policy
episodes (6 distinct world/scenario conditions)**, separately from 48 retraining
rollouts. Existing main evidence comprises **60 controlled smoke episodes and
10 disclosure episodes**. Replaying saved actions verifies evidence, not additional
independent policy-performance samples. See the evidence inventory for legacy and
interrupted runs; they must not be pooled into a larger study.

The unchanged 514-file candidate archive was extracted freshly: its own 58 tests,
data verifier and empty policy invocation passed. It does not include this audit's
new tests/documents. Docker and GitHub CLI are unavailable. Git reports that this
directory is not a repository. The personal repository API request returned 404;
that can mean inaccessible/private or absent and does not establish visibility.

## 2. Scope and authoritative source

Reviewed official specification, interface, data contract, submission guide, FAQ,
changelog, report guide, `kit.py`, `evaluate.py`, original baseline adapter and
original tests. Reviewed all first-party GraphVOI modules, experiment/training/
analysis/packaging scripts and tests, plus implementation plan, progress, decisions,
report, manifests, model metadata and every results JSON. Inventories include file
hashes rather than treating progress notes as execution evidence.

The connected GitHub API reports current official main as
`a8e26b35118cfa8e886a02f93984923e43ab64f6`, matching the restored snapshot.
No newer repository correction was found. Source:
[official main commit](https://api.github.com/repos/RomeoJulietLove/The-Sequential-Matching-Problem/commits/main).
This is a point-in-time check, not a promise that later corrections cannot occur.
Official files are compared against Git blob hashes in `docs/STARTER_SNAPSHOT.json`;
intentional adapters/docs/container changes are distinguished from the unmodified
simulator/evaluator/data. No upstream repository was modified.
The check verified103 unchanged original files (using preserved `.starter`/baseline
copies for replaced adapters); the only unmatched originals are the intentionally
extended README and ignore files. All287 vendored Python hashes match provenance.

## 3. Findings and exact required actions

| ID | Severity | Status | Finding, evidence and required action |
|---|---|---|---|
| C1 | CRITICAL | UNVERIFIED | Assessed Docker build/execution/resource compliance is unrun. `docs/POLICY_INTERFACE.md:37`, `evaluate.py:72`, `Dockerfile:1`. Run the build and official container evaluator across all scenarios on a Docker-capable machine; enforce 2 CPUs, 1 GiB, 64 processes, read-only image, offline networking and startup-inclusive timeout. Local timing is insufficient. |
| C2 | CRITICAL | FAIL | No local Git commit or demonstrated public immutable submitted version exists. `docs/SUBMISSION.md:44`, `scripts/package_source.py:41`. Publish a reviewed commit or versioned archive including report, results and assets, verify public access and full checksum/SHA, and pin it in the final submission. A local archive is not a submitted release. Personal repository visibility remains UNVERIFIED after API 404. |
| H1 | HIGH | FAIL | Answer cache omits age, gender, zone and statuses although outcomes use them. `graphvoi/answers.py:20`, `:25`, `:41`, `:50`; instance survives in the research process via `graphvoi/policy.py:15`. Independent test gives cached age_min=25 versus fresh=45 when age changes from 30 to 50 with the same key. Include every outcome dependency in the key and clear observation-derived caches at each independent episode; verify order-independent and fresh-process comparisons. This is a runner-generalization bug, not proof that the current saved scores changed. |
| H2 | HIGH | FAIL | Static batch scores overlap. `graphvoi/clarification.py:143` scores all actions against one baseline, then `:152` packs without marginal rescoring. Independent AB=10 / AD=9 example spends 6 units and credits 19 individually although joint value is 10. Duplicate asks are prevented; allocation-value double counting is not. Implement conditional/marginal batch acquisition with bounded joint scenarios, or explicitly retain this approximation and evaluate a redundancy-aware ablation before claiming exact batch VOI. |
| H3 | HIGH | FAIL | Confidence interval code drops invalid rows and incomplete pairs, then still emits a performance delta/CI. `graphvoi/analysis.py:123`, `:130`. Independent test emits delta=1 from one surviving pair after the other GraphVOI episode times out. Official summary correctly makes the method ineligible (`evaluate.py:119`). Reject/flag performance inference whenever a compared method has invalid, missing, duplicate or incomplete expected episodes; retain failure counts. Current completed smoke has no invalid rows. |
| H4 | HIGH | FAIL | Mandatory research conclusions remain underpowered. `docs/REPORT.md:64`, `:91`, `:163`; only one paired seed for main comparisons and one standard-world seed for disclosure. There is no full held-out multi-seed study, no robust degradation estimate, and no defensible subgroup uncertainty. Freeze corrected code/analysis and run the prespecified multi-seed study, reporting all failures and paired seed-cluster intervals. Do not reinterpret six scenarios as six independent seeds. |
| H5 | HIGH | UNVERIFIED | Answer probabilities have not been evaluated against held-out clarification answers. Fully disclosed donors and nearest-four support are selective; base model assumes no new refusal (`graphvoi/answers.py:35`, `:58`, `:70`). Temperature perturbations can do nothing when selected donor weights coincide. Validate answer coverage, unsupported-query rate, refusal target and probability scoring on validation rollouts, then test train/evaluation mismatch across seeds/families. Without this, rankings may reflect belief error rather than useful information. |
| M1 | MEDIUM | FAIL | Median/p90 waiting excludes unserved members (`graphvoi/analysis.py:91`, `:99`). Unserved counts are retained and the report discloses conditioning, so this is not falsified coverage. Add a censor-aware time-to-first-introduction analysis and at-risk denominators before population/group waiting comparisons; do not impute unserved waits as zero. |
| M2 | MEDIUM | FAIL | Frontier can leave slots unused: only 8 hard singles survive even if no soft candidates exist (`graphvoi/clarification.py:62`). Degree-weighted frontier also restricts uncertainty-first. Fill remaining slots deterministically, expose frontier recall/sensitivity, and describe comparisons as selector comparisons within this common restricted candidate set. |
| M3 | MEDIUM | FAIL | Traces omit full pre-action observations and experiment-script hashes. Main JSON records only GraphVOI module hashes (`scripts/run_experiments.py:23`, `:196`). Replay requires exact official generator and seeds. Add source/archive hash, runner/training/analysis hashes, observation hashes, expected run matrix and resumable provenance. Preserve old results as distinct versions. |
| M4 | MEDIUM | FAIL | Optional analysis plotting dependency is not pinned: `scripts/plot_calibration.py:14` imports matplotlib but `requirements.txt:4` pins only inference NetworkX. Pin analysis extras and document plotting environment separately. Offline policy itself needs no matplotlib. |
| M5 | MEDIUM | FAIL | Docker allowlist includes local bytecode under graphvoi/vendor/assets (`.dockerignore:6`, `:10`; `!graphvoi/**`). Existing workspace has graphvoi/__pycache__. Source archive excludes it, but build context may include it. Explicitly exclude caches after allow rules; pin the base-image digest for stronger reproducibility and test the actual image contents. No research/world copy is present. |
| M6 | MEDIUM | FAIL | Team Orbit's original-code licence is not selected (`docs/PROVENANCE.md:38`, `docs/REPORT.md:185`). Retain starter/data/NetworkX notices and have the owner select and include the contribution licence before public release. Do not silently assume starter MIT licenses all new work. |
| L1 | LOW | FAIL | Plan mentions directional-independence multiplication (`docs/IMPLEMENTATION_PLAN.md`, Data and estimation), but implemented joint acceptance is trained directly (`graphvoi/models.py:53`). Align plan wording with final design. |
| L2 | LOW | FAIL | Historical progress/test counts are now superseded by audit evidence. Preserve them as dated history and link this audit; do not relabel old archive tests as the new 67-test suite. |

No production correction was made because no confirmed critical policy correctness
bug was discovered. Noncritical findings have exact fixes above. Existing measured
policy outputs and archives are preserved so the audit remains reviewable.

## 4. Source and rules checklist (Phase A)

| Check | Status | Source/evidence and limit of conclusion |
|---|---|---|
| 1 Ask response | PASS | Exactly asks/memory: `graphvoi/policy.py:43`, `:56`; adapter JSON `policy.py:48`; official `validate_response` and fresh six-scenario subprocess run. |
| 2 Match response | PASS | Exactly pairs/memory: `graphvoi/policy.py:62`; `graphvoi/core.py:118`; official simulator atomic validation in all fresh episodes. |
| 3 Memory persistence | PASS | Explicit request memory retained (`graphvoi/policy.py:30`, `:40`); fallback diagnostics modify policy-owned memory. 750,000-byte finite JSON roundtrip tested; no filesystem persistence. Research answer-cache independence is separately H1. |
| 4 No hidden simulator state | PASS | Inference imports only HARD/SOFT/eligibility from kit; audited feature function `graphvoi/core.py:55`; engine JSON whitelist `kit.py:105`; no Simulator/generate/world access on inference path. Training/experimental engine access stays outside policy. |
| 5 No hidden reconstruction | PASS | Explicit public numerical/categorical features; no generator calls, truth lookups, identifier decoding or latent attributes. Boundary tests and asset donor key checks. |
| 6 Training/evaluation leakage | PASS | Present artifacts reproduced from declared public training rollouts; pre-action features `scripts/train_models.py:21`, `:28`; disjoint 31001..31008 versus 41001/41002/61001; no static validation/test training input. Historical absence of manual test-set tuning remains UNVERIFIED without version history. |
| 7 No seed-based inference | PASS | Graph policy has no seed or random generator; IDs used for lookup/canonical ties, not feature inference. Official random baseline's 17+day shuffle is retained, not a world-seed oracle. |
| 8 Reciprocal hard eligibility | PASS | Official `kit.py:69` used in `graphvoi/core.py:50`, `:127`; pool, ages, gender preferences, smoking, children, structure, zones, schedule protected; known failures dominate unknown. |
| 9 Explicit preferences | PASS | Observed values never overwritten by hypothetical answers (`graphvoi/answers.py:94`); utility cannot override official feasibility. Manual D and existing explicit-age test. |
| 10 Missing information | PASS | `graphvoi/core.py:20` normalizes nonobserved/future fields to None; any unresolved hard key blocks eligibility; manual C and empty/sparse tests. |
| 11 Declined fields | PASS | Normalize removes unusable values; legal asks skip hard refusers (`graphvoi/core.py:151`); `apply_answer` only fills not_asked values (`graphvoi/answers.py:96`). Actual match uses refreshed observed state, never donors. |
| 12 Repeated/invalid introductions | PASS | History, availability, response window, disjoint endpoints and official helper rechecked (`graphvoi/core.py:28`, `:40`, `:118`); exact solver does not reuse vertices. Fresh official episodes valid. |
| 13 Invalid/duplicate asks | PASS | Legal named fields/status/availability and same-day log filtering `graphvoi/core.py:142`; duplicate action keys rejected during packing `graphvoi/clarification.py:154`; official resolve_asks checks complete batch. |
| 14 Daily budget | PASS | Cost 3/1, request remaining budget, whole-action packing (`graphvoi/core.py:163`, `graphvoi/clarification.py:145`, `:157`); manual complementary six-unit budget and official runs. |
| 15 Delayed bookkeeping | PASS | Policy is frozen, with cumulative observed history rather than pending online label updates; train/evaluation use receive_feedback after follow-up (`scripts/train_models.py:30`, `scripts/run_experiments.py:116`). No future outcomes used for decisions. |
| 16 Censored outcomes | PASS | Missing response/date/second events exclude conditional labels (`scripts/train_models.py:45`, `:59`, `:68`). Recorded null after deadline is absence of timely Yes, not dislike. Undated pairs have no second preference labels. Stage-label regression tests protect late seconds. |
| 17 Memory size | PASS | Tested normal, dense and 750 kB memory responses below 1 MiB; policy memory only passthrough plus small fallback counter, no stored graphs/models. Request/response/memory limits independently enforced by `evaluate.py:32`, `:45`. This does not certify all malformed external memory values. |
| 18 JSON/stdout | PASS | One JSON object stdout, finite serialization (`policy.py:48`); fresh invocations validate exact keys, zero exit. Unsupported schema exits with stderr and no stdout; malformed requests are outside valid interface. |
| 19 Determinism/ties | PASS | Sorted insertion and output `graphvoi/core.py:92`; no utility epsilon; two PYTHONHASHSEED values across 20 invocations agree, and full repeated episode action hashes agree. Cache H1 means arbitrary in-process cross-episode order independence is not certified. |
| 20 Runtime/CPU/RAM | UNVERIFIED | Official local invocations passed 10-second limits, measured local RSS below 1 GiB. Docker's exact CPU/RAM/process/temp/image constraints unrun (C1). Bounded frontier is not a proof of a private-world worst-case wall-time bound. |

PASS entries describe audited inference semantics and measured cases, not a universal
guarantee for every organiser world. No official rules were replaced speculatively.

## 5. Mathematical GraphVOI audit (Phase B)

`V(G) = max_M sum_(a,b in M) u(a,b)` over presently available, never-introduced,
fully feasible, vertex-disjoint pairs. `u` is the frozen model's product of joint
recorded mutual acceptance, timely date conditional on mutual acceptance, and
timely mutual-second intention conditional on timely date (`graphvoi/models.py:57`).
It is **current-pool predicted MSMI value**, not the full dynamic optimal sequential
return. Zero/negative edges are omitted. NetworkX weighted blossom is the exact
general-graph algorithm; floating-point arithmetic limits numerical precision.

| Algorithm check | Status | Evidence |
|---|---|---|
| 1 Definition of V | PASS | Current feasible matching sum above; `MatchingContext.value`, `graphvoi/clarification.py:18`. |
| 2 Maximum-weight matching | PASS | `graphvoi/core.py:104`; recomputed optimizers, odd-cycle/exhaustive tests and independent displaced allocation. |
| 3 Answer-model expectation | PASS | Empirical probabilities, top-four donor support or all soft categories `graphvoi/answers.py:58`; support is enumerated, not random Monte Carlo samples. Fidelity to actual answer distribution is UNVERIFIED/H5. |
| 4 Hypothetical state modification | PASS | Only allowed missing/not_asked keys updated in copied member `graphvoi/answers.py:85`; incident feasibility/utilities updated `graphvoi/clarification.py:20`. |
| 5 Matching recomputation | PASS | `graphvoi/clarification.py:91` resolves blossom under every outcome; cached unaffected edges do not cache the old matching. |
| 6 Probability weighting | PASS | Cartesian products multiply masses (`:82`); expectation uses p*V (`:91`). Paired example verifies .5*.5*.8=.2. |
| 7 Costs | PASS | Explicit lambda*sumcost (`:93`) and budget/score-per-unit packing. Lambda=0 in actual smoke runs, not a positive cost-regularized objective. |
| 8 Legal bundles | PASS | Official constraints ask is a legal 3-unit bundle. Pair action is two such asks totaling 6 units (`:67`). |
| 9 Joint complementary evaluation | PASS | Paired Cartesian outcomes apply both answers before optimization; independently worthless singles become valuable jointly. |
| 10 Double counting | FAIL | Action-internal matching uses vertices once, but across chosen batch actions static marginal scores overlap (H2). |
| 11 Bounded frontier | PASS | At most 16 singles+8 pairs, four hard supports (five with refusal), soft categorical supports and common >600-current-edge guard (`:62`, `:72`, `:137`). Candidate graph construction itself still examines O(n^2) pairs. |
| 12 Hard rule preservation | PASS | Every hypothetical edge uses official eligibility; actual allocation revalidates actual observations. |
| 13 Inference information | PASS | Public inputs plus lawful training donors; no actual answer/private world read. |
| 14 Determinism | PASS | Exact support enumeration/canonical ties, fresh-process hashseed and episode repeat checks. |
| 15 Allocation can change | PASS | Independent E changes AB+CD to AC+BD after the actual answer. |

Independent fixtures in `tests/test_independent_audit.py` construct public records
directly, without importing existing fixture builders or generator outputs. All
other edges have utility zero; all hard rules are broad and observed unless stated.

| Case | Manual derivation | Computed outcome |
|---|---|---|
| A, uncertainty without value (`:59`) | AB=.8 stays optimal regardless of A's equally probable soft answer. C's missing hard answer enables disjoint CD=.4 deterministically. A entropy=ln2 but VOI=0; C entropy=0 but VOI=.4. | PASS: uncertainty picks A; GraphVOI picks C. |
| B, degree differs (`:71`) | AB=1 and CD=1 dominate AX=.1 and CX=.1. Answering X adds 2 edges, allocation remains 2. Answering Y enables EY=.5, adds 1 edge and raises allocation to 2.5. Same cost, budget3. | PASS: degree picks X; GraphVOI picks Y, gain .5. |
| C, complementarity (`:82`) | AB=.8; both endpoints lack age_min. Each discloses 18 with p=.5 or 40 with p=.5; age30 fails the latter. Either singleton leaves the other unknown. Joint feasible probability=.25, value=.2. Cost6 at lambda=.05 gives -.1. | PASS: singles0, joint .2, legal paired selection, penalized -.1. |
| D, impossible unlock (`:91`) | B explicitly accepts only men, while A is a woman. A's missing age bound cannot cure that violation, even with utility100. | PASS: zero VOI, no selected ask. |
| E, displacement (`:97`) | Baseline AB6+CD2=8. A soft answer increases AC1 to AC10; new optimum AC10+BD1=11. Delta3, not AC's weight10 or its isolated increment9. | PASS: exact delta3 and changed allocation. |
| F, zero values (`:111`) | All hard fields known; random soft answers never alter AB=.5. Every query has expected gain0. | PASS: no asks. |
| Redundancy (`:118`) | Missing B/D hard answers separately enable AB10/AD9. Both compete for A. Individual scores sum19, joint optimum10. | Confirmed FAIL of redundancy handling; six units spent. |

Approximations: nearest-donor truncation, uncalibrated empirical beliefs, independent
member answers in paired support, degree-weighted candidate restriction, myopic
matching objective, static batch packing, zero lambda, positive-score-only asks,
and first-hard-ask dense fallback. Connected-component recomputation is not
implemented; only incident edges are cached, then the full matching is solved.

## 6. Comparison fairness and saved experiments (Phase C)

Main-selector code path: `graphvoi/policy.py:33` loads the same pair asset; `:48`
changes only strategy; `:50` uses the same answer asset, paired frontier and
defaults; `:59` uses optimal matching and zero waiting. Runner creates identical
`generate(seed,200,'evaluation',variant)` worlds (`scripts/run_experiments.py:65`),
same 60+40 horizon and public JSON boundary. Same weights are additionally recorded
by asset hashes in `paired_smoke.json`. Dense fallback is shared. **PASS for the
controlled design and balanced saved run matrix**, qualified by H1 for general
in-process cache isolation. Methods naturally develop different observations and
spend different totals under the same daily cap; identical subsequent graphs are
not expected. Learned-greedy/no-pairs/wait are intentional separate ablations.

Official baselines call the preserved adapter (`scripts/run_experiments.py:85`):
greedy uses baseline_asks/baseline_match, no_asks disables asks but retains the
official matcher, random shuffles feasible edges exactly as upstream. They do not
use the learned scorer for decisions. Diagnostic predictions for their chosen
pairs do use it, after decisions, without affecting actions.

MSMI is one qualifying pair, not two people. Replay/recomputation checks
`100*M/N`; N includes all arrivals by day59 including departed/unserved members.
Coverage uses distinct served members. Official `summarise` (`evaluate.py:118`)
averages within family then equally across families and disqualifies invalid rows.
All ten main methods have six episodes on the same seed, not unequal samples.
Existing .50 versus .00 comparisons remain smoke evidence only.

| Artifact / category | Actual status |
|---|---|
| paired_smoke.json + 60 traces | Complete 60 valid episodes, 10 methods x 6 scenarios x seed41001. |
| robustness_smoke.json + 10 traces | Complete 10 valid standard-scenario episodes at seed41002; 126 static belief comparisons, not 126 episodes. |
| graphvoi_protocol_final.json | Complete 6 official subprocess episodes at seed9103. |
| phase1_all_scenarios.json | Complete 6 safe_core episodes at seed9102; not learned GraphVOI results. |
| audit_greedy.json | 1 legacy official greedy episode seed101. |
| graphvoi_official_protocol.json | 1 earlier GraphVOI development episode seed9103; overlaps the final protocol set, do not count as independent. |
| optimized_single_trace.json | 1 earlier optimized GraphVOI seed41003 episode; profiling/optimization evidence, not part of balanced study. |
| paired_smoke_interrupted_* (three JSONs + traces) | Each incomplete, 7 recorded episodes; mixed earlier implementations. Exclude from completed comparisons. |
| robustness_smoke_interrupted_donor_profile.json | Incomplete snapshot work; zero full episodes. |
| analysis_partial.json | Derived from incomplete data, not finished experiment. |
| analysis_summary.json | Completed-data derived calibration/CI summaries, not new episodes. |
| profile.json, profile_final.json, dense_pool_check.json | Snapshot/stress profiling, not full outcome episodes. |
| independent_official.json / independent_repeat.json | New 6 valid official episodes / 1 repeated episode. No comparison against other methods on this audit seed. |
| independent_runtime/archive/training/evidence/source_inventory JSON | Audit evidence, not policy-performance trials. |
| 100 seeds x 6 families x 10 methods | Planned 6,000 episodes, **unexecuted**. |

Every JSON path, hash, root type, completeness and recorded episode count is in
`results/independent_evidence.json`. Trace JSONs are distinguished from aggregate
files and never counted twice. Historical files total 90 distinct recorded
method/world/belief conditions when including legacy checks and the six new audit
conditions; repeats/early versions are not independent replication. The scientific
main comparison still has only 60 episodes and one paired seed cluster.
All70 main/disclosure saved action sequences were replayed through official
validation. Official-baseline actions agree with their preserved implementations;
outcome counts, score, coverage, first waits and action digests agree. A second
replay independently recomputed saved model predictions and response labels before
checking Brier/log loss. These70 replays are not70 new performance experiments.

## 7. Training and leakage assessment (Phase D)

**PASS for current model artifact provenance and permitted inference inputs.**
Fresh training to `/private/tmp/orbit-audit-retrained-assets` reproduced
pair_model.json, answer_model.json and training_summary.json byte for byte
(`results/independent_training.json`). Training uses 48 public simulator rollouts,
seeds31001..31008 x six variants, official greedy logging, 60+40 days. No static
pool is read by training. Validation seeds41001..41003 and final planned
51001..51100 are disjoint; runner rejects declared training-seed overlap.
Audit evaluation seed61001 is independent and not used to tune anything.

Inputs: bias, public ages/gap, observed waiting age, per-soft-field agreement and
missingness, actor/partner gender and emotional-availability categories
(`graphvoi/core.py:55`). No IDs, world seeds, hidden biases/response propensities,
future fields or simulator coefficients are features. Four L2 logistic models
use 100 fixed full-batch gradient steps, step .4, penalty .05, no online updates;
low support would retain an intercept with an explicit support flag
(`graphvoi/models.py:24`). Directional evaluations swap actor/partner features
and can differ despite sharing parameters (`:51`). Joint acceptance is directly
fitted, not a product of marginal directions.

Actual stage samples: directed7392/2635 positive; joint3696/510; timely date510/382;
timely seconds382/33. 6,285 fully observed donors supply answer beliefs. Seeds
reused across scenarios create correlated people/outcomes; counts are not
independent participants. Labels are selectively observed under greedy allocation.
Null propensity prohibits unbiased IPS claims. No such claim is made.

Pre-action features are preserved before advance; only observed feedback labels
them after follow-up. Pending outcomes are excluded. Conditional second labels
exist only for timely completed dates; a mature null second response is a negative
**recorded timely Yes event**, not a negative preference. Train and report label
definitions match the official window. Response preference among respondents is
not a separately validated model. Historical claims of no manual tuning cannot
be proved from this workspace's absent version history.

Inference assets are JSON, math/stdlib plus vendored NetworkX3.5. No ML service,
GPU, numpy, scipy, LLM or internet dependency is used on the policy path.

## 8. Calibration assessment

Brier is mean `(p-y)^2`; log loss is mean negative Bernoulli log likelihood with
1e-12 protection; reliability is ten fixed bins (`graphvoi/analysis.py:105`).
Held-out predictions were recorded before outcomes (`scripts/run_experiments.py:107`)
and matched to mature observed events after40-day follow-up. Direction-specific,
gender-group and conditional-stage counts/curves are saved. No evaluation-label
calibrator was fitted. **PASS for descriptive held-out evaluation; FAIL for a
statistically supported calibration claim (H4).**

GraphVOI smoke: n956, Brier .2329804106, log loss .6585283091; 478 labels in each
canonical endpoint direction. These are repeated participant/introduction records
from one independent seed cluster. Bootstrap intervals are explicitly unsupported
and degenerate at nclusters=1. A raw label threshold50 is not sufficient evidence
for subgroup reliability with repeated people and one world seed. Only33 positive
training seconds outcomes make rare-stage calibration especially fragile. Current
model predicts timely recorded events, not hidden compatibility or actual consent.

Report tables and caveats match stored smoke evidence. The report does not claim
a win or calibrated real-world probabilities. Its descriptive numbers are supported;
comprehensive organiser feedback conclusions, container claims and exact batch-VOI
claims would be unsupported. Preserve this distinction in the final report.

## 9. Disclosure robustness assessment (Phase E)

Seven belief conditions enumerate changed masses/support: none, biased,
overconfident, underconfident, refusal, non_binary refusal and temporal drift
(`graphvoi/answers.py:61`). Actual disclosure is separate: research wrapper applies
additional bundle refusal .35, subgroup refusal or day/35 ramp after ordinary
public asks (`scripts/run_experiments.py:27`). It preserves previously known values
and underlying preferences; hidden wrapper parameters and RNG never enter policy
JSON. **PASS for separation/no leak; FAIL for sufficient robustness evidence (H4).**

Executed: 18 public snapshots x 7 beliefs=126 static comparisons and 10 full
standard-scenario episodes on one seed. All10 MSMI=0. Coverage/cost changes and
Jaccard .907 are descriptive; MSMI degradation is not estimable here. Other scenario
families have snapshot sensitivity only, not full disclosure-change episodes.
No independently trained alternative disclosure model or multi-seed mismatched
training/evaluation study has run. These remain implemented perturbations/planned
research, not completed validation.

Additional caution: wrapper RNG draws sequentially with ask order, so changed
policies encounter different random refusal draws. Pairing on a seed preserves
the starting world, not identical per-person/question disclosure shocks. For a
stronger causal comparison, key public experimental RNG by world/member/question/
day in the engine (never expose keys to inference), or report this coupling limit.

## 10. Waiting and opportunity assessment

`OpportunityTracker` (`graphvoi/analysis.py:20`) counts public available days,
feasible/unresolved/known-failure/no-other days, hard refusals, distinct eligible
partners excluding past pairs, introductions, first waits and ask costs. Observed
hard rules remain intact; eligibility is time-varying observed feasibility, not
reconstructed hidden feasibility. Some fundamentally ineligible members cannot be
identified from declined/missing observations; do not label all unserved as failures.

First-introduction waits match official assigned_day minus arrival. Unserved have
wait=None and remain in coverage/counts. Report medians/p90 condition on served
members: no silent deletion from denominators, but not a population waiting-time
analysis (M1). Waiting after later introductions is not first-introduction waiting.
Classification priority is served, ever-feasible unserved, hard-declined, unresolved,
no-observed-feasible opportunity; this is a descriptive taxonomy, not causal blame.

GraphVOI records393 served/807 unserved among1,200 member-scenarios; unserved377
hard-refused,350 unresolved,7 ever-feasible,73 no observed opportunity. Group sizes
595 women/546 men/59 non_binary are repeated scenario populations, not independent
people; only17 non_binary records are served. No supported group inequity inference
or hard-preference relaxation is established. Candidate/opportunity coverage is
public graph exposure, not hidden true supply. Full frontier recall and censor-aware
waiting remain needed.

## 11. Runtime, failure handling and reproducibility (Phases F/G)

Fresh six-family official evaluation invokes the policy in a new process for each
ask/match and enforces the ten-second wall-clock limit (`evaluate.py:45`). All720
calls passed. The extra repeated standard episode adds120 calls and agrees on full
action hash and outcome counts. Fresh score .583333 MSMI/100 at seed61001 is a
validity result, not a fair superiority comparison or replacement for the smoke.

Twenty additional fresh-process profiles cover empty/single/declined, day20 public
state and a fully eligible200-member graph, both phases and two Python hash seeds.
Max measured wall time1.029s, max peak RSS58,032,128bytes (55.34MiB), under this
macOS interpreter and these fixtures. Profile wrapper uses resource.getrusage in
the child; `/usr/bin/time -l` was blocked by sandbox sysctl restrictions. Do not
generalize these maxima to all worlds or Docker. 750kB memory roundtrip passes;
unsupported schema fails clearly without stdout. Empty/sparse actions are valid.
Dense fallback is deterministic and counts in memory; match remains exact. There
is no general safe recovery from missing/corrupt model assets, and no demonstrated
timeout rescue for an arbitrary expensive matching graph. Include assets and
benchmark adversarial near-fallback graphs under actual container limits.

Fresh training reproduction and archive extraction establish offline local
reproducibility for the tested interpreter. The pre-audit candidate archive SHA256
is `f91a2248751e4bd0f9860da949f21582d71edbdd4b22cfa2fbd356203e553710`.
All514 file names were checked; no research/.git/credential/key/bytecode paths were
included. Research remains on disk and ignored. Model donors contain no IDs or
latent fields. Targeted credential-pattern scan found none in reviewed source.
This is scoped evidence, not a claim that a future allowlisted directory can never
contain a secret. Docker explicitly copies inference code/assets/notices and no
world files. Required source/assets, pinned inference dependency and notices exist;
clean Docker/Python3.12 validation remains UNVERIFIED, contribution licence absent.

Reproduction commands:

```bash
python3 -m unittest discover -v
python3 verify_data.py
python3 scripts/train_models.py --output /private/tmp/orbit-audit-retrained-assets
python3 scripts/evaluate_method.py --method graphvoi --variants all --seeds 61001 --output results/independent_official.json
python3 scripts/evaluate_method.py --method graphvoi --variants development --seeds 61001 --output results/independent_repeat.json
python3 scripts/audit_runtime.py
python3 scripts/independent_audit.py
# On a Docker-capable machine, still required:
docker build -t orbit-graphvoi:audit .
python3 evaluate.py --image orbit-graphvoi:audit --seeds 61001 --variants all --output results/independent_container.json
```

## 12. Release verdict and next three actions

**FAIL — currently not submit-ready.** Critical compliance cannot be certified
until the actual assessed container runs successfully, and a public immutable
source version with required artifacts is accessible and pinned. See
`docs/RELEASE_CHECKLIST.md`; no UNVERIFIED critical item may be treated as PASS.

1. Validate Docker build and all six scenarios under the exact resource envelope;
   stress the bounded counterfactual frontier, measure phase maxima/RSS and image
   contents, and fix any validity/resource failures before release.
2. Correct cache independence and failure-aware statistical reporting; resolve or
   explicitly scope batch redundancy, then freeze code/assets and run the larger
   paired multi-seed study with answer/disclosure validation and censor-aware
   opportunity/calibration analysis. Preserve old smoke evidence separately.
3. Choose the contribution licence, rebuild/retest the final clean archive including
   this audit and final evidence, publish an accessible immutable commit/archive,
   and verify/pin its full SHA and artifact URLs before the submission deadline.
