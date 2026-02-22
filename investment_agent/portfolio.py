from __future__ import annotations

import json
from pathlib import Path

from .config import PORTFOLIO_PATH
from .models import PortfolioSnapshot


def load_portfolio(path: Path | None = None) -> PortfolioSnapshot:
    target_path = path or PORTFOLIO_PATH
    if not target_path.exists():
        raise FileNotFoundError(f"Portfolio file not found: {target_path}")
    with target_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return PortfolioSnapshot.model_validate(payload)


def get_portfolio_tool() -> dict:
    portfolio = load_portfolio()
    return portfolio.model_dump()
