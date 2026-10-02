def calculate_trade_score(
    trend_strength,
    delta_pass,
    distance_pass,
    questionable
):

    score = 0

    if trend_strength:
        score += 2

    if delta_pass:
        score += 2

    if distance_pass:
        score += 2

    if questionable:
        score -= 1

    if score >= 5:
        grade = "A"

    elif score >= 3:
        grade = "B"

    elif score >= 1:
        grade = "C"

    else:
        grade = "Pass"

    return {
        "score": score,
        "grade": grade
    }
