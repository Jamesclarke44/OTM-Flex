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


if __name__ == "__main__":
    # Example: IWM 288/291 call spread, credit 0.19
    demo = TradeInputs(
        side="call", price=277.27, short_strike=288, long_strike=291, credit=0.19,
        atr=3.74, ema200=276.93, rsi=34.53, macd_hist=0.10, macd_hist_prev=-0.20,
        entry_time=time(9, 30),
    )
    print(evaluate(demo))

# --- Streamlit usage sketch -------------------------------------------------
# import streamlit as st
# from questionable_trade import TradeInputs, evaluate
# result = evaluate(TradeInputs(...values from your sidebar inputs...))
# {"OK": st.success, "FLEX": st.warning, "SKIP": st.error}[result["verdict"]](
#     f'{result["verdict"]}: {result["note"]}')
# st.json(result["flags"])
