"""Questionable Trade checks for the OTM Flex Calculator.

Drop this file next to your Streamlit app and call evaluate(inputs).
All thresholds live in the CONFIG dict so you can tune them from your trade log.
"""
from dataclasses import dataclass
from datetime import time
import math

CONFIG = {
    "ema200_prox_pct": 1.0,      # flag if price within 1% of the 200 EMA
    "rsi_oversold": 35,          # calls: flag if RSI below this
    "rsi_overbought": 65,        # puts: flag if RSI above this
    "min_atr_distance": 3.0,     # short strike should be >= 3 ATR from price
    "no_entry_before": time(10, 30),  # exchange local time (ET)
    "min_credit_pct_width": 8.0, # credit as % of width
    "min_credit_abs": 0.15,      # absolute credit floor
    "flex_atr_step": 0.5,        # move short out by this many ATR when flagged
}


@dataclass
class TradeInputs:
    side: str            # "call" (bear call spread) or "put" (bull put spread)
    price: float
    short_strike: float
    long_strike: float
    credit: float
    atr: float
    ema200: float
    rsi: float
    macd_hist: float         # latest MACD histogram value
    macd_hist_prev: float    # previous bar's histogram value
    entry_time: time         # exchange local time of planned entry


def evaluate(t: TradeInputs, cfg: dict = CONFIG) -> dict:
    is_call = t.side == "call"
    width = abs(t.long_strike - t.short_strike)
    flags = {}

    # 1. Counter-bounce zone: near the 200 EMA or RSI stretched against you
    prox = abs(t.price - t.ema200) / t.ema200 * 100
    rsi_hit = t.rsi < cfg["rsi_oversold"] if is_call else t.rsi > cfg["rsi_overbought"]
    flags["counter_bounce"] = prox <= cfg["ema200_prox_pct"] or rsi_hit

    # 2. Fresh MACD turn against the trade direction
    if is_call:   # bearish trade: a bullish histogram flip is against you
        flags["macd_against"] = t.macd_hist_prev <= 0 < t.macd_hist
    else:         # bullish trade: a bearish histogram flip is against you
        flags["macd_against"] = t.macd_hist_prev >= 0 > t.macd_hist

    # 3. Short strike too close to price
    dist = (t.short_strike - t.price) if is_call else (t.price - t.short_strike)
    atr_dist = dist / t.atr if t.atr else 0.0
    flags["short_too_close"] = atr_dist < cfg["min_atr_distance"]

    # 4. Early entry (open volatility, wide quotes)
    flags["early_entry"] = t.entry_time < cfg["no_entry_before"]

    # 5. Low credit
    credit_pct = t.credit / width * 100 if width else 0.0
    flags["low_credit"] = (
        credit_pct < cfg["min_credit_pct_width"] or t.credit < cfg["min_credit_abs"]
    )

    others = [k for k, v in flags.items() if v and k != "low_credit"]
    max_loss = (width - t.credit) * 100

    if flags["low_credit"] and others:
        verdict = "SKIP"
        note = "Low credit plus another flag: no flex allowed."
    elif others or flags["low_credit"]:
        verdict = "FLEX"
        step = cfg["flex_atr_step"] * t.atr
        new_short = math.ceil(t.short_strike + step) if is_call else math.floor(t.short_strike - step)
        note = (
            f"Move short to ~{new_short}, or halve size, or narrow the width, "
            f"or wait for confirmation. Never move the short closer to price."
        )
    else:
        verdict = "OK"
        note = "No flags."

    return {
        "verdict": verdict,
        "flags": flags,
        "atr_distance": round(atr_dist, 2),
        "credit_pct_width": round(credit_pct, 1),
        "max_loss_per_contract": round(max_loss, 2),
        "note": note,
    }


# ---------------------------------------------------------------------------
# Streamlit screen (used by the Rule Checker page in the main app)
# ---------------------------------------------------------------------------

FLAG_LABELS = {
    "counter_bounce": "Counter-bounce (near 200 EMA or RSI stretched)",
    "macd_against": "Fresh MACD turn against the trade",
    "short_too_close": "Short strike under 3 ATR from price",
    "early_entry": "Early entry (before 10:30 ET)",
    "low_credit": "Low credit",
}


def render_questionable_check(
    spread_type,
    current_price,
    short_strike,
    distance_atr,
    rsi,
    macd,
    macd_signal,
):
    import streamlit as st

    side = "call" if spread_type == "Bear Call" else "put"

    if distance_atr and distance_atr > 0:
        default_atr = abs(current_price - short_strike) / distance_atr
    else:
        default_atr = 3.0

    st.divider()
    st.subheader("Questionable Trade Check")
    st.caption(
        "Any one flag makes a trade questionable. "
        "Flex it (move the short strike farther out) or skip it."
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        ema200 = st.number_input(
            "Daily 200 EMA", min_value=0.0, value=0.0, step=1.0, key="qt_ema200"
        )
        credit = st.number_input(
            "Credit Received", min_value=0.0, value=0.50, step=0.05, key="qt_credit"
        )

    with c2:
        atr = st.number_input(
            "ATR ($)", min_value=0.01, value=max(round(default_atr, 2), 0.01), step=0.1
        )
        width = st.number_input(
            "Spread Width", min_value=0.5, value=5.0, step=0.5, key="qt_width"
        )

    with c3:
        prev_hist = st.number_input(
            "Previous MACD Histogram (prior day)",
            value=0.0, step=0.05, format="%.2f", key="qt_prev_hist",
        )
        entry_time = st.time_input(
            "Planned Entry Time (ET)", value=time(11, 0), key="qt_time"
        )

    if not st.button(
        "Check for Questionable Flags", key="qt_button", use_container_width=True
    ):
        return

    if ema200 <= 0:
        st.warning("Enter the daily 200 EMA first.")
        return

    long_strike = short_strike + width if side == "call" else short_strike - width

    result = evaluate(
        TradeInputs(
            side=side,
            price=current_price,
            short_strike=short_strike,
            long_strike=long_strike,
            credit=credit,
            atr=atr,
            ema200=ema200,
            rsi=rsi,
            macd_hist=macd - macd_signal,
            macd_hist_prev=prev_hist,
            entry_time=entry_time,
        )
    )

    verdict = result["verdict"]

    if verdict == "OK":
        st.success("OK: no flags.")
    elif verdict == "FLEX":
        st.warning(f"FLEX: {result['note']}")
    else:
        st.error(f"SKIP: {result['note']}")

    for key, tripped in result["flags"].items():
        st.write(f"{'🔴' if tripped else '🟢'} **{FLAG_LABELS[key]}**")

    st.caption(
        f"Short strike is {result['atr_distance']} ATR from price. "
        f"Credit is {result['credit_pct_width']}% of width. "
        f"Max loss per contract: ${result['max_loss_per_contract']:,.2f}."
    )


if __name__ == "__main__":
    # Example: IWM 288/291 call spread, credit 0.19
    demo = TradeInputs(
        side="call", price=277.27, short_strike=288, long_strike=291, credit=0.19,
        atr=3.74, ema200=276.93, rsi=34.53, macd_hist=0.10, macd_hist_prev=-0.20,
        entry_time=time(9, 30),
    )
    print(evaluate(demo))
