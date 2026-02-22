from __future__ import annotations

from google.adk.agents.llm_agent import Agent

from .config import MODEL_NAME
from .tools import (
    compute_technical_context,
    generate_technical_chart,
    get_market_context,
    get_portfolio_snapshot,
    prepare_evidence_package,
)


root_agent = Agent(
    model=MODEL_NAME,
    name="investment_analysis_agent",
    description=(
        "Portfolio-aware investment analysis agent that uses yfinance, technical indicators, "
        "and portfolio constraints to produce ranked recommendations."
    ),
    instruction="""
You are a portfolio-aware investment analysis agent.

Always follow this lifecycle:
1) Parse user query and resolve symbol, horizon, and risk preference.
2) Call prepare_evidence_package first unless user asks only for a partial tool response.
3) Use evidence payload to reason across market data, technical indicators, and portfolio constraints.
4) Produce final response as strict JSON only, matching RecommendationContract schema.

Decision policy:
- Final decision must be LLM-reasoned from evidence.
- You may recommend equity actions, options hedges, or no-trade outcomes.
- If data is stale, missing, or conflicting, prefer conservative recommendations.
- Respect max_position_weight and min_cash_buffer constraints.

Output requirements:
- ranked recommendations with priority
- confidence between 0 and 1
- key_signals and risk_flags
- uncertainty_notes when evidence conflicts
- clear rationale
""",
    tools=[
        get_portfolio_snapshot,
        get_market_context,
        compute_technical_context,
        generate_technical_chart,
        prepare_evidence_package,
    ],
)
