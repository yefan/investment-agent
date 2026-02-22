from __future__ import annotations

from .charts import generate_ta_chart
from .config import DEFAULT_INTERVAL, DEFAULT_PERIOD
from .market_data import DataUnavailableError, get_historical_data, get_market_data_tool
from .portfolio import load_portfolio
from .recommendation import build_llm_instruction_payload
from .technical_analysis import compute_indicators


def get_portfolio_snapshot() -> dict:
    """Return the user's portfolio snapshot from local storage."""
    return load_portfolio().model_dump()


def get_market_context(
    symbol: str,
    interval: str = DEFAULT_INTERVAL,
    period: str = DEFAULT_PERIOD,
) -> dict:
    """Return recent OHLCV data plus cache freshness metadata for a symbol."""
    return get_market_data_tool(symbol=symbol, interval=interval, period=period)


def compute_technical_context(
    symbol: str,
    interval: str = DEFAULT_INTERVAL,
    period: str = DEFAULT_PERIOD,
) -> dict:
    """Compute technical indicators and structure signals for the symbol."""
    data, meta = get_historical_data(symbol=symbol, interval=interval, period=period)
    enriched, summary = compute_indicators(data)
    return {
        "symbol": symbol.upper(),
        "interval": interval,
        "period": period,
        "data_quality": meta,
        "summary": summary,
        "indicator_snapshot": enriched.tail(50).reset_index().to_dict(orient="records"),
    }


def generate_technical_chart(
    symbol: str,
    interval: str = DEFAULT_INTERVAL,
    period: str = DEFAULT_PERIOD,
) -> dict:
    """Generate TA candlestick chart image with overlays and return file path."""
    data, meta = get_historical_data(symbol=symbol, interval=interval, period=period)
    enriched, _ = compute_indicators(data)
    chart_path = generate_ta_chart(symbol=symbol, enriched_data=enriched)
    return {
        "symbol": symbol.upper(),
        "chart_path": chart_path,
        "data_quality": meta,
    }


def prepare_evidence_package(
    symbol: str,
    horizon: str = "swing",
    risk_preference: str = "moderate",
    interval: str = DEFAULT_INTERVAL,
    period: str = DEFAULT_PERIOD,
) -> dict:
    """Build full evidence payload for LLM final recommendation synthesis."""
    portfolio = load_portfolio()
    try:
        market = get_market_data_tool(symbol=symbol, interval=interval, period=period)
        ta = compute_technical_context(symbol=symbol, interval=interval, period=period)
        chart = generate_technical_chart(symbol=symbol, interval=interval, period=period)
        chart_paths = [chart["chart_path"]]
    except DataUnavailableError:
        market = {
            "symbol": symbol.upper(),
            "interval": interval,
            "period": period,
            "meta": {
                "cache": "stale_fallback",
                "stale": True,
                "warnings": ["No live or cached data available."],
            },
            "bars": [],
        }
        ta = {"summary": {}, "indicator_snapshot": [], "data_quality": market["meta"]}
        chart_paths = []

    prompt_payload = build_llm_instruction_payload(
        symbol=symbol,
        horizon=horizon,
        risk_preference=risk_preference,
        market_context=market,
        ta_context=ta,
        portfolio=portfolio,
        chart_paths=chart_paths,
    )
    return {
        "evidence_payload_json": prompt_payload,
        "chart_paths": chart_paths,
        "data_quality": market.get("meta", {}),
    }
