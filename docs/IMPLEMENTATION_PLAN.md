# GraphVOI implementation plan

## Audit basis

Team Orbit; official release 1.0.0, source commit
`a8e26b35118cfa8e886a02f93984923e43ab64f6`. Read all three research inputs:
context Markdown, all six PDF pages (Apple PDFKit extraction), and the empty
feedback file. The organizer priorities in the user's task are authoritative
project requirements: controlled clarification comparison, disclosure robustness,
and directional calibration plus waiting/opportunity analysis.

The original workspace contained only research files and no Git metadata.
Git operations are blocked by read-only metadata and shell networking. Source
files were fetched through the GitHub connector and verified against Git blob
hashes. Public data was rebuilt with the official builder in a separate temporary
folder; all 71 published SHA-256 checksums matched before copying into this
workspace. This is source restoration, not a clone or a push. Research inputs
remain local and must be ignored. Existing official tests: 22 passed before edits.

## Architecture and contract

`kit.py` owns generation, simulation, exact public eligibility, greedy asking
and greedy matching. `policy.py` is the stateless JSON adapter. `evaluate.py`
owns protocol validation, subprocess/container isolation, 60 decision days,
40 follow-up days, frozen arrivals, and official metrics. `verify_data.py`
checks synthetic provenance and checksums. Preserve these evaluator semantics.
The report guide is `examples/REPORT_GUIDE.md`, not `docs/REPORT_GUIDE.md`.

Each day has an ask call and then a match call with refreshed observations.
Policy-visible input includes arrived members, availability, fields, their
statuses and observation days, past introductions, observed feedback and asks.
It excludes world seeds, hidden truth, propensities, future arrivals and events.
The policy may import `eligibility`, `HARD`, and `SOFT` from the kit, never
simulator objects or its random-outcome helpers. IDs are opaque join/tie keys.

Constraints bundles cost 3, soft-field asks cost 1; budget 12. Missing hard
fields block matching; known violations dominate missingness. Declined values
are unusable. Availability, no repeat pair, pool membership, distinct endpoints
and disjoint batches must all be checked. Baselines use first-available
constraint asks, equality scores, and greedy or deterministic random allocation.

## Module layout and implementation order

1. `graphvoi/core.py`: public observation normalization, official feasibility,
   feature construction, utility model interface, canonical general-graph
   maximum-weight matching, output revalidation, bounded memory, optional wait.
   Preserve the baseline adapter separately for reproducible official comparisons.
2. `graphvoi/answers.py`, `graphvoi/clarification.py`: empirical conditional
   donor answer model learned only from disclosed training observations; legal
   single and complementary constraint actions; uncertainty, expected-degree
   and true counterfactual optimal-matching value; cost and fixed work caps.
3. `graphvoi/models.py`, `scripts/train_models.py`: small regularized directional
   recorded-Yes models and conditional date/timely-second models. Capture features
   before action, use only matured observed outcomes, keep censorship explicit.
4. `scripts/run_experiments.py`, `graphvoi/analysis.py`: complete trajectories,
   outcome funnel, opportunities/waiting, held-out calibration, paired intervals,
   belief and independent actual-disclosure perturbations.
5. Submission packaging: pinned dependencies/licences, offline inference assets,
   Docker build and official subprocess/container checks, report and provenance.

## Data and estimation

Manifest: training pools public_01..06; validation public_07..08;
development-test public_09..10. Snapshots are day 30 and cannot be attached to
earlier decisions. Use fresh simulator rollouts with disjoint declared training,
validation and final-comparison seed lists. No hyperparameter selection on the
development-test pools or final-comparison runs. Store pre-introduction public
features and process only observable feedback after the full follow-up.

Directional target: recorded introduction Yes by its seven-day deadline;
nonresponse is absence of that event, not rejection. Separate reported response
preference calibration where labels are actually observed. Date model is
conditional on two recorded Yes responses. Timely-second target exists only
after an observed completed date, and is distinct from preference among
respondents. Never create second-preference labels for undated pairs. Directional
products assume conditional independence; document and test that limitation.

## Prespecified experiments

Primary: equal-family mean official MSMI per 100 arrivals. Confirm 60 decision
days and 40 follow-up days. Compare official greedy/no_asks/random, trained
scorer with greedy and optimal allocation, uncertainty_first, degree_first,
graphvoi, no paired asks, and optional waiting. The three clarification methods
share model assets, candidate frontier, optimizer, waiting, budget and worlds.
Only selection differs. Start with validity smoke tests, then validation episodes,
then the proposed 100 paired episodes per family where compute permits.
Declare final comparison seeds separately and freeze parameters before running.

Use a paired seed bootstrap within each family and equal family weighting.
Report all episodes, invalid counts, sample sizes and confidence intervals; never
interpret smoke scores as evidence of a win. Preserve all zero-outcome episodes.
Calibration: directional Brier/log loss, reliability bins, observed subgroups with
sample counts and bootstrap uncertainty, with separate conditional stages.

Robustness: biased, tempered, refusal and subgroup/drift answer beliefs; separately
an experimental public-simulator wrapper changing disclosure only, never hard
preferences. Policy receives no parameters, hidden truth or variant labels.
Measure cost, degradation and question-set stability on identical snapshots as
well as complete policy rollouts. Waiting: first waits (median/p90), unserved,
exposures, feasible member-days and cumulative eligible partners, blocked and
known-infeasible observations. Never label unknown true eligibility as known.

## Runtime and risks

Two CPUs, 1 GiB RAM, 10 s including startup, 1 MiB request/response/memory,
64 processes, no network or persistent disk, 2 GiB inference image. Docker is
currently unavailable. Use lightweight models and bounded counterfactual work.
Exact blossom matching is required; do not silently substitute greedy matching.
Bound the frontier and answer samples with deterministic operation counts, not
wall-clock dependent decisions. Cache unchanged utilities and component values
when demonstrated necessary by profiling. Validate all returned actions.

Principal risks: rare MSMI labels, selective rollout data, answer-model selection
bias, too few jointly disclosed constraint donors, correlated directional
acceptances, sampling variance, myopic information value, sparse geography,
permanent hard refusals, complementary questions, delayed feedback, runtime.
Retain failed/negative results and state support limits. No RL/GNN dependencies.

## Acceptance criteria

Phase 1: all original tests pass; protocol empty/sparse states work; manual graph
optima including odd cycles are exact; unknown/declined/explicit preferences are
protected; original state is immutable; repeated and unavailable pairs excluded;
fixed observations yield identical actions; complete simulator episodes valid.
Phase 2: manually solvable GraphVOI rankings and two-member complementarity pass;
counterfactuals never become actual observations; cost/dedup/budget valid; all
three selectors controlled. Subsequent phases require tested scripts, saved actual
outputs, held-out labels and disclosure/waiting diagnostics, not invented scores.
Final acceptance additionally requires a successful Docker build and official
container evaluation. Unavailable checks remain explicitly blocked, never passed.
