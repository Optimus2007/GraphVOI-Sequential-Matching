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

This report does that. GraphVOI did **not** improve completed meetings or MSMI
over degree-first or uncertainty-first asking. Over 600 paired worlds the three
selectors are level, and the simpler degree-first rule is, if anything, slightly
ahead. Section 9 explains why, and what we would use instead.

On the organisers' other two questions: decisions are insensitive to how
confident the answer model is, but a biased model or one that expects refusals
changes them and costs outcomes, and tuning beliefs to a world where people
refuse more does not help (Section 7). GraphVOI is no more fragile than the
simpler rules when disclosure changes. The model is calibrated in both directions
but barely discriminates, and the three question policies leave the same people
waiting; what changes who waits is whether the budget is spent (Section 8).

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
- **Waiting depends on asking.** Leaving budget unspent cost members time:
  among members who could be served, the share introduced within 14 days of arrival
  dropped from about 45% to 33% when we turned the budget fill off.

Everything here can be rerun from the repository. The code, Dockerfile, model
assets, raw results and the protocol we wrote before each study are all public.

**What the organisers asked, and where we answer it.**

| Question or request | Section |
|--------------------------------------------------|-----:|
| Does GraphVOI improve the final meeting outcome against degree-first and uncertainty-first asking, with the same model, matcher and budget? | 5 |
| How sensitive are decisions to answer-model errors, especially when disclosure behaviour changes? | 7 |
| Directional calibration, and who waits longer or gets fewer opportunities under each question policy | 8 |
| If a simpler method works as well, what did the comparison teach us? | 6 and 9 |
| Supplied baselines, ablations, changing conditions | 5, 6, 7 |
| Completed meetings and MSMI as the main outcome | 5 |
| Stated preferences and hard eligibility preserved | 11 |

# 2 What we built

One decision day has two calls, and the policy is a plain pipeline around one
research component.

| Step | What happens |
|--|----------|
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
a constructed case where it overstates value (Section 11).

**Staying inside the rules.** One invalid episode makes a submission ineligible,
so the match output is re-validated, and the ask phase stops evaluating new
candidates 4.5 seconds into a call and still returns a legal, full ask set. For
GraphVOI and its comparators it never fired in any run reported here.

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

![Mean ask units spent per decision day. Left: the v2 pilot. Right: the v3 build, with the budget fill turned off and on.](figures/daily_ask_spend.pdf){width=95%}

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
- **Main outcome.** As the organisers asked, completed meetings (dates) and mutual
  second-meeting intention are reported side by side for every comparison.
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

All 4,200 confirmatory episodes were valid. Table 1 gives the main outcomes,
averaged over 600 worlds per method.

| Method | MSMI per 100 | Completed dates per episode | Mutual acceptances per episode | Coverage | Ask units per episode |
|------------------------------|------------:|------------:|------------:|------------:|------------:|
| GraphVOI | 0.339 | 8.52 | 10.98 | 33.7% | 238.8 |
| Degree-first | 0.380 | 8.62 | 11.11 | 33.8% | 198.9 |
| Uncertainty-first | 0.331 | 8.47 | 10.85 | 33.8% | 241.7 |
| GraphVOI, no budget fill | 0.304 | 7.25 | 9.21 | 29.2% | 138.6 |
| Official greedy | 0.350 | 8.23 | 10.59 | 33.7% | 198.9 |
| Official random | 0.384 | 8.37 | 10.65 | 33.8% | 198.9 |
| Official no-asks | 0.077 | 2.15 | 2.71 | 11.9% | 0.0 |

Table: Confirmatory study, seeds 71001 to 71100, six scenario families.

![Paired differences, GraphVOI minus each comparator, over 100 seed clusters.](figures/paired_differences.pdf){width=95%}

**H1 is not supported.** Against uncertainty-first, GraphVOI's MSMI difference is
+0.008 per 100 arrived members (Bonferroni 97.5% interval −0.039 to +0.061).
Against degree-first it is −0.041 (−0.086 to +0.006). Neither interval excludes
zero, so by the rule we fixed in advance we make no claim either way. We should be
plain about the direction, though: the point estimate favours degree-first, and
its unadjusted 95% interval (−0.079 to −0.002) only just excludes zero.

**H1b is not supported either.** On completed dates and mutual acceptances, the
outcomes with ten times more events, the three selectors are level: GraphVOI
minus degree-first is −0.10 dates (95% −0.35 to +0.16) and −0.14 mutual
acceptances (−0.42 to +0.15); against uncertainty-first it is +0.05 dates and
+0.12 mutual acceptances, both intervals covering zero.

**What clearly matters is asking at all, and asking early.** Every asking policy
beats no-asks by about 0.26 MSMI and 8 mutual acceptances per episode. The
budget fill from Section 3 adds 1.27 completed dates (0.89 to 1.66), 1.77 mutual
acceptances (1.36 to 2.17) and 4.5 coverage points per episode to GraphVOI. Its
MSMI gain (+0.035) is in the same direction but too rare to resolve.

Official random scores as well as anything here (0.384). That is not a quirk of
our method: when edge weights carry almost no information, which pairs are
chosen matters much less than how many feasible pairs exist.

**By scenario** (MSMI per 100):

| Scenario | GraphVOI | Degree-first | Uncertainty-first | No fill | Greedy | Random | No-asks |
|------------------------------|------------:|------------:|------------:|------------:|------------:|------------:|------------:|
| development | 0.380 | 0.460 | 0.390 | 0.385 | 0.420 | 0.445 | 0.110 |
| sparse | 0.095 | 0.115 | 0.115 | 0.045 | 0.105 | 0.120 | 0.025 |
| cold start | 0.330 | 0.345 | 0.330 | 0.225 | 0.390 | 0.430 | 0.035 |
| delayed | 0.455 | 0.500 | 0.410 | 0.475 | 0.395 | 0.450 | 0.075 |
| shift | 0.415 | 0.420 | 0.375 | 0.330 | 0.400 | 0.430 | 0.110 |
| drift | 0.360 | 0.440 | 0.365 | 0.365 | 0.390 | 0.430 | 0.105 |

No method leads in every family. Sparse geography produces almost nothing for
anyone, as Round 1 predicted. Without the fill, GraphVOI loses most in cold start (0.225 against 0.330) and
sparse geography (0.045 against 0.095), where incomplete constraints or scarce
partners make early asking matter most.

# 6 Ablations: which parts earn their place

Round 1 promised every row of its experiment table, and the organisers liked
that we would drop machinery that did not earn its place. The four remaining rows
ran on the same 600 worlds and commit, so every comparison below is paired with
the confirmatory runs. All 2,400 episodes were valid.

| Comparison | MSMI per 100 | Completed dates per episode | Mutual acceptances per episode |
|----------------------------------------|--------------:|--------------:|--------------:|
| Max-weight minus greedy allocation (learned edge model, official-style asks) | +0.005 (−0.024 to +0.035) | −0.01 (−0.20 to +0.18) | +0.09 (−0.13 to +0.30) |
| Learned edge model minus official soft-field score (both greedy) | −0.008 (−0.067 to +0.052) | −0.16 (−0.52 to +0.18) | −0.22 (−0.62 to +0.20) |
| GraphVOI minus learned model with official-style asks | −0.008 (−0.060 to +0.043) | +0.46 (+0.13 to +0.80) | +0.53 (+0.14 to +0.91) |
| Degree-first minus learned model with official-style asks | +0.033 (−0.023 to +0.087) | +0.56 (+0.21 to +0.93) | +0.66 (+0.26 to +1.08) |
| GraphVOI without paired questions minus GraphVOI | +0.013 (−0.029 to +0.048) | −0.12 (−0.39 to +0.15) | −0.19 (−0.49 to +0.12) |
| GraphVOI with waiting threshold minus GraphVOI | −0.048 (−0.105 to +0.007) | −2.28 (−2.72 to −1.86) | −2.97 (−3.43 to −2.51) |
| GraphVOI without budget fill minus GraphVOI | −0.035 (−0.089 to +0.017) | −1.27 (−1.66 to −0.89) | −1.77 (−2.17 to −1.36) |

Table: Paired differences over 100 seed clusters, 95% intervals.

Reading the rows in order:

- **Global allocation adds nothing here.** Max-weight matching and greedy matching
  give the same outcomes with the same edge model. With nearly flat weights,
  choosing pairs jointly has little to gain.
- **The learned edge model adds nothing over the official score** that counts
  shared soft fields. This matches the held-out result in Section 3.
- **Ranked asking plus the fill beats official-style asking** (constraints for
  available members in list order) by about half a completed date per episode,
  and degree-first gets the same gain. The gain comes from asking members who
  touch many possible pairs first and using the whole budget, not from
  GraphVOI's matching-value criterion.
- **Paired questions did not matter measurably.** We liked the idea, and the
  organisers did too. We did not measure how often two blocked members are each
  other's only option; a likely reason is that once the whole budget is spent,
  both get asked within a few days anyway.
- **The waiting threshold hurts clearly**: 2.3 fewer completed dates per episode.
  Our reading is that holding back an edge here mostly leaves the member idle,
  because better partners rarely appear in time. It
  also makes the ask phase slower, because more members stay available: the
  six-second guard fired in 196 of its 600 episodes (Section 11). We dropped it.
- **The budget fill is the one component that clearly earns its place.**

# 7 Answer-model errors and changing disclosure

We tested this in three ways (Section 4 and the protocol).

**Do the decisions change?** We gave GraphVOI the same 240 saved public states
under six kinds of answer-model error and compared the chosen asks with the
correct model's choice.

| Answer-model error | Mean overlap of chosen asks | Identical choice | First-ranked ask changed |
|------------------------------|------------:|------------:|------------:|
| Overconfident | 0.999 | 99.6% | 0.4% |
| Underconfident | 1.000 | 100% | 0.4% |
| Refusal only in one subgroup | 0.968 | 92.5% | 5.4% |
| Biased towards one answer | 0.903 | 80.4% | 18.8% |
| Refusal rising over time | 0.861 | 67.9% | 0% |
| Expects 35% refusal | 0.825 | 58.8% | 0% |

Getting the confidence of the answer model wrong barely matters. A biased answer
model is the only error that often changes the top question. Expecting refusals
never moves the first pick but reshapes the rest of the day's asks, because
questions that might be refused look less valuable.

**Do outcomes change when only the beliefs are wrong?** Over 60 paired worlds,
over- and under-confidence changed nothing measurable. A biased model cost 1.1
mutual acceptances per episode (95% −2.13 to −0.02). Wrongly expecting refusals
cost 0.11 MSMI (−0.21 to −0.02) and 0.87 mutual acceptances; with these beliefs
the policy also spent about 4 fewer units per episode.

**What if people really do refuse more?** In a research-only wrapper of the
simulator that withholds 35% of answered bundles, every method loses about 7 to 8
coverage points and 2.5 to 3.2 mutual acceptances per episode (GraphVOI −2.5,
degree-first −3.2, greedy −3.0, each against its own unshifted runs). Within the
shifted world the differences between methods are not significant. A refusal rate
that rises over the episode costs much less (about 2 coverage points). So GraphVOI
is no more fragile than the simpler rules when disclosure changes.

**Does it help if the answer model knows disclosure has changed?** We ran
GraphVOI with beliefs that match each shifted world: expecting 35% refusal in the
world that refuses 35%, and expecting rising refusal in the drift world. It did
not help. In the refusal world, matched beliefs gave 0.85 fewer mutual
acceptances (−1.75 to −0.03) and no measurable change in MSMI; in the drift world, MSMI fell by
0.15 (−0.28 to −0.04). A model that expects refusals values each ask less, so the
ranked part of the day asks differently, while every answered constraint is still
worth having. In this setting the robust choice is to keep asking the useful hard
questions rather than tune beliefs to the refusal rate.

These robustness runs use ten seeds per cell, so we treat them as descriptive.

# 8 Calibration, waiting and who gets opportunities

**Directional calibration.** The model predicts "A accepts B" and "B accepts A"
separately, using the same weights with the roles swapped. Over 91,342 recorded
responses in GraphVOI episodes, both directions are equally well calibrated
(Brier 0.230 and 0.228) and calibrated on average: in the bin that holds 96% of
labels, the model predicts 0.356 and 0.359 is observed. The problem is that it
almost never predicts anything else, which is the held-out finding from Section 3
seen again in live episodes. By the gender of the person responding, Brier scores
are 0.230 (women), 0.228 (men) and 0.233 (non-binary members). A larger gap for
non-binary members in our ten-seed development check (0.244) shrank to this
size with 100 seeds, so we do not read much into it.

![Directional reliability for GraphVOI episodes. Bins with fewer than 30 labels are not shown.](figures/calibration.pdf){width=55%}

**Who waits.** About 35% of members declined at least one hard field when they
joined and can never be introduced under any policy. We report waiting for the
rest, and count members who were never introduced as still waiting at day 59
(Kaplan-Meier), so a policy cannot look fast by serving only easy cases.

| Policy | Served (servable members) | Introduced within 14 days | Median wait (days) | Introductions per member |
|------------------------------|------------:|------------:|------------:|------------:|
| GraphVOI | 51.5% | 45.0% | 26 | 0.761 |
| Degree-first | 51.6% | 45.0% | 27 | 0.761 |
| Uncertainty-first | 51.5% | 44.8% | 27 | 0.760 |
| GraphVOI, no fill | 44.6% | 32.9% | not reached | 0.657 |
| Official greedy | 51.4% | 43.7% | 29 | 0.754 |

![Share of servable members introduced within 14 days, by gender and age band.](figures/waiting_by_group.pdf){width=95%}

The three selectors are indistinguishable, and so are the groups they leave
waiting. Two gaps appear under every policy, so they come from the population and
its age windows, not from the question rule: members aged 40 and over get fewer
introductions (0.69 per member against 0.83 for ages 30 to 39), and men wait
slightly longer than women (43.8% against 45.7% introduced within 14 days under
GraphVOI). The one policy choice that does change who waits is spending the
budget. Without the fill, the share introduced within 14 days falls from 45% to
33%, and members aged 21 to 29 fall furthest (29%).

# 9 What the comparison taught us

The organisers asked us to explain what the comparison taught us if a simpler
method worked as well. It did, and the reason is specific to what we measured.

GraphVOI asks which answer would most improve the best matching. That is only
different from asking which answer would add the most feasible pairs if edges
differ in value. In this simulator they barely do: the pair model's predictions
sit in a narrow band around 0.36, because acceptance depends mostly on a hidden
per-member tendency and per-pair noise that the public fields do not reveal.
With nearly equal weights, the best matching is close to the largest matching,
and the question that most improves it is the one that unlocks pairs. That is
exactly what degree-first measures, more cheaply and without an answer model for
soft fields. All three selectors spend exactly the same on hard constraints (196 units per
episode); GraphVOI's extra 40 units all go on soft fields, whose answers cannot
move nearly flat weights by much.

So the matching-aware part of our idea did not help here, and Round 1 committed
us to saying so: "If GraphVOI beats uncertainty-first but not degree-first, then
the matching part of the idea is not what helps." It beat neither.

What did help came from looking closely at the pilot rather than from the
headline method: spending the whole budget early on hard constraints. That
change made more difference to completed meetings, coverage and waiting than
the choice between any of the three ranking rules.

If we were deploying this, we would run degree-first plus the budget fill, and
keep GraphVOI for settings where pair quality is genuinely predictable. Our
expectation, which we have not tested, is that GraphVOI's advantage should grow
with how much the edge values differ, because only then can one answer change
which pairs are best rather than just how many exist.

# 10 Where it fails

The specification asks for failures involving sparse supply, withheld answers,
delayed feedback and competition for the same candidate.

- **Sparse supply.** In sparse geography every method scores close to zero
  (0.095 to 0.120 MSMI for the asking policies). There are too few feasible
  pairs for any question rule to matter, as Round 1 expected, and the budget
  fill matters most here because each unlocked member is scarce.
- **Withheld answers.** About 35% of members decline a hard field and can never be
  introduced; we never fill those fields in and count them separately in the
  waiting analysis. When refusal rises further (Section 7), every method loses
  about 7 to 8 coverage points. GraphVOI's answer model cannot learn the new
  refusal rate inside an episode, and believing in refusals that do not happen
  costs outcomes, so tracking disclosure online is the obvious next step.
- **Delayed feedback.** Our models are trained offline and not updated inside an
  episode, so the delayed-dates family does not hurt us more than others
  (GraphVOI 0.455 MSMI there, among its best families). The cost is the other
  way round: the model cannot learn from this episode's own outcomes either.
- **Competition for the same candidate.** Maximum-weight matching resolves
  conflicts over a popular member globally rather than greedily, but with flat
  weights it cannot tell which conflict is worth winning. The waiting analysis
  shows the consequence that every policy shares: members aged 40 and over get
  about 17% fewer introductions than those aged 30 to 39.
- **Short-sighted value.** One-day VOI ignores the later value of a hard answer.
  This is the failure we found in the pilot; the fill is a simple patch, not a
  model of future value.
- **Approximate batch value.** Compressing large joint answer distributions to
  eight worlds can overstate value; on a constructed example it gives 17.5
  where the exact answer is 15.

# 11 Validity, runtime and limits

| Check | Result |
|---|---|
| Invalid episodes | 0 of 4,200 confirmatory, 2,400 ablation, 720 robustness and 300 development episodes |
| Stated preferences | Every introduction re-checked against members' true hard preferences, read from regenerated worlds on the evaluation side only: 0 violations in 279,261 introductions across all methods, and no member who declined a hard field was ever introduced |
| Official container mode (`--network=none --cpus=2 --memory=1g --read-only`) | All six families valid on ARM (Apple M-series) and on x86 Linux (GCP), seed 101 |
| Determinism | Identical action hashes for the same episode on both machines: 6 of 6 container episodes, 22 of 22 overlapping confirmatory episodes and 320 of 320 overlapping robustness episodes (Python 3.13 on ARM, 3.12 on x86) |
| Time per call, including container start | Ask: median 1.8 s, max 2.5 s on ARM; median 3.6 s, max 4.6 s on a heavily loaded x86 host. Match: max 1.3 s. Limit 10 s |
| Ask-phase guard | At 6 s it never fired for GraphVOI or the comparators in 4,200 episodes; it fired only in the waiting-threshold ablation (196 of 600 episodes), whose slowest ask then reached 7.1 s. We lowered it to 4.5 s for the submission; re-running 24 confirmatory episodes gives identical action hashes and no guard hits |
| Peak memory | 61 MiB of 1 GiB |
| Model assets | Rebuilt byte for byte from seeds 31001 to 31008 |
| Tests | 93 passing, including exact small-graph references and brute-force matching |

The x86 timings were taken while 28 study workers shared the same machine, so they
are pessimistic, but they halve the margin we measured on the Mac. The ablation
also showed the guard can overshoot by about a second. That is why the submitted
build stops evaluating new questions after 4.5 s and still returns a legal, full
ask set; the default policy's slowest ask in the whole study was 3.1 s, so this
changes no decision we evaluated.

**Limits.** All results are from the organisers' synthetic simulator, and MSMI is
rare enough that differences under about 0.04 per 100 arrivals are not resolvable
even with 100 paired seeds. GraphVOI's matching value is myopic, batch selection
is greedy over a restricted frontier with compressed answer worlds, and the
answer model draws hard answers from the four most similar disclosed training
members without held-out validation of those probabilities. The robustness runs
use ten seeds per cell. The disclosure shift is our own research wrapper, not an
official scenario.

# 12 Reproducing this report

Everything in this report comes from files in the repository:
`results/<study>/episodes.csv` and `summary.json` for every study, and
`results/validation/` for the container runs. Raw outputs and per-episode
traces are attached to the GitHub release; each summary records the SHA-256 of
its raw file. The README lists every command. In short:

```bash
python3 -m unittest discover -v && python3 verify_data.py
docker build -t graphvoi-orbit:round2 .
python3 evaluate.py --image graphvoi-orbit:round2 --seeds 101 --variants all --output out.json
python3 scripts/run_study.py --purpose confirmatory --seeds 71001-71100 \
  --methods graphvoi,degree_first,uncertainty_first,graphvoi_nofill,greedy,no_asks,random \
  --workers 8 --output results/v3_confirmatory.json
```

The confirmatory study ran on two machines with identical code and model hashes:
1,428 episodes on a Mac (Python 3.13.7, 6 workers) and 2,772 on a 80-vCPU x86
Linux machine (Python 3.12.7). `scripts/merge_studies.py` refuses to combine parts
whose code or assets differ, requires the full design and checks that overlapping
episodes have identical actions. The full study takes about 65 CPU-hours on Apple M-series cores. Inference
uses no random seed; training seeds are 31001 to 31008.

# References

[1] Romeo & Juliet / Vouchsafe. *The One Introduction Problem: Sequential reciprocal matching under uncertainty.* Final participant specification 1.0.0, 2026.

[2] A. Blum, J. P. Dickerson, N. Haghtalab, A. D. Procaccia, T. Sandholm, A. Sharma. Ignorance is almost bliss: near-optimal stochastic matching with few queries. *Operations Research*, 2020.

[3] S. Singla. The price of information in combinatorial optimization. *SODA*, 2018.

[4] J. Drummond, C. Boutilier. Elicitation and approximately stable matching with partial preferences. *IJCAI*, 2013.

[5] Y. Shi, C. Wang, H. Wang, X. Xiao. NBQ: Next-best-question for dynamic profiling. *KDD*, 2026.

[6] C. Vernade et al. Linear bandits with stochastic delayed feedback. *ICML*, 2020.
