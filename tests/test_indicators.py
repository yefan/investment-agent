from __future__ import annotations

import numpy as np
import pandas as pd

from investment_agent.technical_analysis import compute_indicators


def test_indicator_engine_outputs_core_fields():
    periods = 260
    idx = pd.date_range("2024-01-01", periods=periods, freq="D")
    close = np.linspace(100, 150, periods)
    data = pd.DataFrame(
        {
            "Open": close - 1,
            "High": close + 2,
            "Low": close - 2,
            "Close": close,
            "Volume": np.linspace(1_000_000, 1_400_000, periods),
        },
        index=idx,
    )

    enriched, summary = compute_indicators(data)
    assert "SMA_20" in enriched.columns
    assert "EMA_12" in enriched.columns
    assert "RSI_14" in enriched.columns
    assert summary["trend_regime"] in {"uptrend", "downtrend", "sideways"}
    assert summary["rsi14"] is not None
    assert 0 <= summary["rsi14"] <= 100
