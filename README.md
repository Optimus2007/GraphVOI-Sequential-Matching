# GraphVOI: allocation-aware clarification for sequential reciprocal matching

Team Orbit, Round 2 build for *The Sequential Matching Problem* (Romeo & Juliet / Vouchsafe).

**Research question.** When clarification has a cost, should we ask the most
uncertain question, or the question whose answer is most likely to improve the
best feasible allocation of the whole pool?

GraphVOI scores a possible clarification by imagining its answers, re-solving the
exact maximum-weight matching for each answer, and measuring how much the best
matching improves on average:

```
GraphVOI(q) = E_y[ V(G_t | answer(q) = y) ] - V(G_t) - lambda * cost(q)
```

It values two-member questions jointly, so a pair of asks that is only useful
together is not missed, and it re-scores the remaining questions after each pick
so overlapping questions are not counted twice.

**Report:** [docs/REPORT.md](docs/REPORT.md) ([PDF](docs/GraphVOI_Round2_report.pdf)).
Round 1 research note, unchanged since submission: [docs/GraphVOI_Round1_note.pdf](docs/GraphVOI_Round1_note.pdf).

## Results at a glance

<!-- RESULTS -->

## How one day works

1. Read the public state. Unknown or declined hard fields are never filled in.
2. Ask phase (12 units). Rank legal questions by GraphVOI, then spend any units
   left on hard-constraint questions, ordered by how much matching value each
   member touches.
3. Match phase. Re-check reciprocal eligibility with the official rules and
   introduce the maximum-weight matching of feasible pairs. Every pair is
   validated again before it is returned.

The pair model, matcher, budget, candidate frontier and seeds are identical for
GraphVOI and the degree-first and uncertainty-first comparators. Only the ranking
criterion differs.

## Reproduce

Requirements: Python 3.11 or later and Docker. Inference has no other dependencies
(NetworkX 3.5 is vendored). Figures need `pip install -r requirements-analysis.txt`.

```bash
# 1. Checks (about 10 s)
python3 -m unittest discover -v          # 93 tests
python3 verify_data.py                   # 71 official data checksums

# 2. Container, exactly as the organisers run it (about 15 min)
docker build -t graphvoi-orbit:round2 .
python3 evaluate.py --image graphvoi-orbit:round2 --seeds 101 --variants all \
    --output results/validation/container_six_families.json

# 3. Model assets, rebuilt byte for byte from public rollouts (about 3 min)
python3 scripts/train_models.py

# 4. Confirmatory study, 4,200 paired episodes (about 10 h on 6 cores)
python3 scripts/run_study.py --purpose confirmatory --seeds 71001-71100 \
    --methods graphvoi,degree_first,uncertainty_first,graphvoi_nofill,greedy,no_asks,random \
    --workers 6 --output results/v3_confirmatory.json
python3 scripts/export_results.py results/v3_confirmatory.json --name confirmatory

# 5. Round 1 ablation rows and disclosure robustness
python3 scripts/run_study.py --purpose confirmatory --seeds 71001-71100 \
    --methods learned_greedy,learned_maxweight,graphvoi_wait,graphvoi_no_pairs \
    --workers 8 --output results/v3_ablations.json
python3 scripts/export_results.py results/v3_ablations.json --name ablations
python3 scripts/run_disclosure.py --workers 2 --output results/v3_disclosure.json
python3 scripts/export_results.py results/v3_disclosure.json --name disclosure
python3 scripts/run_disclosure.py --matched --workers 2 --output results/v3_disclosure_matched.json
python3 scripts/decision_sensitivity.py        # same states, every answer-model error
python3 scripts/compare_studies.py             # pairs ablation/disclosure rows with confirmatory rows

# 6. Tables and figures for the report
python3 scripts/summarize_study.py results/v3_confirmatory.json
python3 scripts/make_figures.py
```

`evaluate.py` without `--image` runs the official baselines (`--baseline greedy`,
`no_asks`, `random`). Docker runs GraphVOI by default. To run another method
through the official subprocess path:
`python3 scripts/evaluate_method.py --method degree_first --seeds 101 --variants all --output out.json`.

Raw study outputs and per-episode traces are large and are attached to the GitHub
release; each `results/<study>/summary.json` records their SHA-256.

## Repository layout

```
graphvoi/            policy: feasibility and matching (core), GraphVOI and the
                     comparators (clarification), answer and pair models, policy entry
policy.py            JSON entrypoint used by Docker and the official evaluator
assets/              trained model files and their training summary
scripts/             training, study runners, exports, figures, container profiler
tests/               93 tests: exact small-graph references, rule safety, statistics
results/<study>/     per-episode CSV and summary JSON for each study
results/validation/  official container and subprocess runs, per-call timings
docs/                report, pre-registered protocol, verification record, provenance
vendor/networkx/     pinned NetworkX 3.5 with its licence
kit.py, evaluate.py, data/, ...   official starter, unmodified (docs/STARTER_README.md)
```

## Documents

- [Report](docs/REPORT.md): method, results, ablations, robustness, failures, limits.
- [Protocol](docs/CONFIRMATORY_PROTOCOL.md): every study design, written before it ran.
- [Verification](docs/VERIFICATION.md): what we checked, what broke, how to re-check it.
- [Provenance](docs/PROVENANCE.md): data, models, seeds, tools, licences.

## Licence

MIT, see [LICENSE](LICENSE). The starter kit keeps its own MIT notice and the
synthetic data its conditions in [DATA_LICENSE.md](DATA_LICENSE.md). The
organisers' original README is kept at [docs/STARTER_README.md](docs/STARTER_README.md).
