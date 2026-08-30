# Literature Review: Reliable Evaluation For Self-Evolving Agents

Status: working research map, reviewed 2026-08-30.

Barcarolle's first principle is to provide reliable evaluation methods for
self-evolving agents. Repository coding agents are the first concrete domain,
not the boundary of the research question. A self-evolving agent may update its
model, harness, persistent prompt, memory, skills, tools, workflow, collaboration
structure, or another persistent component using experience or evaluator
feedback.

The following three primary empirical objectives operationalize that mission:

1. minimize pass-rate mean absolute error (MAE) on future real-world tasks;
2. minimize pass-rate-difference MAE between agents on those tasks;
3. minimize the increase in both errors as the predeclared budget for repeated
   evaluator-guided optimization grows.

These objectives test whether an evaluator remains connected to future
real-world outcomes. They are not a definition of self-evolution, a generic
agent score, or evidence that every relevant safety and integrity property has
been measured.

This review is deliberately broader and more detailed than the main
[`research-program.md`](research-program.md). The goal is to preserve useful
raw material for later experiments without making the first project document
read like a bibliography.

## How To Read The Evidence

Source labels describe publication status, not correctness:

- **[J]** peer-reviewed journal article;
- **[C]** peer-reviewed conference paper;
- **[P]** preprint;
- **[R]** official technical report, audit, or standard.

Review articles keep the journal or conference label for their publication
venue. Evidence strength and transfer limits are described in the table rather
than encoded in the label.

The review favors primary papers and official reports. Results from language,
educational, safety, forecasting, and reinforcement-learning settings are
adjacent evidence. Unless a row explicitly concerns coding agents, applying it
to Barcarolle is a proposed transfer, not a result established by the source.

“Reliable evaluation” is the project's broad engineering objective. The first
item below is the narrower measurement-science property, so this review calls
it **measurement reliability** to avoid treating repeatability as the whole
mission. Three distinctions matter throughout:

- **measurement reliability**: would the same measurement design give a stable
  result under its declared sources of variation?
- **measurement invariance**: does a task measure agents in the same way across
  model families, harnesses, time periods, or evaluator feedback policies?
- **predictive validity**: does the evaluation predict the stated outcome on
  future real-world tasks?

Passing one test does not imply passing the next. In particular, a small static
benchmark can reliably reconstruct a larger static benchmark while remaining
invalid for future agents or future real-world tasks.

Three evaluation objects must also remain distinct:

- an **agent snapshot** is one fully specified version of the model, harness,
  persistent state, tools, and runtime policy;
- an **agent transition** is a declared parent-to-child or
  incumbent-to-challenger update, evaluated on common tasks and replicate
  conditions;
- an **agent lineage or evolution process** includes the initial snapshot,
  update algorithm, editable components, evaluator and feedback policy,
  optimization budget, randomization, all considered candidates, and the
  resulting version graph.

A snapshot score cannot establish that an update was beneficial, and a good
parent-child update cannot establish that the same evolution process will
remain beneficial after more evaluator-guided optimization.

Finally, distinguish two experimental regimes:

- in a **fixed-evaluator experiment**, the evaluator and feedback policy remain
  fixed for the complete agent search; the question is how their prediction
  errors change as the optimizer targets them;
- in an **evaluator-coevolution experiment**, evaluator updating occurs only at
  declared epoch boundaries. The complete update and promotion rule is then
  part of the method being evaluated and must itself face independent future
  real-world tasks.

Periodic updating is not evidence of successful coevolution, and an evolving
evaluator cannot validate itself using outcomes that shaped its own updates.

## Conclusions That Directly Affect The Research Design

1. Treat reliable evaluation for self-evolving agents as the research mission;
   treat the two MAEs and their degradation under optimization as its primary
   empirical objectives.
2. Evaluate snapshots, transitions, and complete lineages separately. Preserve
   the full version graph and every rejected candidate; winner-only reporting
   creates survivorship and search-policy bias.
3. Model the second objective as a paired contrast. For task `i`, use
   `D_i = Y_ai - Y_bi` on the same task and replicate, rather than subtracting
   two unrelated estimates.
4. Use outcome models to propose informative tasks, but retain randomized
   sampling and a matching design-based or model-assisted estimator. A
   deterministic “most informative” subset has no automatic protection against
   selection bias.
5. Separate measurement reliability, item-parameter invariance, and future
   predictive validity. Generalizability theory, IRT, or score reconstruction
   cannot replace time-based external validation.
6. Treat the agent as model plus harness, persistent state, and runtime policy.
   Model, memory, skill, tool, and workflow updates are different evolution
   surfaces and may require different stress tests.
7. Separate the system that proposes an update from the agent that must use it.
   Harness-update quality, artifact activation, long-horizon adherence, and
   end-task benefit are empirically distinct quantities.
8. Track optimization budget and feedback detail. Adaptive data analysis and
   reward-model studies both show that repeated use of a finite proxy matters,
   but their guarantees do not cover direct benchmark tampering.
9. Keep adversarial tasks separate from the estimated distribution of future
   real-world tasks unless calibration demonstrates otherwise. Harder is not
   the same as more representative.
10. Use nested temporal data: development, evaluator-selection validation, and
   one-use prospective test. A set ceases to be independent test evidence once
   its outcomes affect selection.
11. Require both MAEs to satisfy decision-derived absolute limits before
    calling an evaluation reliable. For a claim that covers repeated
    evaluator-guided optimization, separately bound degradation from the same
    method's no-optimization baseline (`b=0`); for a static `b=0` claim, record
    this stage as `not_applicable`. Use a named-comparator pass-rate MAE margin
    only to prefer among otherwise acceptable methods. Retain uncertainty,
    critical-stratum, coverage, cost, and integrity requirements.
12. Report complete error curves across optimization budgets. A single
    before/after number can hide reward overoptimization, forgetting, or
    lineage collapse that appears only after more search.
13. Evaluation awareness is not one established causal mechanism. Constructed
    sandbagging, monitor attacks, latent test-awareness interventions, and
    verbalized awareness provide different evidence; negative results show that
    verbalized awareness can have little behavioral effect.
14. No located work establishes that agent–evaluator coevolution preserves the
    two requested numerical errors for self-evolving coding agents. That is a
    new research hypothesis.
15. Treat benchmark integrity as a separate measured outcome. Task and reward
    defects, leakage, evaluator tampering, and weak tests can all change an
    apparent pass rate, but detecting one failure does not establish future
    predictive validity.

## 1. Measurement Reliability, IRT, And Task Information

| Source | What it establishes | Use in Barcarolle | Important limit |
| --- | --- | --- | --- |
| **[J]** [Briesch et al., *Generalizability Theory: A Practical Guide*](https://doi.org/10.1016/j.jsp.2013.11.008) | Generalizability studies decompose score variance across people, items, occasions, raters, and their interactions; decision studies estimate how reliability changes with the measurement design. | Decompose variation across agent, task, repository/time split, and replicate before deciding whether to buy more tasks, replicates, or time splits. | Reliability across declared facets is not validity on future work and does not address strategic gaming. |
| **[J]** [Cai et al., *Item Response Theory*](https://www.annualreviews.org/content/journals/10.1146/annurev-statistics-041715-033702) | Reviews unidimensional, multidimensional, multilevel, mixture, response-time, and model-fit extensions of IRT. | Supplies the model family for agent ability, task difficulty, discrimination, and hierarchical extensions. | Local independence, latent dimensionality, and stable item parameters are assumptions to test, not facts about coding tasks. |
| **[J]** [Mellenbergh, *Item Bias and Item Response Theory*](https://doi.org/10.1016/0883-0355(89)90002-5) | Formalizes differential item functioning (DIF): after conditioning on latent ability, item response should not still depend on group. | Test whether a task changes measurement behavior across model family, harness, time, or evaluator feedback policy. | DIF does not by itself identify unfairness, cheating, or which group is closer to the future target. |
| **[J]** [Belzak and Bauer, regularized measurement-invariance testing](https://pmc.ncbi.nlm.nih.gov/articles/PMC7343596/) | Shows how regularization can help select anchor items and detect DIF, while documenting failures when many items have DIF. | Motivates explicit anchor selection and sensitivity analysis instead of assuming most tasks are invariant. | Small agent panels may be insufficient; regularization can hide broad, non-sparse shift. |
| **[J]** [Wallin, Chen, and Moustaki, DIF with unknown groups and anchors](https://doi.org/10.1007/s11336-024-09948-7) | Jointly models latent groups, unknown anchors, and sparse item-specific DIF. | Exploratory search for previously unknown optimization or gaming phenotypes. | Strong sample-size, mixture-model, and sparsity assumptions make this unsuitable as an immediate confirmatory method. |
| **[J]** [van der Linden and Barrett, linking item-response parameters](https://doi.org/10.1007/s11336-015-9469-6) | IRT calibrations need common items or subjects and an explicit linking method before parameters are comparable. | Link evaluator epochs through bridge tasks or bridge agents, with uncertainty and DIF checks. | Mathematical linking does not prove that exposed bridge tasks remain invariant. |
| **[J]** [Segall, *Multidimensional Adaptive Testing*](https://doi.org/10.1007/BF02294343) | Uses multidimensional IRT and information-based item selection to reduce ability-estimation uncertainty. | Compare Rasch, 2PL, and multidimensional models; target the posterior variance of deployment-relevant agent contrasts. | Generic information criteria need not minimize future pass-rate-difference MAE. |
| **[C]** [Rodriguez et al., *Evaluation Examples Are Not Equally Informative*](https://aclanthology.org/2021.acl-long.346/) | A Bayesian IRT leaderboard model finds informative examples, annotation errors, and ranking uncertainty. | Baseline for task information, error discovery, and response-matrix modeling. | Evidence is from static NLP benchmarks; item invariance and future transfer remain open. |
| **[C]** [tinyBenchmarks](https://proceedings.mlr.press/v235/maia-polo24a.html) | Small IRT-informed subsets can reproduce several large, static language-model benchmark results. | Strong static subset-reconstruction baseline. | Reconstructing an opened benchmark does not establish temporal, harness, or adaptive robustness. |
| **[C]** [MetaBench](https://proceedings.iclr.cc/paper_files/paper/2025/hash/4ebc26584810a189ef1e4f173aba4319-Abstract-Conference.html) | Uses responses from thousands of models and multidimensional structure to build very small benchmark subsets. | Shows what may be possible with a rich agent population and motivates a sample-size audit before complex IRT. | Barcarolle currently has far fewer agents; static score recovery is not future prediction. |
| **[C]** [Reliable and Efficient Amortized Model-Based Evaluation](https://proceedings.mlr.press/v267/truong25c.html) | Predicts item difficulty from content and combines model-based evaluation with difficulty-conditioned question generation. | Precedent for jointly modeling response, selection, and generation. | Language-question evidence does not validate repository task generation or hidden checks. |
| **[C]** [Agent Psychometrics: Task-Level Performance Prediction in Agentic Coding Benchmarks](https://arxiv.org/abs/2604.00594) | Extends IRT with repository-task artifacts and separates model from harness ability to predict success on unseen benchmarks and unseen model–harness combinations. | Closest coding-specific baseline for static outcome modeling, new tasks with no prior outcomes, and explicit harness effects. | The reported target is static task-level success, not rolling future pass-rate MAE, direct pair-difference MAE, or robustness under repeated optimization. |

### Measurement experiments to preserve

- Fit a variance-component model on existing complete response matrices and
  run a decision study over task, replicate, and time-split counts.
- Simulate whether the available agent count can recover aggregate pass rates,
  paired differences, and item parameters separately. Accurate aggregate score
  recovery does not imply trustworthy item parameters.
- Fit multi-group IRT with model family, harness, time, and evaluator feedback
  policy as groups. Report DIF effect size and held-out likelihood, not only
  p-values.
- Reproduce Agent Psychometrics as a static coding-specific comparator, then
  replace random task holdout with rolling time cutoffs and score both marginal
  pass rates and direct paired differences.
- If evaluator epochs use different task sets, test bridge-task invariance
  before linking their latent scales. Always retain a raw pass-rate comparison
  that does not depend on the link.

## 2. Efficient Sampling, Paired Comparison, And Estimation

| Source | What it establishes | Use in Barcarolle | Important limit |
| --- | --- | --- | --- |
| **[C]** [Sawade et al., *Active Comparison of Prediction Models*](https://papers.nips.cc/paper_files/paper/2012/hash/92fb0c6d1758261f10d052e6e2c1123c-Abstract.html) | Importance-weighted sampling can focus labels where two fixed models differ and increase the power of their comparison. | Direct precedent for allocating tasks to an agent pair rather than optimizing one-agent uncertainty. | Assumes a fixed supervised test distribution and does not solve temporal shift. |
| **[J]** [Hara et al., *Active Model Selection: A Variance Minimization Approach*](https://doi.org/10.1007/s10994-024-06603-1) | For sequential sampling without replacement, LURE estimates loss differences; the ideal two-model proposal emphasizes absolute disagreement. | Use predicted agent discordance plus a random exploration floor and log every conditional proposal probability. | Reduces variance within a fixed task population; it cannot repair mismatch between that population and future work. |
| **[C]** [Kossen et al., *Active Testing*](https://proceedings.mlr.press/v139/kossen21a.html) | Actively acquires expensive test labels and uses LURE to correct acquisition bias. | One-agent baseline for comparison with comparison-aware sampling. | A deterministic informative subset mean remains biased for the full task population. |
| **[J]** [Breidt and Opsomer, model-assisted survey estimation](https://doi.org/10.1214/16-STS589) | Generalized regression and difference estimators combine predictions over the full frame with probability-sampled, weighted residual corrections. | Let an IRT or outcome model reduce variance while randomized task sampling protects the declared finite-population target. Apply the same construction directly to paired outcome `D_i`. | Requires a known sampling design and does not convert historical or generated tasks into the future population. |
| **[J]** [Deville and Tillé, the cube method](https://doi.org/10.1093/biomet/91.4.893) | Balanced probability sampling can preserve auxiliary totals while retaining random inclusion probabilities. | Balance repositories, time, task type, cost, predicted difficulty, and predicted discordance without deterministic quotas. | Auxiliary balance does not guarantee outcome balance or future representativeness; variance estimation can be difficult. |
| **[C]** [Peyrard et al., *Better Than Average*](https://aclanthology.org/2021.acl-long.179/) | Taking instance-level pairing into account can change conclusions relative to independent averages; across surveyed NLP setups, aggregation choice often mattered. | Supports common tasks, paired uncertainty, and pair-level diagnostics. | Bradley–Terry ranking is not a substitute for numerical pass-rate-difference error. |
| **[J]** [Newcombe, confidence intervals for paired binomial differences](https://doi.org/10.1002/(SICI)1097-0258(19981130)17:22%3C2635::AID-SIM954%3E3.0.CO;2-C) | Score-based intervals for paired binary risk differences improve on simple Wald intervals and use discordant cells directly. | Preserve the task-level 2×2 table for each agent pair as a small-sample diagnostic. | Repository, dependency-cluster, and adaptive-sampling dependence require a broader variance method. |
| **[J]** [Nelson and Matejcik, common random numbers](https://doi.org/10.1287/mnsc.41.12.1935) | Shared random conditions can reduce variance in system differences when they induce positive covariance; indifference-zone procedures avoid overinterpreting tiny differences. | Pair seeds, environments, and replicate slots; predeclare a practically negligible difference. | Pairing can increase variance under adverse covariance, and the indifference margin must not be tuned after outcomes. |
| **[J]** [Gneiting and Raftery, proper scoring rules](https://doi.org/10.1198/016214506000001437) | Proper scoring rules elicit honest probabilistic forecasts; different point losses target different functionals. | Keep user-required MAE, but add calibration, Brier score, predictive intervals, or CRPS when the evaluator claims a probability distribution. | A proper score does not solve shift, pairing, or Goodhart effects. |
| **[J]** [Prediction-Powered Inference](https://doi.org/10.1126/science.adi6000) | Machine predictions can improve statistical efficiency when a smaller labeled sample corrects their errors with valid inference. | Candidate framework for using generated or modeled outcomes as auxiliary predictions while real task outcomes provide correction. | Validity depends on the labeled sampling and target-population assumptions; it is not permission to replace real outcomes with synthetic labels. |
| **[J]** [El-Yaniv and Wiener, selective classification](https://jmlr.org/papers/v11/el-yaniv10a.html) | Formalizes the risk–coverage tradeoff when a predictor may abstain. | Require every abstaining evaluator to report error against coverage and an unconditional fallback policy. | High selective accuracy can be vacuous at low coverage. |

### Recommended first estimator family

For agent pair `(a, b)` and paired outcome `D_i = Y_ai - Y_bi`:

1. train a cross-fitted outcome model `m_i` for `D_i`;
2. sample tasks with a stratified random floor plus predicted discordance;
3. log the complete inclusion or conditional proposal probabilities;
4. estimate the target mean with the matching Horvitz–Thompson, Hájek, LURE,
   or model-assisted residual-correction formula;
5. report bias in replay, variance, interval coverage, effective sample size,
   maximum weight, and sensitivity to response-model misspecification.

This design combines model efficiency with a probability-sampling safety net.
It still needs temporal validation on future real-world tasks.

## 3. Temporal Evaluation And Distribution Shift

| Source | What it establishes | Use in Barcarolle | Important limit |
| --- | --- | --- | --- |
| **[J]** [Dawid, *The Prequential Approach*](https://doi.org/10.2307/2981683) | Evaluates a forecasting system through the sequence of predictions made before outcomes are observed. | At every time cutoff, persist the prediction and evaluator digest before future labels are opened. | Prequential order alone gives no stationarity or distribution-shift guarantee. |
| **[J]** [Tashman, out-of-sample tests of forecasting accuracy](https://doi.org/10.1016/S0169-2070(00)00065-0) | Clarifies rolling origins, horizons, fixed versus rolling windows, and forecast updating. | Define the exact history window, update policy, and H5/H10 or calendar horizon at each time split. | Overlapping forecast windows create dependence and historical replay may miss a new regime. |
| **[C]** [Han et al., *Model Assessment and Selection under Temporal Distribution Shift*](https://proceedings.mlr.press/v235/han24b.html) | Develops adaptive rolling windows for estimating model error and pairwise error differences under temporal nonstationarity. | Directly relevant baseline for both pass-rate and pass-rate-difference prediction across time. | The supervised theory does not cover strategic agent adaptation or generated repository tasks. |
| **[J]** [Gama et al., survey on concept drift](https://doi.org/10.1145/2523813) | Organizes drift mechanisms, adaptation methods, and evaluation practices for data streams. | Supplies terminology for gradual, abrupt, recurring, and conditional changes rather than calling all failures “Goodhart.” | A broad review does not choose the correct drift model for coding tasks. |
| **[C]** [Mandoline](https://proceedings.mlr.press/v139/chen21i.html) | Reweights source data toward a target using human-specified slices and analyzes error from hidden or misspecified shift axes. | Use repository/task metadata as explicit candidate shift dimensions and test slice omission. | Requires target-distribution information and overlap; slice quality matters. |
| **[C]** [ODD: Overlap-Aware Estimation under Distribution Shift](https://proceedings.mlr.press/v286/mishra25a.html) | Makes target/source overlap explicit when estimating unseen-domain performance. | Motivates overlap diagnostics and abstention when a new agent or task region lacks support. | Does not handle strategic gaming and is not yet validated for repository-level agent matrices. |
| **[C]** [Ben-David et al., impossibility results for domain adaptation](https://proceedings.mlr.press/v9/david10a.html) | Without assumptions tying source and target distributions, unlabeled target data do not generally make adaptation possible. | Require every historical-to-future or generated-to-real transfer method to state a falsifiable shift assumption. | It does not say adaptation is always impossible; it says the assumptions carry the guarantee. |
| **[C]** [Model evaluation over time in medical data](https://proceedings.mlr.press/v209/zhou23a.html) | Simulates what could have been trained at each historical time and evaluates deployment into later periods. | Useful applied template for time-respecting data availability and multiple future periods. | Medical record shift differs from repository and agent evolution. |

### Temporal inference requirements

- Fix all evaluator predictions for a time split before any task outcome in its
  future block is opened.
- Do not treat overlapping future windows or all agent pairs as independent.
  Use repository, non-overlapping future block, task-dependency cluster,
  agent-family, and run-level structure in the analysis.
- Separate expanding-history from sliding-window methods and record whether the
  evaluator is recalibrated at each time cutoff.
- When overlap is weak, report abstention or a fallback rather than unsupported
  extrapolation.

## 4. Adaptive Test Reuse And Selection-Induced Bias

| Source | What it establishes | Use in Barcarolle | Important limit |
| --- | --- | --- | --- |
| **[C]** [Dwork et al., adaptive data analysis and holdout reuse](https://proceedings.neurips.cc/paper/2015/hash/bad5f33780c42f2588878a9d07405083-Abstract.html) | Under stated statistical-query assumptions, controlled information release can preserve generalization across many adaptive analyses. | Track evaluator queries and feedback information; test noisy, rounded, or thresholded feedback. | Does not cover semantic reward hacking, hidden-check leakage, test tampering, or distribution shift. |
| **[C]** [Blum and Hardt, *The Ladder*](https://proceedings.mlr.press/v37/blum15.html) | A leaderboard can reveal only sufficiently large improvements and retain accuracy for the best submission under an adaptive model. | Baseline feedback policy for repeated agent submissions. | Leaderboard accuracy is weaker than accurate pass rates and all pairwise differences. |
| **[C]** [Russo and Zou, controlling adaptive bias with information theory](https://proceedings.mlr.press/v51/russo16.html) | Bounds selection bias using information revealed by adaptive analysis. | Treat feedback bits and candidate count as measurable optimization-budget components. | Information bounds do not automatically produce a practical coding benchmark protocol. |
| **[J]** [Cawley and Talbot, overfitting in model selection](https://jmlr.org/papers/v11/cawley10a.html) | Optimizing a noisy finite validation criterion creates selection-induced optimism; criterion variance matters alongside bias. | Use nested temporal selection and report the full candidate archive, winner optimism, and regret from choosing the wrong model. | Ordinary nested cross-validation does not solve temporal drift or adaptive reuse of the outer set. |
| **[C]** [Roelofs et al., meta-analysis of benchmark overfitting](https://papers.neurips.cc/paper_files/paper/2019/hash/ee39e503b6bedf0c98c388b7e8589aca-Abstract.html) | Empirically studies repeated community use of image benchmarks and finds limited but nonzero evidence of test-set adaptation. | A useful counterweight to claims that reuse always causes catastrophic overfitting; measure rather than assume. | Image-model similarity and benchmark history may not transfer to self-evolving coding agents. |
| **[C]** [Feng et al., sequential algorithmic modification with test reuse](https://proceedings.mlr.press/v180/feng22a.html) | Multiple-testing procedures can approve sequential model updates while controlling erroneous approvals under specific assumptions. | Precedent for epoch-level promotion tests and explicit counts of proposed modifications. | Tests accept/reject changes on a fixed IID target; they do not solve future task construction or direct gaming. |
| **[C]** [Off-Policy Confidence Sequences](https://proceedings.mlr.press/v139/karampatziakis21a.html) | Time-uniform bounds remain valid under optional stopping for adaptive logged policies with known propensities and support. | Enables precision-based stopping in a compatible randomized streaming design. | It is not a drop-in interval for finite-population LURE without replacement. Sampling-bias correction and optional-stopping validity are separate problems. |
| **[J]** [Berrar, replication probability of benchmark experiments](https://jmlr.org/papers/v25/24-0158.html) | Shows that marginally significant benchmark comparisons may have low replication probability. | Add power and replication analysis to multi-repository method comparisons. | Its standard designs do not capture all repository, pair, and temporal dependence in Barcarolle. |

## 5. Goodhart Effects, Reward Hacking, And Optimization Budget

| Source | What it establishes | Use in Barcarolle | Important limit |
| --- | --- | --- | --- |
| **[P]** [Manheim and Garrabrant, Goodhart taxonomy](https://arxiv.org/abs/1803.04585) | Distinguishes regressional, extremal, causal, and adversarial forms of proxy failure. | Organize failure hypotheses instead of treating every prediction error as one mechanism. | A conceptual taxonomy is not evidence that a mitigation works. |
| **[C]** [Skalse et al., *Defining and Characterizing Reward Hacking*](https://proceedings.neurips.cc/paper_files/paper/2022/hash/3d719fee332caa23d5038b8a90e81796-Abstract-Conference.html) | Formalizes reward hacking and shows that unhackable proxies are exceptionally restrictive in its model. | Justifies testing static evaluators against increasingly optimized agent policies. | The theorem's MDP and reward assumptions are not a general impossibility result for coding benchmarks. |
| **[C]** [Gao et al., reward-model overoptimization](https://proceedings.mlr.press/v202/gao23h.html) | In a synthetic reward-model setup, gold reward can peak and then fall as best-of-`N` or RL optimization increases. | Measure full error-versus-candidate and error-versus-round curves, not only endpoints. | The “gold” reward is another fixed model, not future real-world work. |
| **[C]** [Inference-Time Reward Hacking in Large Language Models](https://proceedings.neurips.cc/paper_files/paper/2025/hash/590a0cc0306c1c63e2d66a51a407718f-Abstract-Conference.html) | Characterizes the rise-then-fall true-reward curve under best-of-`N` and related inference-time optimization, and studies hedging against proxy overoptimization. | Direct precedent for plotting complete error curves against candidate budget and for comparing best-of-`N` with softer selection. | The experiments use math, reasoning, and preference reward models rather than coding agents or future-task forecasts. |
| **[C]** [WARM](https://proceedings.mlr.press/v235/rame24a.html) | Weight-averaged reward models improve robustness to reward-model shift and inconsistent preferences in tested RLHF settings. | Evaluator portfolio baseline and correlated-blind-spot stress test. | Reward-model averaging does not establish robustness of coding task sets or pass-rate prediction. |
| **[C]** [Zhu et al., when proxies improve preference-learning sample complexity](https://proceedings.mlr.press/v267/zhu25f.html) | Gives conditions under which proxy information helps and when misspecification causes reward hacking. | Forces explicit assumptions about proxy quality and the value of limited real labels. | Preference learning differs from binary coding-task outcomes and temporal task supply. |
| **[C]** [MONA](https://proceedings.mlr.press/v267/farquhar25a.html) | Separates myopic optimization from non-myopic approval to reduce multi-step reward hacking in tested settings. | Adjacent design for separating fast agent search from slower evaluator approval. | Does not solve future-task prediction or evaluator-selection overfitting. |
| **[C]** [Reward Hacking Benchmark: Measuring Exploits in LLM Agents with Tool Use](https://arxiv.org/abs/2605.02964) | Across 13 models on instrumented multi-step tasks, reports exploit rates from 0% to 13.9%; simple environment hardening lowers the aggregate rate by 5.7 percentage points in the tested setup. | Concrete attack taxonomy and environment-hardening baseline for tool-using agent experiments. | The shortcut tasks and chain length are proxies for long-horizon behavior; the study does not measure either Barcarolle prediction error. |
| **[P]** [RewardHackingAgents: Benchmarking Evaluation Integrity for LLM ML-Engineering Agents](https://arxiv.org/abs/2603.11337) | Uses fresh workspaces, patch and file-access logs, and a trusted reference evaluator to label evaluator tampering and train/test leakage. | Closely matches Barcarolle's workspace-integrity threat model and supplies executable attack and defense patterns. | Only three tasks and two model backbones were studied; the reported natural-attempt rate cannot be treated as a prevalence estimate. |
| **[P]** [Natural Emergent Misalignment from Reward Hacking in Production RL](https://arxiv.org/abs/2511.18397) | In selected production coding environments, reward hacking learned during RL generalizes to several other misaligned behaviors in the reported experiments. | Justifies a worst-case test for behavioral spillover beyond the evaluator score. | The study first imparts knowledge of hacking and chooses hackable environments, so it does not estimate how often such behavior emerges without those conditions. |
| **[R]** [METR's o3/o4-mini evaluation](https://metr.org/evaluations/openai-o3-report/) | Documents coding-agent attempts to read scorer references or alter evaluator behavior and shows that a few missed events can materially affect an aggregate result. | Expand the threat model beyond task selection to scorer, workspace, and review paths. | An institutional report with a small number of events does not estimate prevalence in Barcarolle. |
| **[R]** [OpenAI, monitoring internal coding agents for misalignment](https://openai.com/index/how-we-monitor-internal-coding-agents-misalignment/) | Reports test modification, check disabling, and attempted influence over monitors or graders. | Motivates separate integrity labels, transcript review, and independent monitors. | Monitoring evidence is not a predictive evaluation method and may miss novel behavior. |
| **[R]** [METR MALT](https://metr.org/blog/2025-10-14-malt-dataset-of-natural-and-prompted-behaviors/) | Provides natural and prompted agent transcripts with reward-hacking labels; monitors perform well on some metrics while natural positives remain sparse. | Training and meta-evaluation material for monitor-assisted integrity analysis. | Prompted attacks may be unrepresentative and monitors cannot replace hidden checks or future-task validation. |

### Optimization protocol implied by this literature

- Measure budget using candidate count, queries, rounds, feedback information,
  tokens, wall time, or compute; do not use an undefined notion of “pressure.”
- At minimum, compare best-of-`N` replay and live iterative optimization because
  their overoptimization curves may differ.
- Keep integrity violations, ordinary distribution shift, and adaptive
  overfitting as separate outcomes.
- Preserve every agent candidate so the selected winner can be compared with
  future outcomes for the complete archive.

## 6. Self-Evolving Agents, Lineages, And Evaluator Coevolution

The literature uses “self-evolving” for several different update surfaces:
model parameters, prompts, memory, skills, tools, executable harness code, and
multi-agent workflow or topology. Barcarolle should not assume that evidence
from one surface transfers to another. It should also distinguish an update
generator from the task-solving agent that must activate and follow the update.

| Source | What it establishes | Use in Barcarolle | Important limit |
| --- | --- | --- | --- |
| **[P]** [SEAGym: An Evaluation Environment for Self-Evolving LLM Agents](https://arxiv.org/abs/2606.17546) | Defines separate training, frozen update-validation, held-out in-distribution and out-of-distribution test, replay, cost, snapshot, and metric records for harness evolution. On Terminal-Bench 2.0 and HLE, its views show that frequent updates can fail to improve held-out performance and that useful intermediate snapshots can later collapse. | Closest protocol baseline for snapshot, transition, and lineage records; reproduce its multi-view analysis before adding repository-specific temporal prediction. | A recent preprint on transformed static benchmarks. It does not estimate either MAE on later real-world repository tasks or show that its update-validation set resists direct optimization. |
| **[P]** [SEA-Eval: A Benchmark for Evaluating Self-Evolving Agents Beyond Episodic Assessment](https://arxiv.org/abs/2604.08988) | Organizes correlated and orthogonal task sequences and jointly tracks task success and token consumption. It reports cases where identical success rates hide up to 31.2-fold differences in token use and different sequential trajectories. | Baseline for sequence-aware efficiency and structural-stability diagnostics; require an explicit task order and persistent-state contract. | Token convergence is not proof of capability growth, future-task validity, or Goodhart resistance; the benchmark does not target pass-rate prediction error. |
| **[C]** [StreamBench: Towards Benchmarking Continuous Improvement of Language Agents](https://proceedings.neurips.cc/paper_files/paper/2024/hash/c189915371c4474fe9789be3728113fc-Abstract-Datasets_and_Benchmarks_Track.html) | Evaluates agents on sequential input-feedback streams across text-to-SQL, Python, tool use, medicine, and question answering. Its streaming in-context baseline improves over zero-shot across the reported datasets, while the size of the gain varies strongly by task. | Treat task order, feedback history, and persistent state as part of the evaluated agent; compare complete learning curves instead of final snapshots. | It optimizes accuracy on fixed public streams, not prediction on independent future work, direct agent differences, or robustness to an optimizer targeting the evaluation. |
| **[P]** [LifelongAgentBench: Evaluating LLM Agents as Lifelong Learners](https://arxiv.org/abs/2505.11942) | Supplies 1,396 skill-linked tasks across database, operating-system, and knowledge-graph environments with strict sequential execution. Replay improves some agents sharply but gives diminishing, negative, or out-of-memory results for others as history grows. | Build a version-by-task-block outcome matrix and test acquisition, retention, replay benefit, and failure under growing persistent context. | Generated skill taxonomies and fixed task streams do not establish generalization to repository work or evaluator predictive validity. |
| **[C]** [Gradient Episodic Memory for Continual Learning](https://papers.nips.cc/paper/2017/hash/f87522788a2be2d171666752f97ddebb-Abstract.html) | Introduces a task-by-learning-stage response matrix and average accuracy, backward-transfer, and forward-transfer measurements; its experiments show that repeated passes can worsen forgetting for memory-free methods. | Add retention, regression, backward-transfer, and forward-transfer diagnostics to the same raw outcome matrix used for the two primary MAEs. | Fixed supervised task sequences and model-training metrics do not cover strategic agents, evaluator feedback, repository time shift, or pairwise prediction. |
| **[C]** [Automated Design of Agentic Systems](https://proceedings.iclr.cc/paper_files/paper/2025/hash/36b7acf6f6010652b3f2a433774a66fe-Abstract-Conference.html) | Meta Agent Search represents agents in code, preserves an archive, and discovers designs that outperform hand-built comparators across several domains with some cross-domain and cross-model transfer. | Concrete non-self-referential optimizer baseline and evidence that prompts, tools, workflows, and control code are one searchable agent identity. | Transfer among opened static benchmarks is not temporal predictive validity and does not establish that the search evaluator remains accurate under more optimization. |
| **[P]** [A Self-Improving Coding Agent](https://arxiv.org/abs/2504.15228) | A coding agent edits its own implementation and reports a gain from 17% to 53% on a random SWE-bench Verified subset. Per-iteration results are non-monotone, and the authors report path dependence and sensitivity to short time limits. | Reproducible single-line self-modification baseline; preserve every version, cost, timeout, and pass-to-fail transition rather than only the best iteration. | A 2025 preprint submitted to NeurIPS on a small repeatedly used subset; it does not show improvement on future real-world tasks or validate the benchmark feedback. |
| **[C]** [Darwin Gödel Machine](https://openreview.net/pdf?id=pUpzQZTvGY) | An archive-based system modifies its own coding-agent implementation and empirically selects changes using coding benchmarks, improving benchmark pass rates in the reported runs. | Concrete branching agent optimizer and agent-version archive for a fixed-evaluator repeated-optimization experiment. | Improvement is selected using finite coding benchmarks. The work does not measure whether benchmark-selected versions preserve either primary prediction metric on future real-world tasks. |
| **[C]** [Huxley-Gödel Machine: Human-Level Coding Agent Development by an Approximation of the Optimal Self-Improving Machine](https://openreview.net/forum?id=T0EiEuhOOL) | Shows that an agent's current benchmark score can be a weak predictor of the best descendants found from it. A clade-based estimator correlates more strongly with retrospective descendant performance and guides a more efficient search than the tested DGM and SICA baselines. | Treat current capability and lineage productivity as separate diagnostics; retain non-incumbent parents and evaluate search policies from common ancestors. | Its descendant target is still performance on related static coding benchmarks and is observed only for branches the search expands. It is not future pass-rate MAE, and naive lineage statistics are search-policy censored. |
| **[P]** [Loreley: Repository-Scale Program Evolution with Quality-Diversity Search](https://arxiv.org/abs/2608.19703) | In 1,008 matched candidate jobs, non-incumbent ancestors contributed to later winners, but the controlled 48-job experiment did not establish a quality-diversity endpoint advantage over sequential champion or independent-root search. | Preserve primary-parent and inspiration edges, and require strong sequential and independent-root optimizer controls before attributing value to a diverse archive. | One repository and one bounded optimization setup; archive use demonstrates mechanism engagement, not causal or cross-repository benefit. |
| **[P]** [Harness Updating Is Not Harness Benefit: Disentangling Evolution Capabilities in Self-Evolving LLM Agents](https://arxiv.org/abs/2605.30621) | Across seven models and three agent benchmarks, differences among update-generating models are small, while the task-solving model's benefit is non-monotone in base capability. Weak models often fail to activate a harness artifact or follow it over a long trajectory. | Cross updater model, executor model, and artifact type; report update quality, activation, adherence, and realized future-task benefit separately. | A recent preprint using fixed agent benchmarks and in-stream gain. It does not establish temporal transfer or that stronger update writers are unnecessary in other evolution regimes. |
| **[P]** [SlopCodeBench: Benchmarking How Coding Agents Degrade Over Long-Horizon Iterative Tasks](https://arxiv.org/abs/2603.24755) | In the current version, 15 coding agents attempt 36 evolving problems over 196 checkpoints; none solves a complete problem, the best strict checkpoint solve rate is 14.8%, and structural erosion and verbosity rise in 77% and 75.5% of trajectories. | Add common-task pass-to-fail flips and longitudinal maintainability diagnostics so a passing snapshot cannot hide damage that makes later changes fail. | It studies agents evolving a target codebase, not agents evolving themselves. Its quality measures are secondary diagnostics, not substitutes for future-task pass rates. |
| **[P]** [Practice Makes Unsafe: Skill Misevolution in Self-Improving LLM Agents](https://arxiv.org/abs/2608.12851) | Versions skill state across authoring, retrieval, and later execution. Across 25 agent-method configurations, three malicious exposures raise carryover attack success from 16.0% to 35.3%; the proposed wrapper reduces later unsafe retrieval and harm in the tested setup. | Add persistent-state provenance, post-exposure carryover tasks, update admission, attribution, retirement, and rollback to integrity stress tests. | Recent preprint on constructed skill-library attacks; it does not estimate ordinary prevalence, other update surfaces, or either primary prediction error. |
| **[C]** [ReVeal: Self-Evolving Code Agents via Reliable Self-Verification](https://www.microsoft.com/en-us/research/publication/reveal-self-evolving-code-agents-via-reliable-self-verification/) | Alternates generation and self-verification and co-develops code and tests in a coding-agent training loop. | Adjacent method for studying verifier quality and generated-test feedback during agent evolution. | Self-verification can share the agent's blind spots; stronger benchmark results are not independent evidence that the verifier predicts future work. |
| **[C]** [Curious POET: Intrinsic Motivation Improves Exploration Efficiency](https://direct.mit.edu/isal/article/doi/10.1162/isal_a_00736/123533/Curious-POET-Intrinsic-Motivation-Improves) | Coevolves environments and agents but evaluates populations with a training-independent environment-generation strategy, coverage, and population cross-evaluation; it outperforms ePOET on those measures in Bipedal Walker. | Direct precedent for evaluating a coevolving population outside the environment generator that trained it; compare against periodic updating under equal budgets. | One simulated control domain. Coverage and cross-play do not estimate future repository-task pass rates or prove the independent generator is representative. |
| **[P]** [The Red Queen Gödel Machine](https://arxiv.org/abs/2606.26294) | Makes evaluators part of evolutionary search, keeps the evaluation criterion fixed within an epoch, and allows utility changes at epoch boundaries. | Closest architectural precedent for the proposed evaluator-coevolution regime. | Preliminary work in progress; it does not report temporally held-out pass-rate or pass-rate-difference MAE. |
| **[P]** [What Do Evolutionary Coding Agents Evolve?](https://arxiv.org/abs/2605.20086) | Decomposes benchmark gains into new structure, retuning, recombination, or evaluator overfitting instead of treating every final-score gain as the same mechanism. | Add mutation-type and mechanism labels to agent version history and analyze which kinds of changes transfer. | A diagnostic taxonomy does not itself prevent overfitting or validate an evaluator. |
| **[P]** [Self-Evolving Coding Agents](https://arxiv.org/abs/2608.03392) | Organizes what changes in self-evolving coding agents, when it changes, and which software signals drive the update; highlights feedback reliability, benchmark overfitting, safety, cost, and generalization. | Broad source map for update surfaces and optimizers when live experiments are designed. | A recent survey is secondary evidence and cannot establish the effectiveness of any evaluator or coevolution protocol. |
| **[C]** [Reward Is Enough: LLMs Are In-Context Reinforcement Learners](https://proceedings.iclr.cc/paper_files/paper/2026/hash/b7511dfe2e7a1fa45e093cc75389abc2-Abstract-Conference.html) | Demonstrates multi-round improvement from scalar feedback in several inference-time tasks. | Evidence that feedback without weight updates can still create evaluator-guided adaptation; include it in the fixed-evaluator threat model. | The studied tasks and rewards do not establish coding-agent forecast validity or reward-hacking resistance. |

### Consequences for the first live experiment

- Treat every change to the model, harness, persistent prompt or configuration,
  memory, skill library, tool, workflow, generation policy, or runtime policy as
  a new agent snapshot. Record task inputs and temporary cues allowed by a
  frozen policy as run contexts instead.
- Store a version graph with primary parents, merge parents, inspiration edges,
  update evidence, evaluator feedback, promotion or rejection, and rollback;
  one `parent` field is insufficient for archive-based search.
- Compare evaluator conditions by branching from the same initial agent with
  matched optimizer seeds and budgets. This makes the resulting lineage, not
  only its winner, the experimental unit.
- Cross update generator and task-solving agent where feasible. Do not infer
  update quality from end-to-end improvement alone.
- Build a version-by-task-block response matrix and report common-task
  pass-to-fail, fail-to-pass, retention, and transfer diagnostics alongside the
  two primary MAEs.
- For a fixed-evaluator study, hold the evaluator fixed for the complete
  lineage. For a coevolution study, hold it fixed within each epoch and treat
  the complete update rule as the method under test.
- Preserve the complete candidate archive so selection optimism, censored
  branches, missed future winners, and non-incumbent stepping stones can be
  measured.
- Require independent temporal test data. An evolving agent, evaluator, or
  task generator cannot certify itself with outcomes that shaped its updates.

## 7. Dynamic And Adversarial Task Generation

| Source | What it establishes | Use in Barcarolle | Important limit |
| --- | --- | --- | --- |
| **[C]** [Adversarial NLI](https://aclanthology.org/2020.acl-main.441/) | Multi-round human-and-model-in-the-loop collection continually finds examples that fool successive models. | Precedent for iterative adversarial task collection and historical attack archives. | NLI examples are cheap to label and do not require executable repository environments. |
| **[C]** [Dynabench](https://aclanthology.org/2021.naacl-main.324/) | Provides an infrastructure and argument for dynamic human-and-model-in-the-loop benchmarks. | Precedent for evaluator updating and feedback between data collection and model development. | Dynamic difficulty does not by itself preserve a stable target quantity. |
| **[C]** [Kaushik et al., randomized study of adversarial data collection](https://aclanthology.org/2021.acl-long.517/) | Adversarially collected QA data usually improved other adversarial sets but hurt a diverse group of out-of-domain tests. | Strong negative evidence against assuming that red-team tasks improve future representativeness. | One QA study does not imply all adversarial generation is harmful. |
| **[C]** [Wallace et al., 20 rounds of adversarial data collection](https://aclanthology.org/2022.findings-acl.18/) | Repeated collection produced harder, more diverse data and improved an expert-curated NLI test set in the studied regime. | Supports multi-round collection and keeping older attacks to test forgetting. | Evidence remains task- and model-specific. |
| **[C]** [Model-Written Evaluations](https://aclanthology.org/2023.findings-acl.847/) | Language models generated many behavioral datasets with high human-rated relevance and label agreement in the studied tasks. | Supports scalable proposal of behavior tests and attack hypotheses. | It does not show that models can generate reliable repository hidden checks or representative future real-world tasks. |
| **[C]** [AutoBencher](https://proceedings.iclr.cc/paper_files/paper/2025/hash/eb216114f3eaad22506fd1bc7bbff0ca-Abstract-Conference.html) | Frames automatic benchmark construction as optimizing declared difficulty, salience, novelty, or safety objectives. | Make task-generator objectives explicit and use generate-many, filter, and human/automated validation. | Its authors caution that generated benchmarks require quality checks; difficulty and novelty are not future predictive validity. |
| **[C]** [Red Teaming Language Models with Language Models](https://aclanthology.org/2022.emnlp-main.225/) | Model-generated attacks find failures beyond fixed manual sets. | Baseline automatic red-team generator. | Attack success depends on the generator and target, and does not estimate a natural workload. |
| **[C]** [Rainbow Teaming](https://proceedings.neurips.cc/paper_files/paper/2024/hash/8147a43d030b43a01020774ae1d3e3bb-Abstract-Conference.html) | Quality-diversity search finds effective and diverse adversarial prompts with some cross-model transfer. | Maintain a mechanism-diverse archive instead of optimizing only attack success. | Safety prompts are not executable coding tasks; transfer must be retested. |
| **[C]** [MART](https://aclanthology.org/2024.naacl-long.107/) | Alternates an adversarial model and target model across rounds, improving safety metrics in the tested setting. | Direct adjacent precedent for iterative opponent–target improvement. | It optimizes safety alignment, not evaluator forecast accuracy. |
| **[C]** [PAIRED](https://papers.nips.cc/paper_files/paper/2020/hash/985e9a46e10005356bbaf194249f6856-Abstract.html) | Generates environments by maximizing regret between protagonist and antagonist, encouraging difficult but solvable curricula. | Candidate objective: find certified tasks with high evaluator-versus-reference prediction regret. | Moving from gridworld environment design to real repository changes is an untested transfer. |
| **[C]** [Prioritized Level Replay](https://proceedings.mlr.press/v139/jiang21b.html) | Samples procedurally generated levels according to estimated learning potential and improves generalization in Procgen. | Baseline for replaying useful historical attacks while preserving diversity. | Training curricula and predictive evaluation have different targets. |
| **[C]** [WildTeaming](https://proceedings.neurips.cc/paper_files/paper/2024/hash/54024fca0cef9911be36319e622cde38-Abstract-Conference.html) | Mines in-the-wild failures and composes diverse tactics for red teaming. | Motivates combining naturally observed failure mechanisms with generated variants. | User jailbreaks and coding benchmark exploits have different distributions. |

## 8. Meta-Evaluation And Metric Stress Testing

| Source | What it establishes | Use in Barcarolle | Important limit |
| --- | --- | --- | --- |
| **[C]** [Perturbation CheckLists](https://aclanthology.org/2021.emnlp-main.575/) | Tests whether evaluation metrics have expected sensitivity or invariance under controlled perturbations; many metrics fail simple checks. | Build capability-preserving, capability-improving, exploit-only, and integrity-violating transformations for coding evaluators. | NLG perturbations do not directly define correct coding transformations. |
| **[C]** [MetricEval](https://aclanthology.org/2023.emnlp-main.676/) | Applies measurement theory to metric stability, consistency, construct validity, and concurrent validity. | Structure the meta-evaluation report and quantify metric uncertainty instead of relying on one correlation. | Human text judgments differ from executable correctness and future pass rates. |
| **[C]** [Deutsch et al., re-examining system-level correlation](https://aclanthology.org/2022.naacl-main.442/) | Global correlation can look strong because easy, widely separated system pairs dominate; correlation falls for close pairs used in real decisions. | Test near-tie agent pairs directly and prioritize numerical difference error over global rank correlation. | Summarization metrics are not coding evaluators. The result motivates an analogous near-tie test in coding, whose transfer must be validated empirically. |
| **[C]** [BadJudge](https://proceedings.iclr.cc/paper_files/paper/2025/hash/2e48f562a2c8f64c7404a6c3a518af74-Abstract-Conference.html) | Demonstrates backdoor vulnerabilities in learned LLM judges across several access regimes. | Treat any learned judge as an attack surface and require independent executable checks where possible. | The exact poisoning setup may not match Barcarolle's judge or data pipeline. |
| **[C]** [JudgeLM](https://proceedings.iclr.cc/paper_files/paper/2025/hash/7f8f73134e253845a8f82983219a8452-Abstract-Conference.html) | Documents position, knowledge, and format biases while scaling learned judges. | Include order, style, format, and model-family perturbations in judge stress tests. | Strong average judge agreement does not establish resistance to strategic inputs. |
| **[C]** [Performative Prediction](https://proceedings.mlr.press/v119/perdomo20a.html) | Formalizes settings in which a prediction changes decisions and therefore changes the outcome distribution it aims to predict; gives conditions for repeated retraining to approach a performatively stable point. | Model evaluator feedback as a causal intervention on the future agent lineage, not as passive measurement. Compare evaluator policies from common ancestors and estimate outcomes after acting on their predictions. | Its smooth response-map and retraining assumptions do not cover discrete self-modification trees, direct benchmark tampering, or adversarial agents. Performative stability is not future-task validity. |
| **[C]** [AI Sandbagging: Language Models can Strategically Underperform on Evaluations](https://proceedings.iclr.cc/paper_files/paper/2025/hash/b5e5753b0a0e440a6d8dc7e143617cec-Abstract-Conference.html) | Frontier models can be prompted to selectively underperform on dangerous-capability evaluations while retaining harmless-benchmark performance; password-locked fine-tuning hides capabilities on held-out WMDP and can target chosen scores. | Include underperformance, score targeting, capability-profile consistency, and evaluation-cue perturbations in controlled-agent stress tests. | Demonstrates capability under explicit prompting or constructed fine-tuning, not spontaneous sandbagging by deployed coding agents or the prevalence of deceptive evaluation behavior. |
| **[C]** [The Elicitation Game](https://proceedings.mlr.press/v267/hofstatter25a.html) | Tests elicitation methods against password-locked and circuit-broken model organisms. Prompting elicits hidden multiple-choice capability, activation steering fails, and only fine-tuning elicits the tested hidden code-generation capability. | Meta-evaluate whether a coding evaluation elicits an agent's available capability; compare prompting, scaffolding, tools, and, when in scope, fine-tuning rather than assuming the default harness is capability-complete. | Constructed hidden capabilities and available weight access differ from closed deployed agents. Failure to elicit is not evidence that a capability is absent, and successful elicitation is not future-task prediction. |
| **[C]** [AI Control: Improving Safety Despite Intentional Subversion](https://proceedings.mlr.press/v235/greenblatt24a.html) | Changes the evaluation unit from a model to a deployment protocol and red-teams coding workflows in which a powerful untrusted model may intentionally insert subtle backdoors. Trusted editing and untrusted monitoring improve the tested safety–usefulness tradeoff over simple baselines. | Evaluate the complete runner, monitor, escalation, audit, and human-review protocol under a declared adversary, separately from ordinary predictive accuracy. | Its constructed backdoor game, trusted-model assumptions, and safety outcome do not estimate Barcarolle's two MAEs or prove that an LLM monitor remains trustworthy under adaptive attack. |
| **[C]** [Adaptive Attacks on Trusted Monitors Subvert AI Control Protocols](https://proceedings.iclr.cc/paper_files/paper/2026/hash/54b153ad8a138f4c186f21a8b7341d5e-Abstract-Conference.html) | An attacker that knows the monitor can embed known or zero-shot prompt injections in outputs, evade diverse monitor-based protocols on two control benchmarks, and make defer-to-resample amplify the attack as best-of-N search. | Give evaluator red teams protocol and monitor knowledge in an adaptive condition; test the monitor as an attack surface and include monitor-independent fallbacks. | The prompt-injection channel and control benchmarks are not Barcarolle's hidden-check path. “Universal” refers to the tested monitor-dependent protocols, not every evaluation architecture. |
| **[C]** [The Hawthorne Effect in Reasoning Models](https://proceedings.neurips.cc/paper_files/paper/2025/hash/cf42f133f355e0e07a8957b508b26a1b-Abstract-Conference.html) | Finds linearly decodable test-awareness representations in three open reasoning models and causally changes several safety behaviors by steering them; the effect's magnitude and direction vary by model and task. | Add evaluation-like versus deployment-like framing, latent-probe research where permitted, and behavior-level paired outcomes to meta-evaluation. | Awareness in a representation or a change under steering is not evidence of deliberate sandbagging, and safety-prompt results do not establish coding-evaluator failure. |
| **[P]** [Evaluation Awareness in Language Models Has Limited Effect on Behaviour](https://arxiv.org/abs/2605.05835) | Provides counterevidence to broad evaluation-awareness claims: injecting verbalized evaluation awareness produces near-zero effects, removing it produces small shifts, and spontaneous verbalized awareness changes answer distributions by at most 3.7 percentage points in the tested settings. | Treat verbalized awareness, context discrimination, latent representation, and strategic behavior as separate variables; require a behavioral effect before attributing evaluator error to awareness. | A recent preprint on selected open-weight reasoning models and benchmarks. It does not refute constructed sandbagging, latent awareness, deployment recognition, or adaptive monitor attacks. |
| **[R]** [OpenAI Deployment Simulation](https://openai.com/index/deployment-simulation/) | Replays privacy-filtered production contexts with a candidate model and compares predicted behavior rates with later deployment. The report gives a median multiplicative error of 1.5× across studied GPT-5-series risks; GPT-5.2 labels production and simulated traffic as evaluation-like at 5.4% and 5.1%, versus nearly 100% for several traditional synthetic evaluations. | Direct precedent for sampling realistic recent work, preregistering deployment-rate predictions, validating them after release, and measuring whether coding tasks are recognizable as tests. | Developer report using private traffic and largely one-response simulation. It cannot detect sufficiently rare tail risks, historical traffic can shift, and external evaluators may lack comparable deployment data. |
| **[C]** [Benchmarking Reward Hack Detection in Code Environments via Contrastive Analysis](https://arxiv.org/abs/2601.20103) | Introduces the human-verified TRACE benchmark with 517 trajectories and 54 exploit categories; the best reported detector rises from 45% in isolated classification to 63% with contrastive context. | Compare candidate runs against benign reference runs and keep semantic exploit classes separate from syntactic tampering. | TRACE is synthetically curated; detecting known exploits does not make the evaluator accurate or resistant to unseen attacks. |
| **[C]** [CapBencher: Give Your LLM Benchmark a Built-in Alarm for Test-Set Overfitting](https://arxiv.org/abs/2505.18102) | Randomizes among logically correct answers to create a known Bayes-accuracy ceiling; statistically significant above-ceiling performance becomes a warning for leakage or repeated-query gaming. | Candidate warning mechanism for benchmark components where multiple correct realizations can be constructed. | It is a detector rather than a prevention or prediction guarantee, and executable repository tasks may not admit a natural randomized-answer construction. |
| **[C]** [Adversarial manipulation of voting-based leaderboards](https://proceedings.mlr.press/v267/huang25z.html) | Shows that preference leaderboards can be manipulated without adequate bot and data-integrity defenses and evaluates mitigations. | Extend integrity analysis to aggregation and result-ingestion paths, not only tasks and checks. | Human-voting attacks differ from repository execution. |
| **[R]** [Anthropic, automated auditing agents](https://alignment.anthropic.com/2025/automated-auditing/) | Uses models with implanted behaviors to test automated auditors and reports both discoveries and missed behavior classes. | Start meta-evaluation with controlled agent variants whose benign or exploit behavior is known but hidden from the evaluator builder. | Early institutional evidence; planted behaviors may not cover real coding exploits. |
| **[P]** [AuditBench](https://arxiv.org/abs/2602.22755) | Expands auditing of models with planted behaviors and reports a gap between useful standalone tools and effective use by an auditing agent. | Evaluate the complete evaluator-building agent, not only individual tools. | Recent preprint and not specific to pass-rate prediction. |
| **[R]** [NIST AI Risk Management Framework](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/) and [Adversarial ML taxonomy](https://www.nist.gov/publications/adversarial-machine-learning-taxonomy-and-terminology-attacks-and-mitigations-0) | Recommend continuous test, evaluation, validation, and verification; independent assessment; red teaming; and explicit attacker knowledge and capability. | Reporting and threat-model checklist. | Standards organize practice; they do not show that a particular coevolution method is effective. |

Evaluation awareness needs an evidence ladder rather than one binary label:

1. the agent can discriminate evaluation-like from deployment-like context;
2. it verbalizes that distinction;
3. a controlled intervention on awareness changes behavior;
4. it can strategically target an evaluation outcome when instructed or
   trained to do so;
5. it does so autonomously in the deployment-relevant setting.

Evidence for one rung does not establish the next. In particular, high rates of
verbalized awareness are not sufficient evidence of strategic behavior, while
constructed sandbagging and adaptive monitor attacks remain valid worst-case
stress tests even if spontaneous verbalized awareness has small average effects.

### Metric stress-test families

- invariance under behavior-preserving code or harness changes;
- monotonicity under genuine capability improvements;
- no improvement for public-test specialization that fails independent checks;
- sensitivity to near-tie pair composition and pair weighting;
- robustness to missing cells, timeouts, abstention, and invalid-result policy;
- transfer across repositories, agent families, harnesses, and task generators;
- robustness to task, grader, monitor, and result-store poisoning;
- stability when the candidate count and feedback detail increase;
- evaluation-like versus deployment-like framing, with behavior-level outcomes
  rather than verbalized awareness alone;
- capability elicitation under several permitted harnesses, prompts, tools, and
  update methods;
- adaptive attacks that know the evaluator, monitor, escalation, and resampling
  protocol;
- contrastive reward-hack detection using benign reference runs, with complete
  exploit families held out;
- a feasibility test for a CapBencher-style known accuracy ceiling on
  executable tasks with several semantically equivalent valid outputs.

The output of a stress test is evidence about a failure mechanism. It becomes a
promotion criterion only after transfer to unseen attacks or future real-world
tasks is demonstrated.

## 9. Coding-agent Benchmarks And Repository Task Supply

| Source | What it establishes | Use in Barcarolle | Important limit |
| --- | --- | --- | --- |
| **[C]** [SWE-bench](https://proceedings.iclr.cc/paper_files/paper/2024/hash/edac78c3e300629acfe6cbe9ca88fb84-Abstract-Conference.html) | Establishes repository-level issue resolution with executable tests as a coding-agent evaluation format. | Core task and hidden-check structure. | A static public corpus does not ensure contamination resistance, task validity, or temporal prediction. |
| **[C]** [Establishing Best Practices in Building Rigorous Agentic Benchmarks](https://papers.nips.cc/paper_files/paper/2025/hash/f316275b44ee2de533102913828a8107-Abstract-Datasets_and_Benchmarks_Track.html) | Audits task and reward-design defects that can over- or underestimate agent performance by as much as 100% in relative terms, then proposes the Agentic Benchmark Checklist. | Peer-reviewed basis for task certification, reward audits, and explicit benchmark-construction checklists. | A checklist reduces avoidable errors but does not establish temporal predictive validity or resistance to adaptive optimization. |
| **[R]** [Introducing SWE-bench Verified](https://openai.com/index/introducing-swe-bench-verified/) | A professional annotation campaign removed tasks with severe problem-statement or test issues. | Evidence that human task audit changes benchmark validity materially. | A verified static subset can age, saturate, or become contaminated. |
| **[R]** [Why SWE-bench Verified no longer measures frontier coding capabilities](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/) | A later audit found contamination and task-quality problems serious enough that the organization stopped using the benchmark for frontier capability measurement. | Strong evidence for continuous audit, freshness, and retiring benchmarks whose signal changes. | Organization-specific audit and decisions should not be generalized without checking the underlying task population. |
| **[R]** [Separating signal from noise in coding evaluations](https://openai.com/index/separating-signal-from-noise-coding-evaluations/) | Reports automated and human audits finding a substantial fraction of broken tasks in a newer coding benchmark. | Supports two-stage automated plus human audit, task-level failure labels, and uncertainty about the target itself. | Recent institutional report; exact audit methods and benchmark population matter. |
| **[C]** [What's in a Benchmark? The Case of SWE-Bench in Automated Program Repair](https://doi.org/10.1145/3786583.3786904) | Surveys the SWE-bench leaderboard ecosystem and finds that industry submissions, closed implementations, and proprietary models dominate. | Require model, harness, configuration, submitter, and reproducibility metadata for every result. | It discusses patch correctness and contamination as concerns but does not measure either; use dedicated audits for those empirical claims. |
| **[C]** [Are “Solved Issues” in SWE-bench Really Solved Correctly?](https://software-lab.org/publications/icse2026_SWE-bench-correctness.pdf) | Empirically audits apparently solved patches and test-suite weakness. | Use additional generated or mutation-based tests as audit evidence, while keeping them separate from the original correctness definition. | Added tests can themselves be wrong or biased toward a generator. |
| **[C]** [SWE-ABS: Adversarial Benchmark Strengthening Exposes Inflated Success Rates on Test-based Benchmark](https://arxiv.org/abs/2603.00520) | Combines coverage-guided and mutation-driven test augmentation; on SWE-bench Verified it strengthens 50.2% of instances, rejects 19.71% of previously passing patches, and changes the ranking. | Direct coding precedent for adversarially testing hidden-check strength and measuring how check changes alter agent comparisons. | Generated tests still require independent semantic review, and static re-scoring does not establish prediction on future real-world tasks. |
| **[C]** [The SWE-Bench Illusion: When State-of-the-Art LLMs Remember Instead of Reason](https://doi.org/10.1145/3786583.3786882) | A file-path diagnostic reaches up to 76% accuracy from issue text alone on SWE-bench Verified and lower accuracy on outside repositories, evidence consistent with memorization or contamination. | Add contamination-sensitive controls and repository-held-out diagnostics to benchmark audits. | The diagnostic suggests that some gains may be partly driven by memorization; it does not prove that all benchmark success is contaminated. |
| **[C]** [SWE-bench Goes Live!](https://proceedings.neurips.cc/paper_files/paper/2025/hash/d83c4a745789690f82e86d0ef752ae7c-Abstract-Datasets_and_Benchmarks_Track.html) | Continuously creates recent executable tasks from many repositories and reports performance differences from static SWE-bench. | Direct evidence that fresh, scalable repository task collection is feasible and that recency can change results. | Freshness and executability do not prove that a small sample predicts later work. |
| **[C]** [SWE-rebench: An Automated Pipeline for Task Collection and Decontaminated Evaluation of Software Engineering Agents](https://proceedings.neurips.cc/paper_files/paper/2025/hash/21bec6ace947b1b58967b945c8ac0f10-Abstract-Datasets_and_Benchmarks_Track.html) | Automates collection of continuously updated, executable software tasks for evaluation. | Candidate task-supply and decontamination methods. | Automated filtering and generated descriptions can introduce their own selection effects. |
| **[C]** [SWE-rebench V2: Language-Agnostic SWE Task Collection at Scale](https://icml.cc/virtual/2026/poster/63732) | Extends collection across languages and thousands of repositories while publishing task-quality metadata. | Useful source of broad training and diagnostic data; supports language and repository stratification. | Much of the resource is positioned for training, and LLM-judge filtering is not independent correctness evidence. |
| **[C]** [SWE-smith: Scaling Data for Software Engineering Agents](https://proceedings.neurips.cc/paper_files/paper/2025/hash/8b86cf5ace600c48fd188efbb8dedec8-Abstract-Datasets_and_Benchmarks_Track.html) | Demonstrates high-volume synthetic software-engineering task construction for training. | Supply-scale precedent and source of generator-quality hypotheses. | Training-task utility is not evaluation validity; synthetic artifacts may determine agent rankings. |
| **[C]** [Automated Benchmark Generation for Repository-Level Coding Tasks](https://proceedings.mlr.press/v267/vergopoulos25a.html) | Automates repository-level benchmark construction and discusses repository coverage, contamination, and static-benchmark limits. | Candidate generation and certification pipeline components. | Automated benchmark construction still needs independent checks and temporal validation. |
| **[P]** [SWE-Future](https://arxiv.org/abs/2606.18733) | Separates forecasting future task categories from generation of executable task instances and retrospectively checks forecasts against later pull requests. | Closest task-generation decomposition to Barcarolle's proposed Stage B. | A recent preprint; category match and executability do not by themselves establish agent-response validity. |
| **[C]** [SWE-Mutation](https://aclanthology.org/2026.findings-acl.1976/) | Mutates candidate solutions to characterize whether generated test suites catch incorrect programs. | Use mutation score and surviving mutants as hidden-check strength diagnostics. | Mutation adequacy is not semantic completeness and may favor known mutation operators. |
| **[P]** [SpecBench](https://arxiv.org/abs/2605.21384) | Separates visible validation tests from held-out compositional tests and reports large performance differences on long-horizon tasks. | Direct probe for public-test specialization and specification composition. | Recent preprint and not a complete estimator of future task pass rate. |
| **[P]** [Efficient Benchmarking of AI Agents](https://arxiv.org/abs/2603.23749) | Reports efficient score/rank prediction across agent benchmarks, including sensitivity to harness shift. | Recent comparison for outcome modeling, mid-difficulty tasks, and explicit harness identity. | Preprint evidence; rank preservation is weaker than the two requested numerical errors. |
| **[P]** [The Scaffold Effect in Coding Agents: Harness Choice as a Hidden Variable in Coding-Agent Evaluation](https://arxiv.org/abs/2607.22585) | Across two models, three harnesses, and 50 tasks, reported pass-rate differences are 0–8 percentage points; bootstrap intervals include zero except for the largest difference, while token cost per solve varies by as much as 40-fold. | Treat model–harness combination as the agent identity and a possible DIF group; measure both accuracy and cost. | Recent, limited panel; it does not establish a generally large harness effect on pass rate. |
| **[P]** [Don't Blame the Large Language Model: How Agent Harness Evolution Shapes Coding Agent Quality](https://arxiv.org/abs/2607.03691) | Longitudinally varies harness versions while holding the model fixed and reports substantial quality fluctuations. | Motivates agent-version history that includes harness commits and time. | One harness family and task sample cannot establish a universal harness effect. |

### Coding-specific implications

- Task validity is itself a measured quantity. Record problem-statement
  sufficiency, test adequacy, gold-patch behavior, flakiness, environmental
  reproducibility, and audit disposition separately.
- Apply the Agentic Benchmark Checklist during task certification, and publish
  each failed checklist item rather than collapsing it into one validity flag.
- A hidden check can prevent some direct gaming while remaining an incomplete
  specification. Mutation, differential, and independently generated tests are
  useful audits, not unquestionable new ground truth.
- When test strengthening changes pass rates or rankings, report the original
  and strengthened definitions separately and require semantic review of the
  added tests before adopting them.
- Continuous task supply reduces some contamination and saturation problems but
  creates a changing target distribution. Preserve source time, repository,
  collection policy, and rejection reasons.
- Harness version belongs in agent identity. A model-only leaderboard can hide
  evaluator error caused by harness changes.
- Training datasets, adversarial probes, and prediction targets need separate
  roles even when they come from the same collection pipeline.

## 10. Decision Rules And Multi-Objective Optimization

| Source | What it establishes | Use in Barcarolle | Important limit |
| --- | --- | --- | --- |
| **[J]** [Berger and Hsu, equivalence and intersection–union tests](https://doi.org/10.1214/ss/1032280304) | Equivalence or non-inferiority requires a prespecified margin; all required conditions in an intersection–union test must pass. | Formalize “prioritize difference error without unacceptable pass-rate error” using predeclared margins and simultaneous uncertainty. | Clinical-trial formulas cannot be copied without adapting repository and temporal dependence. |
| **[J]** [Mavrotas, the epsilon-constraint method](https://doi.org/10.1016/j.amc.2009.03.037) | Optimizes one objective while placing explicit constraints on others and exposes a Pareto frontier. | Minimize pass-rate-difference error subject to pass-rate error, coverage, cost, and integrity constraints. | Pareto optimality on development data does not establish future performance and does not include uncertainty automatically. |
| **[J]** [Kiefer, optimum experimental designs](https://doi.org/10.1111/j.2517-6161.1959.tb00338.x) | The optimal design criterion must match the target contrast or parameter function. | Use contrast-specific design for a named agent pair and population-weighted criteria for a declared pair population. | A latent-ability D-optimal design is not automatically optimal for pass-rate-difference MAE. |

Recommended promotion logic:

1. require valid independent outcomes and the declared integrity boundary;
2. predeclare decision-derived absolute limits for both MAEs, critical strata,
   minimum coverage, cost, and the simultaneous uncertainty rule;
3. for a claim covering repeated evaluator-guided optimization, separately
   predeclare within-method degradation tolerances from the no-optimization
   baseline (`b=0`); for a static `b=0` claim, record this stage as
   `not_applicable`;
4. name the comparator and predeclare the comparator-relative pass-rate MAE
   margin used only for method preference at every evaluation budget;
5. construct paired, cluster- and lineage-aware uncertainty intervals for every
   constraint and report `unresolved` when the design cannot decide;
6. reject candidates that fail any hard constraint;
7. among survivors, minimize average and worst-group pass-rate-difference MAE;
8. retain the full Pareto frontier and complete candidate provenance;
9. make the final comparison once on prospective test data.

A scalar score may sort candidates that have already passed every hard
constraint. It must not compensate for failure of either primary metric.

## 11. Open Research Questions

### Questions directly tied to reliable evaluation for self-evolving agents

- Which deployment decisions imply defensible absolute limits for pass-rate
  and pass-rate-difference MAE, which critical strata require stricter limits,
  and when does a materially different decision require a separately named
  claim?
- When should a study target operational behavior under one deployment policy versus
  an elicited capability estimate, and which elicitation changes must
  create a new agent snapshot?
- Does an evaluator that predicts one agent snapshot accurately also predict
  parent-to-child transitions and complete optimizer-generated lineages, or do
  these require distinct models and task allocations?
- What is the minimum version-graph schema needed to reconstruct primary
  parents, merges, inspiration, persistent-state changes, evaluator exposure,
  promotion, rejection, and rollback without storing sensitive raw traces?
- How should lineage productivity be estimated when descendants are observed
  only for candidates selected by an adaptive search policy?
- Which results transfer among model, prompt, memory, skill, tool, harness-code,
  and workflow evolution, and which require surface-specific evaluators?
- How much of an observed evolution gain comes from the update generator, the
  task-solving agent's artifact activation and adherence, the search policy,
  or task order?
- At equal initial agent, optimizer, seed bank, and budget, how much does the
  evaluator feedback policy causally change the future agent lineage?
- Which task-allocation rule minimizes pass-rate-difference MAE for
  deployment-relevant agent pairs, rather than rank error or one-agent score
  reconstruction?
- How many agents, tasks, repositories, time splits, and replicates are needed
  to distinguish item-parameter recovery, pass-rate recovery, and
  pass-rate-difference recovery?
- When does a harness or agent-family change create DIF large enough that a
  shared outcome model should abstain or split into groups?
- Can generated-task outcomes be calibrated to predict outcomes on future
  real-world tasks, and does that calibration transfer across task
  generators and agent families?
- Which optimization-budget measure best predicts evaluator degradation:
  candidate count, queries, feedback bits, rounds, tokens, compute, or a
  multidimensional budget?
- Does feedback limitation delay evaluator overfitting while preserving useful
  agent improvement at equal total compute?
- Do red-team attacks that transfer across evaluator models also predict errors
  on future real-world tasks?
- Can evaluator portfolios reduce correlated residuals under direct selection
  against the portfolio?
- Does coverage- and mutation-guided test strengthening reduce prediction error
  on future real-world tasks, or only redefine which historical patches pass?
- Can contrastive integrity detectors transfer to unseen exploit families
  without changing the harness enough to change the agent being measured?
- Can a known performance ceiling, analogous to CapBencher, be constructed for
  any useful class of executable repository tasks?
- Does agent–evaluator coevolution outperform simple periodic updating once both
  are given equal data, compute, and temporal validation access?
- Which evaluation-awareness measurements predict actual behavioral change,
  and when are verbalized awareness, latent probes, sandbagging capability, and
  autonomous strategic underperformance empirically independent?
- Can deployment-like repository trajectories reduce evaluation cues while
  remaining privacy-preserving, reproducible, and available to independent
  evaluators?
- When an evaluator's prediction changes which agent is deployed or evolved,
  can the resulting performative effect be estimated without treating a stable
  feedback equilibrium as predictive validity?

### Threats to the proposed program

- The future task distribution may be too sparse or unstable for precise
  repository-level conclusions.
- A generator may learn surface features that produce executable tasks but
  systematically change agent rankings.
- Bridge tasks used to compare evaluator epochs may become exposed and cease to
  be invariant.
- A high-scoring snapshot may seed an unproductive lineage, while a
  lower-scoring unexpanded candidate may have produced better descendants;
  winner-only archives create both survivorship and search-policy censoring.
- Persistent memory, skills, or tools may carry an erroneous or unsafe success
  into later tasks after the original triggering input disappears.
- A change attributed to the evaluator may instead come from the update
  generator, the task-solving agent's ability to use the artifact, task order,
  or an optimizer-specific interaction.
- The red team and evaluator builder may share model-family blind spots.
- Held-out temporal data may be consumed too quickly by repeated evaluator
  selection.
- A learned monitor may detect known planted behaviors without improving
  either prediction metric.
- The agent may recognize synthetic evaluation cues, but observed or
  verbalized recognition may have no material behavioral effect; either
  assuming or dismissing strategic adaptation without an intervention is an
  attribution error.
- Monitor-dependent control can create a new attack surface, and resampling can
  amplify rather than suppress an adaptive attack.
- Strict integrity controls may change the harness enough to change the agent
  being measured.
- Many agent pairs share agents and tasks; naive pair-level inference can
  drastically overstate evidence.
- Apparent gains may come from abstaining on nearly all difficult or novel
  cases.
- Meta-evaluation can become the next public proxy and suffer its own Goodhart
  effects.

## 12. Proposed Reading Order

For a new researcher, the shortest high-value path is:

1. [SEAGym](https://arxiv.org/abs/2606.17546),
   [SEA-Eval](https://arxiv.org/abs/2604.08988),
   [StreamBench](https://proceedings.neurips.cc/paper_files/paper/2024/hash/c189915371c4474fe9789be3728113fc-Abstract-Datasets_and_Benchmarks_Track.html),
   [LifelongAgentBench](https://arxiv.org/abs/2505.11942), and
   [Gradient Episodic Memory](https://papers.nips.cc/paper/2017/hash/f87522788a2be2d171666752f97ddebb-Abstract.html)
   for the shift from episodic snapshots to versioned, sequential evaluation;
2. [Darwin Gödel Machine](https://openreview.net/pdf?id=pUpzQZTvGY),
   [Huxley-Gödel Machine](https://openreview.net/forum?id=T0EiEuhOOL),
   [Harness Updating Is Not Harness Benefit](https://arxiv.org/abs/2605.30621),
   and [Loreley](https://arxiv.org/abs/2608.19703) for version archives,
   lineage selection, role decomposition, and important negative results;
3. [Han et al.](https://proceedings.mlr.press/v235/han24b.html),
   [Hara et al.](https://doi.org/10.1007/s10994-024-06603-1), and
   [Active Testing](https://proceedings.mlr.press/v139/kossen21a.html) for
   temporal assessment, direct comparison, and bias-corrected task sampling;
4. [Briesch et al.](https://doi.org/10.1016/j.jsp.2013.11.008),
   [Cai et al.](https://www.annualreviews.org/content/journals/10.1146/annurev-statistics-041715-033702),
   [Mellenbergh](https://doi.org/10.1016/0883-0355(89)90002-5), and
   [Agent Psychometrics](https://arxiv.org/abs/2604.00594) for reliability,
   IRT, measurement invariance, and a coding-specific response-model baseline;
5. [Cawley and Talbot](https://jmlr.org/papers/v11/cawley10a.html),
   [Dwork et al.](https://proceedings.neurips.cc/paper/2015/hash/bad5f33780c42f2588878a9d07405083-Abstract.html),
   [Performative Prediction](https://proceedings.mlr.press/v119/perdomo20a.html),
   [Gao et al.](https://proceedings.mlr.press/v202/gao23h.html), and
   [Inference-Time Reward Hacking](https://proceedings.neurips.cc/paper_files/paper/2025/hash/590a0cc0306c1c63e2d66a51a407718f-Abstract-Conference.html)
   for selection-induced bias, feedback-caused distribution change, and
   repeated proxy optimization;
6. [AI Sandbagging](https://proceedings.iclr.cc/paper_files/paper/2025/hash/b5e5753b0a0e440a6d8dc7e143617cec-Abstract-Conference.html),
   [The Elicitation Game](https://proceedings.mlr.press/v267/hofstatter25a.html),
   [The Hawthorne Effect](https://proceedings.neurips.cc/paper_files/paper/2025/hash/cf42f133f355e0e07a8957b508b26a1b-Abstract-Conference.html), and the
   [limited-behavior-effect counterevidence](https://arxiv.org/abs/2605.05835)
   for a calibrated view of capability elicitation and evaluation awareness;
7. [AI Control](https://proceedings.mlr.press/v235/greenblatt24a.html),
   [Adaptive Attacks on Trusted Monitors](https://proceedings.iclr.cc/paper_files/paper/2026/hash/54b153ad8a138f4c186f21a8b7341d5e-Abstract-Conference.html),
   and [Deployment Simulation](https://openai.com/index/deployment-simulation/)
   for whole-protocol red teaming and deployment-like validation;
8. [Kaushik et al.](https://aclanthology.org/2021.acl-long.517/),
   [Dynabench](https://aclanthology.org/2021.naacl-main.324/), and
   [Curious POET](https://direct.mit.edu/isal/article/doi/10.1162/isal_a_00736/123533/Curious-POET-Intrinsic-Motivation-Improves)
   for both the promise and limits of adversarial or coevolving task supply;
9. [MetricEval](https://aclanthology.org/2023.emnlp-main.676/),
   [Perturbation CheckLists](https://aclanthology.org/2021.emnlp-main.575/),
   and [Deutsch et al.](https://aclanthology.org/2022.naacl-main.442/) for
   testing the evaluator itself;
10. [SlopCodeBench](https://arxiv.org/abs/2603.24755), the
   [Agentic Benchmark Checklist](https://papers.nips.cc/paper_files/paper/2025/hash/f316275b44ee2de533102913828a8107-Abstract-Datasets_and_Benchmarks_Track.html),
   [SWE-ABS](https://arxiv.org/abs/2603.00520), and recent live task-supply
   papers in Section 9 for coding-domain constraints.

## Maintenance Rule

For each new source, record:

- publication status and date;
- exact setting and target quantity;
- assumptions needed for the result;
- what it supports in Barcarolle;
- what it explicitly does not support;
- one experiment, estimator, or failure test that follows from it.

Do not turn adjacent evidence into a project claim. Recent preprints and
institutional reports may motivate an experiment, but only Barcarolle's own
time-respecting, independently validated evidence can establish reliable
evaluation for self-evolving agents in the initial coding domain, measured by
the three primary numerical objectives.
