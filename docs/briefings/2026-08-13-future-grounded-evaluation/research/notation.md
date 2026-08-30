# 技术符号与口径

> 正文只保留两个直觉表达式。本页供技术附录使用，避免 `O`、outcome、optimizer 或 workload 的含义混淆。

| 符号 | 含义 | 口径限制 |
| --- | --- | --- |
| \(t\) | evaluation origin / 历史时间切点 | 所有 evaluator 输入必须在此时可见 |
| \(H\) | origin 后的评估 horizon | 例如 next-5、next-10 或预注册时间窗；不等于历史信息 \(H_t\) |
| \(H_t\) | origin 时可见的历史信息 | 包括历史 Tasks/Results，不包括 later outcomes |
| \(R_t\) | origin 时的 repository state | solver 与任务具体化的基准状态 |
| \(D_{t,H}\) | origin \(t\) 后 horizon \(H\) 内的目标 workload 生成过程/分布 | 不假定稳定、完整可知；最终只能观察它产生的 realized task stream，且不由 Generator/Optimizer 定义 |
| \(z\) | 一项 external demand / future work intent | 可以后来具体化为 executable Task |
| \(A\) | 完整 Agent system state | 包括模型、Harness、prompt、skills、tools、retrieval、retry 等 |
| \(Y(A,z)\) | Agent 面对 demand/task 后的 outcome | 第一阶段为 pass/fail；以后可扩成 time/cost/correction vector |
| \(U(Y)\) | 可选 utility/scalarization | 第一阶段直接令 \(U=Y_{pass}\)，避免过早定义万能价值函数 |
| \(J_{t,H}(A)\) | Agent 在 \(D_{t,H}\) 上的期望 utility | 理想 estimand；只能用后来出现的 task stream 或时间一致的历史回放估计 |
| \(F_\phi\) | future-demand Forecaster | 从 \((H_t,R_t,H)\) 预测指定 horizon 的 future demand families |
| \(M_\psi\) | Materializer | 把 demand family 具体化为 requirement、environment、Task、Check |
| \(G=(F,M)\) | 广义 Generator | Forecaster 与 Materializer 的组合，不自带外部有效性保证 |
| \(Q_{t,H}\) | Generator 针对 horizon \(H\) 产生的 synthetic workload distribution | 必须与同一 \((t,H)\) 口径的 later-real response surface 对账 |
| \(S_\theta\) | Selector | 在 origin 可见 pool 中编译有限 benchmark |
| \(B_t\) | 编译后的有限 benchmark | 包含 task membership、预算和 provenance |
| \(\hat J_{t,H}(A)\) | benchmark 对 \(J_{t,H}(A)\) 的估计 | 不是 ground truth；horizon 改变时 estimand 也改变 |
| \(\mathcal O\) | Optimizer / proposer / self-improver | 根据历史 Agent states 和 evaluation feedback 产生 candidates |
| \(A_0,A_1,\ldots,A_K\) | 优化 trajectory 中的 Agent states | 必须记录 parent、intervention、round 与 exposure |

理想 estimand 定义为：

```text
J_(t,H)(A) = E_[z ~ D_(t,H)] U(Y(A,z))
```

后来出现的有限 task block 只是对该 estimand 的样本估计，不等于完整或稳定的 workload distribution。

## 三个不同命题

### Pointwise predictive validity

```text
J_hat_(t,H)(A) ≈ J_(t,H)(A)
```

固定、自然出现的 Agent 的 benchmark level 是否预测 later-real level。

### Selection validity

```text
J_hat_(t,H)(A_i) - J_hat_(t,H)(A_j) ≈ J_(t,H)(A_i) - J_(t,H)(A_j)
```

固定候选 panel 上的 lift、符号、排序和 winner 是否保留。

### Adaptive selection validity

```text
A_(k+1) = O(A_≤k, J_hat_(t,H)(A_≤k), feedback)
```

即使候选是专门根据 evaluator 反馈产生的，\(\Delta\hat J_{t,H}\) 是否仍预测 \(\Delta J_{t,H}\)。这是新方向要验证的更强命题。

## 容易混淆的三个对象

- `workload` 是外部需求/任务分布，不是“项目改善量”。
- `outcome` 是 Agent 执行 workload 后测得的结果；第一阶段保留 pass/fail。
- `utility` 是可选的 outcome 汇总规则；不是 Generator 可以任意生成的 ground truth。
