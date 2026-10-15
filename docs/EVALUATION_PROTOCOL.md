# Frozen evaluation protocol

Version 1, declared before the first controlled comparison. Asset hashes and all
actual run parameters are captured in result JSON. Do not tune on final seeds.

- Training: public simulator seeds 31001..31008, all six official variants,
  official greedy logging policy, public pre-action features only; 48 rollouts.
- Validation/smoke: 41001..41003. Protocol regression seeds: 9101..9103.
- Final proposed comparison: 51001..51100, 100 paired seeds in each scenario,
  10 methods. These runs are **planned**, not claimed to have completed.
- Static pools: public_01..06 train; public_07..08 validation;
  public_09..10 development-test untouched for model selection.
- Methods: official greedy, no_asks, random; learned_greedy, learned_maxweight;
  uncertainty_first, degree_first, graphvoi; graphvoi_no_pairs, graphvoi_wait.
- Primary: official MSMI per 100 arrived members, equally weighted within and
  across scenario families. Secondary: mutual acceptance, dates, coverage,
  first waiting times, unserved count, opportunities/exposures, cost, runtime.
- All methods use identical worlds and paired seeds. The three clarification
  methods share frozen trained assets, exact solver, legal candidates, 16-single
  frontier (half hard if available), 8 paired actions, 4 donor outcomes and soft
  categorical support, a 12-unit budget and no waiting. Only ranking changes.
- Cost penalty zero initially, as in the proposal; report cost separately.
  Uncertainty-first sums conditional field-answer entropies, weighted by
  disclosure probability, then uses the same cost normalization. Degree-first
  measures expected added feasible edges. Neither uses matching-value deltas.
  Wait ablation threshold .025 declines linearly to zero by day 59. No tuning
  to the smoke results. Joint ask batch uses static VOI/unit packing: document
  redundancy risk; do not describe it as optimal joint information acquisition.
- Confidence intervals: paired seed bootstrap, 2,000 draws, fixed bootstrap
  seed 771, equal family weighting. Cluster shared public world seeds across
  all families together to preserve cross-scenario covariance. With independent
  scenario seed sets, resample within family. Retain zero-MSMI
  episodes. Invalid episodes invalidate a method; never silently drop failures
  for performance claims. Fewer than 20 paired seeds is explicitly low support.
- Calibration: frozen directional recorded-Yes predictions before introduction,
  mature seven-day outcomes after follow-up, Brier/log loss and ten reliability
  bins. Report direction and observed gender groups with counts, not latent
  preferences. Held-out calibration must be assessed separately from fitting.
- Disclosure beliefs: biased, overconfident, underconfident, refusal,
  subgroup_refusal, temporal_drift. Separate actual-disclosure experimental
  wrapper at .35 bundle refusal, non_binary subgroup or temporal ramp. Wrapper
  never changes actual preferences or exposes parameters to the policy. These
  runs are independent public-simulator experiments, not official scenarios.
- Question stability: compare question sets on the same public snapshots, with
  Jaccard overlap and costs. Complete episodes additionally measure degradation.
- Research runner serializes requests/responses and validates official actions,
  but excludes process startup and container isolation. Require independent
  official subprocess and Docker verification before final submission.

## Commands

```bash
python3 -m unittest -v
python3 verify_data.py
python3 scripts/train_models.py
python3 scripts/run_experiments.py --seeds 41001 --output results/paired_smoke.json
python3 scripts/evaluate_method.py --method graphvoi --seeds 9103 --variants all --output results/graphvoi_protocol_all.json
python3 scripts/run_robustness.py --seed 41002 --output results/robustness_smoke.json
# Final comparison, after validation and compute planning:
ORBIT_EVAL_SEEDS=$(python3 -c 'print(",".join(str(i) for i in range(51001,51101)))')
python3 scripts/run_experiments.py --seeds "$ORBIT_EVAL_SEEDS" --output results/final_paired.json
docker build -t orbit-graphvoi:submission .
python3 evaluate.py --image orbit-graphvoi:submission --seeds 41003 --variants all --output results/container_check.json
```

No final run has been performed yet.
