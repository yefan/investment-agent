from __future__ import annotations

from investment_agent.models import PortfolioSnapshot
from investment_agent.recommendation import (
    parse_recommendation_contract,
    validate_recommendation_guardrails,
)


def test_recommendation_contract_parsing_and_guardrails():
    raw = """
{
  "input_symbol": "NVDA",
  "timestamp_utc": "2026-02-20T10:15:00Z",
  "overall_view": "bullish_with_hedge",
  "confidence": 0.78,
  "decision_mode": "llm_reasoned",
  "recommendations": [
    {
      "instrument_type": "equity",
      "symbol": "NVDA",
      "action": "buy",
      "priority": 1,
      "suggested_capital_fraction": 0.02,
      "thesis": "Primary trend continuation with improving momentum"
    }
  ],
  "key_signals": [
    "Price above 50/200 SMA",
    "MACD bullish crossover"
  ],
  "portfolio_impact": {
    "pre_trade_weight": 0.04,
    "post_trade_weight_estimate": 0.07,
    "cash_after_trade_estimate": 0.11
  },
  "risk_flags": [],
  "position_sizing_hint": {
    "suggested_capital_fraction": 0.02,
    "max_allowed_fraction": 0.05
  },
  "ta_chart_images": [],
  "uncertainty_notes": [],
  "rationale": "Trend and momentum are supportive."
}
"""
    contract = parse_recommendation_contract(raw)
    portfolio = PortfolioSnapshot.model_validate(
        {
            "base_currency": "USD",
            "cash_available": 5000,
            "risk_profile": "moderate",
            "constraints": {"max_position_weight": 0.2, "min_cash_buffer": 0.05},
            "holdings": [],
        }
    )
    violations = validate_recommendation_guardrails(contract, portfolio)
    assert violations == []
