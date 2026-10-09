"""
OTM Flex™
Options Scanner

Scans SPY, QQQ, IWM, and VOO for Bull Put and Bear Call
credit spread candidates.
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


DEFAULT_TARGET_DELTA = 0.14
DEFAULT_SPREAD_WIDTH = 5.0
DEFAULT_MIN_DTE = 7
DEFAULT_MAX_DTE = 45
DEFAULT_RISK_FREE_RATE = 0.04
DEFAULT_FALLBACK_IV = 0.30


# ============================================================
# HELPERS
# ============================================================

def safe_float(value, default=None):

    try:

        if value is None or pd.isna(value):
            return default

        value = float(value)

        if not math.isfinite(value):
            return default

        return value

    except (TypeError, ValueError):

        return default


def calculate_mid_price(row):

    bid = safe_float(row.get("bid"))
    ask = safe_float(row.get("ask"))
    last = safe_float(row.get("lastPrice"))

    if (
        bid is not None
        and ask is not None
        and ask >= bid
        and ask > 0
    ):
        return (bid + ask) / 2

    if last is not None and last > 0:
        return last

    return None


def calculate_support_resistance(data):

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


def calculate_atr_distance(
    current_price,
    short_strike,
    atr,
    spread_type,
):

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
# DELTA
# ============================================================

def calculate_option_delta(
    row,
    current_price,
    expiration,
    risk_free_rate,
    option_type,
    fallback_iv=DEFAULT_FALLBACK_IV,
):

    strike = safe_float(
        row.get("strike")
    )

    if strike is None:
        return None

    price = calculate_mid_price(row)

    if price is None or price <= 0:
        return None

    try:

        dte = calculate_dte(
            expiration
        )

    except Exception:

        return None

    if dte is None or dte <= 0:
        return None

    T = float(dte) / 365.0

    return calculate_delta_from_quote(
        market_price=price,
        S=current_price,
        K=strike,
        T=T,
        r=risk_free_rate,
        option_type=option_type,
        fallback_volatility=fallback_iv,
    )


# ============================================================
# SHORT OPTION SELECTION
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

    stats = {
        "rows": 0,
        "usable_prices": 0,
        "delta_estimates": 0,
        "target_matches": 0,
    }

    if data is None or data.empty:

        return None, None, stats

    stats["rows"] = len(data)

    candidates = []

    for _, row in data.iterrows():

        strike = safe_float(
            row.get("strike")
        )

        if strike is None:
            continue

        # Only consider OTM options.
        if option_type == "put":

            if strike >= current_price:
                continue

        else:

            if strike <= current_price:
                continue

        price = calculate_mid_price(row)

        if price is None or price <= 0:
            continue

        stats["usable_prices"] += 1

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

        stats["delta_estimates"] += 1

        absolute_delta = abs(delta)

        if (
            0.10
            <= absolute_delta
            <= 0.18
        ):
            stats["target_matches"] += 1

        candidates.append(
            {
                "row": row,
                "delta": delta,
                "difference": abs(
                    absolute_delta
                    - target_delta
                ),
            }
        )

    if not candidates:

        return None, None, stats

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
# LONG LEGS
# ============================================================

def find_long_put(
    puts,
    short_strike,
    spread_width,
):

    if puts is None or puts.empty:
        return None

    candidates = puts[
        puts["strike"] < short_strike
    ].copy()

    if candidates.empty:
        return None

    target = (
        short_strike
        - spread_width
    )

    candidates["distance"] = (
        candidates["strike"]
        - target
    ).abs()

    return candidates.sort_values(
        "distance"
    ).iloc[0]


def find_long_call(
    calls,
    short_strike,
    spread_width,
):

    if calls is None or calls.empty:
        return None

    candidates = calls[
        calls["strike"] > short_strike
    ].copy()

    if candidates.empty:
        return None

    target = (
        short_strike
        + spread_width
    )

    candidates["distance"] = (
        candidates["strike"]
        - target
    ).abs()

    return candidates.sort_values(
        "distance"
    ).iloc[0]


# ============================================================
# LIQUIDITY
# ============================================================

def calculate_liquidity(
    short_row,
    long_row,
):

    short_bid = safe_float(
        short_row.get("bid"),
        0
    )

    short_ask = safe_float(
        short_row.get("ask"),
        0
    )

    long_bid = safe_float(
        long_row.get("bid"),
        0
    )

    long_ask = safe_float(
        long_row.get("ask"),
        0
    )

    short_mid = calculate_mid_price(
        short_row
    )

    long_mid = calculate_mid_price(
        long_row
    )

    if short_mid is None or long_mid is None:

        return {
            "bid": None,
            "ask": None,
            "mid": None,
            "spread_pct": None,
        }

    spread_bid = (
        short_bid - long_ask
    )

    spread_ask = (
        short_ask - long_bid
    )

    spread_mid = (
        short_mid - long_mid
    )

    if spread_mid > 0:

        spread_width = max(
            0,
            spread_ask - spread_bid
        )

        spread_pct = (
            spread_width
            / spread_mid
        ) * 100

    else:

        spread_pct = None

    return {
        "bid": spread_bid,
        "ask": spread_ask,
        "mid": spread_mid,
        "spread_pct": spread_pct,
    }


# ============================================================
# BUILD CANDIDATE
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
):

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

    credit = (
        short_mid
        - long_mid
    )

    if credit <= 0:
        return None

    actual_width = abs(
        short_strike
        - long_strike
    )

    max_profit = calculate_max_profit(
        credit,
        1
    )

    max_loss = calculate_max_loss(
        actual_width,
        credit,
        1
    )

    dte = calculate_dte(
        expiration
    )

    atr = indicators.get(
        "atr"
    )

    atr_distance = calculate_atr_distance(
        current_price,
        short_strike,
        atr,
        spread_type,
    )

    trend = determine_trend(
        indicators
    )

    if trend in (
        "Bullish",
        "Bearish",
    ):

        market_condition = "strong"

    else:

        market_condition = "choppy"

    liquidity = calculate_liquidity(
        short_row,
        long_row
    )

    rules = evaluate_trade(
        spread_type=spread_type,
        trend=trend,
        delta=abs(short_delta),
        dte=dte,
        atr_distance=atr_distance,
        market_condition=market_condition,
        rsi=indicators.get("rsi"),
        macd=indicators.get("macd"),
        macd_signal=indicators.get(
            "macd_signal"
        ),
        bid=liquidity["bid"],
        ask=liquidity["ask"],
        open_interest=safe_float(
            short_row.get(
                "openInterest"
            )
        ),
        volume=safe_float(
            short_row.get(
                "volume"
            )
        ),
        current_price=current_price,
        short_strike=short_strike,
        support=support,
        resistance=resistance,
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
        "status": get_overall_status(
            rules
        ),
        "rules": rules,
    }


# ============================================================
# EXPIRATION
# ============================================================

def scan_expiration(
    ticker,
    expiration,
    current_price,
    indicators,
    support,
    resistance,
    target_delta=DEFAULT_TARGET_DELTA,
    spread_width=DEFAULT_SPREAD_WIDTH,
    risk_free_rate=DEFAULT_RISK_FREE_RATE,
    fallback_iv=DEFAULT_FALLBACK_IV,
):

    candidates = []

    diagnostics = {
        "calls": 0,
        "puts": 0,
        "delta_estimates": 0,
        "target_matches": 0,
        "spreads_built": 0,
        "error": None,
    }

    try:

        calls, puts = get_option_chain(
            ticker,
            expiration
        )

    except Exception as exc:

        diagnostics["error"] = str(exc)

        return candidates, diagnostics

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

    # --------------------------------------------------------
    # Bull Put
    # --------------------------------------------------------

    short_put, put_delta, put_stats = (
        select_short_option_by_delta(
            puts,
            current_price,
            expiration,
            target_delta,
            risk_free_rate,
            "put",
            fallback_iv,
        )
    )

    diagnostics["delta_estimates"] += (
        put_stats["delta_estimates"]
    )

    diagnostics["target_matches"] += (
        put_stats["target_matches"]
    )

    if (
        short_put is not None
        and put_delta is not None
    ):

        long_put = find_long_put(
            puts,
            safe_float(
                short_put.get("strike")
            ),
            spread_width,
        )

        candidate = build_candidate(
            ticker,
            current_price,
            expiration,
            "Bull Put",
            short_put,
            put_delta,
            long_put,
            indicators,
            support,
            resistance,
        )

        if candidate:

            candidates.append(
                candidate
            )

            diagnostics[
                "spreads_built"
            ] += 1

    # --------------------------------------------------------
    # Bear Call
    # --------------------------------------------------------

    short_call, call_delta, call_stats = (
        select_short_option_by_delta(
            calls,
            current_price,
            expiration,
            target_delta,
            risk_free_rate,
            "call",
            fallback_iv,
        )
    )

    diagnostics["delta_estimates"] += (
        call_stats["delta_estimates"]
    )

    diagnostics["target_matches"] += (
        call_stats["target_matches"]
    )

    if (
        short_call is not None
        and call_delta is not None
    ):

        long_call = find_long_call(
            calls,
            safe_float(
                short_call.get("strike")
            ),
            spread_width,
        )

        candidate = build_candidate(
            ticker,
            current_price,
            expiration,
            "Bear Call",
            short_call,
            call_delta,
            long_call,
            indicators,
            support,
            resistance,
        )

        if candidate:

            candidates.append(
                candidate
            )

            diagnostics[
                "spreads_built"
            ] += 1

    return candidates, diagnostics


# ============================================================
# TICKER
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

    candidates = []

    diagnostics = {
        "ticker": ticker,
        "current_price": None,
        "trend": None,
        "expirations": 0,
        "option_rows": 0,
        "delta_estimates": 0,
        "target_matches": 0,
        "spreads_built": 0,
        "errors": [],
    }

    current_price = get_current_price(
        ticker
    )

    if current_price is None:

        diagnostics["errors"].append(
            "No current price."
        )

        return candidates, diagnostics

    diagnostics[
        "current_price"
    ] = current_price

    history = get_historical_data(
        ticker,
        period="1y",
        interval="1d"
    )

    if history.empty:

        diagnostics["errors"].append(
            "No historical data."
        )

        return candidates, diagnostics

    indicators = get_latest_indicators(
        history
    )

    if indicators is None:

        diagnostics["errors"].append(
            "Indicators unavailable."
        )

        return candidates, diagnostics

    trend = determine_trend(
        indicators
    )

    diagnostics["trend"] = trend

    support, resistance = (
        calculate_support_resistance(
            history
        )
    )

    try:

        expirations = get_valid_expirations(
            ticker,
            min_dte=min_dte,
            max_dte=max_dte,
        )

    except Exception as exc:

        diagnostics["errors"].append(
            f"Expiration error: {exc}"
        )

        return candidates, diagnostics

    diagnostics[
        "expirations"
    ] = len(expirations)

    for expiration in expirations:

        try:

            expiration_candidates, stats = (
                scan_expiration(
                    ticker=ticker,
                    expiration=expiration,
                    current_price=current_price,
                    indicators=indicators,
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
                stats["calls"]
                + stats["puts"]
            )

            diagnostics[
                "delta_estimates"
            ] += stats[
                "delta_estimates"
            ]

            diagnostics[
                "target_matches"
            ] += stats[
                "target_matches"
            ]

            diagnostics[
                "spreads_built"
            ] += stats[
                "spreads_built"
            ]

            if stats["error"]:

                diagnostics[
                    "errors"
                ].append(
                    f"{expiration}: "
                    f"{stats['error']}"
                )

        except Exception as exc:

            diagnostics[
                "errors"
            ].append(
                f"{expiration}: {exc}"
            )

    return candidates, diagnostics


# ============================================================
# MARKET
# ============================================================

def scan_market(
    tickers=None,
    target_delta=DEFAULT_TARGET_DELTA,
    spread_width=DEFAULT_SPREAD_WIDTH,
    min_dte=DEFAULT_MIN_DTE,
    max_dte=DEFAULT_MAX_DTE,
    risk_free_rate=DEFAULT_RISK_FREE_RATE,
    **kwargs,
):
    """
    Scan the ETF universe.

    **kwargs is intentionally accepted so the scanner remains
    compatible with the existing app.py while we debug it.
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

            candidates, stats = scan_ticker(
                ticker=ticker,
                target_delta=target_delta,
                spread_width=spread_width,
                min_dte=min_dte,
                max_dte=max_dte,
                risk_free_rate=risk_free_rate,
            )

            all_candidates.extend(
                candidates
            )

            diagnostics.append(
                stats
            )

        except Exception as exc:

            diagnostics.append(
                {
                    "ticker": ticker,
                    "current_price": None,
                    "trend": None,
                    "expirations": 0,
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
    # Results
    # --------------------------------------------------------

    if all_candidates:

        results = pd.DataFrame(
            all_candidates
        )

        order = {
            "PASS": 0,
            "REVIEW": 1,
            "FAIL": 2,
        }

        results["_order"] = (
            results["status"]
            .map(order)
            .fillna(9)
        )

        results = results.sort_values(
            [
                "_order",
                "short_delta",
                "dte",
            ]
        )

        results = results.drop(
            columns=["_order"]
        )

    else:

        results = pd.DataFrame()

    results.attrs["diagnostics"] = diagnostics
    return results


# ============================================================
# DIAGNOSTIC TABLE
# ============================================================

def summarize_diagnostics(
    diagnostics
):

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

                "0.10–0.18 Matches": item.get(
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
