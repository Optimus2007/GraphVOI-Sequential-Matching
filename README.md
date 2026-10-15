# The Sequential Matching Problem

**Final participant release 1.0.0 | Vouchsafe | 5 October 2026**

Build a policy that decides who to introduce, when to wait and what to clarify, using incomplete reciprocal preferences and delayed feedback. Every person, conversation and outcome in this kit is synthetic.

## Start here

1. Read the [final problem statement](PROBLEM_STATEMENT.md) or [download the PDF](docs/PROBLEM_STATEMENT.pdf).
2. Download this repository with **Code → Download ZIP**, or clone it. The full dataset is already in `data/`; no Supabase account, API key or separate download is required.
3. Install Python 3.10 or later. Open a terminal in the extracted repository folder and run:

```bash
python -m unittest -v
python verify_data.py
python evaluate.py --seeds 101 --output results/first_run.json
```

On Windows, use `py` instead of `python` if needed. On macOS/Linux, use `python3` if your Python executable has that name. The starter has no external Python dependencies. Results are written to the requested JSON file; scores measure this invented simulator only.

## What is included

| File / folder | Purpose |
|---|---|
| [PROBLEM_STATEMENT.md](PROBLEM_STATEMENT.md) | Final challenge, ranking, resources, schedule and ownership rules |
| [data/](data/) | 2,000 synthetic adults, ten disjoint pools and day-30 observable histories |
| [data_manifest.json](data_manifest.json) | Pool counts, source seeds and train/validation/development-test split |
| [docs/DATA_CONTRACT.md](docs/DATA_CONTRACT.md) | Every field, constraint and feedback rule |
| [docs/POLICY_INTERFACE.md](docs/POLICY_INTERFACE.md) | Executable JSON request/response protocol |
| [policy.py](policy.py) | Runnable greedy, no-clarification and random-feasible baselines |
| [evaluate.py](evaluate.py) | 60-day episodes, 40-day follow-up, metrics and scenario-level score |
| [build_public_data.py](build_public_data.py) | Rebuild public synthetic tables in a new folder |
| [kit.py](kit.py) | Reproducible public simulator and reciprocal eligibility checks |
| [organise.py](organise.py) | Prepare and grade 120 private episodes outside the public repo |
| [docs/ORGANISER_RUNBOOK.md](docs/ORGANISER_RUNBOOK.md) | Complete assessment commands and ranking procedure |
| [Dockerfile](Dockerfile) | Offline container packaging for assessed inference |
| [docs/SUBMISSION.md](docs/SUBMISSION.md) | Complete research and build submission instructions |
| [docs/INTEGRATION.md](docs/INTEGRATION.md) | Reusable adapter boundary for later Vouchsafe evaluation |
| [docs/FAQ.md](docs/FAQ.md) | Common questions and communication policy |
| [examples/baseline_results/](examples/baseline_results/) | Checked reference runs for all three baselines |
| [examples/REPORT_GUIDE.md](examples/REPORT_GUIDE.md) | What a complete participant technical report must cover |

## Develop and compare

Edit `policy.py`, keeping the JSON interface. Observe only the input state. Refreshing observations after clarification is handled by the evaluator. Policy memory is passed explicitly between calls and reset between episodes.

```bash
python evaluate.py --baseline greedy --seeds 101,102,103 --variants all --output results/greedy.json
python evaluate.py --baseline no_asks --seeds 101,102,103 --variants all --output results/no_asks.json
python evaluate.py --baseline random --seeds 101,102,103 --variants all --output results/random.json
```

The full commands take longer than the one-episode quick start. Public variants are `development`, `sparse`, `cold_start`, `delayed`, `shift`, and `drift`. Use your own declared training seeds. Keep the supplied six training pools, two validation pools and two development-test pools disjoint. Day-30 snapshots are not observations from earlier decisions.

To check container execution after installing Docker:

```bash
docker build -t sequential-policy:1.0 .
python evaluate.py --image sequential-policy:1.0 --seeds 101 --output results/container.json
```

Local subprocess mode is only for trusted development code. Assessed submissions use offline containers with no host evaluation files mounted. Private organiser worlds are intentionally absent from this public repository.

To regenerate the public tables without changing the supplied data:

```bash
python build_public_data.py --output ../rebuilt-public-data
```

The new folder must not already exist. The generator uses only invented data and public seeds. Do not use seed reconstruction inside an evaluated policy.

## Submit and ask questions

Teams: **1–4 participants**.

| Milestone | Date and time (IST) |
|---|---|
| Round 1 research submission closes | 9 October 2026, 23:59 |
| Round 1 results announced by | 11 October 2026, 22:00 |
| Round 2 build starts | 12 October 2026 |
| Final build submission closes | 18 October 2026, 23:59 |

**Round 1:** submit the research note through a Google Form. The organisers will release the link soon through [Discord](https://discord.gg/GwZdY54Gq) and [the submission guide](docs/SUBMISSION.md#research-submission). GitHub Issues are not the research submission route.

**Round 2:** use the [Final submission](https://github.com/RomeoJulietLove/The-Sequential-Matching-Problem/issues/new?template=final_submission.yml) issue form by the final deadline. Provide the immutable submitted version and required report/results. Use [Question](https://github.com/RomeoJulietLove/The-Sequential-Matching-Problem/issues/new?template=question.yml) for technical questions. Never post personal data, access codes or credentials in public issues.

This repository and public Issues are the shared technical communication hub. Event announcements and reminders are shared through [the IITM Discord server](https://discord.gg/GwZdY54Gq). Questions answered here are visible to every team. See [CHANGELOG.md](CHANGELOG.md) for release corrections.

The [starter-code permission](LICENSE) and [synthetic-data permission](DATA_LICENSE.md) permit reuse of the supplied kit. Students retain ownership of their own work; participation does not grant Vouchsafe a commercial licence to submissions. Later use requires a separate agreement.

## Team Orbit: GraphVOI Round 2

Project: **GraphVOI**. Team: **Orbit**. Competition: **The Sequential Matching
Problem**. Purpose: Round 2 implementation of allocation-aware clarification for
sequential reciprocal matching.

The default container policy ranks legal clarifications by expected improvement
in the exact maximum-weight matching, using a bounded empirical answer model.
It also evaluates complementary two-member constraint asks. Unknown and declined
hard preferences block introductions. The official simulator and evaluator remain
unchanged; `official_policy.py` preserves the original baseline adapter.

Orbit requires Python 3.11 or later. Python 3.12.7 is pinned in Docker; local
checks use Python 3.13.7. The unchanged official kit alone still supports 3.10.
NetworkX 3.5
is pinned and vendored with its BSD licence, so inference runs offline without a
package installation. The shipped JSON assets are required. Training uses only
public simulator observations, seeds 31001..31008 across the six scenario families.
Inference is deterministic and uses no random seed or online model updates.

```bash
python3 -m unittest -v
python3 verify_data.py
# Rebuild shipped models from declared public rollouts, CPU only:
python3 scripts/train_models.py
# Controlled comparisons, including all three official baselines:
python3 scripts/run_experiments.py --seeds 41001 --output results/paired_smoke.json
# Exact official subprocess checks for Orbit's entrypoint:
python3 scripts/evaluate_method.py --method graphvoi --seeds 9103 --variants all --output results/graphvoi_protocol_all.json
# Belief misspecification and independently changed disclosure:
python3 scripts/run_robustness.py --seed 41002 --output results/robustness_smoke.json
python3 scripts/summarize_results.py --input results/paired_smoke.json
docker build -t orbit-graphvoi:submission .
python3 evaluate.py --image orbit-graphvoi:submission --seeds 41003 --variants all --output results/container_check.json
```

`evaluate.py --baseline greedy`, `no_asks` and `random` still select the exact
official policies. To run GraphVOI locally use `scripts/evaluate_method.py`;
the official evaluator's default local command explicitly selects its baseline.
Docker invokes GraphVOI by default. Optional methods are `learned_greedy`,
`learned_maxweight`, `uncertainty_first`, `degree_first`, `graphvoi_no_pairs`
and `graphvoi_wait`.

The research runner serializes only public requests, validates every action and
runs complete 60+40-day episodes. Its runtime excludes process startup and is
not a replacement for official subprocess/Docker verification. Results include
full action traces, pre-action predictions, observed feedback, censor-aware labels,
and per-member opportunity/wait records. Static answer supports and greedy batch
packing approximate the information-acquisition problem; each evaluated action
uses a genuine counterfactual matching optimum. No claim of improvement follows
from a one-seed smoke comparison.

See [implementation plan](docs/IMPLEMENTATION_PLAN.md),
[evaluation protocol](docs/EVALUATION_PROTOCOL.md), [progress](docs/PROGRESS.md),
[decisions](docs/DECISIONS.md), and [provenance](docs/PROVENANCE.md).
The proposed 100 paired episodes per scenario use seeds 51001..51100:

```bash
ORBIT_EVAL_SEEDS=$(python3 -c 'print(",".join(str(i) for i in range(51001,51101)))')
python3 scripts/run_experiments.py --seeds "$ORBIT_EVAL_SEEDS" --output results/final_paired.json
```

That large experiment is a separate run; do not report it as completed unless
its output contains every requested valid episode. `results/` remains ignored
by the starter; explicitly include reviewed final JSON, traces and report when
committing the submission. Research-context files and credentials stay local.
