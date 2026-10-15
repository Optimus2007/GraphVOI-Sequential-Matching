---
title: "GraphVOI: allocation-aware clarification for sequential reciprocal matching"
subtitle: "Round 2 technical report, The Sequential Matching Problem (Romeo & Juliet / Vouchsafe)"
author: "Team Orbit (Aditya Raj)"
date: "October 2026"
---

**Research question.** When clarification has a cost, should we ask the most
uncertain question, or the question whose answer is most likely to improve the
best feasible allocation?

# 1 Summary

In Round 1 we proposed GraphVOI: score a clarification by imagining its possible
answers, re-solving the pool's maximum-weight matching for each one, and asking
the question whose answers improve that matching the most. We promised to test it
against uncertainty-first and degree-first clarification with the same model,
matcher, budget and seeds, and to report the result even if it went against us.

This report does that. [[SUMMARY_RESULT]]

Three things we learned along the way matter as much as the headline number.

- **Our first build lost to the official greedy baseline, and the reason was
  mundane.** GraphVOI only spent about half its daily budget, because a work cap
  ran out and because one-day VOI gives no credit to a hard answer that only pays
  off on later days. Round 1 listed exactly this as a likely failure ("GraphVOI may
  be too short-sighted"). Fixing it closed the gap on coverage and volume.
- **In this simulator, the pair model has almost no signal.** On held-out seeds
  its acceptance predictions are no better than a constant. So the value of a
  question comes almost entirely from whether it makes a pair *feasible*, not from
  how good that pair would be. That limits how far any clarification rule can pull
  ahead of a simpler one.
- **Waiting depends on asking.** Leaving budget unspent cost real people time:
  among members who could be served, the share introduced within 14 days of arrival
  dropped from about 45% to 33% when we turned the budget fill off.

Everything here can be rerun from the repository. The code, Dockerfile, model
assets, raw results and the protocol we wrote before each study are all public.

# 2 What we built

One decision day has two calls, and the policy is a plain pipeline around one
research component.

| Step | What happens |
|---|---|
| Feasibility | The official reciprocal eligibility rules decide which pairs are valid, unresolved or blocked. A learned score never overrides a hard failure, and a missing or declined hard field blocks the pair. A declined field is never filled in. |
| Edge utility | Three small logistic models (both accept, date happens, both give a timely Yes) trained offline on public rollouts, seeds 31001 to 31008. Their product is the edge weight. |
| Clarification | GraphVOI ranks legal asks, then any units left buy hard-constraint asks (Section 3). |
| Allocation | Exact maximum-weight general-graph matching (NetworkX blossom) over feasible pairs, then every pair is checked again before it is returned. |
| Waiting | None in the main build. A fixed day-dependent threshold is tested as an ablation. |

For a possible question $q$ with answer $y$,

$$\mathrm{GraphVOI}(q) = \mathbb{E}_y\left[V(G_t \mid q = y)\right] - V(G_t) - \lambda\, c(q),$$

where $V(G)$ is the value of the best matching under the edge weights. We use
$\lambda = 0$, because unused budget is lost at the end of the day and ask cost is
only the third tie-breaker in the official ranking.

**Answers.** For a constraints bundle, possible answers come from the four most
similar fully disclosed members in the training pools (by age, gender and zone,
the fields that are always visible), with the member's own known fields kept
fixed. For a soft field we use the training frequencies. Nothing hidden in the
simulator is read at inference.

**Asking several questions at once.** Round 1 already noted that two blocked
members who are each other's only option need to be asked together. We score
such pairs as one 6-unit action, and more generally we try two-question
combinations from the candidate frontier. After each pick we re-score every
remaining question against the joint answer worlds of the questions already
chosen, so two questions that unlock the same pair are not both credited with it.
Shared questions are charged once. When the joint answer distribution has more
than eight worlds we compress it to eight; this is an approximation and we know of
a constructed case where it overstates value (Section 10).

**Staying inside the rules.** One invalid episode makes a submission ineligible,
so the match output is re-validated, and the ask phase stops evaluating new
candidates six seconds into a call and still returns a legal, full ask set. That
guard never fired in any run reported here.

**Comparators.** Uncertainty-first ranks questions by the entropy of their
answers. Degree-first ranks them by how many feasible edges they are expected to
add. Both use exactly the same pair model, answer model, frontier, budget, budget
fill, matcher and seeds as GraphVOI. Only the ranking criterion differs.

# 3 What the first build taught us

We ran a ten-seed pilot of the first complete build (v2) before any larger study,
with its design written down first. GraphVOI scored 0.308 MSMI per 100 arrived
members against 0.350 for the official greedy baseline. MSMI is too rare for ten
seeds to separate those numbers, but the secondary metrics could: GraphVOI had
2.3 fewer mutual acceptances per episode than greedy (95% interval −3.2 to −1.5)
and five points less coverage.

![Mean ask units spent per decision day. Left: the v2 pilot. Right: the v3 build, with the budget fill turned off and on.](figures/daily_ask_spend.pdf)

Figure 1 shows why. Greedy spends its full 12 units every day until about day
17, by which time every member worth a constraints ask has been asked. That
matches what we saw in Round 1: the constraint budget is only tight at the start.
GraphVOI spent about 5 units a day over the same period. Members it did not ask
stayed infeasible for longer.

We traced two causes. First, a cap of 256 answer-world evaluations per call ran
out during the second and third picks, and candidates were evaluated in member-ID
order, so the cap cut an arbitrary subset rather than the least promising one. On
real states from the first four days, raising the cap to 1024 made GraphVOI spend
11 to 12 units instead of 9.
Second, one-day VOI only counts today's matching. A hard answer stays known for
every later day, so a question with no value today can still be worth asking.

Rather than raise the cap and spend our runtime margin, we made two changes for
the v3 build: candidates are evaluated in priority order, and after the ranked
questions, any units left buy legal constraints asks, ordered by how much matching
value each member touches. The fill is shared by all three selectors, so the
comparison still isolates the ranking criterion. We kept the old behaviour as the
`graphvoi_nofill` ablation. A ten-seed development check on unused seeds
confirmed that coverage recovered to greedy's level (32.7% against 32.8%) and that
nothing became invalid or slow. We did not try other variants.

We also checked whether a better pair model was available before the main study.
Refitting on seeds 31001 to 31006 and scoring on 31007 and 31008, the directional
acceptance model reached a log loss of 0.6501 against 0.6496 for predicting the
base rate. Weaker regularization made it worse. Adding each member's own past
responses (0.6487) and training on rollouts that also asked soft fields (0.6502)
did not help either. In this simulator acceptance is driven mostly by a hidden
per-member tendency and per-pair noise, and members get too few introductions for
their history to reveal it. We kept the shipped model.

# 4 Experimental setup

All studies were written into `docs/CONFIRMATORY_PROTOCOL.md` and committed
before they ran (commit `db79b4a` and later).

- **Worlds.** Seeds 71001 to 71100, never used before, in all six official
  scenario families: 600 worlds of 200 members, 60 decision days and 40 follow-up
  days. Every method sees the same worlds, and the simulator draws the outcome of
  a given pair on a given day from the same random stream for every method, so
  differences come from decisions.
- **Methods.** GraphVOI, degree-first, uncertainty-first, GraphVOI without the
  fill, the three official baselines, and the remaining Round 1 rows: learned
  edge model with greedy allocation, learned model with max-weight allocation,
  GraphVOI with a waiting threshold, and GraphVOI without paired questions.
- **Code.** Commit `335b0af` for every episode. Results store hashes of every
  policy and runner file and both model assets.
- **Primary analysis.** Official MSMI per 100 arrived members, averaged within
  and then across scenario families. Two primary comparisons: GraphVOI against
  degree-first and against uncertainty-first. Paired bootstrap over whole seeds
  (100 clusters, 2,000 draws), because one seed produces the same population in
  most families. We call a difference real only if its Bonferroni-adjusted 97.5%
  interval excludes zero.
- **Secondary (H1b, fixed in Round 1).** Mutual acceptances, which have about ten
  times more events. Then dates, coverage, waiting, ask cost, missing feedback and
  runtime.
- **Failures.** Any invalid, missing or duplicated episode blocks the score and
  intervals for that method, as in the official scorer. Nothing is dropped.

Before running, we expected the 95% half-width for MSMI to be about 0.03 to 0.04.
Differences smaller than that were not going to be resolvable.

# 5 Main result

[[MAIN_RESULTS]]

# 6 Ablations

[[ABLATIONS]]

# 7 Answer-model errors and changing disclosure

[[DISCLOSURE]]

# 8 Calibration, waiting and who gets opportunities

[[CALIBRATION_WAITING]]

# 9 Where it fails

[[FAILURES]]

# 10 Validity, runtime and limits

[[VALIDITY]]

# 11 Reproducing this report

[[REPRODUCE]]

# References

[1] Romeo & Juliet / Vouchsafe. *The One Introduction Problem: Sequential reciprocal matching under uncertainty.* Final participant specification 1.0.0, 2026.

[2] A. Blum, J. P. Dickerson, N. Haghtalab, A. D. Procaccia, T. Sandholm, A. Sharma. Ignorance is almost bliss: near-optimal stochastic matching with few queries. *Operations Research*, 2020.

[3] S. Singla. The price of information in combinatorial optimization. *SODA*, 2018.

[4] J. Drummond, C. Boutilier. Elicitation and approximately stable matching with partial preferences. *IJCAI*, 2013.

[5] Y. Shi, C. Wang, H. Wang, X. Xiao. NBQ: Next-best-question for dynamic profiling. *KDD*, 2026.

[6] C. Vernade et al. Linear bandits with stochastic delayed feedback. *ICML*, 2020.
