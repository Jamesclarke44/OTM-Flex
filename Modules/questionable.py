# modules/questionable.py

def evaluate_questionable_trade(
    side,
    price,
    ema20,
    ema200,
    rsi,
    atr,
):
    questionable = False
    reasons = []

    if side == "call":

        if rsi < 35:
            questionable = True
            reasons.append(
                "RSI below 35 (oversold bounce risk)"
            )

        if abs(price - ema200) <= atr:
            questionable = True
            reasons.append(
                "Price near EMA200 support"
            )

    elif side == "put":

        if rsi > 65:
            questionable = True
            reasons.append(
                "RSI above 65 (extended rally)"
            )

        if price > (ema20 + (2 * atr)):
            questionable = True
            reasons.append(
                "Price more than 2 ATR above EMA20"
            )

    return {
        "questionable": questionable,
        "reasons": reasons,
    }
