import math


def norm_cdf(x):

    return (
        0.5 *
        (
            1 +
            math.erf(
                x /
                math.sqrt(2)
            )
        )
    )


def bs_delta(
    spot,
    strike,
    years_to_exp,
    risk_free,
    iv,
    option_side
):

    d1 = (
        math.log(
            spot / strike
        )
        +
        (
            risk_free +
            0.5 * iv**2
        ) *
        years_to_exp
    ) / (
        iv *
        math.sqrt(
            years_to_exp
        )
    )

    n_d1 = norm_cdf(d1)

    if option_side == "call":
        return n_d1

    return n_d1 - 1
