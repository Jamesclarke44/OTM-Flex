import pandas as pd


def calculate_ema(close, period):

    return (
        close
        .ewm(
            span=period,
            adjust=False
        )
        .mean()
    )


def calculate_rsi(
    close,
    period=14
):

    delta = close.diff()

    gain = delta.clip(
        lower=0
    )

    loss = -delta.clip(
        upper=0
    )

    avg_gain = gain.ewm(
        alpha=1 / period,
        adjust=False
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / period,
        adjust=False
    ).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (
        100 /
        (1 + rs)
    )

    return rsi


def calculate_macd(
    close,
    fast=12,
    slow=26,
    signal=9
):

    ema_fast = close.ewm(
        span=fast,
        adjust=False
    ).mean()

    ema_slow = close.ewm(
        span=slow,
        adjust=False
    ).mean()

    macd_line = (
        ema_fast -
        ema_slow
    )

    signal_line = macd_line.ewm(
        span=signal,
        adjust=False
    ).mean()

    histogram = (
        macd_line -
        signal_line
    )

    return {
        "macd_line": macd_line,
        "signal_line": signal_line,
        "histogram": histogram
    }


def calculate_atr(
    high,
    low,
    close,
    period=14
):

    prev_close = close.shift(1)

    true_range = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs()
        ],
        axis=1
    ).max(axis=1)

    atr = true_range.ewm(
        alpha=1 / period,
        adjust=False
    ).mean()

    return atr


def calculate_indicators(
    history
):

    close = history["Close"]

    high = history["High"]

    low = history["Low"]

    ema20 = calculate_ema(
        close,
        20
    ).iloc[-1]

    ema50 = calculate_ema(
        close,
        50
    ).iloc[-1]

    ema200 = calculate_ema(
        close,
        200
    ).iloc[-1]

    rsi = calculate_rsi(
        close
    ).iloc[-1]

    macd = calculate_macd(
        close
    )

    atr = calculate_atr(
        high,
        low,
        close
    ).iloc[-1]

    return {
        "price": round(
            float(close.iloc[-1]),
            2
        ),

        "ema20": round(
            float(ema20),
            2
        ),

        "ema50": round(
            float(ema50),
            2
        ),

        "ema200": round(
            float(ema200),
            2
        ),

        "rsi": round(
            float(rsi),
            1
        ),

        "macd_line": round(
            float(
                macd["macd_line"].iloc[-1]
            ),
            2
        ),

        "macd_signal": round(
            float(
                macd["signal_line"].iloc[-1]
            ),
            2
        ),

        "macd_histogram": round(
            float(
                macd["histogram"].iloc[-1]
            ),
            2
        ),

        "atr": round(
            float(atr),
            2
        )
    }
