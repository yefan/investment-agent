from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = BASE_DIR / ".cache" / "market_data"
CHART_DIR = BASE_DIR / ".cache" / "charts"
PORTFOLIO_PATH = Path(os.getenv("PORTFOLIO_PATH", str(DATA_DIR / "portfolio.json")))
MODEL_NAME = os.getenv("INVESTMENT_AGENT_MODEL", "gemini-2.0-flash")

TTL_BY_INTERVAL_SECONDS = {
    "1d": 60 * 60 * 12,
    "1h": 60 * 30,
    "15m": 60 * 10,
}

DEFAULT_INTERVAL = "1d"
DEFAULT_PERIOD = "1y"
