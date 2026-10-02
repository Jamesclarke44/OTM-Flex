import streamlit as st

from modules.trend import evaluate_trend
from modules.questionable import evaluate_questionable_trade
from modules.delta import evaluate_delta
from modules.distance import evaluate_distance
from modules.credit import calculate_credit_metrics
from modules.position_size import calculate_position_size
from modules.support_resistance import (
    evaluate_support_resistance
)

from modules.setup_quality import (
    evaluate_setup_quality
)


st.set_page_config(
    page_title="OTM Flex",
    page_icon="📉",
    layout="centered"
)

st.title("📉 OTM Flex")
st.subheader("Credit Spread Decision Engine")

# --------------------------------------------------
# Inputs
# --------------------------------------------------

price = st.number_input(
    "Current Price",
    value=278.91,
    step=0.01
)

ema20 = st.number_input(
    "EMA20",
    value=284.94,
    step=0.01
)

ema200 = st.number_input(
    "EMA200",
    value=274.53,
    step=0.01
)

rsi = st.number_input(
    "RSI",
    value=32.48,
    step=0.01
)

atr = st.number_input(
    "ATR",
    value=4.50,
    step=0.01
)

delta = st.number_input(
    "Short Strike Delta",
    value=0.11,
    step=0.01
)

strike = st.number_input(
    "Short Strike",
    value=290.00,
    step=1.0
)

credit = st.number_input(
    "Credit Received",
    value=0.39,
    step=0.01
)

width = st.number_input(
    "Spread Width",
    value=5.00,
    step=0.50
)

account_size = st.number_input(
    "Account Size",
    value=5954.00,
    step=100.00
)

risk_pct = st.number_input(
    "Risk Per Trade (%)",
    value=2.0,
    step=0.5
)

# --------------------------------------------------
# Trend
# --------------------------------------------------

st.divider()

trend = evaluate_trend(
    price,
    ema20
)

st.header("Trend")

st.success(
    trend["direction"]
)

# --------------------------------------------------
# Questionable Trade Filter
# --------------------------------------------------

trade_check = evaluate_questionable_trade(
    trend["side"],
    price,
    ema20,
    ema200,
    rsi,
    atr
)

st.header("Questionable Trade Filter")

if trade_check["questionable"]:

    st.warning(
        "⚠️ Questionable Trade"
    )

    for reason in trade_check["reasons"]:
        st.write(
            f"• {reason}"
        )

    if trend["side"] == "call":

        st.markdown("""
### Bear Call Confirmation

Require at least 2:

- Price reaches resistance
- RSI turns down
- MACD rolls over
- Rejection candle forms
""")

    elif trend["side"] == "put":

        st.markdown("""
### Bull Put Confirmation

Require at least 2:

- Price reaches support
- RSI turns higher
- MACD turns higher
- Bullish candle forms
""")

else:

    st.success(
        "✅ No questionable trade conditions detected"
    )

# --------------------------------------------------
# Delta
# --------------------------------------------------

st.header("Delta Check")

delta_result = evaluate_delta(
    delta
)

st.write(
    f"Delta Rating: {delta_result['rating']}"
)

# --------------------------------------------------
# Distance
# --------------------------------------------------

st.header("Distance")

distance_result = evaluate_distance(
    price,
    strike,
    atr
)

st.write(
    f"Distance from Price: {distance_result['distance']}"
)

st.write(
    f"ATR Multiple: {distance_result['atr_multiple']}"
)

# --------------------------------------------------
# Credit
# --------------------------------------------------

st.header("Credit Metrics")

credit_metrics = calculate_credit_metrics(
    credit,
    width
)

st.write(
    f"Max Loss: ${credit_metrics['max_loss']}"
)

st.write(
    f"Profit Target (50%): ${credit_metrics['profit_target']}"
)

st.write(
    f"Stop Loss (2x Credit): ${credit_metrics['stop_loss']}"
)

st.write(
    f"ROC: {credit_metrics['roc']}%"
)

# --------------------------------------------------
# Position Size
# --------------------------------------------------

st.header("Position Size")

position = calculate_position_size(
    account_size,
    risk_pct,
    credit_metrics["max_loss"]
)

st.write(
    f"Risk Budget: ${position['risk_dollars']}"
)

st.write(
    f"Max Contracts: {position['contracts']}"
)
