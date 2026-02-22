from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pandas as pd

from investment_agent.cache import HistoricalDataCache, build_cache_key


def _sample_df() -> pd.DataFrame:
    idx = pd.date_range("2025-01-01", periods=5, freq="D")
    return pd.DataFrame(
        {
            "Open": [1, 2, 3, 4, 5],
            "High": [2, 3, 4, 5, 6],
            "Low": [0.5, 1.5, 2.5, 3.5, 4.5],
            "Close": [1.5, 2.5, 3.5, 4.5, 5.5],
            "Volume": [100, 110, 120, 130, 140],
        },
        index=idx,
    )


def test_cache_put_and_hit(tmp_path):
    cache = HistoricalDataCache(cache_dir=tmp_path)
    key = build_cache_key("NVDA", "1d", "1y")
    cache.put(key, _sample_df(), symbol="NVDA", interval="1d", period="1y")
    entry = cache.get(key)
    assert entry is not None
    assert entry.cache_status == "hit"
    assert entry.stale is False
    assert len(entry.data) == 5


def test_cache_stale_detection(tmp_path):
    cache = HistoricalDataCache(cache_dir=tmp_path)
    key = build_cache_key("NVDA", "1d", "1y")
    cache.put(key, _sample_df(), symbol="NVDA", interval="1d", period="1y")

    meta_path = tmp_path / f"{key}.meta.json"
    with meta_path.open("r", encoding="utf-8") as handle:
        meta = json.load(handle)
    meta["expires_at"] = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    with meta_path.open("w", encoding="utf-8") as handle:
        json.dump(meta, handle)

    entry = cache.get(key)
    assert entry is not None
    assert entry.cache_status == "stale_fallback"
    assert entry.stale is True
