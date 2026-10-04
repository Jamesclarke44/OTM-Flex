"""
OTM Flex™
Options Scanner

Scans SPY, QQQ, IWM, and VOO for Bull Put and Bear Call
credit-spread candidates using the OTM Flex™ rule book.
"""

import math
import pandas as pd
import yfinance as yf

from Modules.market_data import (
    get_current_price,
    get_historical_data,
)

from Modules.indicators import (
    calculate_indicators,
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
    calculate_delta_from_quote,
)

from Modules.rules import (
    evaluate_trade,
    get_overall_status,
)

from Modules.position_sizing import (
    calculate_max_loss,
    calculate_max_profit,
)


# ============================================================
# DEFAULT SETTINGS
# ============================================================

DEFAULT_TARGET_DELTA = 0.14
DEFAULT_SPREAD_WIDTH = 5.0
DEFAULT_MIN_DTE = 7
DEFAULT_MAX_DTE = 45
DEFAULT_RISK_FREE_RATE = 0.04
DEFAULT_FALLBACK_IV = 0.30


# ============================================================
# SAFE CONVERSION
# ============================================================

def safe_float(value, default=None):
    """Safely convert a value to float."""

    try:

        if value is None:
            return default

        if pd.isna(value):
            return default

        result = float(value)

        if not math.isfinite(result):
            return default

        return result

    except (TypeError, ValueError):
        return default


# ============================================================
# MID PRICE
# ============================================================

def calculate_mid_price(row):
    """
    Calculate a usable option mid price.

    Priority:
    1. Bid/ask midpoint
    2. Last price
    """

    bid = safe_float(row.get("bid"))
    ask = safe_float(row.get("ask"))
    last = safe_float(row.get("lastPrice"))

    if bid is not None and ask is not None:

        if bid >= 0 and ask > 0 and ask >= bid:
            return (bid + ask) / 2

    if last is not None and last > 0:
        return last

    return None


# ============================================================
# OPTION ROW
# ============================================================

def get_option_row(data, strike):
    """Return the row closest to a requested strike."""

    if data is None or data.empty:
        return None

    strikes = pd.to_numeric(
        data["strike"],
        errors="coerce"
    )

    if strikes.isna().all():
        return None

    index = (
        (strikes - float(strike))
        .abs()
        .idxmin()
    )

    return data.loc[index]


# ============================================================
# DELTA CALCULATION
# ============================================================

def calculate_option_delta(
    row,
    current_price,
    expiration,
    risk_free_rate,
    option_type,
    fallback_iv=DEFAULT_FALLBACK_IV,
):
    """
    Calculate option delta.

    Uses Yahoo delta if available.

    Otherwise estimates delta from the option quote.
    """

    # --------------------------------------------------------
    # First: use Yahoo-provided delta if available.
    # --------------------------------------------------------

    for column in [
        "delta",
        "Delta",
        "DELTA",
    ]:

        if column in row.index:

            value = safe_float(row[column])

            if value is not None:

                return value

    # --------------------------------------------------------
    # Strike
    # --------------------------------------------------------

    strike = safe_float(row.get("strike"))

    if strike is None or current_price is None:
        return None

    # --------------------------------------------------------
    # Option price
    # --------------------------------------------------------

    option_price = calculate_mid_price(row)

    if option_price is None or option_price <= 0:
        return None

    # --------------------------------------------------------
    # Time to expiration
    # --------------------------------------------------------

    try:
        dte = calculate_dte(expiration)

        if dte is None:
            return None

        dte = float(dte)

    except Exception:
        return None

    if dte <= 0:
        return None

    T = dte / 365.0

    # --------------------------------------------------------
    # Delta
    # --------------------------------------------------------

    delta = calculate_delta_from_quote(
        market_price=option_price,
        S=current_price,
        K=strike,
        T=T,
        r=risk_free_rate,
        option_type=option_type,
        fallback_volatility=fallback_iv,
    )

    return safe_float(delta)


# ============================================================
# SELECT SHORT OPTION
# ============================================================

def select_short_option_by_delta(
    data,
    current_price,
    expiration,
    target_delta,
    risk_free_rate,
    option_type,
    fallback_iv=DEFAULT_FALLBACK_IV,
):
    """
    Select the option with delta closest to the requested
    OTM Flex target.

    Returns:
        row
        delta
        statistics
    """

    if data is None or data.empty:
        return None, None, {
            "rows": 0,
            "usable_prices": 0,
            "delta_estimates": 0,
            "target_matches": 0,
        }

    candidates = []

    usable_prices = 0
    delta_estimates = 0
    target_matches = 0

    for _, row in data.iterrows():

        strike = safe_float(row.get("strike"))

        if strike is None:
            continue

        # ----------------------------------------------------
        # Ensure the option is OTM.
        # ----------------------------------------------------

        if option_type == "put":

            if strike >= current_price:
                continue

        elif option_type == "call":

            if strike <= current_price:
                continue

        # ----------------------------------------------------
        # Price
        # ----------------------------------------------------

        price = calculate_mid_price(row)

        if price is None or price <= 0:
            continue

        usable_prices += 1

        # ----------------------------------------------------
        # Delta
        # ----------------------------------------------------

        delta = calculate_option_delta(
            row=row,
            current_price=current_price,
            expiration=expiration,
            risk_free_rate=risk_free_rate,
            option_type=option_type,
            fallback_iv=fallback_iv,
        )

        if delta is None:
            continue

        delta_estimates += 1

        absolute_delta = abs(delta)

        # ----------------------------------------------------
        # Target delta range
        # ----------------------------------------------------

        if 0.10 <= absolute_delta <= 0.18:
            target_matches += 1

        # We still keep candidates outside the range.
        # The rule checker will classify them.
        difference = abs(
            absolute_delta - target_delta
        )

        candidates.append(
            {
                "row": row,
                "delta": delta,
                "difference": difference,
                "strike": strike,
            }
        )

    stats = {
        "rows": len(data),
        "usable_prices": usable_prices,
        "delta_estimates": delta_estimates,
        "target_matches": target_matches,
    }

    if not candidates:
        return None, None, stats

    # Closest to target delta.
    candidates.sort(
        key=lambda x: x["difference"]
    )

    selected = candidates[0]

    return (
        selected["row"],
        selected["delta"],
        stats,
    )


# ============================================================
# LONG LEG
# ============================================================

def find_long_put(
    puts,
    short_strike,
    spread_width,
):
    """Find the long put at approximately the desired width."""

    target = short_strike - spread_width

    if puts is None or puts.empty:
        return None

    candidates = puts[
        puts["strike"] < short_strike
    ].copy()

    if candidates.empty:
        return None

    candidates["distance"] = (
        candidates["strike"] - target
    ).abs()

    candidates = candidates.sort_values(
        "distance"
    )

    return candidates.iloc[0]


def find_long_call(
    calls,
    short_strike,
    spread_width,
):
    """Find the long call at approximately the desired width."""

    target = short_strike + spread_width

    if calls is None or calls.empty:
        return None

    candidates = calls[
        calls["strike"] > short_strike
    ].copy()

    if candidates.empty:
        return None

    candidates["distance"] = (
        candidates["strike"] - target
    ).abs()

    candidates = candidates.sort_values(
        "distance"
    )

    return candidates.iloc[0]


# ============================================================
# LIQUIDITY
# ============================================================

def calculate_liquidity(short_row, long_row):
    """
    Calculate approximate combined bid/ask width.
    """

    short_bid = safe_float(short_row.get("bid"), 0)
    short_ask = safe_float(short_row.get("ask"), 0)

    long_bid = safe_float(long_row.get("bid"), 0)
    long_ask = safe_float(long_row.get("ask"), 0)

    short_mid = calculate_mid_price(short_row)
    long_mid = calculate_mid_price(long_row)

    if short_mid is None or long_mid is None:
        return {
            "bid": None,
            "ask": None,
            "mid": None,
            "spread_pct": None,
        }

    spread_bid = short_bid - long_ask
    spread_ask = short_ask - long_bid

    spread_mid = (
        short_mid - long_mid
    )

    if spread_mid <= 0:
        spread_pct = None
    else:
        spread_width = max(
            0,
            spread_ask - spread_bid
        )

        spread_pct = (
            spread_width / spread_mid
        ) * 100

    return {
        "bid": spread_bid,
        "ask": spread_ask,
        "mid": spread_mid,
        "spread_pct": spread_pct,
    }


# ============================================================
# SUPPORT / RESISTANCE
# ============================================================

def calculate_support_resistance(data):
    """Calculate simple 20-day support and resistance."""

    if data is None or data.empty:
        return None, None

    recent = data.tail(20)

    support = safe_float(
        recent["Low"].min()
    )

    resistance = safe_float(
        recent["High"].max()
    )

    return support, resistance


# ============================================================
# ATR DISTANCE
# ============================================================

def calculate_atr_distance(
    current_price,
    short_strike,
    atr,
    spread_type,
):
    """Calculate distance between price and short strike in ATRs."""

    if (
        current_price is None
        or short_strike is None
        or atr is None
        or atr <= 0
    ):
        return None

    if spread_type == "Bull Put":

        distance = (
            current_price - short_strike
        )

    else:

        distance = (
            short_strike - current_price
        )

    return distance / atr


# ============================================================
# CANDIDATE BUILDER
# ============================================================

def build_candidate(
    ticker,
    current_price,
    expiration,
    spread_type,
    short_row,
    short_delta,
    long_row,
    indicators,
    support,
    resistance,
    spread_width,
    risk_free_rate,
):
    """Build a complete spread candidate."""

    if short_row is None or long_row is None:
        return None

    short_strike = safe_float(
        short_row.get("strike")
    )

    long_strike = safe_float(
        long_row.get("strike")
    )

    short_mid = calculate_mid_price(
        short_row
    )

    long_mid = calculate_mid_price(
        long_row
    )

    if (
        short_strike is None
        or long_strike is None
        or short_mid is None
        or long_mid is None
    ):
        return None

    # --------------------------------------------------------
    # Credit
    # --------------------------------------------------------

    credit = (
        short_mid - long_mid
    )

    if credit <= 0:
        return None

    # --------------------------------------------------------
    # Actual width
    # --------------------------------------------------------

    actual_width = abs(
        short_strike - long_strike
    )

    # --------------------------------------------------------
    # Max profit/loss
    # --------------------------------------------------------

    max_profit = calculate_max_profit(
        credit,
        1
    )

    max_loss = calculate_max_loss(
        actual_width,
        credit,
        1
    )

    # --------------------------------------------------------
    # DTE
    # --------------------------------------------------------

    dte = calculate_dte(
        expiration
    )

    # --------------------------------------------------------
    # ATR
    # --------------------------------------------------------

    atr = indicators.get("atr")

    atr_distance = calculate_atr_distance(
        current_price=current_price,
        short_strike=short_strike,
        atr=atr,
        spread_type=spread_type,
    )

    # --------------------------------------------------------
    # Market condition
    # --------------------------------------------------------

    trend = determine_trend(
        indicators
    )

    if trend in ["Bullish", "Bearish"]:
        market_condition = "strong"
    else:
        market_condition = "choppy"

    # --------------------------------------------------------
    # Liquidity
    # --------------------------------------------------------

    liquidity = calculate_liquidity(
        short_row,
        long_row
    )

    # --------------------------------------------------------
    # Rule evaluation
    # --------------------------------------------------------

    rule_results = evaluate_trade(
        spread_type=spread_type,
        trend=trend,
        delta=abs(short_delta),
        dte=dte,
        atr_distance=atr_distance,
        market_condition=market_condition,
        rsi=indicators.get("rsi"),
        macd=indicators.get("macd"),
        macd_signal=indicators.get("macd_signal"),
        bid=liquidity["bid"],
        ask=liquidity["ask"],
        open_interest=safe_float(
            short_row.get("openInterest")
        ),
        volume=safe_float(
            short_row.get("volume")
        ),
        current_price=current_price,
        short_strike=short_strike,
        support=support,
        resistance=resistance,
    )

    overall_status = get_overall_status(
        rule_results
    )

    return {
        "ticker": ticker,
        "spread_type": spread_type,
        "expiration": expiration,
        "dte": dte,

        "current_price": current_price,

        "short_strike": short_strike,
        "long_strike": long_strike,

        "short_delta": abs(short_delta),

        "short_bid": safe_float(
            short_row.get("bid")
        ),

        "short_ask": safe_float(
            short_row.get("ask")
        ),

        "short_mid": short_mid,

        "long_bid": safe_float(
            long_row.get("bid")
        ),

        "long_ask": safe_float(
            long_row.get("ask")
        ),

        "long_mid": long_mid,

        "credit": credit,

        "spread_width": actual_width,

        "max_profit": max_profit,

        "max_loss": max_loss,

        "atr": atr,

        "atr_distance": atr_distance,

        "rsi": indicators.get("rsi"),

        "macd": indicators.get("macd"),

        "macd_signal": indicators.get(
            "macd_signal"
        ),

        "support": support,

        "resistance": resistance,

        "trend": trend,

        "liquidity_spread_pct": liquidity[
            "spread_pct"
        ],

        "status": overall_status,

        "rules": rule_results,
    }


# ============================================================
# EXPIRATION SCANNER
# ============================================================

def scan_expiration(
    ticker,
    expiration,
    current_price,
    indicators,
    trend,
    support,
    resistance,
    target_delta=DEFAULT_TARGET_DELTA,
    spread_width=DEFAULT_SPREAD_WIDTH,
    risk_free_rate=DEFAULT_RISK_FREE_RATE,
    fallback_iv=DEFAULT_FALLBACK_IV,
):
    """
    Scan one expiration for Bull Put and Bear Call spreads.

    Returns:
        candidates
        diagnostics
    """

    diagnostics = {
        "expiration": expiration,
        "calls": 0,
        "puts": 0,
        "put_price_candidates": 0,
        "call_price_candidates": 0,
        "put_delta_estimates": 0,
        "call_delta_estimates": 0,
        "put_target_matches": 0,
        "call_target_matches": 0,
        "spreads_built": 0,
    }

    candidates = []

    # --------------------------------------------------------
    # Get option chain
    # --------------------------------------------------------

    try:

        calls, puts = get_option_chain(
            ticker,
            expiration
        )

    except Exception as exc:

        diagnostics["error"] = str(exc)

        return candidates, diagnostics

    # --------------------------------------------------------
    # Clean data
    # --------------------------------------------------------

    try:

        calls = clean_option_data(
            calls
        )

    except Exception:

        calls = pd.DataFrame()

    try:

        puts = clean_option_data(
            puts
        )

    except Exception:

        puts = pd.DataFrame()

    diagnostics["calls"] = len(calls)
    diagnostics["puts"] = len(puts)

    # ========================================================
    # BULL PUT
    # ========================================================

    if not puts.empty:

        short_put, put_delta, put_stats = (
            select_short_option_by_delta(
                data=puts,
                current_price=current_price,
                expiration=expiration,
                target_delta=target_delta,
                risk_free_rate=risk_free_rate,
                option_type="put",
                fallback_iv=fallback_iv,
            )
        )

        diagnostics[
            "put_price_candidates"
        ] = put_stats["usable_prices"]

        diagnostics[
            "put_delta_estimates"
        ] = put_stats["delta_estimates"]

        diagnostics[
            "put_target_matches"
        ] = put_stats["target_matches"]

        if (
            short_put is not None
            and put_delta is not None
        ):

            short_strike = safe_float(
                short_put.get("strike")
            )

            long_put = find_long_put(
                puts,
                short_strike,
                spread_width
            )

            if long_put is not None:

                candidate = build_candidate(
                    ticker=ticker,
                    current_price=current_price,
                    expiration=expiration,
                    spread_type="Bull Put",
                    short_row=short_put,
                    short_delta=put_delta,
                    long_row=long_put,
                    indicators=indicators,
                    support=support,
                    resistance=resistance,
                    spread_width=spread_width,
                    risk_free_rate=risk_free_rate,
                )

                if candidate is not None:

                    candidates.append(
                        candidate
                    )

                    diagnostics[
                        "spreads_built"
                    ] += 1

    # ========================================================
    # BEAR CALL
    # ========================================================

    if not calls.empty:

        short_call, call_delta, call_stats = (
            select_short_option_by_delta(
                data=calls,
                current_price=current_price,
                expiration=expiration,
                target_delta=target_delta,
                risk_free_rate=risk_free_rate,
                option_type="call",
                fallback_iv=fallback_iv,
            )
        )

        diagnostics[
            "call_price_candidates"
        ] = call_stats["usable_prices"]

        diagnostics[
            "call_delta_estimates"
        ] = call_stats["delta_estimates"]

        diagnostics[
            "call_target_matches"
        ] = call_stats["target_matches"]

        if (
            short_call is not None
            and call_delta is not None
        ):

            short_strike = safe_float(
                short_call.get("strike")
            )

            long_call = find_long_call(
                calls,
                short_strike,
                spread_width
            )

            if long_call is not None:

                candidate = build_candidate(
                    ticker=ticker,
                    current_price=current_price,
                    expiration=expiration,
                    spread_type="Bear Call",
                    short_row=short_call,
                    short_delta=call_delta,
                    long_row=long_call,
                    indicators=indicators,
                    support=support,
                    resistance=resistance,
                    spread_width=spread_width,
                    risk_free_rate=risk_free_rate,
                )

                if candidate is not None:

                    candidates.append(
                        candidate
                    )

                    diagnostics[
                        "spreads_built"
                    ] += 1

    return candidates, diagnostics


# ============================================================
# TICKER SCANNER
# ============================================================

def scan_ticker(
    ticker,
    target_delta=DEFAULT_TARGET_DELTA,
    spread_width=DEFAULT_SPREAD_WIDTH,
    min_dte=DEFAULT_MIN_DTE,
    max_dte=DEFAULT_MAX_DTE,
    risk_free_rate=DEFAULT_RISK_FREE_RATE,
    fallback_iv=DEFAULT_FALLBACK_IV,
):
    """
    Scan one underlying.
    """

    candidates = []

    diagnostics = {
        "ticker": ticker,
        "current_price": None,
        "trend": None,
        "expirations": 0,
        "expiration_scans": 0,
        "option_rows": 0,
        "delta_estimates": 0,
        "target_matches": 0,
        "spreads_built": 0,
        "errors": [],
    }

    # --------------------------------------------------------
    # Current price
    # --------------------------------------------------------

    current_price = get_current_price(
        ticker
    )

    if current_price is None:

        diagnostics["errors"].append(
            "Could not retrieve current price."
        )

        return candidates, diagnostics

    diagnostics[
        "current_price"
    ] = current_price

    # --------------------------------------------------------
    # Historical data
    # --------------------------------------------------------

    history = get_historical_data(
        ticker,
        period="1y",
        interval="1d"
    )

    if history.empty:

        diagnostics["errors"].append(
            "Could not retrieve historical data."
        )

        return candidates, diagnostics

    # --------------------------------------------------------
    # Indicators
    # --------------------------------------------------------

    indicators = get_latest_indicators(
        history
    )

    if indicators is None:

        diagnostics["errors"].append(
            "Could not calculate indicators."
        )

        return candidates, diagnostics

    trend = determine_trend(
        indicators
    )

    diagnostics["trend"] = trend

    # --------------------------------------------------------
    # Support / resistance
    # --------------------------------------------------------

    support, resistance = (
        calculate_support_resistance(
            history
        )
    )

    # --------------------------------------------------------
    # Expirations
    # --------------------------------------------------------

    try:

        expirations = get_valid_expirations(
            ticker,
            min_dte=min_dte,
            max_dte=max_dte
        )

    except Exception as exc:

        diagnostics["errors"].append(
            f"Expiration error: {exc}"
        )

        return candidates, diagnostics

    diagnostics[
        "expirations"
    ] = len(expirations)

    # --------------------------------------------------------
    # Scan expirations
    # --------------------------------------------------------

    for expiration in expirations:

        diagnostics[
            "expiration_scans"
        ] += 1

        try:

            expiration_candidates, expiration_stats = (
                scan_expiration(
                    ticker=ticker,
                    expiration=expiration,
                    current_price=current_price,
                    indicators=indicators,
                    trend=trend,
                    support=support,
                    resistance=resistance,
                    target_delta=target_delta,
                    spread_width=spread_width,
                    risk_free_rate=risk_free_rate,
                    fallback_iv=fallback_iv,
                )
            )

            candidates.extend(
                expiration_candidates
            )

            diagnostics[
                "option_rows"
            ] += (
                expiration_stats["calls"]
                + expiration_stats["puts"]
            )

            diagnostics[
                "delta_estimates"
            ] += (
                expiration_stats[
                    "put_delta_estimates"
                ]
                + expiration_stats[
                    "call_delta_estimates"
                ]
            )

            diagnostics[
                "target_matches"
            ] += (
                expiration_stats[
                    "put_target_matches"
                ]
                + expiration_stats[
                    "call_target_matches"
                ]
            )

            diagnostics[
                "spreads_built"
            ] += expiration_stats[
                "spreads_built"
            ]

            if "error" in expiration_stats:

                diagnostics["errors"].append(
                    f"{expiration}: "
                    f"{expiration_stats['error']}"
                )

        except Exception as exc:

            diagnostics["errors"].append(
                f"{expiration}: {exc}"
            )

    return candidates, diagnostics


# ============================================================
# MARKET SCANNER
# ============================================================

def scan_market(
    tickers=None,
    target_delta=DEFAULT_TARGET_DELTA,
    spread_width=DEFAULT_SPREAD_WIDTH,
    min_dte=DEFAULT_MIN_DTE,
    max_dte=DEFAULT_MAX_DTE,
    risk_free_rate=DEFAULT_RISK_FREE_RATE,
    fallback_iv=DEFAULT_FALLBACK_IV,
):
    """
    Scan the selected ETF universe.
    """

    if tickers is None:

        tickers = [
            "SPY",
            "QQQ",
            "IWM",
            "VOO",
        ]

    all_candidates = []

    diagnostics = []

    for ticker in tickers:

        try:

            candidates, ticker_stats = (
                scan_ticker(
                    ticker=ticker,
                    target_delta=target_delta,
                    spread_width=spread_width,
                    min_dte=min_dte,
                    max_dte=max_dte,
                    risk_free_rate=risk_free_rate,
                    fallback_iv=fallback_iv,
                )
            )

            all_candidates.extend(
                candidates
            )

            diagnostics.append(
                ticker_stats
            )

        except Exception as exc:

            diagnostics.append(
                {
                    "ticker": ticker,
                    "current_price": None,
                    "trend": None,
                    "expirations": 0,
                    "expiration_scans": 0,
                    "option_rows": 0,
                    "delta_estimates": 0,
                    "target_matches": 0,
                    "spreads_built": 0,
                    "errors": [
                        str(exc)
                    ],
                }
            )

    # --------------------------------------------------------
    # Sort candidates
    # --------------------------------------------------------

    if all_candidates:

        results = pd.DataFrame(
            all_candidates
        )

        # Best candidates first:
        # PASS → REVIEW → FAIL
        status_order = {
            "PASS": 0,
            "REVIEW": 1,
            "FAIL": 2,
        }

        results["_status_order"] = (
            results["status"]
            .map(status_order)
            .fillna(9)
        )

        results = results.sort_values(
            [
                "_status_order",
                "short_delta",
                "dte",
            ]
        )

        results = results.drop(
            columns=["_status_order"]
        )

    else:

        results = pd.DataFrame()

    return results, diagnostics


# ============================================================
# DIAGNOSTIC SUMMARY
# ============================================================

def summarize_diagnostics(diagnostics):
    """
    Convert scanner diagnostics into a DataFrame
    suitable for Streamlit display.
    """

    rows = []

    for item in diagnostics:

        rows.append(
            {
                "Ticker": item.get(
                    "ticker"
                ),

                "Price": item.get(
                    "current_price"
                ),

                "Trend": item.get(
                    "trend"
                ),

                "Expirations": item.get(
                    "expirations",
                    0
                ),

                "Option Rows": item.get(
                    "option_rows",
                    0
                ),

                "Delta Estimates": item.get(
                    "delta_estimates",
                    0
                ),

                "0.10–0.18 Delta": item.get(
                    "target_matches",
                    0
                ),

                "Spreads Built": item.get(
                    "spreads_built",
                    0
                ),

                "Errors": "; ".join(
                    item.get(
                        "errors",
                        []
                    )
                ),
            }
        )

    return pd.DataFrame(rows)
