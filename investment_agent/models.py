from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class Holding(BaseModel):
    symbol: str
    quantity: float
    avg_cost: float
    market_value: float


class Constraints(BaseModel):
    max_position_weight: float = 0.2
    max_sector_weight: float | None = None
    min_cash_buffer: float = 0.05


class PortfolioSnapshot(BaseModel):
    base_currency: str = "USD"
    cash_available: float
    risk_profile: Literal["conservative", "moderate", "aggressive"] = "moderate"
    constraints: Constraints = Field(default_factory=Constraints)
    holdings: list[Holding] = Field(default_factory=list)


class UserQueryContext(BaseModel):
    symbol: str
    horizon: str = "swing"
    risk_preference: str = "moderate"
    intent: str = "analyze"


class RecommendationItem(BaseModel):
    instrument_type: Literal["equity", "option"]
    symbol: str | None = None
    underlier: str | None = None
    action: str | None = None
    strategy: str | None = None
    priority: int
    suggested_capital_fraction: float | None = None
    thesis: str


class PortfolioImpact(BaseModel):
    pre_trade_weight: float | None = None
    post_trade_weight_estimate: float | None = None
    cash_after_trade_estimate: float | None = None


class PositionSizingHint(BaseModel):
    suggested_capital_fraction: float | None = None
    max_allowed_fraction: float | None = None


class RecommendationContract(BaseModel):
    input_symbol: str
    timestamp_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    overall_view: str
    confidence: float
    decision_mode: Literal["llm_reasoned"] = "llm_reasoned"
    recommendations: list[RecommendationItem]
    key_signals: list[str]
    portfolio_impact: PortfolioImpact = Field(default_factory=PortfolioImpact)
    risk_flags: list[str] = Field(default_factory=list)
    position_sizing_hint: PositionSizingHint = Field(default_factory=PositionSizingHint)
    ta_chart_images: list[str] = Field(default_factory=list)
    uncertainty_notes: list[str] = Field(default_factory=list)
    rationale: str


class DataQuality(BaseModel):
    cache_status: Literal["hit", "miss_refreshed", "stale_fallback"]
    stale: bool = False
    warnings: list[str] = Field(default_factory=list)
