"""
OTM Flex™
Trading Rules Module

Converts the OTM Flex™ Rule Book into
machine-readable trade checks.
"""


# ============================================================
# CONFIGURATION
# ============================================================

MIN_DELTA = 0.10
MAX_DELTA = 0.18

MIN_DTE = 7
MAX_DTE = 45

PROFIT_TARGET = 0.50


# ============================================================
# HELPER
# ============================================================

def rule_result(
    name,
    status,
    value=None,
    explanation=""
):
    """
    Create a standardized rule result.
    """

    return {
        "rule": name,
        "status": status,
        "value": value,
        "explanation": explanation,
    }


# ============================================================
# TREND RULE
# ============================================================

def check_trend(
    spread_type,
    trend
):
    """
    Check whether the spread agrees with the trend.

    Bull Put → Bullish trend
    Bear Call → Bearish trend
    """

    spread_type = spread_type.lower()
    trend = trend.lower()

    if spread_type == "bull put":

        if trend == "bullish":
            return rule_result(
                "Trend",
                "PASS",
                trend,
                "Bull Put agrees with bullish trend."
            )

        if trend == "neutral":
            return rule_result(
                "Trend",
                "REVIEW",
                trend,
                "Trend is neutral."
            )

        return rule_result(
            "Trend",
            "FAIL",
            trend,
            "Bull Put conflicts with bearish trend."
        )

    if spread_type == "bear call":

        if trend == "bearish":
            return rule_result(
                "Trend",
                "PASS",
                trend,
                "Bear Call agrees with bearish trend."
            )

        if trend == "neutral":
            return rule_result(
                "Trend",
                "REVIEW",
                trend,
                "Trend is neutral."
            )

        return rule_result(
            "Trend",
            "FAIL",
            trend,
            "Bear Call conflicts with bullish trend."
        )

    return rule_result(
        "Trend",
        "FAIL",
        trend,
        "Unknown spread type."
    )


# ============================================================
# DELTA RULE
# ============================================================

def check_delta(delta):
    """
    Check short-leg delta.

    Target:
        0.10–0.18
    """

    delta = abs(float(delta))

    if MIN_DELTA <= delta <= MAX_DELTA:

        return rule_result(
            "Short Delta",
            "PASS",
            delta,
            "Delta is inside the OTM Flex™ target range."
        )

    if delta < MIN_DELTA:

        return rule_result(
            "Short Delta",
            "REVIEW",
            delta,
            "Delta is farther OTM than the target range."
        )

    return rule_result(
        "Short Delta",
        "FAIL",
        delta,
        "Delta is too close to the money."
    )


# ============================================================
# DTE RULE
# ============================================================

def check_dte(dte):
    """
    Check days to expiration.
    """

    dte = int(dte)

    if MIN_DTE <= dte <= MAX_DTE:

        return rule_result(
            "DTE",
            "PASS",
            dte,
            "DTE is inside the preferred range."
        )

    return rule_result(
        "DTE",
        "REVIEW",
        dte,
        "DTE is outside the preferred 7–45 day range."
    )


# ============================================================
# ATR DISTANCE
# ============================================================

def check_atr_distance(
    distance_atr,
    market_condition="normal"
):
    """
    Evaluate distance from the current price
    using ATR.

    General guideline:

    Strong trend:
        1–2 ATR

    Normal:
        approximately 2 ATR

    Choppy / uncertain:
        2–3 ATR
    """

    distance_atr = float(distance_atr)

    market_condition = market_condition.lower()

    if market_condition == "strong":

        minimum = 1.0

        if distance_atr >= minimum:
            return rule_result(
                "ATR Distance",
                "PASS",
                distance_atr,
                "Distance provides at least 1 ATR of room."
            )

    elif market_condition == "choppy":

        minimum = 2.0

        if distance_atr >= minimum:
            return rule_result(
                "ATR Distance",
                "PASS",
                distance_atr,
                "Distance provides at least 2 ATR of room."
            )

    else:

        minimum = 1.5

        if distance_atr >= minimum:
            return rule_result(
                "ATR Distance",
                "PASS",
                distance_atr,
                "Distance provides reasonable ATR room."
            )

    return rule_result(
        "ATR Distance",
        "REVIEW",
        distance_atr,
        "Consider moving the short strike farther OTM."
    )


# ============================================================
# RSI RULE
# ============================================================

def check_rsi(
    spread_type,
    rsi
):
    """
    Evaluate RSI direction.

    Bull Put:
        RSI > 50 preferred

    Bear Call:
        RSI < 50 preferred
    """

    rsi = float(rsi)

    spread_type = spread_type.lower()

    if spread_type == "bull put":

        if rsi > 50:
            return rule_result(
                "RSI",
                "PASS",
                rsi,
                "RSI supports bullish conditions."
            )

        return rule_result(
            "RSI",
            "REVIEW",
            rsi,
            "RSI is below 50."
        )

    if spread_type == "bear call":

        if rsi < 50:
            return rule_result(
                "RSI",
                "PASS",
                rsi,
                "RSI supports bearish conditions."
            )

        return rule_result(
            "RSI",
            "REVIEW",
            rsi,
            "RSI is above 50."
        )

    return rule_result(
        "RSI",
        "REVIEW",
        rsi,
        "Unknown spread type."
    )


# ============================================================
# MACD RULE
# ============================================================

def check_macd(
    spread_type,
    macd,
    signal
):
    """
    Evaluate MACD direction.
    """

    macd = float(macd)
    signal = float(signal)

    spread_type = spread_type.lower()

    if spread_type == "bull put":

        if macd > signal:
            return rule_result(
                "MACD",
                "PASS",
                macd,
                "MACD is above the signal line."
            )

        return rule_result(
            "MACD",
            "REVIEW",
            macd,
            "MACD is below the signal line."
        )

    if spread_type == "bear call":

        if macd < signal:
            return rule_result(
                "MACD",
                "PASS",
                macd,
                "MACD is below the signal line."
            )

        return rule_result(
            "MACD",
            "REVIEW",
            macd,
            "MACD is above the signal line."
        )

    return rule_result(
        "MACD",
        "REVIEW",
        macd,
        "Unknown spread type."
    )


# ============================================================
# LIQUIDITY RULE
# ============================================================

def check_liquidity(
    bid,
    ask,
    open_interest=None,
    volume=None
):
    """
    Basic option liquidity check.

    Uses bid/ask spread as the primary measure.
    """

    bid = float(bid)
    ask = float(ask)

    if bid <= 0 or ask <= 0:

        return rule_result(
            "Liquidity",
            "FAIL",
            None,
            "Invalid bid/ask prices."
        )

    midpoint = (bid + ask) / 2

    spread = ask - bid

    spread_percent = (
        spread / midpoint
    ) * 100

    if spread_percent <= 5:

        return rule_result(
            "Liquidity",
            "PASS",
            spread_percent,
            "Bid/ask spread is reasonably tight."
        )

    if spread_percent <= 10:

        return rule_result(
            "Liquidity",
            "REVIEW",
            spread_percent,
            "Bid/ask spread is somewhat wide."
        )

    return rule_result(
        "Liquidity",
        "FAIL",
        spread_percent,
        "Bid/ask spread is too wide."
    )


# ============================================================
# SUPPORT / RESISTANCE
# ============================================================

def check_price_level(
    spread_type,
    current_price,
    short_strike,
    support=None,
    resistance=None
):
    """
    Check whether the short strike is positioned
    appropriately relative to a known support/resistance level.
    """

    spread_type = spread_type.lower()

    current_price = float(current_price)
    short_strike = float(short_strike)

    if spread_type == "bull put":

        if support is None:

            return rule_result(
                "Support",
                "REVIEW",
                None,
                "No support level supplied."
            )

        if short_strike < support:

            return rule_result(
                "Support",
                "PASS",
                support,
                "Short put is below identified support."
            )

        return rule_result(
            "Support",
            "REVIEW",
            support,
            "Short put is not below identified support."
        )

    if spread_type == "bear call":

        if resistance is None:

            return rule_result(
                "Resistance",
                "REVIEW",
                None,
                "No resistance level supplied."
            )

        if short_strike > resistance:

            return rule_result(
                "Resistance",
                "PASS",
                resistance,
                "Short call is above identified resistance."
            )

        return rule_result(
            "Resistance",
            "REVIEW",
            resistance,
            "Short call is not above identified resistance."
        )

    return rule_result(
        "Price Level",
        "REVIEW",
        None,
        "Unknown spread type."
    )


# ============================================================
# COMPLETE TRADE CHECK
# ============================================================

def evaluate_trade(
    spread_type,
    trend,
    delta,
    dte,
    distance_atr,
    rsi,
    macd,
    macd_signal,
    bid,
    ask,
    current_price,
    short_strike,
    market_condition="normal",
    support=None,
    resistance=None,
    open_interest=None,
    volume=None
):
    """
    Run the complete OTM Flex™ rule set.
    """

    results = []

    results.append(
        check_trend(
            spread_type,
            trend
        )
    )

    results.append(
        check_delta(delta)
    )

    results.append(
        check_dte(dte)
    )

    results.append(
        check_atr_distance(
            distance_atr,
            market_condition
        )
    )

    results.append(
        check_rsi(
            spread_type,
            rsi
        )
    )

    results.append(
        check_macd(
            spread_type,
            macd,
            macd_signal
        )
    )

    results.append(
        check_liquidity(
            bid,
            ask,
            open_interest,
            volume
        )
    )

    results.append(
        check_price_level(
            spread_type,
            current_price,
            short_strike,
            support,
            resistance
        )
    )

    return results


# ============================================================
# TRADE STATUS
# ============================================================

def get_overall_status(results):
    """
    Determine the overall status of a trade.

    FAIL:
        At least one hard rule fails.

    REVIEW:
        No hard failures, but one or more
        rules require review.

    PASS:
        All rules pass.
    """

    statuses = [
        result["status"]
        for result in results
    ]

    if "FAIL" in statuses:
        return "FAIL"

    if "REVIEW" in statuses:
        return "REVIEW"

    return "PASS"


# ============================================================
# PROFIT TARGET
# ============================================================

def calculate_profit_target(
    max_profit
):
    """
    Calculate the 50% profit-taking target.
    """

    return float(max_profit) * PROFIT_TARGET
