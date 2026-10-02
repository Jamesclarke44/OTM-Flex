def evaluate_delta(delta):

    if 0.10 <= delta <= 0.18:
        return {
            "pass": True,
            "rating": "Ideal"
        }

    elif 0.08 <= delta < 0.10:
        return {
            "pass": True,
            "rating": "Conservative"
        }

    elif 0.18 < delta <= 0.25:
        return {
            "pass": True,
            "rating": "Aggressive"
        }

    return {
        "pass": False,
        "rating": "Outside Rules"
    }
