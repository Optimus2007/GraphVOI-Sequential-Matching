# Decisions and evidence

Independent audit, 10 October 2026: preserve measured inference code/assets and
the pre-audit candidate archive. Add direct public-record manual cases rather than
reusing existing synthetic fixtures. Confirm known batch/cache/CI limitations with
adversarial tests, and distinguish their passing evidence tests from correctness
certification. No confirmed critical policy correctness bug was found; container
validation and accessible pinned publication are critical release blockers.
Noncritical fixes are specified in INDEPENDENT_AUDIT.md, including cache isolation,
invalid-episode inference gating and batch redundancy. No new architectures added.

1. Preserve official simulator/evaluator/tests. Restore exact starter files before
   extending them. Pin restoration to a commit and verify content hashes.
2. Read PDF through Apple PDFKit because pdftotext/pypdf/pdfplumber are unavailable
   in the default interpreter. Six pages extracted successfully; no contents guessed.
3. The empty organizer-feedback file cannot establish additional feedback. Use the
   explicit requirements in the task and request supplementary text asynchronously.
4. Missing, not_asked, declined and observed are distinct. Only observed values
   influence actual hard eligibility. Hypothetical values stay in copied states.
5. Prefer a lightweight, auditable model with exact matching. No end-to-end RL,
   GNN, generator-based attribute reconstruction, or hidden parameter access.
6. Public source restoration is not Git initialization. No commits or pushes are
   represented as complete while Git metadata is unavailable.
7. Final results require actual runs. Historical numbers in the Round 1 PDF are
   prior research claims, not results reproduced by this implementation.
8. Fit joint acceptance directly rather than multiplying directional marginals:
   observable feedback supports the joint event, and dependence is plausible.
   Directional models share a regularized logistic function with swapped features.
9. No in-episode coefficient updates: freeze models across clarification methods
   so delayed selective updates do not confound the controlled comparison.
10. Initial uncertainty prototype used missing-coordinate count plus entropy.
    Replaced it with conditional field-answer entropy weighted by disclosure;
    a tested uncertainty comparison must measure uncertainty, not missingness.
11. Static greedy VOI/unit batch packing evaluates real matching counterfactuals
    but does not resolve joint redundancy. Complementary two-member questions
    are explicitly scored. This approximation is reported as a limitation.
12. Dense feasible graphs (>600 edges) use the same deterministic first-legal-hard
    ask fallback for all three clarification methods. Memory counts fallback calls.
    The matching phase always retains the exact solver and validates introductions.
13. Profiling found avoidable copies of full public history and each empirical
    donor. Copy only the changed member and the donor mapping; values are copied
    on application. Cached edge tests and full action hashes verify equivalence.
14. Interrupted pre-optimization comparisons are preserved separately and marked
    incomplete. The final inference version is frozen for the completed smoke run.
15. One-seed smoke intervals are not meaningful evidence of improvement. Cluster
    calibration bootstrap by whole seed across scenarios/directions; explicitly
    report unsupported uncertainty when only one independent seed is available.
16. An early empty-state subprocess regression tried to load assets before training
    finished. Fixed the empty-available-pool path to return the valid empty action
    without loading models. The completed suite now passes 58 tests.
17. Official GraphVOI subprocess evaluation passed six scenarios at seed 9103.
    These validity runs are separate from the one-seed controlled comparison.
18. Actual-disclosure sensitivity: at seed 41002, standard-scenario coverage fell
    from .38 to .315 under .35 bundle refusal; all ten sensitivity conditions had
    zero MSMI. This cannot establish MSMI degradation. Preserve cost/coverage and
    question-stability diagnostics, and report insufficient rare-outcome evidence.
19. Docker build was attempted and failed because the executable is unavailable,
    not because the Dockerfile was validated and rejected. Container checks remain
    unrun. Python 3.11+ is required for Orbit's NetworkX dependency; original kit
    support for Python 3.10 remains distinct from Orbit's declared environment.
20. Final analysis review corrected the large-study bootstrap to retain covariance
    when public world seeds are shared across scenario families. A paired-seed
    cancellation regression verifies this. The one-seed smoke intervals remain
    degenerate and unsupported. This changes analysis, not policy actions; the
    prior analysis source is preserved and derived summaries identify the correction.


## Correctness repair decisions

21. Reproduce defects before fixing: three initial regressions failed; later a
    zero-singleton-value soft alternating-path complement failed. Preserve logs
    and old source in audit_history.400 randomized cache comparisons exposed
    declined None-bound ordering; keep that value unavailable and skip undefined
    numeric order comparison. No belief from declined hard information is used.
22. Cache exact dependencies and return deep copies, immutable model snapshot;
    clear observation caches every ask invocation. Uncached reference uses the
    same numeric calculation but never caches; tests compare exact outputs.
23. Greedy conditional batch VOI uses the distribution after selected asks. Never
    subtract independent VOIs. Deduplicate residual asks/costs and recompute true
    matching.8-world deterministic quadrature and256 coalesced outcome work bound
    are explicit production approximations. Exact small reference remains uncapped.
24. Reserve four direct hard-complement pairs, fill remaining paired slots from
    general singleton combinations, including soft/nonpartner questions. Apply
    identical frontier and limits to all three selectors. No candidate-tuning on
    pilot results; freeze before first evaluation seed62001.
25. Invocation-local immutable-record fingerprint memo avoids repeated full JSON
    serialization; before/after snapshot action equality and brute-force tests
    establish correctness. Do not introduce partial-dependency numeric caches.
26. Invalid episodes disqualify official scoring and block numerical comparisons.
    Missing/duplicate/undeclared expected pairs also block inference. Keep every
    failure record; suppress incomplete checkpoint scores and bootstrap results.
27. Resample whole paired seeds across families within scenario-membership strata
    to preserve covariance and denominators. Ten clusters are limited support;
    extreme family imbalance does not change equal-family weighting.
28. Freeze10-seed/six-family/six-method360-episode pilot, three independent host
    workers. Model assets unchanged; no fitting or parameter tuning. Actual host
    timings exclude startup in research mode and do not certify Docker resources.
29.83 tests/71 checksums and seven fresh official episodes (six + one repeat)
    passed before launching pilot. Do not include intermediate v1 runs in the
    frozen comparison count. Full100-seed study remains explicitly unrun.

- Verification-only quadrature counterexample confirms that8-world compression can overestimate joint value (17.5 vs exact15). Keep approximation explicit; no error-bound/exact-full-batch claim. Preserve frozen pilot version and assess cap sensitivity separately before stronger methodological claims.

30. Completed360-episode pilot preserved separately from historical smoke/intermediate builds. Independent check recomputed every primary metric, trace digest, coverage/wait count and paired MSMI interval; no failure deletion or parameter retuning. Ten seed clusters remain insufficient for final superiority/disclosure/subgroup claims. Proceeding with local prespecified100-seed comparison is correctness-safe, but do not treat that as submission certification.

Completion recorded11 October2026. Corrected pilot and verification artifact hashes: f3e6bc045cbf3610625532aa4d6c0e68d365524d94f61a26cf0f5cc0f54d1c13 (pilot), 3026aa02251a3e13a78e7c6c371871c882a0e87b88dbb3a5b31255eacd3251c4 (verification).

## Second-review decisions (15 October 2026)

31. Treat the Codex pilot summary as a claim, not evidence; re-run tests,
    checksums, hashes and recompute pilot tables before building on them.
32. Fix the measured budget under-spend with one shared hard-bundle fill rather
    than raising the work cap: the fill is legal, cheap and identical for all
    selectors, so the comparison still isolates the ranking criterion. A larger
    cap costs runtime margin that eligibility needs.
33. Enumerate work-capped candidates in frontier-priority order. ID order made
    truncation arbitrary.
34. Add a 6 s ask deadline. One timed-out private episode disqualifies the
    entry; an eligibility guard that never triggers in normal runs is worth a
    theoretical loss of determinism in pathological ones.
35. Do not change model assets. Held-out refits, history features and
    soft-asking training rollouts gave no material log-loss gain; changing
    models now would add risk without evidence of benefit.
36. Development check on unused seeds 64001–64010 only confirms validity,
    runtime and coverage recovery; no variant selection. Confirmatory seeds
    71001–71100, protocol and Bonferroni decision rule declared before launch.
37. Precompile bytecode in the image; base the git history on the official
    upstream commit so the diff shows exactly what Team Orbit changed.
