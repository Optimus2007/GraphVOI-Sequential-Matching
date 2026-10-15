# Release checklist — corrected candidate

Original audit10 October2026; correctness follow-up11 October2026. Every item is PASS, FAIL or UNVERIFIED. PASS is scoped to the
named evidence, not all possible private worlds. **Overall: FAIL / not ready.**
Critical UNVERIFIED items must pass before submission. Original checklist is
preserved in `audit_history/RELEASE_CHECKLIST_original.md`; current corrections
and scope are recorded in the audit follow-up. Findings and exact fixes:
[INDEPENDENT_AUDIT.md](INDEPENDENT_AUDIT.md).

## Critical rule and execution gates

| Item | Status | Evidence / remaining action |
|---|---|---|
| Exact ask JSON protocol | PASS | `graphvoi/policy.py:43`, `policy.py:48`; fresh official episodes. |
| Exact match JSON protocol | PASS | `graphvoi/policy.py:62`, `evaluate.py:26`. |
| Official reciprocal hard rules and explicit preferences | PASS | `graphvoi/core.py:118`, `kit.py:69`; manual violation test. |
| Missing/declined hard values never authorize matching | PASS | `graphvoi/core.py:20`, `graphvoi/answers.py:96`. |
| Actual matching never uses hypothetical answers | PASS | Separate refreshed match request, `scripts/run_experiments.py:78`, `graphvoi/policy.py:62`. |
| No hidden world/seed/latent reconstruction in inference | PASS | Explicit feature/import audit and boundary tests. |
| Permitted training source and current assets | PASS | 48 lawful observed rollouts; byte-identical retraining in `independent_training.json`. |
| Censoring and conditional recorded-event labels | PASS | `scripts/train_models.py:45`, `:59`, `:68`; independent label replay. |
| Valid nonrepeated disjoint introductions | PASS | `graphvoi/core.py:118`; 6 fresh full scenarios, 70 saved-action replays. |
| Legal duplicate-free asks within 12-unit cap | PASS | `graphvoi/core.py:142`, `graphvoi/clarification.py:154`; official engine validation. |
| Finite JSON and stdout-only response | PASS | Real invocations; invalid schema emits no stdout. |
| Empty/sparse population handling | PASS | Fresh empty/single cases and tests. |
| Explicit stateless memory persistence and tested byte limits | PASS | 750,000-byte roundtrip; no model/graph memory payload. |
| Determinism for fixed observation/memory in fresh processes | PASS | Two PYTHONHASHSEED values, 20 profiles; full episode repeat hash identical. |
| Ten-second local invocation validity | PASS | All calls in 6 fresh official scenarios + repeat under official subprocess timeout. |
| Docker build and entrypoint | UNVERIFIED | Docker executable unavailable; C1. |
| Offline isolated official Docker episodes | UNVERIFIED | Must actually run all six families in container. |
| 2 CPU / 1 GiB / 64 process / 64 MiB tmp envelope | UNVERIFIED | Local RSS is scoped evidence, not container compliance. |
| Image size below 2 GiB | UNVERIFIED | Source/assets small, but image not built/measured. |
| Immutable publicly accessible source version and pin | FAIL | No Git metadata/commit, no demonstrated public archive URL; C2. |
| Personal repository visibility / public access | UNVERIFIED | GitHub API 404; private/inaccessible/absent cannot be distinguished. |
| Submitted report/results/assets in the exact pinned version | UNVERIFIED | Final version not published/pinned. |

## Algorithm and scientific gates

| Item | Status | Evidence / remaining action |
|---|---|---|
| Counterfactual maximum-weight matching value | PASS | `graphvoi/clarification.py:88`; independent manual A–F cases. |
| Probability-weighted expectations and actual state updates | PASS | `graphvoi/clarification.py:76`, `graphvoi/answers.py:85`. |
| Joint two-member complementary questions | PASS | Manual .25 probability x .8=.2 example. |
| Cost formula and declared zero lambda | PASS | `graphvoi/clarification.py:93`; explicit nonzero-penalty test. |
| Conditional batch redundancy within declared approximation | PASS | H2 fixed: joint marginal re-evaluation, unique residual costs; exact small/random oracle tests.8-world quadrature/greedy frontier remain approximate. |
| Common pair model/weights/solver/wait/frontier/budget/worlds | PASS | Shared code path and balanced 60-episode matrix; actual spending differs naturally. |
| Cached/uncached equivalence and invocation isolation | PASS | H1 fixed: full dependency key,400 exact randomized comparisons, immutable copies, per-call clearing. |
| Official greedy/no_asks/random decisions retained | PASS | Preserved adapter source and replayed baseline actions agree. |
| Official MSMI and equal-family aggregation | PASS | Recomputed summaries and official engine replays. |
| All invalid/missing/duplicate episodes block CI inference | PASS | H3 fixed: expected matrices and preserved failures; incomplete/invalid scores and CIs suppressed. |
| Multiple independent paired seeds with meaningful intervals | FAIL | H4: one cluster in main smoke, final 100-seed study unrun. |
| No superiority claim based on smoke | PASS | Report explicitly disclaims it; baselines tie GraphVOI's .50 score. |
| Directional probabilities separately evaluated | PASS | Shared directed model with swapped features, `graphvoi/models.py:51`. |
| Held-out Brier/log loss/reliability evaluation | PASS | Measured mature labels, descriptive counts and bins; no fitted calibration claim. |
| Statistically supported directional/subgroup calibration | FAIL | One seed cluster, repeated people, limited rare outcomes. |
| Answer-model held-out fidelity and support validation | UNVERIFIED | H5: probabilities/unsupported donors/refusal not validated. |
| Disclosure beliefs separated from actual environment changes | PASS | Public JSON boundary and independent wrapper. |
| Multi-seed, multi-family disclosure degradation study | FAIL | Only snapshots across families; full episodes only one standard seed. |
| First waits/unserved/coverage counted correctly | PASS | Official replay; unserved retained with wait=None. |
| Population waiting analysis including censoring | FAIL | Served-only medians/p90; M1. |
| Observed opportunity/clarification allocation accounting | PASS | Tracker fields and separate blocking classifications. |
| Subgroup conclusions supported by independent samples | FAIL | Raw subgroup counts are not independent seed clusters. |
| Historical absence of final/test tuning proved | UNVERIFIED | Present code/seeds safe; absent version history cannot prove manual history. |

## Packaging and reproducibility gates

| Item | Status | Evidence / remaining action |
|---|---|---|
| Required policy/module/model files exist | PASS | Source inventory and fresh archive extraction. |
| Inference dependency pinned and included offline | PASS | Vendored NetworkX3.5, requirements pin, 287 hashes verified. |
| Starter/data/dependency notices retained | PASS | LICENSE, DATA_LICENSE.md, NETWORKX_LICENSE.txt and provenance. |
| Team Orbit contribution licence selected | FAIL | M6: owner must select/include it. |
| Setup/evaluation/training commands documented | PASS | README and EVALUATION_PROTOCOL; tested current interpreter. |
| Analysis-only dependencies pinned | FAIL | Matplotlib missing from separate analysis pin; M4. |
| Machine-readable completed results and traces | PASS | Corrected360-episode pilot and43,200 action records; historical60 main +10 disclosure preserved as prior builds. |
| Interrupted/planned runs distinguished from completed ones | PASS | Audit inventory and explicit report caveats. |
| Report descriptive numbers supported | PASS | Recomputed summaries, trace metrics and calibration. |
| Report proves research superiority/robustness | FAIL | Insufficient evidence; report does not claim such proof. |
| Fresh existing candidate source archive runs locally | PASS | 514 files; 58 archive tests, 71 data checksums, empty protocol call. |
| New audit artifacts included in candidate archive | FAIL | Existing archive deliberately preserved; rebuild after final fixes. |
| Private research files excluded from current archive/image copy list | PASS | Archive path/content scan, explicit Docker COPY, research preserved locally. |
| Credentials absent in reviewed source/archive | PASS | Targeted credential patterns/path scan found none; scope limited to reviewed version. |
| Docker bytecode/cache exclusions | FAIL | Broad inference-directory allow rules include local __pycache__; M5. |
| Full source/observation/archive provenance | FAIL | Corrected pilot hashes all inference/runner scripts and assets, declares matrix; M3 still requires full observation/archive hashes and resumability. |
| Current official corrections incorporated | PASS | API main SHA matches a8e26b35118cfa8e886a02f93984923e43ab64f6; unmodified kit/evaluator hashes. |
| Git setup, branch, commit and push complete | FAIL | This directory is not a Git repository; gh unavailable; no push claimed. |

Release order: validate container; correct scientific runner/analysis and gather
the multi-seed evidence; choose licence and publish/retest/pin the exact final
source version. Keep every unresolved critical item visible until it passes.


## Corrected-build verification gates

| Item | Status | Evidence / remaining action |
|---|---|---|
| Entire corrected suite | PASS |85 actually executed tests, zero failures; audit_history/corrected_tests_85.txt. |
| Official public data | PASS |71 checksums verified; preserved verifier output. |
| Manual and random counterfactual reference | PASS | A–F, soft alternating complement,30 brute-force small graphs; finite-support exact reference. |
| Paired overlapping costs and redundant edges | PASS | Unique residual asks/costs, probabilistic joint9.5 case, paired BC11 example. |
| Full global batch optimality | UNVERIFIED | Not claimed; greedy/frontier/support/quadrature limits are explicit. |
| Exact joint expectation after8-world compression | FAIL | Explicit16-world counterexample:15 exact vs17.5 capped; production is approximate. |
| Large-support cap sensitivity quantified broadly | UNVERIFIED | Small exact/reference cases pass; no broad cap sensitivity study conducted. |
| Full frozen-build official episodes | PASS | All six families seed63004; repeated development action hash equal. |
| Fresh-process profiling | PASS |20 calls, maxask1.4344s/maxmatch0.7580s/RSS61.14MiB; measured host scope only. |
| Serialized memory and failure handling | PASS |750,000-byte roundtrip; invalid schema rejects without policy stdout. |
| Models load and training assets unchanged | PASS | Fresh invocation/tests; fixed hashes in CORRECTED_BUILD_MANIFEST.json. |
| Frozen10-seed paired pilot complete | PASS |360 valid episodes,60/method, zero invalids; expected matrix/43,200 actions/metrics/source/paired bootstrap independently verified. |
| Full100-seed study run | UNVERIFIED | Explicitly not launched. |
| Corrected source archive rebuilt/validated | FAIL | Existing candidate archive retains superseded implementation; rebuild before publishing. |
| Docker and immutable release | UNVERIFIED | Both release blockers remain; no readiness claim. |


## Completed pilot verdict

| Item | Status | Evidence / limitation |
|---|---|---|
| Balanced complete pilot and retained failures | PASS |360 expected/recorded,60/method,10 seed clusters, zero invalids. |
| Independent aggregate/trace/MSMI-bootstrap verification | PASS |corrected_pilot_verification.json;43,200 phase actions, all denominators and frozen hashes checked. |
| Pilot intervals establish definitive superiority | UNVERIFIED |Limited10-cluster sample, rare outcomes; no superiority claim. |
| Safe to begin frozen local prespecified100-seed study | PASS |Correctness tests, official validity and balanced pilot clear; study not launched. |
| Submission-ready | FAIL |Docker/resource/image validation and accessible immutable pinned release remain unresolved; additional methodological/packaging findings documented. |


## v3 release gates (second review, 15 October 2026)

Earlier tables are kept as historical record. Where a row below covers the same
item, this table is current.

| Item | Status | Evidence / remaining action |
|---|---|---|
| Unit/integration suite | PASS | 93 tests (85 earlier + 8 in `tests/test_budget_fill.py`) |
| Official data checksums | PASS | 71 files, `verify_data.py` |
| Model assets reproducible | PASS | `train_models.py` rerun: all three asset SHA-256 identical |
| Budget under-spend (V1) | PASS | Shared `fill_hard_budget`; dev check coverage 28.2% → 32.7% (greedy 32.8%) |
| Disqualifying-timeout guard (V2) | PASS | 6 s ask deadline; tests; `deadline_count` recorded per episode |
| Docker build and entrypoint | PASS | `graphvoi-orbit:round2`, Python 3.12.7, 227 MB, bytecode precompiled |
| Offline isolated official Docker episodes | PASS | `evaluate.py --image`, six families, seed 101, all valid, eligible |
| Per-call container runtime | PASS | 216 calls on heavy real states: ask max 2.55 s, match max 0.80 s incl. startup; deterministic |
| 2 CPU / 1 GiB / 64 pids / read-only / no network | PASS | Official `docker_command` flags enforced by Docker in every container call |
| Image size below 2 GiB | PASS | 227 MB |
| Docker bytecode/cache exclusions (M5) | PASS | `.dockerignore` excludes `**/__pycache__`, `**/*.pyc` |
| Official subprocess path, v3 | PASS | `results/v3_official_subprocess.json`, six families, seed 65001, all valid |
| Git repository on official upstream | PASS | Based on `a8e26b3`; kit/evaluator/data unchanged |
| Branch pushed | PASS | `orbit-graphvoi-round2` on private origin |
| Repository public, accessible without credentials | FAIL | Owner must switch visibility before submission |
| Final 40-character SHA pinned in Final submission issue | FAIL | Owner action after the final commit |
| Team contribution licence (M6) | FAIL | Owner must choose; starter LICENSE covers only the kit |
| Confirmatory 100-seed study | UNVERIFIED | Running: `results/v3_confirmatory.json`, 4,200 expected episodes |
| GraphVOI superiority | UNVERIFIED | Decided only by the prespecified Bonferroni rule after the study |
