我已阅读 `README_FOR_EXTERNAL_GPT55_PRO.md`、核心 JSON/CSV、选择脚本和报告，并核验了 `MANIFEST.sha256`。结论很直接：

**不要继续把当前 weighted target-profile 方法微调后再付费跑。下一步应改成“分层/成对阻塞 + 收缩权重 + 不确定性约束 + 本地滚动回测”的 benchmark compiler。短期主线应以 simple stratified/unweighted 作为保守候选，weighted 只能作为研究分支，直到本地回测证明它稳定优于基线。**

---

## 0. 关键证据摘要

付费 pilot 本身是干净的：`44/44/44` planned/completed/scoreable，policy violation 为 0，成本 `$22.0`。失败不是执行层问题，而是设计层问题。

| design                                    | attrs gap | boltons gap | max gap | 结论                |
| ----------------------------------------- | --------: | ----------: | ------: | ----------------- |
| `barcarolle_weighted_time_family_matched` |    0.3148 |      0.7481 |  0.7481 | 明显失败              |
| `repo_unweighted_same_budget`             |      0.25 |       0.125 |    0.25 | 虽未达 0.15，但好得多     |
| `repo_stratified_by_target_profile`       |      0.25 |       0.125 |    0.25 | 与 unweighted 并列最好 |

weighted design 的 boltons 结果尤其说明问题：

```text
boltons / B_eval:
  weighted pass rate = 0.2519
  task outcomes = [0, 0, 1, 0]

boltons / H_future:
  weighted pass rate = 1.0000
  task outcomes = [1, 1, 1, 1]

gap = 0.7481
```

也就是说，metadata matching 看起来更好，但实际把 boltons 的失败任务集中到了 B_eval，把通过任务集中到了 H_future。这个失败形态不支持“再调一点权重就能解决”的判断。

---

## 1. Diagnosis：为什么 weighted design 可能失败

### 高置信原因

**第一，target profile 不是一个独立估计的 future-work distribution，而更像 candidate supply distribution。**
`build_target_profiles()` 从 eligible target-profile rows 里统计 `task_family_label / module / time bucket / source_kind / file count / statement_quality`。这没有用 H_future outcome，也没有用 hidden oracle，合规上干净；但统计对象本质上是当前候选池和历史候选池的混合，而不是独立的“未来真实工作分布”估计。它还混入了旧 release 的生成工件，例如 `task_time_bucket = None`、`statement_source = reused_codex_loop` 等，而新候选池根本不可能匹配这些 strata。

**第二，当前 features 主要是 provenance/metadata，不足以平衡 agent 难度。**
boltons weighted split 中，B_eval 和 H_future 在 `source_kind`、`statement_source`、`statement_quality_status` 上几乎完全一样；但 outcome 完全不同。说明这些 metadata 对当前 ACUT 的难度预测力很弱。`task_family_label` 也不够：例如 boltons 的 `funcutils` 既有 fail 也有 pass，`iterutils` 也既有 fail 也有 pass。

**第三，split construction 优化的是 marginal L1 matching，不是 predictive risk。**
脚本中的核心目标是：

```python
score = max(b_distance, h_distance) + abs(b_distance - h_distance) + 0.25 * split_distance
```

这会让两个 split 在表层 metadata 上看起来接近 target 和彼此接近，但它没有约束 latent difficulty、没有约束 outcome variance、没有约束 effective sample size，也没有对 tie / near-tie 做随机化或稳健性检查。

我复算了 boltons 的组合空间：存在多个 metadata-optimal 或近似 metadata-optimal split；它们的真实 outcome gap 可以从 0 到 0.75 不等。当前 deterministic tie-break 选到了 gap 最大的一类。这不是事后要求算法知道 outcome，而是说明 **metadata objective 对真正要预测的量 underidentified**。

**第四，task-level weights 的定义不是真正的 survey/post-stratification estimator。**
当前 weighted task weight 是若干 marginal profile weights 的平均值：

```python
raw_weight_i = mean(
  profile_weight(task_family),
  profile_weight(task_time_bucket),
  profile_weight(source_kind),
  profile_weight(statement_quality_status)
)
```

这既不是 inverse probability weighting，也不是 raking/entropy balancing，也不是基于 joint strata 的 post-stratification。它容易把噪声任务放大。attrs 就出现了这种情况：unweighted gap 是 0.25，但 weighted 后变成 0.3148，因为 B_eval 中 fail task 拿到了较高权重，而 H_future 中 pass task 也拿到了较高权重。

**第五，样本太小，阈值本身 underpowered。**
每个 repo/split 只有 4 个 task、2 个 adapter cell。`threshold_preregistration` 自己也写了：达到 0.15 half-width 需要约 78 task units per split。当前 pilot 可以做方向判断，但不能做精密 calibration claim。小 N 不能单独解释 weighted 明显差于 baseline，但它会放大错误 split 和错误权重的后果。

### 不确定原因

**statement quality 可能有影响，但证据不强。**
boltons 的 weighted split 基本都是 `certified_solver_statement` + `pass_with_minor_risk`，baseline 也大量如此，所以无法把失败归因于 statement source。

**adapter-specific behavior 不是主因。**
score table 里只有一个 task 出现 adapter disagreement：`boltons__hist__014`。codex/kilo 总体 pass rate 也接近，因此当前失败不是明显的 adapter 偏差。

**temporal drift 可能存在，但不能断言。**
boltons 的 failures 分布在 2020H1、2022H2、2023H2；passes 也分布多个时期。时间桶可能相关，但现有 n 太小，不能把失败归因于时间。

---

## 2. Method critique：当前 weighting / split matching 的脆弱点

当前方法的问题不是“加权”这个方向本身错了，而是 **小样本下用高维稀疏 metadata 做精确 matching，再用未经校准的 marginal weights 估计 future performance**。

主要脆弱点如下：

1. **profile 估计对象错位**：它估计 candidate pool 的 metadata distribution，而不是独立的 target future-work distribution。
2. **高基数 strata 太多**：`task_family_label`、`module_or_package`、`task_time_bucket` 在每 repo 只有 18–20 support 时已经很稀疏；实际每 split 只有 4 task。
3. **confidence label 过乐观**：repo-level support 被标为 high，但很多 strata count=1；这应该触发“不足以 profile-weight”的降级，而不是继续 weighted matching。
4. **matching 目标缺少 difficulty balance**：它只匹配 metadata，不匹配历史难度、静态复杂度、agent-family risk 或 cheap surrogate signal。
5. **没有 blocked randomization**：split assignment 是 deterministic combinatorial optimum + lexicographic tie-break；这在小 N 下非常危险。
6. **weights 没有 ESS/weight cap**：没有约束最大权重、有效样本量、weight variance，也没有当 infeasible 时自动回退 uniform。
7. **没有本地回测门槛**：在付费前，应该证明 weighted compiler 在多个 retrospective pseudo-future split 上稳定优于 stratified/unweighted，而不是只证明 metadata L1 更低。
8. **B_eval 与 H_future 的验证形式本身偏 transductive**：两个 split 都来自已知候选池。真正的 claim 是预测 future repo work，下一轮需要更严格的 time-cutoff / rolling-origin 验证。

---

## 3. 推荐的下一代算法：Blocked Shrinkage-Weighted Compiler

我建议把下一代算法定义为：

> **BSWC: Blocked Shrinkage-Weighted Compiler**
> 用独立 target profile 估计目标分布；用低维、可审计、带不确定性的 task representation；用整数规划或约束优化选 task/block；用 capped entropy/raking weights；用 hierarchical beta-binomial 或 bootstrap 输出预测区间；当 supply 不足时自动回退到 simple stratified/unweighted。

### 3.1 Task feature representation

不要只用现在的 metadata。建议分四层：

```text
A. provenance features
   repo_id
   source_kind
   source_reservoir
   task_time
   statement_source
   statement_quality_status

B. work-distribution features
   module/package
   task type: bugfix / feature / refactor / test / docs / dependency
   touched API surface
   single-file vs multi-file
   implementation_file_count
   test_file_count
   dependency radius
   public issue/PR labels when available

C. difficulty/risk features, solver-visible or pre-outcome only
   statement length bucket
   source context length bucket
   edit locality
   expected patch size from public metadata, not hidden reference internals
   test breadth proxy
   environment/build risk
   ambiguity/leakage/flakiness risk from certification

D. learned/latent features
   issue/statement embedding cluster
   file-path embedding cluster
   lightweight classifier-predicted task type
   optional prior difficulty score trained only on previous evidence
```

重要原则：**高维原始 category 不直接进入 matching objective**。先合并成低维 strata，例如：

```text
work_cluster ∈ 8–20 buckets
difficulty_band ∈ easy / medium / hard / unknown
source_quality ∈ clean / minor_risk
locality ∈ single_file / multi_file
time_recency ∈ recent / older / unknown
```

### 3.2 Target profile estimation

target profile 不能再直接等于候选池分布。应改为：

```text
target events = pre-cutoff repo work stream
  recent issues
  recent PRs
  maintainer labels
  changed files
  public metadata
  optional user-declared business weights

exclude:
  H_future outcomes
  hidden verifier/oracle
  raw solver traces
  post-cutoff validation outcomes
```

估计方式：

```text
1. 从 pre-cutoff event stream 抽取 public metadata。
2. 用同一个 featurizer 映射到 low-dimensional strata。
3. 用 Dirichlet-multinomial / empirical Bayes 平滑 strata weights。
4. 输出 target_profile:
   stratum_weight_mean
   stratum_weight_interval
   support_count
   confidence_label
   unreachable_by_candidate_supply flag
```

当 target stratum 在 candidate pool 中没有 supply 时，不应该强行匹配；应报告：

```text
uncovered target mass = x%
predictive claim narrowed to covered target mass
```

### 3.3 Split construction

小样本下不要单独贪心选 B_eval 和 H_future。要先建 block，再随机化：

```text
1. 在候选任务中构造 matched blocks。
   每个 block 包含 2 或 4 个 feature-near tasks。

2. block 内任务在 metadata、work_cluster、difficulty_band、source_quality 上接近。

3. 用 seeded randomization 把 block 内任务分到 B_eval / H_future。

4. 重复多个 seed，选择 expected imbalance 最低且 variance 稳定的 release；
   或 preregister seed，避免人工挑 outcome-friendly split。
```

如果 H_future 是真正未来 holdout，则不应从候选池里“构造 H_future”。正确流程是：

```text
pre-cutoff candidate pool -> compile B_eval
post-cutoff real future tasks -> H_future validation
```

如果当前阶段必须用本地 retrospective validation，就做 rolling-origin pseudo-future：

```text
cutoff_1: train/profile before t1 -> B_eval from before/near t1 -> validate on t1..t2
cutoff_2: train/profile before t2 -> B_eval from before/near t2 -> validate on t2..t3
...
```

### 3.4 Task weighting

建议从“平均 marginal profile weight”改为 **capped entropy balancing / raking**。

目标：

```text
find weights w_i close to uniform
subject to:
  selected weighted covariate moments ≈ target profile moments
  0 <= w_i <= w_max
  ESS(w) >= ESS_min
  sum_i w_i = 1
```

其中：

```text
ESS(w) = (sum_i w_i)^2 / sum_i w_i^2
```

建议默认约束：

```text
w_max <= 2 / n_selected
ESS >= 0.7 * n_selected
```

如果 infeasible：

```text
1. 放宽到 coarser strata；
2. 仍 infeasible，则 shrink toward uniform；
3. 仍不稳定，则使用 unweighted stratified score，并报告 target imbalance。
```

这样做的核心是：**权重只能修正可支撑的轻微分布差异，不能用来制造不存在的信息。**

### 3.5 Uncertainty model

每个 release 不应只输出 point estimate。建议输出：

```text
predicted_target_pass_rate_mean
predicted_target_pass_rate_50/80/95 interval
B_eval -> H_future gap posterior / bootstrap distribution
covered_target_mass
uncovered_target_mass
effective_sample_size
max_weight
sparse_strata_flags
```

统计模型可以从简单到复杂：

```text
Level 0:
  Wilson / Agresti-Coull intervals by repo/split

Level 1:
  beta-binomial by stratum
  bootstrap over blocks, not just cells

Level 2:
  hierarchical logistic / beta-binomial:
    outcome ~ repo + work_cluster + difficulty_band + source_quality + adapter
```

小样本下，hierarchical model 的价值主要是 **shrinkage 和 honest uncertainty**，不是假装能精确预测。

### 3.6 Pseudocode

```python
def compile_release(candidate_tasks, target_events, prior_evidence, budget, seed):
    # 1. certify and featurize
    tasks = [t for t in candidate_tasks if t.certified and not t.leakage_risk_blocker]
    X = featurize_tasks(tasks)

    # 2. estimate independent target profile
    E = featurize_target_events(target_events)          # pre-cutoff only
    target = dirichlet_smoothed_profile(E)

    # 3. coarsen sparse strata
    strata = build_low_dim_strata(
        X,
        min_support_per_stratum=3,
        merge_rare=True,
        include_unknown_bucket=True,
    )

    # 4. optional prior difficulty model
    difficulty_prior = fit_or_load_prior_difficulty_model(
        prior_evidence,
        allowed_inputs="previous evidence only",
    )
    X["difficulty_band"] = predict_difficulty_band(difficulty_prior, X)

    # 5. build matched blocks
    blocks = make_candidate_blocks(
        tasks,
        features=[
            "work_cluster",
            "difficulty_band",
            "source_quality",
            "locality",
            "time_recency",
        ],
        block_size=2,
        seed=seed,
    )

    # 6. select blocks under coverage and supply constraints
    selected_blocks = solve_block_selection(
        blocks=blocks,
        target_profile=target,
        budget=budget,
        objective=[
            "minimize target imbalance",
            "maximize covered target mass",
            "minimize uncertainty",
            "penalize sparse strata",
        ],
        constraints=[
            "per_repo_budget",
            "no hidden oracle inputs",
            "min_effective_support",
            "max_single_stratum_share",
        ],
    )

    # 7. randomized split within blocks
    B_eval, H_shadow = randomized_block_split(selected_blocks, seed=seed)

    # 8. compute capped shrinkage weights for B_eval
    weights, diagnostics = entropy_balance_or_shrink(
        tasks=B_eval,
        target_profile=target,
        max_weight_factor=2.0,
        min_ess_ratio=0.7,
    )

    if diagnostics.infeasible or diagnostics.ess_too_low:
        weights = uniform_weights(B_eval)
        diagnostics.mode = "fallback_unweighted_or_stratified"

    # 9. preregister validation and uncertainty
    return Release(
        tasks=B_eval,
        shadow_split=H_shadow,
        weights=weights,
        target_profile=target,
        diagnostics=diagnostics,
        seed=seed,
        validation_plan="rolling_origin_or_future_holdout",
    )
```

---

## 4. Baseline strategy

**是的，simple stratified baseline 应该暂时成为 mainline candidate。**
不是因为它已经达到 0.15 threshold，而是因为它在这次干净 pilot 中显著优于 weighted design，而且更少自由度、更少过拟合风险。

建议保留/新增这些 baselines：

```text
A. repo_unweighted_same_budget
   当前必须保留。

B. repo_stratified_by_target_profile
   暂时升为 mainline candidate。

C. seeded_random_same_budget
   多 seed 本地重复，不只一个 deterministic sample。

D. temporal_recent_baseline
   最近 n 个 pre-cutoff tasks 预测 post-cutoff tasks。

E. coverage_constrained_unweighted
   最大化 coarse strata coverage，但不加权。

F. block_randomized_stratified
   新算法的无权重版本，用来隔离“blocking”本身的收益。

G. shrinkage_weighted_after_stratified
   只在 ESS 和 weight cap 通过时启用权重。

H. metadata_nearest_general_or_external_generator_default
   后续接 SWE-Bench++/SWE-smith/R2E-Gym 类上游时需要。
```

同时应保留两个 diagnostic，不作为 claim：

```text
oracle_posthoc_best_split:
  用 outcome 后验挑最好 split，只作为上限诊断，不能作为算法结果。

oracle_difficulty_balanced_split:
  用 outcome 后验平衡 pass/fail，只显示当前 metadata objective 离 oracle 有多远。
```

---

## 5. 下一次 local-only runbook 应做什么

下一步不该直接写 paid runbook。应写一个 **local-only algorithm bakeoff runbook**。

### 5.1 必做步骤

```text
1. Reproduce current pilot metrics
   - 从 release_candidates + score_table 复算所有 gap。
   - 生成 per-task metadata/outcome audit。

2. Quantify objective underidentification
   - 枚举或采样所有 feasible split。
   - 画出 metadata objective vs observed gap。
   - 检查 optimal/near-optimal split 的 outcome gap variance。

3. Build independent target profile prototype
   - 不再用 candidate pool 直接当 profile。
   - 从 pre-cutoff public event stream 或历史 task metadata 模拟 target events。
   - 输出 covered/uncovered target mass。

4. Implement block-randomized stratified compiler
   - matched blocks
   - seeded randomization
   - repeated seeds
   - imbalance diagnostics

5. Implement capped shrinkage weighting
   - entropy/raking weights
   - max weight
   - ESS
   - automatic fallback

6. Rolling-origin retrospective validation
   - 多 repo
   - 多 cutoff
   - 多 random seed
   - 多 ACUT 或至少多 adapter/harness condition
   - 指标：MAE、RMSE、NLL/Brier、coverage、catastrophic miss rate

7. Ablation study
   - unweighted
   - stratified
   - blocked only
   - blocked + shrinkage weights
   - blocked + difficulty prior
   - old weighted method

8. Paid-readiness gate
   - 只有本地结果通过后，才写新的 paid replication runbook。
```

### 5.2 什么证据足够支持再次付费

建议 preregister 以下 paid gate：

```text
1. local rolling-origin MAE:
   新算法相对 stratified baseline 至少降低 15–25%，
   且不是由单个 repo/window 驱动。

2. catastrophic gap:
   新算法在本地 pseudo-future 中没有频繁出现 > baseline + 0.15 的灾难性失败。

3. weight diagnostics:
   ESS >= 0.7 * n
   max_weight <= 2 / n
   uncovered target mass 明确报告。

4. supply diagnostics:
   每个目标 repo 至少 20–30 个可选 certified tasks；
   每个 coarse stratum 至少 3 个 support，或者合并进 unknown/rare。

5. split stability:
   多 seed 下预测误差方差低；
   不依赖 lexicographic tie-break。

6. preregistration:
   target profile、features、weights、split seed、fallback rule、primary metric 全部 frozen before paid calls。
```

如果这些 gate 达不到，下一次付费只会重复当前问题：样本小、权重大、metadata objective 与 outcome 弱相关。

---

## 6. Modern stack 建议

当前 Python 脚本可审计，但过多 hand-rolled statistical/optimization logic。建议保留 JSON artifact + deterministic CLI 的审计风格，把核心算法迁到成熟库。

**优化 / split selection：**

* 小型 MILP 可先用 `scipy.optimize.milp`；SciPy 官方文档提供了 mixed-integer linear programming API。([SciPy Documentation][1])
* 更复杂的 boolean/block/assignment 约束可用 OR-Tools CP-SAT；Google 文档说明 CP-SAT 面向整数约束优化，并返回 OPTIMAL/FEASIBLE/INFEASIBLE 等求解状态。([Google for Developers][2])
* 如果目标函数需要更自然地表达 convex/MIQP，可用 CVXPY；CVXPY 是 Python embedded optimization modeling language，也支持 mixed-integer programs via boolean/integer variables。([CVXPY][3])

**统计 / uncertainty：**

* `statsmodels` 适合 frequentist intervals、GLM、基础统计模型；其官方说明定位为提供统计模型估计和统计检验的 Python 模块。([Statsmodels][4])
* `PyMC` 适合 hierarchical beta-binomial / logistic models；PyMC 官方文档描述它是 Python 中的 probabilistic programming framework，示例库也覆盖 multilevel/hierarchical modeling。([PyMC][5])
* `scikit-learn` 可用于 calibration curves、probability calibration、embedding clustering、baseline classifiers；官方 calibration 文档说明其 calibration 模块用于校准概率预测并提供 calibration_curve 等工具。([Scikit-learn][6])

**数据与 artifact：**

* `DuckDB` 适合把 JSON/CSV/parquet score tables、candidate inventories、run manifests 做本地可复现 SQL 分析；DuckDB 官方文档提供 Python API、DB API、relational API 等入口。([DuckDB][7])
* `Pydantic` 适合 release schema、target_profile schema、runbook artifact schema；官方文档说明 Pydantic 可从 models 生成 JSON Schema，并支持 JSON Schema Draft 2020-12 / OpenAPI v3.1.0。([Pydantic][8])

建议工程形态：

```text
barcarolle/
  schemas/
    release.py
    target_profile.py
    score_table.py

  features/
    task_featurizer.py
    target_event_featurizer.py

  compiler/
    block_builder.py
    selection_milp.py
    entropy_weights.py
    fallback.py

  validation/
    rolling_origin.py
    bootstrap.py
    metrics.py
    bakeoff.py

  artifacts/
    manifest.py
    digest.py
    audit.py
```

每次 run 输出：

```text
release.json
target_profile.json
selection_problem.json
selection_solution.json
weights.json
uncertainty.json
bakeoff_metrics.json
MANIFEST.sha256
```

---

## 7. Stop/go recommendation

**建议：Go，但要 narrow claim，并停止当前 weighted 方法的付费推进。**

更具体地说：

```text
不要说：
  Barcarolle weighted target-profile compiler 已经能预测 future repo work。

改成：
  Barcarolle 正在构建一个 auditable repo-specific benchmark compiler。
  当前 pilot 表明 naive target-profile weighting 不可靠；
  下一阶段目标是证明 blocked stratified + shrinkage weighting
  在 sufficient supply 和 preregistered rolling validation 下
  是否能稳定优于 unweighted/stratified baselines。
```

短期路线：

```text
mainline:
  repo_stratified_by_target_profile / block_randomized_stratified

research branch:
  shrinkage-weighted compiler with uncertainty gates

fallback product value:
  task certification
  regression benchmark packaging
  tuning feedback
  failure taxonomy
  target coverage reporting
```

当前证据不支持继续把“weighted design beats simple baselines”作为近期 claim。它支持一个更有价值的结论：

**Barcarolle 的核心难点不是能否计算 target-profile weights，而是如何在 small-N、expensive validation、sparse target strata 下构造一个低方差、可审计、自动知道何时回退的 estimator。**

[1]: https://docs.scipy.org/doc/scipy-1.16.1/reference/generated/scipy.optimize.milp.html?utm_source=chatgpt.com "milp — SciPy v1.16.1 Manual"
[2]: https://developers.google.com/optimization/cp/cp_solver?utm_source=chatgpt.com "CP-SAT Solver | OR-Tools"
[3]: https://www.cvxpy.org/?utm_source=chatgpt.com "cvxpy"
[4]: https://www.statsmodels.org/?utm_source=chatgpt.com "statsmodels 0.14.6"
[5]: https://www.pymc.io/projects/docs/en/stable/learn/core_notebooks/pymc_overview.html?utm_source=chatgpt.com "Introductory Overview of PyMC — PyMC 6.0.1 documentation"
[6]: https://scikit-learn.org/stable/modules/calibration.html?utm_source=chatgpt.com "1.16. Probability calibration"
[7]: https://duckdb.org/docs/current/?utm_source=chatgpt.com "Documentation"
[8]: https://pydantic.dev/docs/validation/latest/concepts/json_schema/?utm_source=chatgpt.com "JSON Schema | Pydantic Docs"
