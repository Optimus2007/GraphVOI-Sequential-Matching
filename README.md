# GraphVOI

**Allocation-aware clarification for sequential reciprocal matching.**
Team Orbit's Round 2 build for *The Sequential Matching Problem* (Romeo & Juliet / Vouchsafe).

A matchmaking policy has to decide every day which members to ask clarifying
questions and which pairs to introduce, with a small question budget, hard
reciprocal constraints and outcomes that arrive weeks later. We asked one
question about that loop:

> When clarification has a cost, should we ask the most uncertain question, or the
> question whose answer is most likely to improve the best feasible allocation of
> the whole pool?

GraphVOI answers the second way. For each legal question it imagines the possible
answers, re-solves the exact maximum-weight matching of the pool for each answer,
and asks the questions that improve that matching the most:

```
GraphVOI(q) = E_y[ V(G_t | answer(q) = y) ] - V(G_t) - lambda * cost(q)
```

This repository contains the policy, the Docker image the organisers run, the
experiments we pre-registered and ran, their results, and the technical report.

| | |
|---|---|
| Technical report | [docs/REPORT.md](docs/REPORT.md) and [PDF](docs/GraphVOI_Round2_report.pdf) |
| Round 1 research note | [docs/GraphVOI_Round1_note.pdf](docs/GraphVOI_Round1_note.pdf) |
| Pre-registered protocol | [docs/CONFIRMATORY_PROTOCOL.md](docs/CONFIRMATORY_PROTOCOL.md) |
| Verification record | [docs/VERIFICATION.md](docs/VERIFICATION.md) |
| Raw results and traces | GitHub release `v1.0-round2` |

## Results

We compared GraphVOI with two simpler question rules, degree-first (ask whoever
unlocks the most feasible pairs) and uncertainty-first (ask the most uncertain
field), holding the pair model, matcher, budget and worlds fixed, and with the
three official baselines. The confirmatory study used 100 never-before-used seeds
in all six scenario families: 4,200 episodes, every one valid.

| Method | MSMI per 100 arrived | Completed dates | Mutual acceptances | Coverage |
|---|---:|---:|---:|---:|
| GraphVOI | 0.339 | 8.52 | 10.98 | 33.7% |
| Degree-first | 0.380 | 8.62 | 11.11 | 33.8% |
| Uncertainty-first | 0.331 | 8.47 | 10.85 | 33.8% |
| GraphVOI without budget fill | 0.304 | 7.25 | 9.21 | 29.2% |
| Official greedy | 0.350 | 8.23 | 10.59 | 33.7% |
| Official random | 0.384 | 8.37 | 10.65 | 33.8% |
| Official no-asks | 0.077 | 2.15 | 2.71 | 11.9% |

*Mean per episode over 600 worlds (200 members, 60 decision days, 40 follow-up days).*

What we found:

- **GraphVOI did not beat the simpler rules.** On MSMI and on completed dates,
  GraphVOI, degree-first and uncertainty-first are level; every paired interval
  covers zero, and degree-first is if anything slightly ahead. The reason is
  specific: in this simulator the pair model can barely tell good pairs from
  average ones, so the best matching is simply the largest one, and degree-first
  measures that directly and more cheaply.
- **What clearly helps is spending the budget early.** Our pilot showed GraphVOI
  leaving half its daily budget unused. Spending the rest on hard-constraint
  questions adds 1.3 completed dates, 1.8 mutual acceptances and 4.5 coverage
  points per episode, and cuts how long members wait.
- **Answer-model errors.** Decisions ignore how confident the answer model is.
  A biased model, or one that expects refusals, changes the questions asked and
  costs outcomes. When people really do refuse more, GraphVOI degrades no more
  than the simpler rules.
- **Who waits.** The three question rules leave the same people waiting. Members
  aged 40 and over receive fewer introductions under every policy; spending the
  budget is what changes waiting times.
- **Hard constraints are never broken.** Zero violations of members' true stated
  preferences in 279,261 introductions.

The report covers the method, all ablations, calibration, waiting, failure cases
and limits.

## Quick start

Requirements: Python 3.11 or newer, and Docker for the container check. The
policy has no other dependencies: NetworkX 3.5 is vendored in `vendor/`.

```bash
git clone https://github.com/Optimus2007/GraphVOI-Sequential-Matching.git
cd GraphVOI-Sequential-Matching

python3 -m unittest discover -v     # 93 tests, about 10 seconds
python3 verify_data.py              # checks the 71 official data files
```

### Run the policy on one decision

The policy reads one JSON request on stdin and writes one JSON response on stdout,
following the official interface in [docs/POLICY_INTERFACE.md](docs/POLICY_INTERFACE.md).
To try it on a real simulator state:

```bash
python3 -c "import json, kit; s = kit.Simulator(kit.generate(101, 200, 'evaluation', 'development')); \
print(json.dumps({'schema_version': '1.0.0', 'phase': 'ask', 'state': s.observe(), 'memory': None}))" > request.json

python3 policy.py < request.json                         # GraphVOI (default)
python3 policy.py --method degree_first < request.json   # a comparator
python3 policy.py --baseline greedy < request.json       # an official baseline
```

An ask response looks like `{"asks": [{"member_id": "...", "field": "constraints"}, ...], "memory": {}}`;
a match response looks like `{"pairs": [["id_a", "id_b"], ...], "memory": {}}`.

Selectable methods: `graphvoi`, `degree_first`, `uncertainty_first`, and the
ablations `graphvoi_nofill`, `graphvoi_no_pairs`, `graphvoi_wait`,
`learned_greedy`, `learned_maxweight`. `--answer-perturbation` runs GraphVOI with a
deliberately wrong answer model (used in the robustness study).

### Run it the way the organisers do

```bash
docker build -t graphvoi-orbit:round2 .
python3 evaluate.py --image graphvoi-orbit:round2 --seeds 101 --variants all \
    --output results/validation/container_six_families.json
```

This runs six complete episodes in offline containers limited to 2 CPUs and 1 GiB
of memory, exactly as in assessment, and takes about 15 minutes. Without
`--image`, `evaluate.py` runs the official baselines; to run any of our methods
through the same subprocess path, use
`python3 scripts/evaluate_method.py --method graphvoi --seeds 101 --variants all --output out.json`.

## How the policy works

Each decision day has two calls.

1. **Read the public state.** Fields that are unknown or that a member declined
   stay unknown; nothing hidden in the simulator is read.
2. **Ask (12 units).** Rank legal questions by GraphVOI, re-scoring the remaining
   questions after each pick against the joint answers of those already chosen,
   and valuing two-member questions together. Then spend any units left on hard
   constraint questions, ordered by how much possible matching each member touches.
3. **Match.** Apply the official reciprocal eligibility rules, solve the exact
   maximum-weight matching over feasible pairs, and check every pair again before
   returning it.

Edge weights come from small logistic models trained offline on public simulator
rollouts (seeds 31001 to 31008). Possible answers come from similar members in the
training pools who disclosed theirs. The policy is deterministic: no random seed,
no online updates, and the same decisions on ARM and x86.

Two safety measures matter for assessment, where one invalid episode disqualifies
an entry: every introduction is re-validated against the official rules, and the
ask phase stops evaluating new questions 4.5 seconds into a call while still
returning a full, legal set of asks.

## Reproducing the experiments

Every number in the report comes from the files in `results/`, which are produced
by the commands below. Model assets rebuild byte for byte with
`python3 scripts/train_models.py`.

| Study | Command | Episodes | Approximate cost |
|---|---|---:|---|
| Confirmatory comparison | `python3 scripts/run_study.py --purpose confirmatory --seeds 71001-71100 --methods graphvoi,degree_first,uncertainty_first,graphvoi_nofill,greedy,no_asks,random --workers 8 --output results/v3_confirmatory.json` | 4,200 | 65 CPU-hours |
| Round 1 ablation rows | same, with `--methods learned_greedy,learned_maxweight,graphvoi_wait,graphvoi_no_pairs --output results/v3_ablations.json` | 2,400 | 40 CPU-hours |
| Disclosure robustness | `python3 scripts/run_disclosure.py --workers 8 --output results/v3_disclosure.json`, then the same with `--matched` | 720 | 12 CPU-hours |
| Decision sensitivity | `python3 scripts/decision_sensitivity.py` | 240 states | 1 CPU-hour |

Then build the tables, figures and report:

```bash
python3 scripts/export_results.py results/v3_confirmatory.json --name confirmatory
python3 scripts/export_results.py results/v3_ablations.json --name ablations
python3 scripts/export_results.py results/v3_disclosure.json --name disclosure
python3 scripts/compare_studies.py            # paired comparisons across studies
python3 scripts/summarize_study.py results/v3_confirmatory.json
pip install -r requirements-analysis.txt && python3 scripts/make_figures.py
./scripts/build_report.sh                     # needs pandoc and tectonic
```

Studies can be split across machines and combined with
`scripts/merge_studies.py`, which refuses to merge parts whose code or model hashes
differ and checks that overlapping episodes made identical decisions.
`scripts/check_determinism.py` re-runs study episodes and compares their action
hashes. The raw study outputs and per-episode traces (about 200 MB) are attached to
the `v1.0-round2` release; each `results/<study>/summary.json` records the
SHA-256 of the raw file it was computed from.

## Repository layout

```
graphvoi/                 the policy
  core.py                 public-state handling, eligibility, exact matching
  clarification.py        GraphVOI, degree-first, uncertainty-first, budget fill
  answers.py, models.py   answer model and pair model
  policy.py               decision entry point
policy.py                 JSON entrypoint used by Docker and the evaluator
assets/                   trained model files and their training summary
scripts/                  training, study runners, analysis, figures, report build
tests/                    93 tests, including exact small-graph references
results/                  per-study episode tables and summaries, validation runs
docs/                     report, protocol, verification, provenance, official spec
kit.py, evaluate.py,      official simulator, evaluator and data, unchanged
verify_data.py, data/
vendor/networkx/          NetworkX 3.5 with its licence
```

## Limitations

All results come from the organisers' synthetic simulator, and the main outcome
is rare enough that differences below about 0.04 MSMI per 100 arrivals cannot be
resolved even with 100 paired seeds. GraphVOI values today's matching only, its
batch selection is greedy over a restricted set of candidates, and its answer
probabilities have not been validated on held-out members. The report discusses
each of these.

## Licence and acknowledgements

Released under the MIT licence (see [LICENSE](LICENSE)). The simulator,
evaluator and synthetic data come from the organisers' starter kit,
[RomeoJulietLove/The-Sequential-Matching-Problem](https://github.com/RomeoJulietLove/The-Sequential-Matching-Problem),
which carries its own MIT notice; the data keeps the conditions in
[DATA_LICENSE.md](DATA_LICENSE.md). Exact matching uses
[NetworkX](https://networkx.org) (BSD-3-Clause).

Team Orbit: Aditya Raj.
