from __future__ import annotations

import numpy as np
import pandas as pd


def _sma(series: pd.Series, length: int) -> pd.Series:
    return series.rolling(length).mean()


def _ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()


def _wma(series: pd.Series, length: int) -> pd.Series:
    weights = np.arange(1, length + 1)
    return series.rolling(length).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)


def _rsi(series: pd.Series, length: int = 14) -> pd.Series:
    delta = series.diff()
    gains = delta.clip(lower=0).ewm(alpha=1 / length, adjust=False).mean()
    losses = (-delta.clip(upper=0)).ewm(alpha=1 / length, adjust=False).mean()
    rs = gains / losses.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.where(losses != 0, 100)
    rsi = rsi.where(gains != 0, 0)
    return rsi


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / length, adjust=False).mean()


def _adx(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> tuple[pd.Series, pd.Series, pd.Series]:
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    tr = _atr(high, low, close, length=1)
    plus_di = 100 * pd.Series(plus_dm, index=high.index).ewm(alpha=1 / length, adjust=False).mean() / tr.replace(0, np.nan)
    minus_di = 100 * pd.Series(minus_dm, index=high.index).ewm(alpha=1 / length, adjust=False).mean() / tr.replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.ewm(alpha=1 / length, adjust=False).mean()
    return adx, plus_di, minus_di


def _cci(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 20) -> pd.Series:
    tp = (high + low + close) / 3
    sma_tp = tp.rolling(length).mean()
    md = tp.rolling(length).apply(lambda x: np.mean(np.abs(x - np.mean(x))), raw=True)
    return (tp - sma_tp) / (0.015 * md.replace(0, np.nan))


def _roc(close: pd.Series, length: int = 12) -> pd.Series:
    return (close / close.shift(length) - 1) * 100


def _willr(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.Series:
    highest = high.rolling(length).max()
    lowest = low.rolling(length).min()
    return -100 * (highest - close) / (highest - lowest).replace(0, np.nan)


def _stoch(high: pd.Series, low: pd.Series, close: pd.Series, k: int = 14, d: int = 3) -> tuple[pd.Series, pd.Series]:
    lowest = low.rolling(k).min()
    highest = high.rolling(k).max()
    stoch_k = 100 * (close - lowest) / (highest - lowest).replace(0, np.nan)
    stoch_d = stoch_k.rolling(d).mean()
    return stoch_k, stoch_d


def _mfi(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, length: int = 14) -> pd.Series:
    tp = (high + low + close) / 3
    raw_flow = tp * volume
    direction = tp.diff()
    pos = raw_flow.where(direction > 0, 0.0)
    neg = raw_flow.where(direction < 0, 0.0).abs()
    pos_sum = pos.rolling(length).sum()
    neg_sum = neg.rolling(length).sum()
    ratio = pos_sum / neg_sum.replace(0, np.nan)
    return 100 - (100 / (1 + ratio))


def _cmf(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, length: int = 20) -> pd.Series:
    mf_multiplier = ((close - low) - (high - close)) / (high - low).replace(0, np.nan)
    mf_volume = mf_multiplier * volume
    return mf_volume.rolling(length).sum() / volume.rolling(length).sum().replace(0, np.nan)


def _adl(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    mf_multiplier = ((close - low) - (high - close)) / (high - low).replace(0, np.nan)
    return (mf_multiplier.fillna(0) * volume).cumsum()


def _vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    typical_price = (high + low + close) / 3
    cum_vol = volume.cumsum().replace(0, np.nan)
    return (typical_price * volume).cumsum() / cum_vol


def _obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    direction = np.sign(close.diff().fillna(0))
    return (direction * volume).cumsum()


def _safe_last(value: pd.Series) -> float | None:
    if value is None or value.empty:
        return None
    val = value.dropna()
    if val.empty:
        return None
    return float(val.iloc[-1])


def _market_structure(close: pd.Series, high: pd.Series, low: pd.Series) -> dict:
    rolling_high = high.rolling(window=20).max()
    rolling_low = low.rolling(window=20).min()
    latest_close = close.iloc[-1]
    resistance = rolling_high.iloc[-1]
    support = rolling_low.iloc[-1]
    breakout = latest_close > resistance * 0.995
    breakdown = latest_close < support * 1.005

    sma50 = close.rolling(50).mean()
    sma200 = close.rolling(200).mean()
    regime = "sideways"
    if len(sma200.dropna()) > 0:
        if sma50.iloc[-1] > sma200.iloc[-1]:
            regime = "uptrend"
        elif sma50.iloc[-1] < sma200.iloc[-1]:
            regime = "downtrend"

    pivot = (high.iloc[-1] + low.iloc[-1] + close.iloc[-1]) / 3
    return {
        "support_zone": float(support) if not np.isnan(support) else None,
        "resistance_zone": float(resistance) if not np.isnan(resistance) else None,
        "pivot_point": float(pivot),
        "breakout_detected": bool(breakout),
        "range_breakdown_detected": bool(breakdown),
        "trend_regime": regime,
    }


def compute_indicators(data: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    df = data.copy()

    df["SMA_20"] = _sma(df["Close"], 20)
    df["SMA_50"] = _sma(df["Close"], 50)
    df["SMA_200"] = _sma(df["Close"], 200)
    df["EMA_12"] = _ema(df["Close"], 12)
    df["EMA_26"] = _ema(df["Close"], 26)
    df["EMA_50"] = _ema(df["Close"], 50)
    df["WMA_20"] = _wma(df["Close"], 20)

    macd_line = df["EMA_12"] - df["EMA_26"]
    macd_signal = _ema(macd_line, 9)
    df["MACD_12_26_9"] = macd_line
    df["MACDs_12_26_9"] = macd_signal
    df["MACDh_12_26_9"] = macd_line - macd_signal

    adx, dmp, dmn = _adx(df["High"], df["Low"], df["Close"], 14)
    df["ADX_14"] = adx
    df["DMP_14"] = dmp
    df["DMN_14"] = dmn

    conversion = (df["High"].rolling(9).max() + df["Low"].rolling(9).min()) / 2
    base = (df["High"].rolling(26).max() + df["Low"].rolling(26).min()) / 2
    span_a = ((conversion + base) / 2).shift(26)
    span_b = ((df["High"].rolling(52).max() + df["Low"].rolling(52).min()) / 2).shift(26)
    df["ICHIMOKU_TENKAN_9"] = conversion
    df["ICHIMOKU_KIJUN_26"] = base
    df["ICHIMOKU_SENKOU_A"] = span_a
    df["ICHIMOKU_SENKOU_B"] = span_b

    stoch_k, stoch_d = _stoch(df["High"], df["Low"], df["Close"], 14, 3)
    df["STOCHk_14_3_3"] = stoch_k
    df["STOCHd_14_3_3"] = stoch_d
    df["CCI_20"] = _cci(df["High"], df["Low"], df["Close"], 20)
    df["ROC_12"] = _roc(df["Close"], 12)
    df["WILLR_14"] = _willr(df["High"], df["Low"], df["Close"], 14)

    df["ATR_14"] = _atr(df["High"], df["Low"], df["Close"], 14)
    bb_mid = _sma(df["Close"], 20)
    bb_std = df["Close"].rolling(20).std()
    df["BBL_20_2.0"] = bb_mid - 2 * bb_std
    df["BBM_20_2.0"] = bb_mid
    df["BBU_20_2.0"] = bb_mid + 2 * bb_std

    kc_mid = _ema(df["Close"], 20)
    kc_range = _atr(df["High"], df["Low"], df["Close"], 20) * 2
    df["KCL_20_2.0"] = kc_mid - kc_range
    df["KCB_20_2.0"] = kc_mid
    df["KCU_20_2.0"] = kc_mid + kc_range

    df["DCL_20_20"] = df["Low"].rolling(20).min()
    df["DCU_20_20"] = df["High"].rolling(20).max()
    df["DCM_20_20"] = (df["DCL_20_20"] + df["DCU_20_20"]) / 2

    df["OBV"] = _obv(df["Close"], df["Volume"])
    df["MFI_14"] = _mfi(df["High"], df["Low"], df["Close"], df["Volume"], 14)
    df["CMF_20"] = _cmf(df["High"], df["Low"], df["Close"], df["Volume"], 20)
    df["ADL"] = _adl(df["High"], df["Low"], df["Close"], df["Volume"])
    df["VWAP"] = _vwap(df["High"], df["Low"], df["Close"], df["Volume"])
    df["RSI_14"] = _rsi(df["Close"], 14)

    structure = _market_structure(df["Close"], df["High"], df["Low"])
    summary = {
        "close": _safe_last(df["Close"]),
        "sma20": _safe_last(df["SMA_20"]),
        "sma50": _safe_last(df["SMA_50"]),
        "sma200": _safe_last(df["SMA_200"]),
        "ema12": _safe_last(df["EMA_12"]),
        "ema26": _safe_last(df["EMA_26"]),
        "ema50": _safe_last(df["EMA_50"]),
        "rsi14": _safe_last(df["RSI_14"]),
        "atr14": _safe_last(df.get("ATR_14")),
        "mfi14": _safe_last(df.get("MFI_14")),
        "cmf20": _safe_last(df.get("CMF_20")),
        "macd_line": _safe_last(df.get("MACD_12_26_9")),
        "macd_signal": _safe_last(df.get("MACDs_12_26_9")),
        "adx14": _safe_last(df.get("ADX_14")),
        "stoch_k": _safe_last(df.get("STOCHk_14_3_3")),
        "stoch_d": _safe_last(df.get("STOCHd_14_3_3")),
        "roc12": _safe_last(df.get("ROC_12")),
        "willr14": _safe_last(df.get("WILLR_14")),
    }
    summary.update(structure)
    return df, summary


def compute_ta_tool_from_records(bars: list[dict]) -> dict:
    df = pd.DataFrame(bars)
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date")
    elif "Datetime" in df.columns:
        df["Datetime"] = pd.to_datetime(df["Datetime"])
        df = df.set_index("Datetime")
    df = df.sort_index()
    enriched, summary = compute_indicators(df)
    return {
        "summary": summary,
        "indicator_snapshot": enriched.tail(30).reset_index().to_dict(orient="records"),
    }
