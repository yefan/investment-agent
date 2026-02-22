from __future__ import annotations

import time

import pandas as pd
import yfinance as yf

from .cache import HistoricalDataCache, build_cache_key
from .config import DEFAULT_INTERVAL, DEFAULT_PERIOD


class DataUnavailableError(RuntimeError):
    pass


def _fetch_from_yfinance(symbol: str, interval: str, period: str) -> pd.DataFrame:
    ticker = yf.Ticker(symbol)
    history = ticker.history(period=period, interval=interval, auto_adjust=False)
    if history is None or history.empty:
        raise DataUnavailableError(f"No market data returned for {symbol}")
    history = history[["Open", "High", "Low", "Close", "Volume"]].dropna()
    return history


def get_historical_data(
    symbol: str,
    interval: str = DEFAULT_INTERVAL,
    period: str = DEFAULT_PERIOD,
    *,
    cache: HistoricalDataCache | None = None,
    max_retries: int = 2,
) -> tuple[pd.DataFrame, dict]:
    cache_instance = cache or HistoricalDataCache()
    key = build_cache_key(symbol, interval, period)

    cache_entry = cache_instance.get(key)
    if cache_entry and not cache_entry.stale:
        return cache_entry.data, {"cache": "hit", "stale": False, "warnings": []}

    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            fresh = _fetch_from_yfinance(symbol=symbol, interval=interval, period=period)
            cache_instance.put(
                key,
                fresh,
                symbol=symbol,
                interval=interval,
                period=period,
                source="yfinance",
            )
            return fresh, {"cache": "miss_refreshed", "stale": False, "warnings": []}
        except Exception as exc:
            last_error = exc
            if attempt < max_retries:
                time.sleep(1.5 * (attempt + 1))

    if cache_entry is not None:
        return cache_entry.data, {
            "cache": "stale_fallback",
            "stale": True,
            "warnings": ["Using stale cached data because live fetch failed."],
        }
    raise DataUnavailableError(f"No historical data for {symbol}") from last_error


def get_market_data_tool(
    symbol: str,
    interval: str = DEFAULT_INTERVAL,
    period: str = DEFAULT_PERIOD,
) -> dict:
    data, meta = get_historical_data(symbol=symbol, interval=interval, period=period)
    latest = data.tail(120).copy()
    return {
        "symbol": symbol.upper(),
        "interval": interval,
        "period": period,
        "meta": meta,
        "bars": latest.reset_index().to_dict(orient="records"),
    }
