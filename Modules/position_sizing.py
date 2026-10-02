"""
OTM Flex™
Position Sizing Module

Calculates position size and risk for defined-risk
credit spreads.
"""


# ============================================================
# BASIC SPREAD CALCULATIONS
# ============================================================

def calculate_max_profit(
    credit: float,
    contracts: int = 1,
):
    """
    Calculate maximum potential profit.

    Credit is entered per share.

    Example:
        $1.00 credit
        2 contracts

        $1.00 × 100 × 2 = $200
    """

    return (
        float(credit)
        * 100
        * int(contracts)
    )


def calculate_max_loss(
    spread_width: float,
    credit: float,
    contracts: int = 1,
):
    """
    Calculate maximum theoretical loss.

    Maximum loss per spread:

        (Spread Width - Credit) × 100
    """

    spread_width = float(
        spread_width
    )

    credit = float(
        credit
    )

    contracts = int(
        contracts
    )

    loss_per_contract = (
        spread_width - credit
    ) * 100

    return (
        loss_per_contract
        * contracts
    )


def calculate_loss_per_contract(
    spread_width: float,
    credit: float,
):
    """
    Calculate maximum theoretical loss
    for one contract.
    """

    return (
        float(spread_width)
        - float(credit)
    ) * 100


# ============================================================
# ACCOUNT RISK
# ============================================================

def calculate_max_account_risk(
    account_size: float,
    risk_percent: float,
):
    """
    Calculate the maximum dollar amount
    allowed to be at risk.
    """

    return (
        float(account_size)
        * (
            float(risk_percent)
            / 100
        )
    )


# ============================================================
# MAX CONTRACTS
# ============================================================

def calculate_max_contracts(
    account_size: float,
    risk_percent: float,
    spread_width: float,
    credit: float,
):
    """
    Calculate the maximum number of contracts
    that fit within the selected account-risk limit.
    """

    max_risk = calculate_max_account_risk(
        account_size,
        risk_percent,
    )

    loss_per_contract = (
        calculate_loss_per_contract(
            spread_width,
            credit,
        )
    )

    if loss_per_contract <= 0:
        return 0

    return int(
        max_risk
        // loss_per_contract
    )


# ============================================================
# TOTAL POSITION RISK
# ============================================================

def calculate_position_risk(
    spread_width: float,
    credit: float,
    contracts: int,
):
    """
    Calculate total theoretical maximum loss.
    """

    return calculate_max_loss(
        spread_width,
        credit,
        contracts,
    )


# ============================================================
# ACTUAL ACCOUNT RISK %
# ============================================================

def calculate_actual_risk_percent(
    account_size: float,
    position_risk: float,
):
    """
    Calculate the percentage of the account
    represented by maximum theoretical loss.
    """

    if account_size <= 0:
        return 0.0

    return (
        float(position_risk)
        / float(account_size)
    ) * 100


# ============================================================
# POTENTIAL RETURN
# ============================================================

def calculate_return_on_risk(
    credit: float,
    spread_width: float,
):
    """
    Calculate maximum profit as a percentage
    of maximum loss for one spread.

    Example:

        $1 credit
        $5 spread

        Max profit = $100
        Max loss = $400

        Return on risk = 25%
    """

    max_loss = (
        float(spread_width)
        - float(credit)
    )

    if max_loss <= 0:
        return 0.0

    return (
        float(credit)
        / max_loss
    ) * 100


# ============================================================
# PROFIT TARGET
# ============================================================

def calculate_profit_target(
    credit: float,
    target_percent: float = 50.0,
    contracts: int = 1,
):
    """
    Calculate the dollar profit at the selected
    percentage of maximum credit.

    Default:
        50% profit target.
    """

    maximum_profit = calculate_max_profit(
        credit,
        contracts,
    )

    return (
        maximum_profit
        * (
            float(target_percent)
            / 100
        )
    )


# ============================================================
# RISK CHECK
# ============================================================

def check_position_risk(
    account_size: float,
    risk_percent: float,
    spread_width: float,
    credit: float,
    contracts: int,
):
    """
    Determine whether a position is within
    the selected account-risk limit.
    """

    allowed_risk = (
        calculate_max_account_risk(
            account_size,
            risk_percent,
        )
    )

    position_risk = (
        calculate_position_risk(
            spread_width,
            credit,
            contracts,
        )
    )

    actual_risk_percent = (
        calculate_actual_risk_percent(
            account_size,
            position_risk,
        )
    )

    if position_risk <= allowed_risk:

        status = "PASS"

    else:

        status = "FAIL"

    return {
        "status": status,
        "allowed_risk": allowed_risk,
        "position_risk": position_risk,
        "actual_risk_percent": actual_risk_percent,
    }


# ============================================================
# COMPLETE POSITION ANALYSIS
# ============================================================

def analyze_position(
    account_size: float,
    risk_percent: float,
    spread_width: float,
    credit: float,
    contracts: int,
    profit_target_percent: float = 50.0,
):
    """
    Complete position-sizing analysis.
    """

    account_size = float(
        account_size
    )

    risk_percent = float(
        risk_percent
    )

    spread_width = float(
        spread_width
    )

    credit = float(
        credit
    )

    contracts = int(
        contracts
    )

    max_allowed_risk = (
        calculate_max_account_risk(
            account_size,
            risk_percent,
        )
    )

    loss_per_contract = (
        calculate_loss_per_contract(
            spread_width,
            credit,
        )
    )

    maximum_loss = (
        calculate_position_risk(
            spread_width,
            credit,
            contracts,
        )
    )

    maximum_profit = (
        calculate_max_profit(
            credit,
            contracts,
        )
    )

    actual_risk_percent = (
        calculate_actual_risk_percent(
            account_size,
            maximum_loss,
        )
    )

    return_on_risk = (
        calculate_return_on_risk(
            credit,
            spread_width,
        )
    )

    profit_target = (
        calculate_profit_target(
            credit,
            profit_target_percent,
            contracts,
        )
    )

    max_contracts = (
        calculate_max_contracts(
            account_size,
            risk_percent,
            spread_width,
            credit,
        )
    )

    within_risk_limit = (
        maximum_loss
        <= max_allowed_risk
    )

    return {
        "account_size": account_size,
        "risk_percent": risk_percent,
        "max_allowed_risk": max_allowed_risk,
        "spread_width": spread_width,
        "credit": credit,
        "contracts": contracts,
        "loss_per_contract": loss_per_contract,
        "maximum_loss": maximum_loss,
        "maximum_profit": maximum_profit,
        "actual_risk_percent": actual_risk_percent,
        "return_on_risk": return_on_risk,
        "profit_target": profit_target,
        "max_contracts": max_contracts,
        "within_risk_limit": within_risk_limit,
    }
