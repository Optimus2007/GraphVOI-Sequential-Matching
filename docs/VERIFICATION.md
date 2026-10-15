# Verification record

This file lists what we checked before trusting any result, what broke, how we
fixed it, and the command that re-checks it. We wrote it because a policy that
looks good on a buggy evaluation is worse than no result at all, and because one
invalid assessed episode makes a submission ineligible.

Every check below was run on the submitted code. Where something is approximate
or unverified, we say so.

## How to re-run every check

```bash
python3 -m unittest discover -v        # 93 tests, starter tests included
python3 scripts/check_determinism.py   # same episodes, identical action hashes
python3 verify_data.py                 # 71 official data checksums
python3 scripts/train_models.py --output /tmp/retrain   # assets rebuild byte for byte
shasum -a 256 /tmp/retrain/*.json assets/pair_model.json assets/answer_model.json
docker build -t graphvoi-orbit:round2 .
python3 evaluate.py --image graphvoi-orbit:round2 --seeds 101 --variants all \
    --output results/validation/container_six_families.json
python3 scripts/profile_container.py --image graphvoi-orbit:round2 \
    --output results/validation/container_per_call_profile.json
python3 scripts/evaluate_method.py --method graphvoi --seeds 65001 --variants all \
    --output results/validation/official_subprocess_six_families.json
```

## The environment is unchanged

The repository is built on the official starter commit `a8e26b3`. `git diff
a8e26b3 -- kit.py evaluate.py verify_data.py data/` is empty, so the simulator,
evaluator, scoring and data are exactly what every other team uses.

## Rules the policy must never break

| Rule | Where it is enforced | Test |
|---|---|---|
| Only reciprocally feasible pairs are introduced; a learned score never overrides a hard failure | `graphvoi/core.py` `validate_pairs` re-checks every pair with the official `eligibility` | `tests/test_core.py` |
| Missing or declined hard fields block an introduction; a declined field is never filled in | `core.normalize`, `answers.apply_answer` | `tests/test_core.py`, `tests/test_correctness_fixes.py` |
| No member twice, no repeat pair, no busy member | `validate_pairs` | `tests/test_core.py` |
| Asks are legal, unique and within the 12-unit daily cap | `core.legal_asks`, `clarification.fill_hard_budget` | `tests/test_budget_fill.py` |
| Real matching never uses imagined answers | Hypothetical worlds exist only inside the ask phase; the match phase reads the refreshed public state | `tests/test_core.py` (unobserved and future fields unusable) |
| No hidden simulator state, seeds or truth at inference | Policy receives serialized public JSON only; assets hold no member IDs or latent fields | `tests/test_inference_boundary.py`, `tests/test_core.py` |

## Correctness problems found and fixed

We list every problem we found, including the ones in our own earlier builds.

**H1. Answer cache missed inputs (fixed in v2).** The cached answer distribution
ignored age, gender, zone and field statuses, so two different members could
share a stale answer. The key now holds every input of the calculation, an
uncached reference exists, and 400 randomized comparisons check exact equality.
The cache is also cleared on every call.

**H2. Overlapping asks got double credit (fixed in v2).** Two asks that unlock
the same pair were each credited with the full gain (10 + 9 = 19 when the joint
value is 10). Selection now re-evaluates each remaining candidate against the
joint answer worlds of the asks already chosen, charges shared asks once, and
values two-member complementary asks jointly. Exact small-graph references and
brute-force matching confirm the values. One approximation remains: above 8
joint worlds we compress the distribution, and a constructed example shows this
can overstate value (17.5 instead of 15). We keep it for runtime and say so.

**H3. Invalid runs were dropped before computing intervals (fixed in v2).** The
official scorer disqualifies a method with any invalid episode. Our analysis now
keeps every record, checks the full expected scenario by seed matrix, and gives
no score or interval when anything is invalid, missing or duplicated.

**V1. GraphVOI left budget unspent (found in the v2 pilot, fixed in v3).** In the
pilot GraphVOI used about 5 of 12 daily units early on, while greedy used all 12
and finished every hard-constraint ask by about day 17. Members waited longer to
become feasible, and versus greedy GraphVOI had 2.3 fewer mutual acceptances per
episode (95% CI [−3.2, −1.5]) and 5 points less coverage. Two causes: the
256-evaluation work cap ran out and dropped candidates in member-ID order, and
one-day VOI gives no credit to a hard answer that pays off on later days. v3
spends unused units on legal hard asks (the same rule for all three selectors)
and evaluates candidates in priority order.

**V2. No protection against a timeout (fixed in v3, tightened for submission).**
One call over 10 seconds disqualifies the entry. The ask phase stops evaluating
new candidates after a deadline and still returns a legal, filled ask set. At
6 seconds it never fired for GraphVOI or its comparators in 4,200 episodes, but in
the waiting-threshold ablation it fired in 196 of 600 episodes and calls still
reached 7.1 s, so it can overshoot by about a second. The submitted build uses
4.5 seconds. The default policy's slowest ask in the study was 3.1 s, and
`scripts/check_determinism.py` re-runs 24 confirmatory episodes with identical
action hashes and no guard hits (`results/validation/final_guard_determinism.json`).

**V3. The pair model has almost no held-out signal (negative result, no change).**
Refitting on training seeds 31001 to 31006 and scoring on 31007 and 31008 gave a
directional acceptance log loss of 0.6501 against 0.6496 for a constant. Weaker
regularization, members' own response history and training rollouts that also
ask soft fields did not materially help. We kept the shipped model.

## Runtime and container

| Check | Result |
|---|---|
| Image | 227 MB, Python 3.12.7, NetworkX 3.5 vendored, bytecode compiled at build |
| Official container evaluation, six families, seed 101 | all valid and eligible on ARM (Apple M-series) and on x86 Linux (GCP); action hashes identical on both (`results/validation/`) |
| Final build (4.5 s guard), container, six families | all valid; see `container_six_families_final.json` |
| Per-call container time on heavy real states, 216 calls per machine | ARM: ask max 2.55 s, match max 0.80 s. x86 under heavy load: ask max 4.62 s, match max 1.30 s. Startup included |
| Cross-machine determinism | identical action hashes for 22 of 22 overlapping confirmatory episodes and 320 of 320 robustness episodes (ARM Python 3.13, x86 Python 3.12) |
| Final code against the study | 24 of 24 confirmatory episodes re-run with identical action hashes |
| Stated preferences, checked against true preferences | 0 violations in 279,261 introductions |
| Official subprocess evaluation, six families, seed 65001 | all valid |
| Peak memory, fresh process on heavy states | 61.0 MiB of the 1 GiB limit |
| Carried memory | 2 bytes in normal runs (counters only if a guard fires) |

The container flags are the official ones: no network, 2 CPUs, 1 GiB memory,
64 processes, read-only filesystem, non-root user.

## Reproducibility

- Model assets: `scripts/train_models.py` rebuilds `pair_model.json`,
  `answer_model.json` and `training_summary.json` byte for byte from seeds
  31001 to 31008.
- Inference is deterministic. There is no random seed and no online update.
- Every study result stores the SHA-256 of all policy and runner source files and
  both model assets, and every episode stores a SHA-256 of its full action
  sequence.
- Raw study outputs and per-episode traces are too large for the repository.
  They are published as a release archive; `results/<study>/summary.json` records
  the SHA-256 of each raw file it was computed from.

## What is still approximate

- GraphVOI is myopic about the matching: it values today's best matching, and
  the fill rule stands in for the future value of hard answers.
- Batch selection is greedy over a 16-single, 8-pair frontier, with 8-world
  compression and a 256-evaluation cap.
- The answer model draws hard answers from the four most similar disclosed
  training members. We have not validated these probabilities on held-out
  members.
