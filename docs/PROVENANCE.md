# Provenance, licences and tools

## Starter kit and data

Built on the official starter, RomeoJulietLove/The-Sequential-Matching-Problem,
commit `a8e26b35118cfa8e886a02f93984923e43ab64f6`. The simulator (`kit.py`),
evaluator (`evaluate.py`), data verifier, public data and the starter tests are
unmodified; `git diff a8e26b3` shows every file we changed. `official_policy.py`
keeps the original baseline adapter so the greedy, no-clarification and random
baselines run exactly as supplied. All data is the organisers' synthetic data;
no private worlds, real records or external personal data were used.

## Models

Pure-Python regularized logistic regression, trained by `scripts/train_models.py`
on public simulator rollouts of the official greedy policy, seeds 31001 to 31008
in all six scenario families, CPU only, a few minutes. Labels are recorded events
only; responses still inside their window are censored, not counted as No. The
answer model stores disclosed constraint answers of training members (no IDs)
with their public age, gender and zone, plus soft-field frequencies.
`assets/training_summary.json` declares seeds, counts and settings; retraining
reproduces the assets byte for byte. No pretrained or external models are used.

Evaluation seeds never overlap training seeds: pilot 62001 to 62010, development
check 64001 to 64010, validation 65001 and 101, confirmatory 71001 to 71100.

## Dependencies

| Component | Version | Licence | Use |
|---|---|---|---|
| Python | 3.12.7 (Docker), 3.13.7 (local) | PSF | runtime |
| NetworkX | 3.5, vendored in `vendor/` | BSD-3-Clause (`vendor/NETWORKX_LICENSE.txt`) | exact max-weight matching |
| matplotlib | 3.10.7, analysis only (`requirements-analysis.txt`) | PSF-based | report figures |

Inference needs no installation and no network.

## Tools

Coding, testing and documentation assistance: OpenAI Codex and Anthropic Claude
Code. The design, hypotheses and the Round 1 research note are the team's own.
Container runtime for local validation: Colima with the Docker CLI.

## Licence

Team Orbit's contributions are released under the MIT licence in `LICENSE`,
alongside the starter's own MIT notice. The synthetic data keeps the conditions in
`DATA_LICENSE.md`.
