from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ModelPrice:
    endpoint_host_hash: str
    model: str
    pricing_source: str
    input_rate_per_1m_usd: float
    cached_input_rate_per_1m_usd: float
    output_rate_per_1m_usd: float
    reasoning_output_policy: str


def parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if value in {"null", "None"}:
        return None
    if value in {"true", "false"}:
        return value == "true"
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def load_model_prices(path: Path) -> list[ModelPrice]:
    prices: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    in_prices = False
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent == 0:
            in_prices = stripped == "prices:"
            continue
        if not in_prices:
            continue
        if stripped.startswith("- "):
            if current is not None:
                prices.append(current)
            current = {}
            item = stripped[2:].strip()
            if ":" in item:
                key, value = item.split(":", 1)
                current[key.strip()] = parse_scalar(value)
            continue
        if current is not None and ":" in stripped:
            key, value = stripped.split(":", 1)
            current[key.strip()] = parse_scalar(value)
    if current is not None:
        prices.append(current)
    return [
        ModelPrice(
            endpoint_host_hash=str(row["endpoint_host_hash"]),
            model=str(row["model"]),
            pricing_source=str(row["pricing_source"]),
            input_rate_per_1m_usd=float(row["input_rate_per_1m_usd"]),
            cached_input_rate_per_1m_usd=float(row["cached_input_rate_per_1m_usd"]),
            output_rate_per_1m_usd=float(row["output_rate_per_1m_usd"]),
            reasoning_output_policy=str(row["reasoning_output_policy"]),
        )
        for row in prices
    ]


def lookup_price(prices: list[ModelPrice], endpoint_host_hash: str, model: str, allow_missing_price_estimate: bool = False) -> ModelPrice | None:
    for price in prices:
        if price.endpoint_host_hash == endpoint_host_hash and price.model == model:
            return price
    if allow_missing_price_estimate:
        return None
    raise KeyError(f"missing price for endpoint_host_hash={endpoint_host_hash!r} model={model!r}")


def estimate_token_cost_usd(
    price: ModelPrice,
    *,
    input_tokens: int,
    cached_input_tokens: int,
    output_tokens: int,
    reasoning_output_tokens: int = 0,
) -> float:
    if price.reasoning_output_policy != "included_in_output_tokens" and reasoning_output_tokens:
        raise ValueError(f"unsupported reasoning output policy: {price.reasoning_output_policy}")
    uncached_input_tokens = max(input_tokens - cached_input_tokens, 0)
    total = (
        uncached_input_tokens * price.input_rate_per_1m_usd
        + cached_input_tokens * price.cached_input_rate_per_1m_usd
        + output_tokens * price.output_rate_per_1m_usd
    ) / 1_000_000
    return round(total, 8)
