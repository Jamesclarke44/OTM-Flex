"""
OTM Flex™
Scanner Module

Combines:
- Market data
- Technical indicators
- Option chains
- Estimated Greeks
- OTM Flex™ rule checks

to identify potential Bull Put and Bear Call credit spreads.
"""

import math
import pandas as pd

from Modules.market_data import (
    get_current_price,
    get_historical_data,
)

from Modules.indicators import (
    get_latest_indicators,
    determine_trend,
)

from Modules.options import (
    get_valid_expirations,
    get_option_chain,
    clean_option_data,
    calculate_dte,
)

from Modules.greeks import (
    calculate_delta,
    calculate_implied_volatility,
)

from Modules.rules import (
    evaluate_trade,
    get_overall_status,
)


# ---------------------------------------------------------
# DEFAULT SCANNER SETTINGS
# ---------------------------------------------------------

DEFAULT_SHORT_DELTA = 0.14
DEFAULT_SPREAD_WIDTH = 5.0
DEFAULT_MIN_DTE = 7
DEFAULT_MAX_DTE = 45
DEFAULT_RISK_FREE_RATE = 0.04


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def safe_float(value):
    """Convert a value to float safely."""

    try:
        if pd.isna(value):
            return None

        value = float(value)

        if not math.isfinite(value):
            return None

        return value

    except (TypeError, ValueError):
        return None


def calculate_mid_price(bid, ask, last_price=None):
    """
    Calculate a reasonable option mid price.

    Uses bid/ask midpoint when both are available.
    Falls back to last price when necessary.
    """

    bid = safe_float(bid)
    ask = safe_float(ask)
    last_price = safe_float(last_price)

    if bid is not None and ask is not None:
        if bid >= 0 and ask >= bid:
            return (bid + ask) / 2

    if last_price is not None and last_price >= 0:
        return last_price

    return None


def find_nearest_strike(data, target_strike):
    """Find the available strike closest to the target strike."""

    if data.empty or target_strike is None:
        return None

    strikes = pd.to_numeric(data["strike"], errors="coerce").dropna()

    if strikes.empty:
        return None

    return float(strikes.iloc[(strikes - target_strike).abs().argmin()])


def get_option_row(data, strike):
    """Return the option row matching a strike."""

    if data.empty or strike is None:
        return None

    matches = data[
        pd.to_numeric(data["strike"], errors="coerce").round(4)
        == round(float(strike), 4)
    ]

    if matches.empty:
        return None

    return matches.iloc[0]


def calculate_option_delta(
    option_row,
    stock_price,
    dte,
    option_type,
    risk_free_rate=DEFAULT_RISK_FREE_RATE,
):
    """
    Calculate estimated Black-Scholes delta.

    If an option already contains a broker/Yahoo delta,
    use that value first.
    """

    if option_row is None:
        return None

    # Check for an existing delta first.
    for column in ["delta", "Delta", "DELTA"]:
        if column in option_row.index:
            existing_delta = safe_float(option_row[column])

            if existing_delta is not None:
                return existing_delta

    strike = safe_float(option_row.get("strike"))

    if strike is None or stock_price is None or dte <= 0:
        return None

    bid = safe_float(option_row.get("bid"))
    ask = safe_float(option_row.get("ask"))
    last_price = safe_float(option_row.get("lastPrice"))

    option_price = calculate_mid_price(
        bid,
        ask,
        last_price,
    )

    if option_price is None or option_price <= 0:
        return None

    time_to_expiration = dte / 365.0

    # Estimate IV from the market price.
    implied_volatility = calculate_implied_volatility(
        market_price=option_price,
        stock_price=stock_price,
        strike=strike,
        time_to_expiration=time_to_expiration,
        risk_free_rate=risk_free_rate,
        dividend_yield=0.0,
        option_type=option_type,
    )

    if implied_volatility is None:
        return None

    if implied_volatility <= 0:
        return None

    return calculate_delta(
        stock_price=stock_price,
        strike=strike,
        time_to_expiration=time_to_expiration,
        volatility=implied_volatility,
        risk_free_rate=risk_free_rate,
        dividend_yield=0.0,
        option_type=option_type,
    )


def select_short_option_by_delta(
    data,
    stock_price,
    dte,
    option_type,
    target_delta=DEFAULT_SHORT_DELTA,
    risk_free_rate=DEFAULT_RISK_FREE_RATE,
):
    """
    Search the option chain and find the strike whose estimated
    absolute delta is closest to the requested target.

    For puts, delta is negative.
    For calls, delta is positive.
    """

    if data.empty:
        return None

    candidates = []

    for _, row in data.iterrows():

        strike = safe_float(row.get("strike"))

        if strike is None:
            continue

        delta = calculate_option_delta(
            row,
            stock_price,
            dte,
            option_type,
            risk_free_rate,
        )

        if delta is None:
            continue

        # OTM short options use absolute delta for selection.
        distance = abs(abs(delta) - target_delta)

        candidates.append(
            {
                "strike": strike,
                "delta": delta,
                "row": row,
                "delta_distance": distance,
            }
        )

    if not candidates:
        return None

    candidates.sort(key=lambda x: x["delta_distance"])

    return candidates[0]


def calculate_atr_distance(
    spread_type,
    current_price,
    short_strike,
    atr,
):
    """Calculate distance between price and short strike in ATRs."""

    if current_price is None or short_strike is None:
        return None

    if atr is None or atr <= 0:
        return None

    if spread_type == "Bull Put":
        price_distance = current_price - short_strike

    elif spread_type == "Bear Call":
        price_distance = short_strike - current_price

    else:
        return None

    return price_distance / atr


def calculate_support_resistance(data, lookback=20):
    """
    Calculate simple recent support/resistance levels.

    Support = lowest low over lookback period.
    Resistance = highest high over lookback period.

    These are used as context rather than absolute signals.
    """

    if data.empty:
        return None, None

    recent = data.tail(lookback)

    support = safe_float(recent["Low"].min())
    resistance = safe_float(recent["High"].max())

    return support, resistance


def classify_market_condition(trend):
    """
    Basic market-condition classification.

    Neutral trends are treated as choppy.
    Fully aligned bullish/bearish trends are treated as strong.
    """

    if trend == "Neutral":
        return "Choppy"

    if trend in ["Bullish", "Bearish"]:
        return "Strong"

    return "Normal"


def build_candidate(
    ticker,
    expiration,
    spread_type,
    current_price,
    indicators,
    trend,
    market_condition,
    support,
    resistance,
    short_option,
    long_option,
    dte,
):
    """Build one complete OTM Flex™ candidate."""

    if short_option is None or long_option is None:
        return None

    short_row = short_option["row"]
    long_row = long_option

    short_strike = safe_float(short_row.get("strike"))
    long_strike = safe_float(long_row.get("strike"))

    short_bid = safe_float(short_row.get("bid"))
    short_ask = safe_float(short_row.get("ask"))
    short_last = safe_float(short_row.get("lastPrice"))

    long_bid = safe_float(long_row.get("bid"))
    long_ask = safe_float(long_row.get("ask"))
    long_last = safe_float(long_row.get("lastPrice"))

    short_mid = calculate_mid_price(
        short_bid,
        short_ask,
        short_last,
    )

    long_mid = calculate_mid_price(
        long_bid,
        long_ask,
        long_last,
    )

    if short_mid is None or long_mid is None:
        return None

    credit = short_mid - long_mid

    if credit <= 0:
        return None

    spread_width = abs(short_strike - long_strike)

    if spread_width <= 0:
        return None

    max_profit = credit * 100
    max_loss = (spread_width - credit) * 100

    if max_loss <= 0:
        return None

    atr = indicators.get("atr")

    atr_distance = calculate_atr_distance(
        spread_type,
        current_price,
        short_strike,
        atr,
    )

    short_delta = short_option.get("delta")

    if spread_type == "Bull Put":
        short_option_type = "put"

    else:
        short_option_type = "call"

    # Estimate option liquidity.
    if short_bid is not None and short_ask is not None:
        short_bid_ask_width = short_ask - short_bid

        if short_mid and short_mid > 0:
            short_bid_ask_pct = (
                short_bid_ask_width / short_mid
            ) * 100
        else:
            short_bid_ask_pct = None
    else:
        short_bid_ask_pct = None

    # Run OTM Flex™ rules.
    rule_results = evaluate_trade(
        spread_type=spread_type,
        trend=trend,
        delta=abs(short_delta) if short_delta is not None else 0,
        dte=dte,
        distance_atr=atr_distance if atr_distance is not None else 0,
        market_condition=market_condition.lower(),
        rsi=indicators.get("rsi", 0),
        macd=indicators.get("macd", 0),
        macd_signal=indicators.get("macd_signal", 0),
        bid=short_bid if short_bid is not None else 0,
        ask=short_ask if short_ask is not None else 0,
        open_interest=short_row.get("openInterest"),
        volume=short_row.get("volume"),
        current_price=current_price,
        short_strike=short_strike,
        support=support,
        resistance=resistance,
    )

    overall_status = get_overall_status(rule_results)

    return {
        "Ticker": ticker,
        "Type": spread_type,
        "Expiration": expiration,
        "DTE": dte,
        "Current Price": round(current_price, 2),
        "Short Strike": round(short_strike, 2),
        "Long Strike": round(long_strike, 2),
        "Short Delta": round(abs(short_delta), 3)
        if short_delta is not None
        else None,
        "Credit": round(credit, 2),
        "Max Profit": round(max_profit, 2),
        "Max Loss": round(max_loss, 2),
        "Spread Width": round(spread_width, 2),
        "ATR Distance": round(atr_distance, 2)
        if atr_distance is not None
        else None,
        "RSI": round(indicators.get("rsi", 0), 1),
        "MACD": round(indicators.get("macd", 0), 3),
        "Trend": trend,
        "Market Condition": market_condition,
        "Support": round(support, 2)
        if support is not None
        else None,
        "Resistance": round(resistance, 2)
        if resistance is not None
        else None,
        "Bid/Ask %": round(short_bid_ask_pct, 1)
        if short_bid_ask_pct is not None
        else None,
        "Status": overall_status,
        "Rules": rule_results,
    }


# ---------------------------------------------------------
# SCAN ONE EXPIRATION
# ---------------------------------------------------------

def scan_expiration(
    ticker,
    expiration,
    current_price,
    indicators,
    trend,
    market_condition,
    support,
    resistance,
    short_delta=DEFAULT_SHORT_DELTA,
    spread_width=DEFAULT_SPREAD_WIDTH,
    risk_free_rate=DEFAULT_RISK_FREE_RATE,
):
    """
    Scan one expiration for Bull Put and Bear Call spreads.
    """

    dte = calculate_dte(expiration)

    if dte is None:
        return []

    if dte < DEFAULT_MIN_DTE or dte > DEFAULT_MAX_DTE:
        return []

    try:
        calls, puts = get_option_chain(
            ticker,
            expiration,
        )
    except Exception:
        return []

    calls = clean_option_data(calls)
    puts = clean_option_data(puts)

    candidates = []

    # -----------------------------------------------------
    # BULL PUT SPREAD
    # -----------------------------------------------------

    short_put = select_short_option_by_delta(
        puts,
        current_price,
        dte,
        "put",
        target_delta=short_delta,
        risk_free_rate=risk_free_rate,
    )

    if short_put is not None:

        short_put_strike = short_put["strike"]

        target_long_put = short_put_strike - spread_width

        long_put_strike = find_nearest_strike(
            puts,
            target_long_put,
        )

        if (
            long_put_strike is not None
            and long_put_strike < short_put_strike
        ):

            long_put_row = get_option_row(
                puts,
                long_put_strike,
            )

            candidate = build_candidate(
                ticker=ticker,
                expiration=expiration,
                spread_type="Bull Put",
                current_price=current_price,
                indicators=indicators,
                trend=trend,
                market_condition=market_condition,
                support=support,
                resistance=resistance,
                short_option=short_put,
                long_option=long_put_row,
                dte=dte,
            )

            if candidate is not None:
                candidates.append(candidate)

    # -----------------------------------------------------
    # BEAR CALL SPREAD
    # -----------------------------------------------------

    short_call = select_short_option_by_delta(
        calls,
        current_price,
        dte,
        "call",
        target_delta=short_delta,
        risk_free_rate=risk_free_rate,
    )

    if short_call is not None:

        short_call_strike = short_call["strike"]

        target_long_call = (
            short_call_strike + spread_width
        )

        long_call_strike = find_nearest_strike(
            calls,
            target_long_call,
        )

        if (
            long_call_strike is not None
            and long_call_strike > short_call_strike
        ):

            long_call_row = get_option_row(
                calls,
                long_call_strike,
            )

            candidate = build_candidate(
                ticker=ticker,
                expiration=expiration,
                spread_type="Bear Call",
                current_price=current_price,
                indicators=indicators,
                trend=trend,
                market_condition=market_condition,
                support=support,
                resistance=resistance,
                short_option=short_call,
                long_option=long_call_row,
                dte=dte,
            )

            if candidate is not None:
                candidates.append(candidate)

    return candidates


# ---------------------------------------------------------
# SCAN ONE TICKER
# ---------------------------------------------------------

def scan_ticker(
    ticker,
    short_delta=DEFAULT_SHORT_DELTA,
    spread_width=DEFAULT_SPREAD_WIDTH,
    min_dte=DEFAULT_MIN_DTE,
    max_dte=DEFAULT_MAX_DTE,
    risk_free_rate=DEFAULT_RISK_FREE_RATE,
):
    """
    Scan a supported ETF for OTM Flex™ credit spread candidates.
    """

    current_price = get_current_price(ticker)

    if current_price is None:
        return pd.DataFrame()

    historical_data = get_historical_data(
        ticker,
        period="1y",
        interval="1d",
    )

    if historical_data.empty:
        return pd.DataFrame()

    indicators = get_latest_indicators(
        historical_data
    )

    if indicators is None:
        return pd.DataFrame()

    trend = determine_trend(indicators)

    market_condition = classify_market_condition(
        trend
    )

    support, resistance = calculate_support_resistance(
        historical_data,
        lookback=20,
    )

    expirations = get_valid_expirations(
        ticker,
        min_dte=min_dte,
        max_dte=max_dte,
    )

    if not expirations:
        return pd.DataFrame()

    candidates = []

    for expiration in expirations:

        expiration_candidates = scan_expiration(
            ticker=ticker,
            expiration=expiration,
            current_price=current_price,
            indicators=indicators,
            trend=trend,
            market_condition=market_condition,
            support=support,
            resistance=resistance,
            short_delta=short_delta,
            spread_width=spread_width,
            risk_free_rate=risk_free_rate,
        )

        candidates.extend(
            expiration_candidates
        )

    if not candidates:
        return pd.DataFrame()

    result = pd.DataFrame(candidates)

    # Put PASS candidates first, followed by REVIEW,
    # then FAIL.
    status_order = {
        "PASS": 0,
        "REVIEW": 1,
        "FAIL": 2,
    }

    result["_status_order"] = (
        result["Status"]
        .map(status_order)
        .fillna(99)
    )

    result = result.sort_values(
        by=[
            "_status_order",
            "DTE",
        ],
        ascending=[
            True,
            True,
        ],
    )

    result = result.drop(
        columns=["_status_order"]
    )

    return result.reset_index(drop=True)


# ---------------------------------------------------------
# SCAN MULTIPLE TICKERS
# ---------------------------------------------------------

def scan_market(
    tickers=None,
    short_delta=DEFAULT_SHORT_DELTA,
    spread_width=DEFAULT_SPREAD_WIDTH,
    min_dte=DEFAULT_MIN_DTE,
    max_dte=DEFAULT_MAX_DTE,
    risk_free_rate=DEFAULT_RISK_FREE_RATE,
):
    """
    Scan multiple ETF underlyings.
    """

    if tickers is None:
        tickers = [
            "SPY",
            "QQQ",
            "IWM",
            "VOO",
        ]

    all_candidates = []

    for ticker in tickers:

        try:
            results = scan_ticker(
                ticker=ticker,
                short_delta=short_delta,
                spread_width=spread_width,
                min_dte=min_dte,
                max_dte=max_dte,
                risk_free_rate=risk_free_rate,
            )

            if not results.empty:
                all_candidates.append(results)

        except Exception:
            continue

    if not all_candidates:
        return pd.DataFrame()

    combined = pd.concat(
        all_candidates,
        ignore_index=True,
    )

    return combined
