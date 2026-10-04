"""
OTM Flex™
Position Sizing Module

Calculates position size, maximum risk, maximum profit,
and account-level risk for credit spreads.
"""


# ============================================================
# BASIC PROFIT / LOSS
# ============================================================

def calculate_max_profit(credit, contracts=1):
    """
    Maximum profit for a credit spread.

    Credit is entered per share.
    One option contract controls 100 shares.
    """
    return float(credit) * 100 * int(contracts)


def calculate_max_loss(spread_width, credit, contracts=1):
    """
    Maximum possible loss for a credit spread.
    """
    loss_per_contract = (
        (float(spread_width) - float(credit)) * 100
    )

    return max(0.0, loss_per_contract * int(contracts))


def calculate_loss_per_contract(spread_width, credit):
    """
    Maximum loss for one spread contract.
    """
    return max(
        0.0,
        (float(spread_width) - float(credit)) * 100
    )


# ============================================================
# ACCOUNT RISK
# ============================================================

def calculate_max_account_risk(account_size, risk_percent):
    """
    Maximum dollar amount allowed to be at risk.
    """

    account_size = float(account_size)
    risk_percent = float(risk_percent)

    return account_size * (risk_percent / 100)


# ============================================================
# CONTRACT COUNT
# ============================================================

def calculate_max_contracts(
    account_size,
    risk_percent,
    spread_width,
    credit
):
    """
    Calculate the maximum number of contracts allowed
    by the selected account risk percentage.
    """

    allowed_risk = calculate_max_account_risk(
        account_size,
        risk_percent
    )

    loss_per_contract = calculate_loss_per_contract(
        spread_width,
        credit
    )

    if loss_per_contract <= 0:
        return 0

    return int(
        allowed_risk // loss_per_contract
    )


# ============================================================
# POSITION RISK
# ============================================================

def calculate_position_risk(
    spread_width,
    credit,
    contracts
):
    """
    Calculate the maximum risk of the selected position.
    """

    loss_per_contract = calculate_loss_per_contract(
        spread_width,
        credit
    )

    return loss_per_contract * int(contracts)


def calculate_actual_risk_percent(
    account_size,
    max_loss
):
    """
    Calculate actual account risk percentage.
    """

    account_size = float(account_size)

    if account_size <= 0:
        return 0.0

    return (
        float(max_loss) / account_size
    ) * 100


def calculate_return_on_risk(
    credit,
    spread_width
):
    """
    Maximum return on risk as a percentage.
    """

    max_loss = calculate_loss_per_contract(
        spread_width,
        credit
    )

    max_profit = float(credit) * 100

    if max_loss <= 0:
        return 0.0

    return (
        max_profit / max_loss
    ) * 100


# ============================================================
# PROFIT TARGET
# ============================================================

def calculate_profit_target(
    credit,
    profit_target_percent=50
):
    """
    Dollar profit target based on the percentage of
    maximum possible credit profit.
    """

    max_profit = float(credit) * 100

    return max_profit * (
        float(profit_target_percent) / 100
    )


# ============================================================
# RISK CHECK
# ============================================================

def check_position_risk(
    account_size,
    risk_percent,
    spread_width,
    credit,
    contracts
):
    """
    Determine whether a position is within the
    selected account risk limit.
    """

    allowed_risk = calculate_max_account_risk(
        account_size,
        risk_percent
    )

    max_loss = calculate_position_risk(
        spread_width,
        credit,
        contracts
    )

    return {
        "allowed_risk": allowed_risk,
        "max_loss": max_loss,
        "within_risk_limit": max_loss <= allowed_risk,
    }


# ============================================================
# COMPLETE POSITION ANALYSIS
# ============================================================

def analyze_position(
    account_size,
    risk_percent,
    spread_width,
    credit,
    contracts=None,
    profit_target_percent=50
):
    """
    Complete position-sizing analysis.

    Returns all keys expected by app.py.
    """

    account_size = float(account_size)
    risk_percent = float(risk_percent)
    spread_width = float(spread_width)
    credit = float(credit)

    # Maximum dollar risk permitted by account settings.
    allowed_risk = calculate_max_account_risk(
        account_size,
        risk_percent
    )

    # Risk for one contract.
    loss_per_contract = calculate_loss_per_contract(
        spread_width,
        credit
    )

    # Maximum number of contracts allowed.
    max_contracts = calculate_max_contracts(
        account_size,
        risk_percent,
        spread_width,
        credit
    )

    # If the user hasn't specified contracts,
    # use the maximum allowed.
    if contracts is None:
        contracts = max_contracts

    contracts = max(0, int(contracts))

    # Position totals.
    max_loss = calculate_max_loss(
        spread_width,
        credit,
        contracts
    )

    max_profit = calculate_max_profit(
        credit,
        contracts
    )

    actual_risk_percent = calculate_actual_risk_percent(
        account_size,
        max_loss
    )

    return_on_risk = calculate_return_on_risk(
        credit,
        spread_width
    )

    profit_target = calculate_profit_target(
        credit,
        profit_target_percent
    ) * contracts

    within_risk_limit = max_loss <= allowed_risk

    return {
        # Account
        "account_size": account_size,
        "risk_percent": risk_percent,

        # Risk allowance
        "allowed_risk": allowed_risk,

        # Spread
        "spread_width": spread_width,
        "credit": credit,

        # Contracts
        "contracts": contracts,
        "max_contracts": max_contracts,

        # Per-contract risk
        "loss_per_contract": loss_per_contract,

        # Position totals
        "max_loss": max_loss,
        "max_profit": max_profit,

        # Risk metrics
        "actual_risk_percent": actual_risk_percent,
        "return_on_risk": return_on_risk,

        # Profit target
        "profit_target_percent": profit_target_percent,
        "profit_target": profit_target,

        # Risk check
        "within_risk_limit": within_risk_limit,
    }


# ============================================================
# ALIAS / COMPATIBILITY FUNCTIONS
# ============================================================

def calculate_position_size(
    account_size,
    risk_percent,
    spread_width,
    credit
):
    """
    Compatibility helper returning the maximum
    contract count.
    """

    return calculate_max_contracts(
        account_size,
        risk_percent,
        spread_width,
        credit
    )
