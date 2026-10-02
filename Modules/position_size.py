def calculate_position_size(
    account_size,
    risk_pct,
    max_loss
):

    risk_dollars = account_size * (
        risk_pct / 100
    )

    contracts = int(
        risk_dollars //
        max_loss
    )

    return {
        "risk_dollars": round(
            risk_dollars,
            2
        ),
        "contracts": contracts
    }
