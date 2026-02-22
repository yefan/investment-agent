from __future__ import annotations

import json

from pydantic import ValidationError

from .models import PortfolioSnapshot, RecommendationContract


def build_llm_instruction_payload(
    *,
    symbol: str,
    horizon: str,
    risk_preference: str,
    market_context: dict,
    ta_context: dict,
    portfolio: PortfolioSnapshot,
    chart_paths: list[str],
) -> str:
    payload = {
        "user_query_context": {
            "symbol": symbol.upper(),
            "horizon": horizon,
            "risk_preference": risk_preference,
            "intent": "analysis_and_strategy_recommendation",
        },
        "market_context": market_context,
        "technical_indicators": ta_context,
        "ta_chart_images": chart_paths,
        "portfolio_context": portfolio.model_dump(),
        "response_contract": {
            "required_format": "json_only",
            "schema_name": "RecommendationContract",
            "requirements": [
                "Must include ranked recommendations list.",
                "May include equity and options hedge recommendations.",
                "Must respect max_position_weight and min_cash_buffer constraints.",
                "If stale or conflicting data, prefer conservative hold/reduced sizing.",
                "Include confidence, uncertainty_notes, key_signals, and rationale.",
            ],
        },
    }
    return json.dumps(payload, indent=2)


def validate_recommendation_guardrails(
    recommendation: RecommendationContract,
    portfolio: PortfolioSnapshot,
) -> list[str]:
    violations: list[str] = []
    if not 0 <= recommendation.confidence <= 1:
        violations.append("confidence must be between 0 and 1")
    if not recommendation.recommendations:
        violations.append("at least one recommendation item is required")
    suggested = recommendation.position_sizing_hint.suggested_capital_fraction
    max_allowed = recommendation.position_sizing_hint.max_allowed_fraction
    constraint_max = portfolio.constraints.max_position_weight
    if suggested is not None and suggested > constraint_max:
        violations.append("suggested_capital_fraction exceeds portfolio max_position_weight")
    if max_allowed is not None and max_allowed > constraint_max:
        violations.append("max_allowed_fraction exceeds portfolio max_position_weight")
    return violations


def parse_recommendation_contract(raw_json: str) -> RecommendationContract:
    try:
        payload = json.loads(raw_json)
        return RecommendationContract.model_validate(payload)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError(f"Invalid recommendation output: {exc}") from exc
