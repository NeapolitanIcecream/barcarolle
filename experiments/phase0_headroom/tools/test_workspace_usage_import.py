from __future__ import annotations

from pathlib import Path

import pytest

import workspace_usage_import as usage


def write_pricing(path: Path) -> Path:
    config = path / "model_pricing.yaml"
    config.write_text(
        "\n".join(
            [
                "schema_version: barcarolle.model_pricing.v1",
                "default_currency: USD",
                "prices:",
                '  - endpoint_host_hash: "host123"',
                "    model: gpt-5.4-mini",
                "    pricing_source: test",
                "    input_rate_per_1m_usd: 3.0",
                "    cached_input_rate_per_1m_usd: 0.3",
                "    output_rate_per_1m_usd: 15.0",
                "    reasoning_output_policy: included_in_output_tokens",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return config


def test_price_lookup_by_endpoint_hash_and_model(tmp_path: Path) -> None:
    prices = usage.load_model_prices(write_pricing(tmp_path))

    price = usage.lookup_price(prices, "host123", "gpt-5.4-mini")

    assert price is not None
    assert price.pricing_source == "test"
    assert price.output_rate_per_1m_usd == 15.0


def test_missing_model_price_fails_closed(tmp_path: Path) -> None:
    prices = usage.load_model_prices(write_pricing(tmp_path))

    with pytest.raises(KeyError, match="missing price"):
        usage.lookup_price(prices, "host123", "unknown-model")


def test_missing_model_price_can_be_explicitly_allowed(tmp_path: Path) -> None:
    prices = usage.load_model_prices(write_pricing(tmp_path))

    assert usage.lookup_price(prices, "host123", "unknown-model", allow_missing_price_estimate=True) is None


def test_token_cost_uses_uncached_cached_and_output_rates(tmp_path: Path) -> None:
    price = usage.lookup_price(usage.load_model_prices(write_pricing(tmp_path)), "host123", "gpt-5.4-mini")

    cost = usage.estimate_token_cost_usd(
        price,
        input_tokens=1_000_000,
        cached_input_tokens=100_000,
        output_tokens=10_000,
        reasoning_output_tokens=500,
    )

    assert cost == 2.88
