"""
OTM Flex™
Technical Indicators Module

Calculates the technical indicators used by the
OTM Flex™ credit spread strategy.
"""

import pandas as pd
import numpy as np


# ============================================================
# EMA
# ============================================================

def calculate_ema(data: pd.DataFrame, period: int):
    """
    Calculate Exponential Moving Average.
    """

    if data.empty:
        return pd.Series(dtype=float)

    return data["Close"].ewm(
        span=period,
        adjust=False
    ).mean()


# ============================================================
# RSI
# ============================================================

def calculate_rsi(
    data: pd.DataFrame,
    period: int = 14
):
    """
    Calculate Relative Strength Index.
    """

    if data.empty:
        return pd.Series(dtype=float)

    delta = data["Close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    average_gain = gain.ewm(
        alpha=1 / period,
        adjust=False
    ).mean()

    average_loss = loss.ewm(
        alpha=1 / period,
        adjust=False
    ).mean()

    rs = average_gain / average_loss.replace(
        0,
        np.nan
    )

    rsi = 100 - (
        100 / (1 + rs)
    )

    return rsi


# ============================================================
# MACD
# ============================================================

def calculate_macd(
    data: pd.DataFrame,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
):
    """
    Calculate MACD, signal line and histogram.
    """

    if data.empty:
        return pd.DataFrame()

    fast_ema = data["Close"].ewm(
        span=fast_period,
        adjust=False
    ).mean()

    slow_ema = data["Close"].ewm(
        span=slow_period,
        adjust=False
    ).mean()

    macd = fast_ema - slow_ema

    signal = macd.ewm(
        span=signal_period,
        adjust=False
    ).mean()

    histogram = macd - signal

    result = pd.DataFrame(
        {
            "MACD": macd,
            "Signal": signal,
            "Histogram": histogram,
        },
        index=data.index,
    )

    return result


# ============================================================
# ATR
# ============================================================

def calculate_atr(
    data: pd.DataFrame,
    period: int = 14
):
    """
    Calculate Average True Range.
    """

    if data.empty:
        return pd.Series(dtype=float)

    high = data["High"]
    low = data["Low"]
    close = data["Close"]

    previous_close = close.shift(1)

    true_range = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr = true_range.ewm(
        alpha=1 / period,
        adjust=False
    ).mean()

    return atr


# ============================================================
# ALL INDICATORS
# ============================================================

def calculate_indicators(data: pd.DataFrame):
    """
    Calculate all OTM Flex™ technical indicators.

    Returns:
        DataFrame containing price and indicators.
    """

    if data.empty:
        return pd.DataFrame()

    result = data.copy()

    # Moving averages
    result["EMA20"] = calculate_ema(
        data,
        20
    )

    result["EMA50"] = calculate_ema(
        data,
        50
    )

    result["EMA200"] = calculate_ema(
        data,
        200
    )

    # RSI
    result["RSI"] = calculate_rsi(
        data,
        14
    )

    # MACD
    macd = calculate_macd(data)

    result["MACD"] = macd["MACD"]
    result["MACD_Signal"] = macd["Signal"]
    result["MACD_Histogram"] = macd["Histogram"]

    # ATR
    result["ATR"] = calculate_atr(
        data,
        14
    )

    return result


# ============================================================
# LATEST INDICATOR VALUES
# ============================================================

def get_latest_indicators(data: pd.DataFrame):
    """
    Return the most recent indicator values.
    """

    indicators = calculate_indicators(data)

    if indicators.empty:
        return None

    latest = indicators.iloc[-1]

    return {
        "price": float(latest["Close"]),

        "ema20": float(latest["EMA20"]),

        "ema50": float(latest["EMA50"]),

        "ema200": float(latest["EMA200"]),

        "rsi": float(latest["RSI"]),

        "macd": float(latest["MACD"]),

        "macd_signal": float(
            latest["MACD_Signal"]
        ),

        "macd_histogram": float(
            latest["MACD_Histogram"]
        ),

        "atr": float(latest["ATR"]),
    }


# ============================================================
# TREND CLASSIFICATION
# ============================================================

def determine_trend(indicators: dict):
    """
    Determine the basic OTM Flex™ trend.

    Bullish:
        Price > EMA20 > EMA50 > EMA200

    Bearish:
        Price < EMA20 < EMA50 < EMA200

    Otherwise:
        Neutral
    """

    if not indicators:
        return "Unknown"

    price = indicators["price"]
    ema20 = indicators["ema20"]
    ema50 = indicators["ema50"]
    ema200 = indicators["ema200"]

    if (
        price > ema20
        and ema20 > ema50
        and ema50 > ema200
    ):
        return "Bullish"

    if (
        price < ema20
        and ema20 < ema50
        and ema50 < ema200
    ):
        return "Bearish"

    return "Neutral"
