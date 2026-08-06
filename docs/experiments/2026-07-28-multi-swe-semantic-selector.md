# Multi-SWE Outcome-Free Semantic Selector

Date: 2026-07-28

## Question

Can a fixed, outcome-free semantic rule select ten historical Tasks from one
repository whose Task distribution and 36-configuration Agent pass rates are
closer to that repository's next Tasks than the complete eligible history?

The study evaluates one predeclared candidate, ALG-012 minimax temporal
semantic herding. It is a development test on opened Multi-SWE outcomes, not
independent confirmation.

## Frozen contract

The plan was committed before Task-space or Agent-outcome replay. Its digest is
`6619ab258039d3f12cf865421faeba7c23248b302f72b06bb6f311b8f65bde05`.
The candidate:

1. embeds only issue number, title, and body from eligible historical Tasks;
2. forms one mean over complete history and one over the latest `h` Tasks;
3. greedily adds the Task that minimizes the larger squared kernel-mean
   distance to those two targets;
4. selects ten equal-weight Tasks, performs no fitting and no swaps, and never
   reads Agent outcomes.

H5 is primary: 221 Origins from 13 repositories, including eight deep
repositories. H10 is the frozen sensitivity view: 107 Origins from 11 common
repositories, including five deep repositories. Full history is the primary
baseline. Twenty thousand equal-budget random Selections calibrate the
sampling landscape.

The exact dataset revision
`56ff018c04a38e27ada1e9d0a6d5839a51f88f0d` was downloaded locally. All 39
allowlisted Git or Git LFS objects and 1,603,542,672 declared bytes were
verified before projecting 1,632 nonempty issue texts. The projection excludes
pull-request text, patches, tests, hints, and outcomes. The local
`sentence-transformers/all-MiniLM-L12-v2` revision
`c004d8e3e901237d8fa7e9fff12774962e391ce5` produced 384-dimensional normalized
vectors without an embedding API.

Multi-SWE has no native Task time. Origins use projected GitHub pull-request
creation time and therefore support source-time-safe counterfactual evidence,
not strict historical replay.

## Results

Negative candidate-minus-full-history values favor Selection.

| Evidence | Horizon | Full-history loss | ALG-012 loss | Difference | Favorable repositories | Deep difference | Random percentile |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Semantic MMD² | H5 | `0.16634` | `0.20197` | `+0.03563` | 0/13 | `+0.03920` | 99.14 |
| Semantic MMD² | H10 | `0.10603` | `0.13210` | `+0.02607` | 0/11 | `+0.02869` | 100.00 |
| Agent pass-rate MAE | H5 | `0.06735` | `0.06707` | `-0.00027` | 8/13 | `+0.00080` | 81.59 |
| Agent pass-rate MAE | H10 | `0.05281` | `0.05522` | `+0.00241` | 3/11 | `+0.00224` | 84.37 |

The H5 repository-bootstrap interval for the outcome difference is
`[-0.00415, +0.00334]`; H10 is `[-0.00129, +0.00638]`. The H5 random mean is
`+0.00182`, and 18.42% of random draws are as good as or better than ALG-012.
The task-space H5 random mean is `+0.04401`, and 0.86% of random draws are as
good as or better.

The unchanged ALG-007 transfer control reaches H5 outcome difference
`-0.00225` with 7/13 favorable repositories, but H10 is `+0.00216`. It also
fails the frozen gate and is not a candidate to tune.

On the primary H5 outcome view, ALG-012 is favorable for 20/36 configurations,
10/12 model families, and 6/7 provider families, but only 1/3 harnesses and
3/7 languages. The language-first macro difference is `-0.00055`. The deep
direction is positive. These failures rule out a portable effect.

## Interpretation

The random comparison and the full-history comparison answer different
questions:

- ALG-012's 81.59th H5 outcome percentile shows that it uses some structure in
  the Task Pool rather than behaving like an arbitrary ten-Task subset.
- Its `-0.00027` effect is nearly zero, its interval crosses zero, and it
  reverses at H10. It therefore does not show that the selected benchmark is
  meaningfully closer to future Tasks than the unselected benchmark.
- In embedding space, ALG-012 is among the best equal-budget subsets but every
  repository is worse than full history. The ten-Task compression penalty is
  larger than the semantic-drift signal captured by this representation.

The task-space and outcome gates both failed. The frozen decision order did not
reach either temporal-null test. The plan allowed the one predeclared outcome
join after memberships were fixed, so that join was completed and recorded;
no further candidate search is licensed by these results.

ALG-012 is closed and no Selector is nominated. The result neither authorizes
the six sealed SWE-bench Agent vectors nor paid validation nor Runner
promotion.

## Follow-up decision

A separately frozen exact hindsight diagnostic subsequently reached H5
`-0.03264` with 13/13 repositories favorable and H10 `-0.02562` with 11/11
favorable. It certified all 328 Origin optima. Budget ten has adequate
representational capacity for this opened estimand; pre-Origin identification
is the current bottleneck.

The leaked diagnostic does not nominate an algorithm. Do not tune another
semantic target, embedding, budget, or horizon from the opened ALG-012 result,
and do not train on hindsight memberships. The full method and boundary are in
[`2026-07-28-multi-swe-budget-ten-capacity.md`](2026-07-28-multi-swe-budget-ten-capacity.md).

## Evidence identity and resources

The ignored task-space artifact digest is
`d9916f4c9acdcf615262f92cb771ed0079a696b4605805ef0c82b17f4f4e401d`.
The ignored outcome artifact digest is
`7b314e1239981c38574960e15f8117ba33c350dbb61fb1e9c0d52eb96e013e36`.
The committed compact summary digest is
`c91459da16d42bb2c0a3ebb20a0c0df10fa441ae15037d736c9615c35cef6e61`.
Reproduction commands are in
[`examples/multi_swe_research/README.md`](../../examples/multi_swe_research/README.md).

The study made zero paid API calls, zero embedding API calls, and opened zero
sealed SWE-bench holdout Agents.
