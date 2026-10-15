# Correctness repair record

This supersedes the historical H1/H2/H3 audit findings without erasing them.
Original source, audit/checklist/report, and reproduced failures are retained in
`docs/audit_history/`. Initial three regressions failed before code changes.
A fourth soft-complementarity regression also failed before its frontier fix.

## Answer calculations (H1)

Root: cache identity omitted age, gender, zone and disclosure statuses. Age30 to50
returned age_min25 from cache instead of45 from fresh calculation. `outcomes_uncached`
now supplies the no-cache reference. The full dependency key is day, requested
field, age, gender, zone, all fields/statuses, support count and perturbation.
The inference asset is an immutable snapshot exposed through copies. Member IDs
only look up records; scenario labels, memory and histories never enter beliefs.
Return copies prevent cache/asset poisoning. Clear observation caches on every
ask invocation, including trusted in-process episodes. A new randomized declined
case also exposed a None-bound comparison; validate order only when both bounds
exist, without filling refused fields.

400 randomized state/model variants compare cached and uncached answers exactly,
including changes across hypothetical worlds, observations/statuses/missingness,
scenario labels/memory and perturbations. Tests also mutate returned results,
external assets, and reuse models across policy invocations. Exact equality is
stricter than a numerical tolerance. This demonstrates cache equivalence for the
current calculation, not that empirical answer probabilities are calibrated.

## Conditional batch acquisition (H2)

Root: independent AB10 / AD9 gains were packed as19 though their joint optimum
is10. Selection now carries joint worlds for selected asks and recomputes each
candidate's conditional expected matching-value increment. Overlapping actions
become unseen residual asks, with unique costs; no independent-score subtraction.
Paired candidates use Cartesian answer outcomes jointly. Every world uses exact
maximum-weight general-graph matching and official eligibility.

`joint_value_reference` is uncapped for finite support. Independent tests use
brute-force matching and naive uncached joint enumeration on30 random small
instances. Adversarial AB10(p=.5), AD9 yields joint9.5, not14. Paired overlap BC11
versus AB10 buys BC once for6 units, not all three endpoints for9. Soft questions
on nonpartner A,C can change an alternating allocation from AD6+BC6=12 to
AB7+CD7=14; either singleton has zero value, the pair has2. The paired frontier
now reserves up to4 direct hard pairs and fills the remaining8-total slots from
all singleton combinations. The shared16-single frontier remains restricted.

Production approximation: greedy acquisition, nearest-four donor support,
16 singles/8 pairs,8 joint worlds,256 coalesced candidate-outcome evaluations.
Above8 selected outcomes systematic deterministic probability quadrature
compresses the joint distribution. It can bias future conditional estimates.
Work exhaustion skips unaffordable evaluations and stops with legal selected asks;
no wall-clock randomness. Dense >600-edge common fallback is unchanged. This
fixes static duplicated allocation credit; it does not prove globally optimal
batch information acquisition or zero quadrature error on arbitrary large worlds.

## Failure-aware statistics (H3)

Root: invalid rows/missing pairs disappeared before bootstrapping, although the
official scorer disqualifies a method with any invalid episode. All records and
validity flags now remain. Explicit expected scenario/seed/method matrices detect
missing BOTH-policy runs, duplicates and incomplete sets. Invalid/missing/duplicate
comparisons produce no numerical performance delta or CI. Checkpoint summaries
also remain ineligible until each declared matrix is complete.

Complete comparisons align by scenario and seed. Zero-MSMI worlds remain. Primary
means weight six families equally, not by available sample counts. Bootstrap
resamples whole paired world-seed clusters, retaining cross-family dependence.
Scenario-membership signature strata preserve family denominators when seed sets
are partially overlapping or severely imbalanced.2,000 replicates, seed771;
10 pilot clusters are flagged as limited support. Tests cover valid/invalid,
missing/duplicate/unequal runs, missing both, zero/identical outcomes,100:1 scenario
imbalance, shared-seed cancellation and checkpoint failure retention.

## Verification commands

```bash
python3 -m unittest discover -v
python3 verify_data.py
python3 scripts/audit_runtime.py --output results/corrected_runtime_v2.json
python3 scripts/evaluate_method.py --method graphvoi --variants all --seeds 63004 --output results/corrected_verified_v2.json
python3 scripts/evaluate_method.py --method graphvoi --variants development --seeds 63004 --output results/corrected_repeat_v2.json
python3 scripts/run_pilot.py --workers 3 --output results/corrected_pilot.json
```

Executed suite:85 passing tests, zero failures. Data:71 checksums verified.
Fresh-process pathological/normal/dense profiles:20 calls, two PYTHONHASHSEED
values, identical actions; maxask1.4344s, maxmatch0.7580s, peakRSS61.14MiB.
750,000-byte serialized memory roundtrip succeeds; unsupported schema emits no
policy JSON. Models load in fresh invocations. Container limits remain unverified.
Final six-scenario/repeat/pilot completion is recorded in the appended audit and
updated report; do not infer pilot completion merely from this protocol.

Only inference answer/clarification/policy modules, analysis, experiment/profiling
runners, regression tests and documentation are changed. Official simulator,
evaluator, baseline code and model weights are unchanged. No training, model
architecture, Docker configuration or full100-seed study changes were made.


## Changed source and test locations

| Concern | Source |
|---|---|
| Cache lifecycle/key/reference/assets | `graphvoi/answers.py:10`, `:24`, `:27`, `:43`; `graphvoi/policy.py:51` |
| Joint paired frontier/reference/conditional batch | `graphvoi/clarification.py:45`, `:139`, `:175` |
| Expected matrix/failure-aware paired bootstrap | `graphvoi/analysis.py:122`, `:141` |
| General runner incomplete-score gate/provenance | `scripts/run_experiments.py:23`, `:27`, `:177` |
| Frozen pilot/failure retention/checkpoints | `scripts/run_pilot.py:35`, `:66` |
| Output-scoped runtime profiler | `scripts/audit_runtime.py` |
| New cache/batch/statistics/oracle/runner tests | `tests/test_correctness_fixes.py` (19 new tests) |
| Historical defect assertions replaced by resolved regressions | `tests/test_independent_audit.py:107`, `:114`; original preserved |

One old test that asserted incorrect CI behavior was replaced by corrected
failure-aware tests.67 original tests minus1 superseded defect assertion plus19
new tests =85 currently executed passing tests. Contrast-donor test added during
pilot validates existing frozen calculation without changing inference/runner/
model hashes; before-launch gate was83 tests.

Independent completed-matrix replay commands (run only when pilot complete):

```bash
python3 docs/audit_history/verify_completed_pilot.py.txt
```

The verifier has its source checksum in corrected_pilot_verification.json and
recomputes primary paired intervals independently of graphvoi.analysis.

Explicit quadrature counterexample: two independent four-outcome hard questions
produce16 worlds; each unlocks a disjoint weight10 pair with probability.75, so
exact expectation15. Eight systematic midpoint worlds miss every second-member
failure, yielding17.5. Regression asserts both results and measured bias2.5.
This is a runtime-bounded approximation, with no small universal error bound or
global-batch exactness guarantee. Cap sensitivity remains a research limitation.
The static additive-credit bug is fixed; arbitrary joint expectation is not exact
after compression. No policy change was made after the pilot freeze.
