"""Small configuration records for Selection orchestration."""

from __future__ import annotations

from dataclasses import dataclass

from .inputs import SelectionBudget


@dataclass(frozen=True)
class SelectorEvaluationConfig:
    origin_times: tuple[str, ...]
    budget: SelectionBudget
