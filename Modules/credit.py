def calculate_credit_metrics(
    credit,
    width
):

    max_loss = width - credit

    profit_target = credit * 0.50

    stop_loss = credit * 2

    roc = (credit / max_loss) * 100

    return {
        "max_loss": round(max_loss, 2),
        "profit_target": round(profit_target, 2),
        "stop_loss": round(stop_loss, 2),
        "roc": round(roc, 2)
    }
