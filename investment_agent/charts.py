from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import mplfinance as mpf
import pandas as pd

from .config import CHART_DIR


def generate_ta_chart(
    symbol: str,
    enriched_data: pd.DataFrame,
    output_dir: Path | None = None,
) -> str:
    target_dir = output_dir or CHART_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = (
        f"{symbol.upper()}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.png"
    )
    output_path = target_dir / filename

    chart_df = enriched_data.copy().tail(180)
    overlays = []
    for col in ["SMA_20", "SMA_50", "SMA_200", "EMA_12", "EMA_26"]:
        if col in chart_df.columns:
            overlays.append(mpf.make_addplot(chart_df[col]))

    macd_cols = [c for c in chart_df.columns if "MACD_12_26_9" in c or "MACDs_12_26_9" in c]
    if len(macd_cols) >= 2:
        overlays.extend(
            [
                mpf.make_addplot(chart_df[macd_cols[0]], panel=1, color="blue"),
                mpf.make_addplot(chart_df[macd_cols[1]], panel=1, color="orange"),
            ]
        )

    bb_cols = [c for c in chart_df.columns if c.startswith("BBL_20_2.0") or c.startswith("BBU_20_2.0")]
    for col in bb_cols:
        overlays.append(mpf.make_addplot(chart_df[col], color="gray"))

    mpf.plot(
        chart_df,
        type="candle",
        style="yahoo",
        volume=True,
        addplot=overlays or None,
        panel_ratios=(3, 1) if len(macd_cols) >= 2 else (1,),
        savefig=str(output_path),
    )
    return str(output_path)
