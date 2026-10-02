def evaluate_setup_quality(
    trend_direction,
    delta_pass,
    questionable,
    support_warnings,
):
    score = 0

    reasons = []

    if trend_direction != "No Trend":

        score += 2

        reasons.append(
            "Trend aligned"
        )

    if delta_pass:

        score += 2

        reasons.append(
            "Delta aligned"
        )

    if not questionable:

        score += 2

        reasons.append(
            "No questionable conditions"
        )

    if len(support_warnings) == 0:

        score += 2

        reasons.append(
            "No support/resistance conflicts"
        )

    if score >= 8:

        grade = "A"

    elif score >= 6:

        grade = "B"

    elif score >= 4:

        grade = "C"

    else:

        grade = "PASS"

    return {
        "score": score,
        "grade": grade,
        "reasons": reasons,
    }
