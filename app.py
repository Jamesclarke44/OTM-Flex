from modules.trend import evaluate_trend
from modules.questionable import evaluate_questionable_trade
from modules.delta import evaluate_delta
from modules.distance import evaluate_distance
from modules.credit import calculate_credit_metrics
from modules.position_size import calculate_position_size
trend = evaluate_trend(
    price,
    ema20
)

trade_check = evaluate_questionable_trade(
    trend["side"],
    price,
    ema20,
    ema200,
    rsi,
    atr
)
if trade_check["questionable"]:

    st.warning(
        "⚠️ Questionable Trade"
    )

    for reason in trade_check["reasons"]:
        st.write(
            f"• {reason}"
        )

else:

    st.success(
        "✅ Normal Trade"
    )
