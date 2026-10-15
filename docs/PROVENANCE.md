# Provenance and permissions

Official source: RomeoJulietLove/The-Sequential-Matching-Problem, commit
`a8e26b35118cfa8e886a02f93984923e43ab64f6`, retrieved through the connected
GitHub API. Original source contents were Git-blob SHA-1 verified. The original
baseline adapter is preserved as `official_policy.py`; the original Dockerfile
and dependency file are preserved with `.starter` naming. Simulator, evaluator,
verification code, public data and original tests are unmodified.
The original CI workflow is retained as verify.yml.starter; Orbit's workflow tests
Python 3.11 and 3.12 because NetworkX 3.5 requires Python 3.11 or later.

Public static data was regenerated outside the project with the official builder,
then copied only after all 71 supplied SHA-256 checksums matched. All records are
synthetic. See retained LICENSE and DATA_LICENSE.md for starter permissions.
No private organizer worlds, production records or external personal data used.
Local research-context Markdown/PDF/feedback files are ignored, preserved on disk,
and excluded from Docker. The official problem PDF was not needed for semantics:
the complete Markdown specification was read instead.

GraphVOI models: pure-Python logistic regression fitted to observed public
simulator rollouts; assets/training_summary.json declares seeds, counts, settings,
and asset hashes. No pretrained language models or learned hidden-state oracle.
The answer asset contains only disclosed constraint donors (no IDs), public age,
gender and zone, and aggregate observed soft counts. Answer distribution is
empirical and conditional, not an estimate of a specific unknown consent value.

NetworkX 3.5 is vendored from the installed Anaconda distribution, retaining its
BSD-3-Clause notice at vendor/NETWORKX_LICENSE.txt. Python sources are unchanged;
tests and bytecode are omitted. vendor/PROVENANCE.json inventories content hashes.
It supplies exact general-graph maximum-weight blossom matching. Requirements
pins its version; inference requires no pip install or network.

Coding and documentation assistance: OpenAI Codex. PDF text extraction: Apple's
PDFKit. Runtime: Python standard library and vendored NetworkX. Training CPU only.
Python 3.12.7 is the declared Docker base; local interpreter versions are recorded
with results. Docker execution remains unverified until an actual successful run.

Starter permissions do not automatically license Team Orbit's contributions.
Team Orbit must select a licence for its own code before publication; this task
does not silently grant a commercial licence to original contributions.
