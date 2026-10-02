"""
OTM Flex™
Market Data Module

Provides current market prices and historical price data
for the supported ETF underlyings.
"""

import yfinance as yf
import pandas as pd


# ============================================================
# SUPPORTED UNDERLYINGS
# ============================================================

SUPPORTED_TICKERS = [
    "SPY",
    "QQQ",
    "IWM",
    "VOO",
]


# ============================================================
# CURRENT PRICE
# ============================================================

def get_current_price(ticker: str):
    """
    Get the most recent available market price.

    Returns:
        float or None
    """

    if ticker not in SUPPORTED_TICKERS:
        raise ValueError(
            f"{ticker} is not a supported underlying."
        )

    try:
        stock = yf.Ticker(ticker)

        history = stock.history(
            period="5d",
            interval="1d",
        )

        if history.empty:
            return None

        price = history["Close"].dropna().iloc[-1]

        return float(price)

    except Exception:
        return None


# ============================================================
# HISTORICAL DATA
# ============================================================

def get_historical_data(
    ticker: str,
    period: str = "1y",
    interval: str = "1d",
):
    """
    Download historical OHLCV data.

    Parameters:
        ticker: ETF symbol
        period: Yahoo Finance period
        interval: Candle interval

    Returns:
        pandas DataFrame
    """

    if ticker not in SUPPORTED_TICKERS:
        raise ValueError(
            f"{ticker} is not a supported underlying."
        )

    try:

        stock = yf.Ticker(ticker)

        data = stock.history(
            period=period,
            interval=interval,
            auto_adjust=False,
        )

        if data.empty:
            return pd.DataFrame()

        data = data.dropna(
            subset=["Open", "High", "Low", "Close"]
        )

        return data

    except Exception:
        return pd.DataFrame()


# ============================================================
# MARKET SNAPSHOT
# ============================================================

def get_market_snapshot():
    """
    Return current prices for all supported ETFs.

    Returns:
        Dictionary containing prices.
    """

    snapshot = {}

    for ticker in SUPPORTED_TICKERS:

        price = get_current_price(ticker)

        snapshot[ticker] = price

    return snapshot


# ============================================================
# PRICE CHANGE
# ============================================================

def get_price_change(ticker: str):
    """
    Calculate the latest daily price change.

    Returns:
        Dictionary containing:
        current price
        previous close
        dollar change
        percentage change
    """

    if ticker not in SUPPORTED_TICKERS:
        raise ValueError(
            f"{ticker} is not a supported underlying."
        )

    try:

        stock = yf.Ticker(ticker)

        data = stock.history(
            period="5d",
            interval="1d",
        )

        if len(data) < 2:
            return None

        current = float(data["Close"].iloc[-1])
        previous = float(data["Close"].iloc[-2])

        change = current - previous

        percent_change = (
            change / previous
        ) * 100

        return {
            "current_price": current,
            "previous_close": previous,
            "change": change,
            "percent_change": percent_change,
        }

    except Exception:
        return None
