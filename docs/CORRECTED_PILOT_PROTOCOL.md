# Correctness fixes and frozen paired pilot

Declared before launching the pilot. This is a validation pilot, not final testing
or the proposed 100-seed study. No model fitting or hyperparameter tuning uses it.

- Seeds: 62001 through62010, disjoint from training31001..31008, prior smoke41001..
  41003 and proposed final51001..51100. All six official scenario variants.
- Six methods: graphvoi, degree_first, uncertainty_first, official greedy, no_asks,
  random. 10 x6 x6 =360 complete200-member60+40-day episodes, 60 per method.
- Freeze pair_model.json and answer_model.json; unchanged inference assets.
  Main selectors use the same exact matching solver, zero waiting threshold,
  candidate generation, paired actions, budget12, lambda0 and world generator.
- Conditional marginal selection evaluates E[V after selected asks plus candidate]
  minus E[V after selected asks], not differences of independent VOIs. Candidate
  pairs remain joint; overlapping questions are reduced to unseen residual asks
  and charged exactly once. Identical worlds coalesce with summed mass.
- Production work: at most256 coalesced candidate-outcome evaluations and8 joint worlds.
  Above8 outcomes, deterministic systematic probability quadrature compresses
  the selected joint distribution. Stop acquisition when no positive evaluable
  marginal remains. These are bounded approximations, not global optimal joint
  acquisition or a claim that all useful frontier questions were evaluated.
  Exact finite-support reference and high-limit small-instance tests are uncapped.
- Shared frontier16 singles/8 paired actions (up to4 direct hard pairs reserved;
  remaining slots consider all singleton pairs, including soft and nonpartner
  questions). The >600-current-edge common
  dense fallback remain. No change to official eligibility, simulator or baselines.
- Fresh policy invocations clear answer caches; models snapshot assets and return
  copies. Cache keys include day, question field, age/gender/zone, full fields and
  disclosure statuses, support size and perturbation. Memory/scenario labels,
  histories and identifiers beyond lookup do not enter answer calculation.
- Primary official MSMI/100: mean within scenario, then equal mean across scenarios.
  Zero outcomes retained; any invalid episode makes that method ineligible.
  Missing/duplicate/invalid expected records suppress paired inference. Checkpoints
  declare the full matrix and suppress all CIs until it finishes.
- Bootstrap2,000 draws, seed771: paired world-seed clusters across scenarios,
  stratified by scenario-membership signature if seed sets overlap partially.
  This preserves within-family episode counts and equal-family weighting. Ten
  clusters remain a small pilot; intervals are flagged below20-cluster support.
- Report MSMI, mutual acceptance, completed dates, distinct-member coverage,
  ask cost, served-only waiting quantiles with unserved counts, failure counts,
  phase runtime and measured worker peak RSS. In-process runtime excludes startup;
  parallel host timing does not certify Docker's resource envelope.

Commands after correctness gates pass:

```bash
python3 -m unittest discover -v
python3 verify_data.py
python3 scripts/evaluate_method.py --method graphvoi --seeds 63004 --variants all --output results/corrected_verified_v2.json
python3 scripts/audit_runtime.py --output results/corrected_runtime_v2.json
python3 scripts/run_pilot.py --workers 3 --output results/corrected_pilot.json
```

Output refusal prevents overwriting a completed pilot. All rows, including failures,
remain in machine-readable output. Do not change the frozen algorithm after launch
without labeling a new version and rerunning the entire balanced comparison.
