import streamlit as st


# ============================================================
# OTM FLEX™ CREDIT SPREAD TRADING APP
# ============================================================

st.set_page_config(
    page_title="OTM Flex™",
    page_icon="📈",
    layout="wide",
)


# ============================================================
# HEADER
# ============================================================

st.title("📈 OTM Flex™")
st.subheader("Credit Spread Trading System")

st.markdown(
    """
    **Mission:** Generate consistent option income by selling
    high-probability credit spreads while managing risk primarily
    through distance from price.
    """
)

st.divider()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("OTM Flex™")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Scanner",
        "Rule Checker",
        "Position Sizing",
        "Trade Journal",
        "Rule Book",
    ],
)


# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":

    st.header("Market Dashboard")

    st.info(
        "Live market data and technical indicators will be connected "
        "in the next modules."
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("SPY", "—")

    with col2:
        st.metric("QQQ", "—")

    with col3:
        st.metric("IWM", "—")

    with col4:
        st.metric("VOO", "—")

    st.divider()

    st.subheader("OTM Flex™ Status")

    st.write(
        "The scanner will evaluate trend, delta, distance, ATR, "
        "volatility, liquidity and DTE."
    )


# ============================================================
# SCANNER
# ============================================================

elif page == "Scanner":

    st.header("🔎 Credit Spread Scanner")

    st.write(
        "Find potential Bull Put and Bear Call spreads "
        "using the OTM Flex™ rules."
    )

    ticker = st.selectbox(
        "Underlying",
        ["SPY", "QQQ", "IWM", "VOO"],
    )

    st.info(
        f"Scanner for **{ticker}** will be connected next."
    )


# ============================================================
# RULE CHECKER
# ============================================================

elif page == "Rule Checker":

    st.header("✅ OTM Flex™ Rule Checker")

    st.write(
        "Every potential trade will be checked against "
        "your trading rules."
    )

    rules = [
        "Trend",
        "EMA structure",
        "RSI",
        "MACD",
        "Short-leg delta",
        "OTM distance",
        "ATR distance",
        "Volatility",
        "Liquidity",
        "DTE",
        "Earnings",
    ]

    for rule in rules:
        st.write(f"⬜ {rule}")


# ============================================================
# POSITION SIZING
# ============================================================

elif page == "Position Sizing":

    st.header("💰 Position Sizing")

    account_size = st.number_input(
        "Account Size ($)",
        min_value=0.0,
        value=20000.0,
        step=1000.0,
    )

    risk_percent = st.number_input(
        "Maximum Risk Per Trade (%)",
        min_value=0.1,
        max_value=100.0,
        value=20.0,
        step=1.0,
    )

    spread_width = st.number_input(
        "Spread Width ($)",
        min_value=1.0,
        value=5.0,
        step=1.0,
    )

    credit = st.number_input(
        "Credit Received Per Spread ($)",
        min_value=0.01,
        value=1.00,
        step=0.05,
    )

    max_risk = account_size * (risk_percent / 100)

    max_loss_per_contract = (spread_width - credit) * 100

    if max_loss_per_contract > 0:

        contracts = int(max_risk // max_loss_per_contract)

        total_risk = contracts * max_loss_per_contract

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Maximum Allowed Risk",
                f"${max_risk:,.2f}",
            )

        with col2:
            st.metric(
                "Max Loss / Contract",
                f"${max_loss_per_contract:,.2f}",
            )

        with col3:
            st.metric(
                "Contracts",
                contracts,
            )

        st.write(
            f"Maximum theoretical risk: "
            f"**${total_risk:,.2f}**"
        )

    else:

        st.error(
            "Credit must be less than the spread width."
        )


# ============================================================
# TRADE JOURNAL
# ============================================================

elif page == "Trade Journal":

    st.header("📓 Trade Journal")

    st.info(
        "Trade journaling will be added in a later module."
    )

    st.write(
        "The journal will eventually track entries, exits, "
        "credits, losses, winners, DTE, delta and rule compliance."
    )


# ============================================================
# RULE BOOK
# ============================================================

elif page == "Rule Book":

    st.header("📖 OTM Flex™ Rule Book")

    st.subheader("Mission")

    st.write(
        "Generate consistent option income by selling "
        "high-probability credit spreads while managing "
        "risk through distance from price."
    )

    st.subheader("Core Rules")

    st.markdown(
        """
        **1. Trend**
        
        Trade in the direction of the prevailing trend.

        **2. Short Delta**

        Target approximately **0.10–0.18 delta**.

        **3. OTM Flex™**

        If the trade becomes uncomfortable, move the
        short strike farther OTM.

        **4. ATR Distance**

        Give the trade sufficient room for normal market movement.

        **5. Volatility**

        Higher volatility → greater distance from price.

        **6. Support / Resistance**

        Use important levels as additional context.

        **7. DTE**

        Typical target: **7–45 DTE**.

        **8. Liquidity**

        Prefer liquid ETFs and tight option spreads.

        **9. Earnings**

        Avoid individual-stock earnings exposure.

        **10. Profit Taking**

        Target approximately **50% of maximum profit**.

        **11. Threatened Trades**

        Reassess the original thesis before allowing
        the position to approach maximum loss.

        **12. Position Sizing**

        Size trades according to the account's defined
        maximum risk.
        """
    )

    st.success(
        "OTM Flex™ principle: Stay out of the money. "
        "Stay flexible. Collect premium."
    )
