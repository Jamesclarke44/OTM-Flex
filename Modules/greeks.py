"""
OTM Flex™
Greeks Module

Black-Scholes option pricing and Greeks calculations.

Also includes a practical delta estimator for Yahoo Finance
option-chain data. When a market quote cannot produce a valid
implied volatility, a fallback volatility is used for estimating
delta so the scanner does not unnecessarily discard the option.
"""

import math


# ============================================================
# NORMAL DISTRIBUTION
# ============================================================

def normal_pdf(x):
    """Standard normal probability density function."""
    return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)


def normal_cdf(x):
    """Standard normal cumulative distribution function."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


# ============================================================
# BLACK-SCHOLES d1 / d2
# ============================================================

def calculate_d1(S, K, T, r, sigma):
    """Calculate Black-Scholes d1."""

    if S <= 0 or K <= 0 or T <= 0 or sigma <= 0:
        return None

    return (
        math.log(S / K)
        + (r + 0.5 * sigma ** 2) * T
    ) / (
        sigma * math.sqrt(T)
    )


def calculate_d2(S, K, T, r, sigma):
    """Calculate Black-Scholes d2."""

    d1 = calculate_d1(
        S,
        K,
        T,
        r,
        sigma
    )

    if d1 is None:
        return None

    return d1 - sigma * math.sqrt(T)


# ============================================================
# DELTA
# ============================================================

def calculate_delta(
    S,
    K,
    T,
    r,
    sigma,
    option_type="call"
):
    """
    Calculate Black-Scholes delta.

    Returns:
        Call delta: 0 to 1
        Put delta: -1 to 0
    """

    d1 = calculate_d1(
        S,
        K,
        T,
        r,
        sigma
    )

    if d1 is None:
        return None

    option_type = str(option_type).lower()

    if option_type == "call":
        return normal_cdf(d1)

    if option_type == "put":
        return normal_cdf(d1) - 1.0

    raise ValueError(
        "option_type must be 'call' or 'put'"
    )


# ============================================================
# GAMMA
# ============================================================

def calculate_gamma(
    S,
    K,
    T,
    r,
    sigma
):
    """Calculate Black-Scholes gamma."""

    d1 = calculate_d1(
        S,
        K,
        T,
        r,
        sigma
    )

    if d1 is None:
        return None

    return (
        normal_pdf(d1)
        / (
            S
            * sigma
            * math.sqrt(T)
        )
    )


# ============================================================
# VEGA
# ============================================================

def calculate_vega(
    S,
    K,
    T,
    r,
    sigma
):
    """Calculate Black-Scholes vega."""

    d1 = calculate_d1(
        S,
        K,
        T,
        r,
        sigma
    )

    if d1 is None:
        return None

    return (
        S
        * normal_pdf(d1)
        * math.sqrt(T)
        / 100.0
    )


# ============================================================
# THETA
# ============================================================

def calculate_theta(
    S,
    K,
    T,
    r,
    sigma,
    option_type="call"
):
    """Calculate approximate daily theta."""

    d1 = calculate_d1(
        S,
        K,
        T,
        r,
        sigma
    )

    d2 = calculate_d2(
        S,
        K,
        T,
        r,
        sigma
    )

    if d1 is None or d2 is None:
        return None

    first_term = (
        -(
            S
            * normal_pdf(d1)
            * sigma
        )
        / (
            2.0
            * math.sqrt(T)
        )
    )

    option_type = str(option_type).lower()

    if option_type == "call":

        second_term = (
            -r
            * K
            * math.exp(-r * T)
            * normal_cdf(d2)
        )

    elif option_type == "put":

        second_term = (
            r
            * K
            * math.exp(-r * T)
            * normal_cdf(-d2)
        )

    else:

        raise ValueError(
            "option_type must be 'call' or 'put'"
        )

    # Convert annual theta to daily theta.
    return (
        first_term + second_term
    ) / 365.0


# ============================================================
# BLACK-SCHOLES PRICE
# ============================================================

def black_scholes_price(
    S,
    K,
    T,
    r,
    sigma,
    option_type="call"
):
    """Calculate theoretical Black-Scholes option price."""

    d1 = calculate_d1(
        S,
        K,
        T,
        r,
        sigma
    )

    d2 = calculate_d2(
        S,
        K,
        T,
        r,
        sigma
    )

    if d1 is None or d2 is None:
        return None

    option_type = str(option_type).lower()

    if option_type == "call":

        price = (
            S * normal_cdf(d1)
            - K
            * math.exp(-r * T)
            * normal_cdf(d2)
        )

    elif option_type == "put":

        price = (
            K
            * math.exp(-r * T)
            * normal_cdf(-d2)
            - S
            * normal_cdf(-d1)
        )

    else:

        raise ValueError(
            "option_type must be 'call' or 'put'"
        )

    return max(
        0.0,
        price
    )


# ============================================================
# IMPLIED VOLATILITY
# ============================================================

def calculate_implied_volatility(
    market_price,
    S,
    K,
    T,
    r,
    option_type="call",
    max_iterations=100
):
    """
    Calculate implied volatility using bisection.

    Returns None when the option price is outside the
    theoretical Black-Scholes range.
    """

    if (
        market_price is None
        or S is None
        or K is None
        or T is None
    ):
        return None

    if (
        market_price <= 0
        or S <= 0
        or K <= 0
        or T <= 0
    ):
        return None

    option_type = str(
        option_type
    ).lower()

    discounted_strike = (
        K * math.exp(-r * T)
    )

    # --------------------------------------------------------
    # Theoretical price boundaries
    # --------------------------------------------------------

    if option_type == "call":

        minimum_price = max(
            0.0,
            S - discounted_strike
        )

        maximum_price = S

    elif option_type == "put":

        minimum_price = max(
            0.0,
            discounted_strike - S
        )

        maximum_price = discounted_strike

    else:

        return None

    tolerance = 1e-8

    if (
        market_price
        < minimum_price - tolerance
    ):
        return None

    if (
        market_price
        > maximum_price + tolerance
    ):
        return None

    # --------------------------------------------------------
    # Search range
    # --------------------------------------------------------

    low = 0.0001
    high = 5.0

    low_price = black_scholes_price(
        S,
        K,
        T,
        r,
        low,
        option_type
    )

    high_price = black_scholes_price(
        S,
        K,
        T,
        r,
        high,
        option_type
    )

    if low_price is None or high_price is None:
        return None

    # Essentially intrinsic value.
    if abs(
        market_price - low_price
    ) < 1e-7:

        return low

    if market_price < low_price:
        return None

    if market_price > high_price:
        return None

    # --------------------------------------------------------
    # Bisection
    # --------------------------------------------------------

    for _ in range(max_iterations):

        mid = (
            low + high
        ) / 2.0

        mid_price = black_scholes_price(
            S,
            K,
            T,
            r,
            mid,
            option_type
        )

        if mid_price is None:
            return None

        difference = (
            mid_price - market_price
        )

        if abs(difference) < 1e-6:
            return mid

        if difference > 0:
            high = mid
        else:
            low = mid

    return (
        low + high
    ) / 2.0


# ============================================================
# DELTA FROM MARKET QUOTE
# ============================================================

def calculate_delta_from_quote(
    market_price,
    S,
    K,
    T,
    r,
    option_type="put",
    fallback_volatility=0.30
):
    """
    Estimate delta from an option's market price.

    Process:

    1. Try to calculate implied volatility from the quote.
    2. If that fails, use fallback_volatility.
    3. Calculate Black-Scholes delta.

    The fallback is intentional because Yahoo Finance can provide
    stale, crossed, or otherwise imperfect option quotes.
    """

    if (
        market_price is None
        or S is None
        or K is None
        or T is None
    ):
        return None

    if (
        market_price <= 0
        or S <= 0
        or K <= 0
        or T <= 0
    ):
        return None

    # --------------------------------------------------------
    # Try actual implied volatility first.
    # --------------------------------------------------------

    volatility = calculate_implied_volatility(
        market_price=market_price,
        S=S,
        K=K,
        T=T,
        r=r,
        option_type=option_type
    )

    # --------------------------------------------------------
    # Fallback volatility
    # --------------------------------------------------------

    if (
        volatility is None
        or volatility <= 0
    ):

        volatility = float(
            fallback_volatility
        )

    # Safety check.
    if volatility <= 0:
        return None

    # --------------------------------------------------------
    # Calculate delta
    # --------------------------------------------------------

    return calculate_delta(
        S=S,
        K=K,
        T=T,
        r=r,
        sigma=volatility,
        option_type=option_type
    )


# ============================================================
# COMPLETE GREEKS
# ============================================================

def calculate_greeks(
    S,
    K,
    T,
    r,
    sigma,
    option_type="call"
):
    """Return the major Black-Scholes Greeks."""

    return {
        "delta": calculate_delta(
            S,
            K,
            T,
            r,
            sigma,
            option_type
        ),

        "gamma": calculate_gamma(
            S,
            K,
            T,
            r,
            sigma
        ),

        "vega": calculate_vega(
            S,
            K,
            T,
            r,
            sigma
        ),

        "theta": calculate_theta(
            S,
            K,
            T,
            r,
            sigma,
            option_type
        ),
    }


# ============================================================
# FIND STRIKE BY DELTA
# ============================================================

def find_strike_by_delta(
    S,
    strikes,
    T,
    r,
    sigma,
    target_delta,
    option_type="put"
):
    """
    Find the strike with delta closest to target_delta.
    """

    if strikes is None:
        return None

    best_strike = None
    best_difference = float("inf")

    for strike in strikes:

        try:
            strike = float(strike)
        except (TypeError, ValueError):
            continue

        delta = calculate_delta(
            S=S,
            K=strike,
            T=T,
            r=r,
            sigma=sigma,
            option_type=option_type
        )

        if delta is None:
            continue

        difference = abs(
            abs(delta)
            - abs(float(target_delta))
        )

        if difference < best_difference:

            best_difference = difference
            best_strike = strike

    return best_strike
