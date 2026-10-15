# Confirmatory paired study protocol (v3 build)

Declared 15 October 2026, before any confirmatory episode was run. Results are
reported whatever their direction. Nothing here was tuned on these seeds.

## What changed since the frozen v2 pilot, and why

The v2 pilot (`CORRECTED_PILOT_PROTOCOL.md`, seeds 62001–62010) placed GraphVOI
below the official greedy baseline (0.308 vs 0.350 MSMI/100) with lower coverage
(28.0% vs 33.0%). Trace diagnosis, not outcome tuning, identified the cause:

1. GraphVOI spent ~5 of 12 daily units over days 0–19 while greedy spent all 12
   and finished every askable hard bundle by about day 17. Unasked members stay
   infeasible, so coverage and introduction volume fell.
2. The 256-evaluation work cap was the binding stop in later acquisition rounds
   (measured: limit 256 → 9 units spent; 1024 → 12), and candidates were
   enumerated in member-ID order, so the cap removed an arbitrary subset.
3. Myopic VOI scores only today's matching. Answered hard constraints remain
   observed on every later day, and ask cost is not in the primary score, so an
   unspent unit has no benefit.

v3 changes, applied identically to GraphVOI, degree-first and uncertainty-first:

- `fill_hard_budget`: after the selector's ranked asks, remaining units buy
  legal hard bundles ordered by the shared frontier potential, then member ID.
  Selectors therefore differ only in the ranked prefix they choose first.
- Work-capped candidate evaluation follows frontier-priority order, not ID order.

Unchanged: pair/answer model assets, matcher, waiting rule, candidate frontier,
world/work limits, lambda = 0, official simulator/evaluator/baselines.
`graphvoi_nofill` (v3 enumeration, no fill) is retained as an ablation.

A 10-seed development check (seeds 64001–64010, `results/v3_dev_check.json`) was
run only to confirm validity, runtime and that coverage recovers. It was not
used to choose among alternative policies; no other variant was tried.

## Separate negative finding (no model change)

Held-out refits (train seeds 31001–31006, test 31007–31008) show the pair model's
acceptance predictions are no better than intercept-only (directional log loss
0.6501 vs 0.6496). Weaker regularisation, member-history features and
soft-field-asking training rollouts did not materially improve held-out loss
(best 0.6487 / 0.6502). Shipped assets are therefore unchanged. This bounds what
any clarification policy can gain from soft-field information here.

## Design

- Seeds 71001–71100, never used before; all six official families; 200 members,
  60 decision + 40 follow-up days.
- Methods: graphvoi, degree_first, uncertainty_first, graphvoi_nofill (ablation),
  official greedy, no_asks, random. 4,200 expected episodes.
- Runner: `scripts/run_study.py --purpose confirmatory` (in-process trusted
  research mode with a strict JSON boundary; official subprocess/Docker
  validity is checked separately).

## Analysis (fixed in advance)

- Primary metric: official equal-family mean MSMI per 100 arrived members.
- Primary comparisons (two): GraphVOI − degree-first, GraphVOI − uncertainty-first.
- Inference: paired bootstrap over whole world-seed clusters (100 clusters,
  2,000 draws, seed 771), equal scenario weights. Superiority or inferiority is
  claimed only if the Bonferroni-adjusted 97.5% interval (`ci97_5_bonferroni2`)
  excludes zero. Otherwise the result is reported as inconclusive, with the
  interval width stated.
- Secondary (95% intervals, descriptive): versus greedy, no_asks, random and
  graphvoi_nofill; mutual acceptances, dates, coverage, unserved members, ask
  cost, inference time; per-scenario deltas.
- Any invalid, missing or duplicate episode blocks scoring and intervals for the
  affected method, per official semantics. Failures are reported, not dropped.

## Expected power (stated before running)

The v2 pilot's 10-cluster 95% half-widths were about 0.10–0.13 MSMI/100. With
100 clusters, half-widths of about 0.03–0.04 are expected. Differences between
the three selectors smaller than that are not expected to be resolvable, because
MSMI events are rare (under one per episode).
