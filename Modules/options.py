"""
OTM Flex™
Options Chain Module

Retrieves option-chain data and builds potential
Bull Put and Bear Call credit spreads.
"""

from datetime import date

import pandas as pd
import yfinance as yf


# ============================================================
# CONFIGURATION
# ============================================================

MIN_DTE = 7
MAX_DTE = 45

TARGET_DELTA_MIN = 0.10
TARGET_DELTA_MAX = 0.18


# ============================================================
# EXPIRATIONS
# ============================================================

def get_expirations(ticker: str):
    """
    Get all available option expiration dates.
    """

    stock = yf.Ticker(ticker)

    try:
        expirations = stock.options
    except Exception:
        return []

    return list(expirations)


# ============================================================
# DTE
# ============================================================

def calculate_dte(expiration: str):
    """
    Calculate days to expiration.
    """

    expiration_date = date.fromisoformat(expiration)

    today = date.today()

    return (
        expiration_date - today
    ).days


# ============================================================
# VALID EXPIRATIONS
# ============================================================

def get_valid_expirations(
    ticker: str,
    min_dte: int = MIN_DTE,
    max_dte: int = MAX_DTE,
):
    """
    Return expirations within the desired DTE range.
    """

    expirations = get_expirations(ticker)

    valid = []

    for expiration in expirations:

        dte = calculate_dte(expiration)

        if min_dte <= dte <= max_dte:

            valid.append(
                {
                    "expiration": expiration,
                    "dte": dte,
                }
            )

    return valid


# ============================================================
# OPTION CHAIN
# ============================================================

def get_option_chain(
    ticker: str,
    expiration: str,
):
    """
    Retrieve calls and puts for a specific expiration.
    """

    stock = yf.Ticker(ticker)

    try:

        chain = stock.option_chain(
            expiration
        )

        calls = chain.calls.copy()
        puts = chain.puts.copy()

        return calls, puts

    except Exception:

        return (
            pd.DataFrame(),
            pd.DataFrame(),
        )


# ============================================================
# DELTA COLUMN
# ============================================================

def find_delta_column(data: pd.DataFrame):
    """
    Find the delta column returned by the data source.

    Different data providers may name this differently.
    """

    possible_columns = [
        "delta",
        "Delta",
        "DELTA",
    ]

    for column in possible_columns:

        if column in data.columns:
            return column

    return None


# ============================================================
# CLEAN OPTION DATA
# ============================================================

def clean_option_data(
    data: pd.DataFrame,
):
    """
    Clean and standardize option-chain data.
    """

    if data.empty:
        return pd.DataFrame()

    result = data.copy()

    # Ensure required columns exist
    required = [
        "strike",
        "bid",
        "ask",
        "lastPrice",
        "volume",
        "openInterest",
    ]

    for column in required:

        if column not in result.columns:

            result[column] = 0.0

    # Numeric conversion
    for column in required:

        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        )

    # Remove invalid strikes
    result = result[
        result["strike"] > 0
    ]

    # Midpoint
    result["mid"] = (
        result["bid"] +
        result["ask"]
    ) / 2

    # Bid/ask width
    result["bid_ask_width"] = (
        result["ask"] -
        result["bid"]
    )

    # Percentage width
    result["bid_ask_width_pct"] = (
        result["bid_ask_width"] /
        result["mid"].replace(0, pd.NA)
    ) * 100

    return result


# ============================================================
# FIND OPTIONS BY DELTA
# ============================================================

def find_options_by_delta(
    data: pd.DataFrame,
    target_delta: float = 0.14,
):
    """
    Find options closest to the desired delta.

    Requires a delta column from the data provider.
    """

    if data.empty:
        return pd.DataFrame()

    delta_column = find_delta_column(data)

    if delta_column is None:
        return pd.DataFrame()

    result = data.copy()

    result[delta_column] = pd.to_numeric(
        result[delta_column],
        errors="coerce",
    )

    result = result.dropna(
        subset=[delta_column]
    )

    if result.empty:
        return pd.DataFrame()

    result["delta_distance"] = (
        result[delta_column].abs() -
        abs(target_delta)
    ).abs()

    result = result.sort_values(
        "delta_distance"
    )

    return result


# ============================================================
# FIND SHORT STRIKE
# ============================================================

def find_short_strike(
    data: pd.DataFrame,
    target_delta: float = 0.14,
):
    """
    Find the option closest to the target delta.
    """

    matches = find_options_by_delta(
        data,
        target_delta,
    )

    if matches.empty:
        return None

    return matches.iloc[0].to_dict()


# ============================================================
# FIND NEAREST LONG STRIKE
# ============================================================

def find_long_put(
    puts: pd.DataFrame,
    short_strike: float,
    width: float,
):
    """
    Find the put strike approximately one spread-width
    below the short put.
    """

    target = short_strike - width

    if puts.empty:
        return None

    puts = puts.copy()

    puts["strike_distance"] = (
        puts["strike"] - target
    ).abs()

    result = puts.sort_values(
        "strike_distance"
    ).iloc[0]

    return result.to_dict()


def find_long_call(
    calls: pd.DataFrame,
    short_strike: float,
    width: float,
):
    """
    Find the call strike approximately one spread-width
    above the short call.
    """

    target = short_strike + width

    if calls.empty:
        return None

    calls = calls.copy()

    calls["strike_distance"] = (
        calls["strike"] - target
    ).abs()

    result = calls.sort_values(
        "strike_distance"
    ).iloc[0]

    return result.to_dict()


# ============================================================
# BULL PUT SPREAD
# ============================================================

def build_bull_put_spread(
    puts: pd.DataFrame,
    short_delta: float = 0.14,
    width: float = 5.0,
):
    """
    Build a Bull Put credit spread.
    """

    if puts.empty:
        return None

    short_put = find_short_strike(
        puts,
        short_delta,
    )

    if short_put is None:
        return None

    short_strike = float(
        short_put["strike"]
    )

    long_put = find_long_put(
        puts,
        short_strike,
        width,
    )

    if long_put is None:
        return None

    long_strike = float(
        long_put["strike"]
    )

    short_bid = float(
        short_put.get("bid", 0)
    )

    short_ask = float(
        short_put.get("ask", 0)
    )

    long_bid = float(
        long_put.get("bid", 0)
    )

    long_ask = float(
        long_put.get("ask", 0)
    )

    short_mid = (
        short_bid +
        short_ask
    ) / 2

    long_mid = (
        long_bid +
        long_ask
    ) / 2

    credit = (
        short_mid -
        long_mid
    )

    actual_width = (
        short_strike -
        long_strike
    )

    max_loss = (
        actual_width -
        credit
    ) * 100

    max_profit = credit * 100

    return {
        "type": "Bull Put",
        "short_strike": short_strike,
        "long_strike": long_strike,
        "short_delta": short_put.get(
            "delta"
        ),
        "credit": credit,
        "max_profit": max_profit,
        "max_loss": max_loss,
        "risk_reward": (
            max_profit / max_loss
            if max_loss > 0
            else 0
        ),
    }


# ============================================================
# BEAR CALL SPREAD
# ============================================================

def build_bear_call_spread(
    calls: pd.DataFrame,
    short_delta: float = 0.14,
    width: float = 5.0,
):
    """
    Build a Bear Call credit spread.
    """

    if calls.empty:
        return None

    short_call = find_short_strike(
        calls,
        short_delta,
    )

    if short_call is None:
        return None

    short_strike = float(
        short_call["strike"]
    )

    long_call = find_long_call(
        calls,
        short_strike,
        width,
    )

    if long_call is None:
        return None

    long_strike = float(
        long_call["strike"]
    )

    short_bid = float(
        short_call.get("bid", 0)
    )

    short_ask = float(
        short_call.get("ask", 0)
    )

    long_bid = float(
        long_call.get("bid", 0)
    )

    long_ask = float(
        long_call.get("ask", 0)
    )

    short_mid = (
        short_bid +
        short_ask
    ) / 2

    long_mid = (
        long_bid +
        long_ask
    ) / 2

    credit = (
        short_mid -
        long_mid
    )

    actual_width = (
        long_strike -
        short_strike
    )

    max_loss = (
        actual_width -
        credit
    ) * 100

    max_profit = credit * 100

    return {
        "type": "Bear Call",
        "short_strike": short_strike,
        "long_strike": long_strike,
        "short_delta": short_call.get(
            "delta"
        ),
        "credit": credit,
        "max_profit": max_profit,
        "max_loss": max_loss,
        "risk_reward": (
            max_profit / max_loss
            if max_loss > 0
            else 0
        ),
    }


# ============================================================
# SPREAD SCANNER
# ============================================================

def scan_expiration(
    ticker: str,
    expiration: str,
    short_delta: float = 0.14,
    width: float = 5.0,
):
    """
    Scan one expiration for Bull Put and Bear Call spreads.
    """

    calls, puts = get_option_chain(
        ticker,
        expiration,
    )

    calls = clean_option_data(
        calls
    )

    puts = clean_option_data(
        puts
    )

    dte = calculate_dte(
        expiration
    )

    bull_put = build_bull_put_spread(
        puts,
        short_delta,
        width,
    )

    bear_call = build_bear_call_spread(
        calls,
        short_delta,
        width,
    )

    results = []

    if bull_put is not None:

        bull_put["ticker"] = ticker
        bull_put["expiration"] = expiration
        bull_put["dte"] = dte

        results.append(
            bull_put
        )

    if bear_call is not None:

        bear_call["ticker"] = ticker
        bear_call["expiration"] = expiration
        bear_call["dte"] = dte

        results.append(
            bear_call
        )

    return results


# ============================================================
# FULL SCANNER
# ============================================================

def scan_ticker(
    ticker: str,
    short_delta: float = 0.14,
    width: float = 5.0,
):
    """
    Scan all valid expirations for a ticker.
    """

    expirations = get_valid_expirations(
        ticker
    )

    all_results = []

    for expiration_data in expirations:

        expiration = expiration_data[
            "expiration"
        ]

        results = scan_expiration(
            ticker,
            expiration,
            short_delta,
            width,
        )

        all_results.extend(
            results
        )

    return pd.DataFrame(
        all_results
    )
