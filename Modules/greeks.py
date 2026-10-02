"""
OTM Flex™
Option Greeks Module

Calculates option Greeks using the Black-Scholes model.

Primary purpose:
    Calculate reliable estimated Delta values for
    selecting OTM Flex™ credit spread strikes.
"""

import math


# ============================================================
# NORMAL DISTRIBUTION
# ============================================================

def normal_pdf(x):
    """
    Standard normal probability density function.
    """

    return (
        math.exp(-0.5 * x * x)
        / math.sqrt(2 * math.pi)
    )


def normal_cdf(x):
    """
    Standard normal cumulative distribution function.
    """

    return (
        0.5
        * (
            1
            + math.erf(
                x / math.sqrt(2)
            )
        )
    )


# ============================================================
# D1 / D2
# ============================================================

def calculate_d1(
    stock_price,
    strike_price,
    time_to_expiration,
    volatility,
    risk_free_rate=0.04,
    dividend_yield=0.0,
):
    """
    Calculate Black-Scholes d1.
    """

    if (
        stock_price <= 0
        or strike_price <= 0
        or time_to_expiration <= 0
        or volatility <= 0
    ):
        return None

    numerator = (
        math.log(
            stock_price / strike_price
        )
        + (
            risk_free_rate
            - dividend_yield
            + 0.5 * volatility ** 2
        )
        * time_to_expiration
    )

    denominator = (
        volatility
        * math.sqrt(
            time_to_expiration
        )
    )

    return numerator / denominator


def calculate_d2(
    stock_price,
    strike_price,
    time_to_expiration,
    volatility,
    risk_free_rate=0.04,
    dividend_yield=0.0,
):
    """
    Calculate Black-Scholes d2.
    """

    d1 = calculate_d1(
        stock_price,
        strike_price,
        time_to_expiration,
        volatility,
        risk_free_rate,
        dividend_yield,
    )

    if d1 is None:
        return None

    return (
        d1
        - volatility
        * math.sqrt(
            time_to_expiration
        )
    )


# ============================================================
# DELTA
# ============================================================

def calculate_delta(
    stock_price,
    strike_price,
    time_to_expiration,
    volatility,
    option_type,
    risk_free_rate=0.04,
    dividend_yield=0.0,
):
    """
    Calculate Black-Scholes Delta.

    Call:
        0 to +1

    Put:
        -1 to 0
    """

    d1 = calculate_d1(
        stock_price,
        strike_price,
        time_to_expiration,
        volatility,
        risk_free_rate,
        dividend_yield,
    )

    if d1 is None:
        return None

    option_type = option_type.lower()

    discount = math.exp(
        -dividend_yield
        * time_to_expiration
    )

    if option_type == "call":

        return (
            discount
            * normal_cdf(d1)
        )

    if option_type == "put":

        return (
            discount
            * (
                normal_cdf(d1)
                - 1
            )
        )

    raise ValueError(
        "option_type must be 'call' or 'put'."
    )


# ============================================================
# GAMMA
# ============================================================

def calculate_gamma(
    stock_price,
    strike_price,
    time_to_expiration,
    volatility,
    risk_free_rate=0.04,
    dividend_yield=0.0,
):
    """
    Calculate Gamma.
    """

    d1 = calculate_d1(
        stock_price,
        strike_price,
        time_to_expiration,
        volatility,
        risk_free_rate,
        dividend_yield,
    )

    if d1 is None:
        return None

    return (
        math.exp(
            -dividend_yield
            * time_to_expiration
        )
        * normal_pdf(d1)
        / (
            stock_price
            * volatility
            * math.sqrt(
                time_to_expiration
            )
        )
    )


# ============================================================
# VEGA
# ============================================================

def calculate_vega(
    stock_price,
    strike_price,
    time_to_expiration,
    volatility,
    risk_free_rate=0.04,
    dividend_yield=0.0,
):
    """
    Calculate Vega.

    Result represents the approximate option
    price change for a 1.00 change in volatility.
    """

    d1 = calculate_d1(
        stock_price,
        strike_price,
        time_to_expiration,
        volatility,
        risk_free_rate,
        dividend_yield,
    )

    if d1 is None:
        return None

    return (
        stock_price
        * math.exp(
            -dividend_yield
            * time_to_expiration
        )
        * normal_pdf(d1)
        * math.sqrt(
            time_to_expiration
        )
    )


# ============================================================
# THETA
# ============================================================

def calculate_theta(
    stock_price,
    strike_price,
    time_to_expiration,
    volatility,
    option_type,
    risk_free_rate=0.04,
    dividend_yield=0.0,
):
    """
    Calculate approximate daily Theta.
    """

    d1 = calculate_d1(
        stock_price,
        strike_price,
        time_to_expiration,
        volatility,
        risk_free_rate,
        dividend_yield,
    )

    d2 = calculate_d2(
        stock_price,
        strike_price,
        time_to_expiration,
        volatility,
        risk_free_rate,
        dividend_yield,
    )

    if d1 is None or d2 is None:
        return None

    option_type = option_type.lower()

    first_term = (
        -(
            stock_price
            * math.exp(
                -dividend_yield
                * time_to_expiration
            )
            * normal_pdf(d1)
            * volatility
        )
        / (
            2
            * math.sqrt(
                time_to_expiration
            )
        )
    )

    if option_type == "call":

        theta = (
            first_term
            - (
                risk_free_rate
                * strike_price
                * math.exp(
                    -risk_free_rate
                    * time_to_expiration
                )
                * normal_cdf(d2)
            )
            + (
                dividend_yield
                * stock_price
                * math.exp(
                    -dividend_yield
                    * time_to_expiration
                )
                * normal_cdf(d1)
            )
        )

    elif option_type == "put":

        theta = (
            first_term
            + (
                risk_free_rate
                * strike_price
                * math.exp(
                    -risk_free_rate
                    * time_to_expiration
                )
                * normal_cdf(-d2)
            )
            - (
                dividend_yield
                * stock_price
                * math.exp(
                    -dividend_yield
                    * time_to_expiration
                )
                * normal_cdf(-d1)
            )
        )

    else:

        raise ValueError(
            "option_type must be 'call' or 'put'."
        )

    # Convert annual theta to daily theta
    return theta / 365


# ============================================================
# IMPLIED VOLATILITY
# ============================================================

def black_scholes_price(
    stock_price,
    strike_price,
    time_to_expiration,
    volatility,
    option_type,
    risk_free_rate=0.04,
    dividend_yield=0.0,
):
    """
    Calculate theoretical Black-Scholes option price.
    """

    d1 = calculate_d1(
        stock_price,
        strike_price,
        time_to_expiration,
        volatility,
        risk_free_rate,
        dividend_yield,
    )

    d2 = calculate_d2(
        stock_price,
        strike_price,
        time_to_expiration,
        volatility,
        risk_free_rate,
        dividend_yield,
    )

    if d1 is None or d2 is None:
        return None

    discount_r = math.exp(
        -risk_free_rate
        * time_to_expiration
    )

    discount_q = math.exp(
        -dividend_yield
        * time_to_expiration
    )

    option_type = option_type.lower()

    if option_type == "call":

        return (
            stock_price
            * discount_q
            * normal_cdf(d1)
            - strike_price
            * discount_r
            * normal_cdf(d2)
        )

    if option_type == "put":

        return (
            strike_price
            * discount_r
            * normal_cdf(-d2)
            - stock_price
            * discount_q
            * normal_cdf(-d1)
        )

    raise ValueError(
        "option_type must be 'call' or 'put'."
    )


def calculate_implied_volatility(
    market_price,
    stock_price,
    strike_price,
    time_to_expiration,
    option_type,
    risk_free_rate=0.04,
    dividend_yield=0.0,
):
    """
    Estimate implied volatility using bisection.

    Returns:
        Decimal volatility.

        Example:
            0.25 = 25% IV
    """

    if market_price <= 0:
        return None

    low = 0.0001
    high = 5.0

    for _ in range(100):

        mid = (
            low + high
        ) / 2

        price = black_scholes_price(
            stock_price,
            strike_price,
            time_to_expiration,
            mid,
            option_type,
            risk_free_rate,
            dividend_yield,
        )

        if price is None:
            return None

        difference = (
            price - market_price
        )

        if abs(difference) < 0.0001:
            return mid

        if price > market_price:

            high = mid

        else:

            low = mid

    return (
        low + high
    ) / 2


# ============================================================
# COMPLETE GREEKS
# ============================================================

def calculate_greeks(
    stock_price,
    strike_price,
    dte,
    market_price,
    option_type,
    risk_free_rate=0.04,
    dividend_yield=0.0,
):
    """
    Calculate IV and all major Greeks.

    Returns a dictionary.
    """

    if dte <= 0:
        return None

    time_to_expiration = (
        dte / 365
    )

    implied_volatility = (
        calculate_implied_volatility(
            market_price,
            stock_price,
            strike_price,
            time_to_expiration,
            option_type,
            risk_free_rate,
            dividend_yield,
        )
    )

    if (
        implied_volatility is None
        or implied_volatility <= 0
    ):
        return None

    delta = calculate_delta(
        stock_price,
        strike_price,
        time_to_expiration,
        implied_volatility,
        option_type,
        risk_free_rate,
        dividend_yield,
    )

    gamma = calculate_gamma(
        stock_price,
        strike_price,
        time_to_expiration,
        implied_volatility,
        risk_free_rate,
        dividend_yield,
    )

    theta = calculate_theta(
        stock_price,
        strike_price,
        time_to_expiration,
        implied_volatility,
        option_type,
        risk_free_rate,
        dividend_yield,
    )

    vega = calculate_vega(
        stock_price,
        strike_price,
        time_to_expiration,
        implied_volatility,
        risk_free_rate,
        dividend_yield,
    )

    return {
        "iv": implied_volatility,
        "delta": delta,
        "gamma": gamma,
        "theta": theta,
        "vega": vega,
    }


# ============================================================
# FIND STRIKE BY TARGET DELTA
# ============================================================

def find_strike_by_delta(
    options,
    stock_price,
    dte,
    option_type,
    target_delta=0.14,
    risk_free_rate=0.04,
    dividend_yield=0.0,
):
    """
    Find the option strike whose calculated delta is
    closest to the target delta.

    'options' should be a DataFrame containing:

        strike
        bid
        ask

    Returns:
        Dictionary containing strike and Greeks.
    """

    if options is None or options.empty:
        return None

    best_option = None
    smallest_difference = float("inf")

    for _, option in options.iterrows():

        strike = option.get(
            "strike"
        )

        bid = option.get(
            "bid",
            0
        )

        ask = option.get(
            "ask",
            0
        )

        if strike is None:
            continue

        try:

            strike = float(strike)
            bid = float(bid)
            ask = float(ask)

        except (
            TypeError,
            ValueError,
        ):

            continue

        if strike <= 0:
            continue

        # Use midpoint when possible
        if bid > 0 and ask > 0:

            market_price = (
                bid + ask
            ) / 2

        elif bid > 0:

            market_price = bid

        elif ask > 0:

            market_price = ask

        else:

            continue

        greeks = calculate_greeks(
            stock_price=stock_price,
            strike_price=strike,
            dte=dte,
            market_price=market_price,
            option_type=option_type,
            risk_free_rate=risk_free_rate,
            dividend_yield=dividend_yield,
        )

        if greeks is None:
            continue

        delta = greeks["delta"]

        difference = abs(
            abs(delta)
            - abs(target_delta)
        )

        if difference < smallest_difference:

            smallest_difference = difference

            best_option = {
                "strike": strike,
                "bid": bid,
                "ask": ask,
                "mid": market_price,
                "delta": delta,
                "iv": greeks["iv"],
                "gamma": greeks["gamma"],
                "theta": greeks["theta"],
                "vega": greeks["vega"],
            }

    return best_option
