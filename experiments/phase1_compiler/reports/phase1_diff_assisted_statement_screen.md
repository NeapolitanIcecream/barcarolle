# Phase 1 Diff-Assisted Statement Screen

Generated: `2026-05-25T02:52:58Z`.

## Summary

- Candidate count: `22`.
- Regenerated statement count: `22`.
- Review pass/reject: `19` / `3`.
- Deterministic QA pass/reject: `19` / `3`.
- Eligible before regeneration: `4`.
- Eligible after regeneration: `19`.
- Selected counts by repo/split: `{'attrs/B_eval': 4, 'attrs/H_future': 4, 'boltons/B_eval': 4, 'boltons/H_future': 0}`.
- Remaining missing supply: `{'boltons/H_future': ['needed 4, found 0 eligible regenerated statements without using paid outcomes']}`.
- Replacement supply still needed: `True`.

## Interpretation

The regenerated statements recover many old candidates that were previously rejected because the old renderer cut public body summaries at 240 characters. Generation, review, and QA failures are tracked separately from true task invalidity.

Paid validation is not recommended here because no release manifest is frozen in this runbook. Future paid validation requires a subsequent preregistration runbook.

## Candidate Outcomes

### boltons__clean_ext__001

- Eligible before: `False`.
- Eligible after: `True`.
- Review: `pass`.
- QA: `pass`.
- After-regeneration rejection reasons: `[]`.

### boltons__clean_ext__008

- Eligible before: `False`.
- Eligible after: `True`.
- Review: `pass`.
- QA: `pass`.
- After-regeneration rejection reasons: `[]`.

### boltons__clean_ext__010

- Eligible before: `True`.
- Eligible after: `True`.
- Review: `pass`.
- QA: `pass`.
- After-regeneration rejection reasons: `[]`.

### boltons__clean_ext__017

- Eligible before: `True`.
- Eligible after: `True`.
- Review: `pass`.
- QA: `pass`.
- After-regeneration rejection reasons: `[]`.

### attrs__hist__001

- Eligible before: `False`.
- Eligible after: `True`.
- Review: `pass`.
- QA: `pass`.
- After-regeneration rejection reasons: `[]`.

### attrs__hist__003

- Eligible before: `False`.
- Eligible after: `False`.
- Review: `reject`.
- QA: `reject`.
- After-regeneration rejection reasons: `['review_status:reject', 'deterministic_qa_status:reject']`.

### attrs__hist__004

- Eligible before: `False`.
- Eligible after: `True`.
- Review: `pass`.
- QA: `pass`.
- After-regeneration rejection reasons: `[]`.

### attrs__hist__008

- Eligible before: `True`.
- Eligible after: `False`.
- Review: `reject`.
- QA: `reject`.
- After-regeneration rejection reasons: `['review_status:reject', 'deterministic_qa_status:reject']`.

### attrs__hist__009

- Eligible before: `False`.
- Eligible after: `True`.
- Review: `pass`.
- QA: `pass`.
- After-regeneration rejection reasons: `[]`.

### attrs__hist__010

- Eligible before: `False`.
- Eligible after: `True`.
- Review: `pass`.
- QA: `pass`.
- After-regeneration rejection reasons: `[]`.

### attrs__hist__012

- Eligible before: `False`.
- Eligible after: `True`.
- Review: `pass`.
- QA: `pass`.
- After-regeneration rejection reasons: `[]`.

### attrs__hist__013

- Eligible before: `False`.
- Eligible after: `True`.
- Review: `pass`.
- QA: `pass`.
- After-regeneration rejection reasons: `[]`.

### attrs__hist__023

- Eligible before: `False`.
- Eligible after: `True`.
- Review: `pass`.
- QA: `pass`.
- After-regeneration rejection reasons: `[]`.

### attrs__hist__027

- Eligible before: `False`.
- Eligible after: `False`.
- Review: `reject`.
- QA: `reject`.
- After-regeneration rejection reasons: `['review_status:reject', 'deterministic_qa_status:reject']`.

### attrs__hist__032

- Eligible before: `False`.
- Eligible after: `True`.
- Review: `pass`.
- QA: `pass`.
- After-regeneration rejection reasons: `[]`.

### attrs__hist__033

- Eligible before: `False`.
- Eligible after: `True`.
- Review: `pass`.
- QA: `pass`.
- After-regeneration rejection reasons: `[]`.

### attrs__hist__035

- Eligible before: `False`.
- Eligible after: `True`.
- Review: `pass`.
- QA: `pass`.
- After-regeneration rejection reasons: `[]`.

### attrs__hist__036

- Eligible before: `False`.
- Eligible after: `True`.
- Review: `pass`.
- QA: `pass`.
- After-regeneration rejection reasons: `[]`.

### attrs__hist__039

- Eligible before: `True`.
- Eligible after: `True`.
- Review: `pass`.
- QA: `pass`.
- After-regeneration rejection reasons: `[]`.

### attrs__hist__041

- Eligible before: `False`.
- Eligible after: `True`.
- Review: `pass`.
- QA: `pass`.
- After-regeneration rejection reasons: `[]`.

### attrs__hist__045

- Eligible before: `False`.
- Eligible after: `True`.
- Review: `pass`.
- QA: `pass`.
- After-regeneration rejection reasons: `[]`.

### attrs__hist__047

- Eligible before: `False`.
- Eligible after: `True`.
- Review: `pass`.
- QA: `pass`.
- After-regeneration rejection reasons: `[]`.
