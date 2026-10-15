# Release checklist — independently audited candidate

10 October 2026. Every item is PASS, FAIL or UNVERIFIED. PASS is scoped to the
named evidence, not all possible private worlds. **Overall: FAIL / not ready.**
Critical UNVERIFIED items must pass before submission. Findings and exact fixes:
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
| Full joint batch redundancy handling | FAIL | H2: individually19 versus joint10. |
| Common pair model/weights/solver/wait/frontier/budget/worlds | PASS | Shared code path and balanced 60-episode matrix; actual spending differs naturally. |
| Arbitrary in-process cache correctness/episode isolation | FAIL | H1: demographic/status dependencies omitted; no collisions observed in saved-query probe. |
| Official greedy/no_asks/random decisions retained | PASS | Preserved adapter source and replayed baseline actions agree. |
| Official MSMI and equal-family aggregation | PASS | Recomputed summaries and official engine replays. |
| All invalid/missing episodes block CI inference | FAIL | H3: CI currently drops invalid rows. |
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
| Machine-readable completed results and traces | PASS | 60 main +10 disclosure episodes, complete flags, scenario summaries. |
| Interrupted/planned runs distinguished from completed ones | PASS | Audit inventory and explicit report caveats. |
| Report descriptive numbers supported | PASS | Recomputed summaries, trace metrics and calibration. |
| Report proves research superiority/robustness | FAIL | Insufficient evidence; report does not claim such proof. |
| Fresh existing candidate source archive runs locally | PASS | 514 files; 58 archive tests, 71 data checksums, empty protocol call. |
| New audit artifacts included in candidate archive | FAIL | Existing archive deliberately preserved; rebuild after final fixes. |
| Private research files excluded from current archive/image copy list | PASS | Archive path/content scan, explicit Docker COPY, research preserved locally. |
| Credentials absent in reviewed source/archive | PASS | Targeted credential patterns/path scan found none; scope limited to reviewed version. |
| Docker bytecode/cache exclusions | FAIL | Broad inference-directory allow rules include local __pycache__; M5. |
| Exact analysis/runner source provenance in every result | FAIL | M3: main hashes exclude experiment scripts; old analysis hash documented separately. |
| Current official corrections incorporated | PASS | API main SHA matches a8e26b35118cfa8e886a02f93984923e43ab64f6; unmodified kit/evaluator hashes. |
| Git setup, branch, commit and push complete | FAIL | This directory is not a Git repository; gh unavailable; no push claimed. |

Release order: validate container; correct scientific runner/analysis and gather
the multi-seed evidence; choose licence and publish/retest/pin the exact final
source version. Keep every unresolved critical item visible until it passes.
