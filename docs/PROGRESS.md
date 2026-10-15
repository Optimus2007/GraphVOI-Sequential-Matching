# Progress

## Independent audit — 10 October 2026

See INDEPENDENT_AUDIT.md and RELEASE_CHECKLIST.md for the adversarial review.
Fresh workspace suite: 67 tests pass, including independent manual GraphVOI cases
and tests documenting batch redundancy, answer-cache dependencies and invalid-row
CI behavior. Data verifier: 71 files pass. Retraining to a temporary directory
reproduces all model/summary bytes. Six new official GraphVOI scenario episodes at
seed61001 pass; one repeated standard episode has identical actions/outcomes.
The unchanged pre-audit archive passes its own 58 tests and verifier after fresh
extraction. Audit additions are not in that preserved archive. No superiority or
submission-readiness claim: Docker and public immutable publication remain blocked.
Noncritical source/analysis findings have exact required fixes in the audit.

The historical phase entries below describe the earlier implementation version;
their test counts and smoke evidence are not the new audit's execution counts.

## Phase 0

- Research context and six PDF pages read; feedback file is empty. Task message
  supplies required feedback priorities.
- Official source snapshot restored and Git blob hashes verified.
- All 71 public data checksums verified; 2,000 members, 613 introductions,
  1,270 feedback events, 1,129 conversations.
- Original unittest suite: 22 tests passed.
- Architecture, contract, split, baseline and resource audit documented in
  IMPLEMENTATION_PLAN.md. Official greedy baseline seed 101: valid, MSMI/100 = 0.5, coverage = 0.46, ask cost = 198; saved in results/audit_greedy.json (smoke only).
- No Git checkout, no Docker executable. Git clone/push and container verification
  remain blocked by environment. No competition scores claimed.

## Phase 1

Implemented and passed: normalization, official reciprocal feasibility, public
directional feature construction, bounded prior utility, exact weighted blossom,
canonical tie order, output revalidation, waiting threshold, legal asks and
stateless memory round-trip. Six complete 200-member scenario episodes passed
under the official subprocess runner (seed 9102). Results:
results/phase1_all_scenarios.json. No simulator/evaluator changes.

## Phases 2 and 3

- True counterfactual optimal-matching values implemented, with complementary
  two-member constraint actions, cost-aware batch packing, legal candidate
  frontier, edge caching and deterministic dense-graph fallback.
- Controlled selectors use the same assets and solver. Uncertainty uses field
  answer entropy; degree uses expected added edges. Static batch packing is a
  documented approximation, not an optimal joint-VOI batch.
- Trained on 48 public observed rollouts: 7,392 directional labels, 3,696 joint
  response labels, 510 mutual acceptances, 382 timely completed-date examples,
  33 timely mutual second-meeting positives, 6,285 disclosed constraint donors.
- Joint acceptance is fitted directly; directional probabilities are distinct
  evaluations of the shared directed model, not multiplied as independent.
- Unit tests cover manually solvable rankings, paired complementarity, exact
  answer expectations, no inference on refused fields, and censored/undated labels.
- A GraphVOI episode passed official subprocess validation (seed 9103), with
  identical action hash before/after copy optimization. All six final-code scenario episodes passed the official subprocess runner; results/graphvoi_protocol_final.json.

## Phases 4 through 7

- Disclosure belief perturbations, independent actual-disclosure wrapper,
  static question stability, opportunity/waiting tracking, directional and
  conditional-stage calibration, paired intervals and profiling implemented.
- Experiment runners persist complete actions, pre-action predictions, observed
  feedback and member opportunity records. Research JSON boundaries are checked.
- Controlled smoke comparison: ten methods, all six families, paired seed 41001,
  complete: 60/60 valid episodes; results/paired_smoke.json. Disclosure smoke complete: seed 41002, 10 valid full episodes and 126 paired snapshot comparisons; results/robustness_smoke.json.
- Profiling found full-state and donor deep-copy overhead. Optimizations preserve
  actions. Earlier interrupted runs are saved with explicit interrupted filenames,
  not counted as completed comparisons. Final inference code is frozen for runs.
- Proposed 100-seed-per-family study remains unrun. No superiority claim.

## Phase 8 and blockers

Offline assets, pinned vendored dependency with licence, explicit Docker copy
boundary, training/evaluation commands and provenance are present. The technical report and actual smoke results are complete. Docker executable is absent; container build,
container resource validation and official Docker evaluation are blocked.
No Git checkout, commit or push exists in this workspace.

## Final verification

- 58 unit/integration tests passed; all 71 data checksums and 287 vendor hashes pass.
- Official GraphVOI subprocess runner: six of six valid scenario episodes at seed 9103.
- Controlled research comparison: ten methods times six scenarios, seed 41001, 60 valid full episodes. GraphVOI MSMI/100 = .50; uncertainty = .00; degree = .00; random and learned greedy/maxweight also = .50. This is an underpowered smoke result, not a win claim.
- Disclosure study: 10 valid full episodes and 126 snapshot comparisons.
- Dense 200-member subprocess test: ask fallback 1.14 s, exact matching 3.01 s including startup, 100 valid introductions.
- Report and calibration reliability artifacts generated from actual outputs.
- 100-seed-per-family comparison remains unrun; Docker build attempt failed because docker is absent. Git metadata remains unavailable.

- Clean candidate archive extracted to a fresh temporary directory: all 58 tests and data verification passed with no research files or Git metadata included. Source archive is output/GraphVOI_Orbit_Round2_candidate.tar.gz.


## Correctness repairs and frozen pilot

- Original H1/H2/H3 failures reproduced and preserved. Complete cache dependency
  identity, immutable asset/result copies, per-invocation clearing, uncached
  reference and declined-bound crash handling implemented.
- Static batch packing replaced by conditional joint matching-value acquisition;
  exact small oracle, probabilistic redundancy and hard/soft complement tests.
  Bounded8-world/256-work production approximation documented.
- Statistics retain invalid runs, expected matrices, missing/duplicate detection;
  failure-aware official scores and stratified paired-seed bootstrap.
-83 tests executed/pass;71 checksums verified. Fresh six official families at
  seed63004 valid; repeat development hash equal. Max fresh ask1.4344s,
  match0.7580s,61.14MiB RSS,750kB memory roundtrip. Docker remains unverified.
- Frozen pilot launched:62001..62010, six families, three selectors plus three
  official baselines,360 expected episodes. Completion and measured results are
  appended after actual run. No full100-seed experiment launched.

- Additional contrasting-donor cache test verifies numerically changing age/gender/zone/status distributions; complete suite rerun:84 passed. Inference/runner/asset hashes unchanged during pilot.

- Quantified16-world quadrature test added: exact15 vs capped17.5, bias2.5 explicitly documented. Full suite rerun:85 passing. Inference/runner/asset hashes unchanged; approximation is not hidden.

- Frozen pilot completed:360 valid episodes,60/method,10 paired seeds ×6 families, zero invalids; 58.0min host wall time.43,200 action records and all metric/trace/source/paired-CI checks passed. Report includes measured tables and limited-support CIs. Full100-seed study still unrun; submission remains blocked by Docker/immutable publication.

Completion recorded11 October2026. Corrected pilot and verification artifact hashes: f3e6bc045cbf3610625532aa4d6c0e68d365524d94f61a26cf0f5cc0f54d1c13 (pilot), 3026aa02251a3e13a78e7c6c371871c882a0e87b88dbb3a5b31255eacd3251c4 (verification).
