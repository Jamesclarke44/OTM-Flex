def evaluate_support_resistance(
    price,
    ema20,
    ema50,
    ema200,
    atr
):

    warnings = []

    near_ema20 = abs(
        price - ema20
    ) <= atr

    near_ema50 = abs(
        price - ema50
    ) <= atr

    near_ema200 = abs(
        price - ema200
    ) <= atr

    if near_ema20:
        warnings.append(
            "Price near EMA20"
        )

    if near_ema50:
        warnings.append(
            "Price near EMA50"
        )

    if near_ema200:
        warnings.append(
            "Price near EMA200"
        )

    return {
        "near_ema20": near_ema20,
        "near_ema50": near_ema50,
        "near_ema200": near_ema200,
        "warnings": warnings,
    }
