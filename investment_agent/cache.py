from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from .config import CACHE_DIR, TTL_BY_INTERVAL_SECONDS


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_cache_key(symbol: str, interval: str, period: str) -> str:
    return f"{symbol.upper()}_{interval}_{period}"


@dataclass
class CacheEntry:
    data: pd.DataFrame
    cache_status: str
    stale: bool
    metadata: dict


class HistoricalDataCache:
    def __init__(self, cache_dir: Path | None = None):
        self.cache_dir = cache_dir or CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _csv_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.csv"

    def _meta_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.meta.json"

    def get(self, key: str) -> CacheEntry | None:
        csv_path = self._csv_path(key)
        meta_path = self._meta_path(key)
        if not csv_path.exists() or not meta_path.exists():
            return None

        with meta_path.open("r", encoding="utf-8") as handle:
            metadata = json.load(handle)
        data = pd.read_csv(csv_path, index_col=0, parse_dates=True)
        stale = datetime.fromisoformat(metadata["expires_at"]) <= _utc_now()
        return CacheEntry(
            data=data,
            cache_status="stale_fallback" if stale else "hit",
            stale=stale,
            metadata=metadata,
        )

    def put(
        self,
        key: str,
        data: pd.DataFrame,
        *,
        symbol: str,
        interval: str,
        period: str,
        source: str = "yfinance",
    ) -> None:
        ttl = TTL_BY_INTERVAL_SECONDS.get(interval, TTL_BY_INTERVAL_SECONDS["1d"])
        created_at = _utc_now()
        expires_at = created_at + timedelta(seconds=ttl)

        data.to_csv(self._csv_path(key))
        metadata = {
            "symbol": symbol.upper(),
            "interval": interval,
            "period": period,
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "row_count": int(len(data)),
            "source": source,
        }
        with self._meta_path(key).open("w", encoding="utf-8") as handle:
            json.dump(metadata, handle, indent=2)
