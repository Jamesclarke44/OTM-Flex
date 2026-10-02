def evaluate_distance(
    price,
    strike,
    atr
):

    distance = abs(price - strike)

    atr_multiple = distance / atr

    return {
        "distance": round(distance, 2),
        "atr_multiple": round(atr_multiple, 2)
    }
