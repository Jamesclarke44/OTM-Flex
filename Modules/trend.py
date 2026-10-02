def evaluate_trend(price, ema20):

    if price > ema20:
        return {
            "direction": "Bull Put Spread",
            "side": "put"
        }

    elif price < ema20:
        return {
            "direction": "Bear Call Spread",
            "side": "call"
        }

    return {
        "direction": "No Trend",
        "side": None
    }
