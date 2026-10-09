import streamlit as st
import pandas as pd

from Modules.market_data import (
    get_current_price,
    get_price_change,
    get_historical_data,
)

from Modules.indicators import (
    get_latest_indicators,
    determine_trend,
)

from Modules.scanner import scan_market

from Modules.rules import (
    evaluate_trade,
    get_overall_status,
    calculate_profit_target,
)

from Modules.questionable_trade import render_questionable_check

from Modules.position_sizing import (
    analyze_position,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="OTM Flex™",
    page_icon="📈",
    layout="wide",
)


# =========================================================
# TITLE
# =========================================================

st.title("📈 OTM Flex™")

st.caption(
    "Stay out of the money. Stay flexible. Collect premium."
)


# =========================================================
# SIDEBAR
# =========================================================

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


# =========================================================
# DASHBOARD
# =========================================================

if page == "Dashboard":

    st.header("Market Dashboard")

    st.write(
        "Current market overview for the primary OTM Flex™ ETFs."
    )

    tickers = [
        "SPY",
        "QQQ",
        "IWM",
        "VOO",
    ]

    columns = st.columns(4)

    for column, ticker in zip(columns, tickers):

        with column:

            try:

                price_data = get_price_change(ticker)

                if price_data is None:

                    st.metric(
                        ticker,
                        "Unavailable",
                    )

                    continue

                current_price = price_data["current_price"]
                change = price_data["change"]
                percent_change = price_data["percent_change"]

                st.metric(
                    ticker,
                    f"${current_price:,.2f}",
                    f"{change:+.2f} ({percent_change:+.2f}%)",
                )

            except Exception:

                st.metric(
                    ticker,
                    "Unavailable",
                )

    st.divider()

    st.subheader("Technical Overview")

    selected_ticker = st.selectbox(
        "Select ETF",
        tickers,
        key="dashboard_ticker",
    )

    data = get_historical_data(
        selected_ticker,
        period="1y",
        interval="1d",
    )

    if data.empty:

        st.warning(
            "Unable to retrieve historical market data."
        )

    else:

        indicators = get_latest_indicators(data)

        if indicators is not None:

            trend = determine_trend(indicators)

            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.metric(
                    "Price",
                    f"${indicators['price']:,.2f}",
                )

            with c2:
                st.metric(
                    "RSI",
                    f"{indicators['rsi']:.1f}",
                )

            with c3:
                st.metric(
                    "ATR",
                    f"{indicators['atr']:.2f}",
                )

            with c4:
                st.metric(
                    "Trend",
                    trend,
                )

            st.subheader("EMA Structure")

            ema_data = pd.DataFrame(
                {
                    "Indicator": [
                        "EMA 20",
                        "EMA 50",
                        "EMA 200",
                    ],
                    "Value": [
                        indicators["ema20"],
                        indicators["ema50"],
                        indicators["ema200"],
                    ],
                }
            )

            st.dataframe(
                ema_data,
                use_container_width=True,
                hide_index=True,
            )


# =========================================================
# SCANNER
# =========================================================

elif page == "Scanner":

    st.header("OTM Flex™ Scanner")

    st.write(
        "Scan the primary ETFs for potential Bull Put and Bear Call credit spreads."
    )

    st.subheader("Scanner Settings")

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        short_delta = st.number_input(
            "Target Short Delta",
            min_value=0.05,
            max_value=0.30,
            value=0.14,
            step=0.01,
            format="%.2f",
        )

    with c2:

        spread_width = st.number_input(
            "Spread Width",
            min_value=1.0,
            max_value=25.0,
            value=5.0,
            step=1.0,
        )

    with c3:

        min_dte = st.number_input(
            "Minimum DTE",
            min_value=1,
            max_value=90,
            value=7,
            step=1,
        )

    with c4:

        max_dte = st.number_input(
            "Maximum DTE",
            min_value=1,
            max_value=120,
            value=45,
            step=1,
        )

    st.divider()

    tickers = st.multiselect(
        "Underlyings",
        [
            "SPY",
            "QQQ",
            "IWM",
            "VOO",
        ],
        default=[
            "SPY",
            "QQQ",
            "IWM",
            "VOO",
        ],
    )

    scan_button = st.button(
        "🔎 Scan Market",
        type="primary",
        use_container_width=True,
    )

    if scan_button:

        if not tickers:

            st.warning(
                "Select at least one underlying."
            )

        elif min_dte > max_dte:

            st.error(
                "Minimum DTE cannot be greater than Maximum DTE."
            )

        else:

            with st.spinner(
                "Scanning option chains and calculating OTM Flex™ rules..."
            ):

                results = scan_market(
                    tickers=tickers,
                    short_delta=short_delta,
                    spread_width=spread_width,
                    min_dte=min_dte,
                    max_dte=max_dte,
                )

            if results.empty:

                st.warning(
                    "No candidates were found. "
                    "This can happen when option-chain data or estimated Greeks are unavailable."
                )

            else:

                st.success(
                    f"Found {len(results)} candidate spread(s)."
                )

                # -------------------------------------------------
                # SUMMARY
                # -------------------------------------------------

                pass_count = (
                    results["Status"] == "PASS"
                ).sum()

                review_count = (
                    results["Status"] == "REVIEW"
                ).sum()

                fail_count = (
                    results["Status"] == "FAIL"
                ).sum()

                c1, c2, c3 = st.columns(3)

                with c1:
                    st.metric(
                        "PASS",
                        pass_count,
                    )

                with c2:
                    st.metric(
                        "REVIEW",
                        review_count,
                    )

                with c3:
                    st.metric(
                        "FAIL",
                        fail_count,
                    )

                st.divider()

                # -------------------------------------------------
                # FILTER
                # -------------------------------------------------

                status_filter = st.multiselect(
                    "Show Status",
                    [
                        "PASS",
                        "REVIEW",
                        "FAIL",
                    ],
                    default=[
                        "PASS",
                        "REVIEW",
                    ],
                )

                if status_filter:

                    display_results = results[
                        results["Status"].isin(
                            status_filter
                        )
                    ]

                else:

                    display_results = results

                # -------------------------------------------------
                # DISPLAY RESULTS
                # -------------------------------------------------

                display_columns = [
                    "Ticker",
                    "Type",
                    "Expiration",
                    "DTE",
                    "Current Price",
                    "Short Strike",
                    "Long Strike",
                    "Short Delta",
                    "Credit",
                    "Max Profit",
                    "Max Loss",
                    "ATR Distance",
                    "RSI",
                    "Trend",
                    "Status",
                ]

                available_columns = [
                    column
                    for column in display_columns
                    if column in display_results.columns
                ]

                st.dataframe(
                    display_results[
                        available_columns
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

                # -------------------------------------------------
                # CANDIDATE DETAILS
                # -------------------------------------------------

                if not display_results.empty:

                    st.divider()

                    st.subheader(
                        "Candidate Details"
                    )

                    selected_index = st.selectbox(
                        "Select Candidate",
                        display_results.index,
                        format_func=lambda index: (
                            f"{display_results.loc[index, 'Ticker']} "
                            f"{display_results.loc[index, 'Type']} — "
                            f"{display_results.loc[index, 'Expiration']} — "
                            f"{display_results.loc[index, 'Status']}"
                        ),
                    )

                    selected = display_results.loc[
                        selected_index
                    ]

                    c1, c2, c3, c4 = st.columns(4)

                    with c1:

                        st.metric(
                            "Credit",
                            f"${selected['Credit']:.2f}",
                        )

                    with c2:

                        st.metric(
                            "Max Profit",
                            f"${selected['Max Profit']:.2f}",
                        )

                    with c3:

                        st.metric(
                            "Max Loss",
                            f"${selected['Max Loss']:.2f}",
                        )

                    with c4:

                        st.metric(
                            "Short Delta",
                            f"{selected['Short Delta']:.3f}",
                        )

                    st.write(
                        f"**Trend:** {selected['Trend']}"
                    )

                    st.write(
                        f"**ATR Distance:** "
                        f"{selected['ATR Distance']} ATR"
                    )

                    st.write(
                        f"**Support:** "
                        f"{selected['Support']}"
                    )

                    st.write(
                        f"**Resistance:** "
                        f"{selected['Resistance']}"
                    )

                    st.write(
                        f"**Market Condition:** "
                        f"{selected['Market Condition']}"
                    )

                    st.subheader(
                        "OTM Flex™ Rule Results"
                    )

                    rules = selected["Rules"]

                    for rule in rules:

                        status = rule["status"]

                        if status == "PASS":
                            icon = "🟢"

                        elif status == "REVIEW":
                            icon = "🟡"

                        else:
                            icon = "🔴"

                        st.write(
                            f"{icon} **{rule['rule']}** — "
                            f"{status}"
                        )

                        if rule.get("explanation"):
                            st.caption(
                                rule["explanation"]
                            )


# =========================================================
# RULE CHECKER
# =========================================================

elif page == "Rule Checker":

    st.header("OTM Flex™ Rule Checker")

    st.write(
        "Evaluate a proposed credit spread against the OTM Flex™ rules."
    )

    c1, c2 = st.columns(2)

    with c1:

        spread_type = st.selectbox(
            "Spread Type",
            [
                "Bull Put",
                "Bear Call",
            ],
        )

        trend = st.selectbox(
            "Trend",
            [
                "Bullish",
                "Neutral",
                "Bearish",
            ],
        )

        delta = st.number_input(
            "Short-Leg Delta",
            min_value=0.01,
            max_value=0.50,
            value=0.14,
            step=0.01,
            format="%.2f",
        )

        dte = st.number_input(
            "DTE",
            min_value=1,
            max_value=365,
            value=30,
            step=1,
        )

    with c2:

        distance_atr = st.number_input(
            "Distance From Price (ATR)",
            min_value=0.0,
            max_value=10.0,
            value=2.0,
            step=0.1,
        )

        market_condition = st.selectbox(
            "Market Condition",
            [
                "Strong",
                "Normal",
                "Choppy",
            ],
        )

        rsi = st.number_input(
            "RSI",
            min_value=0.0,
            max_value=100.0,
            value=55.0,
            step=1.0,
        )

        macd = st.number_input(
            "MACD",
            value=1.0,
            step=0.1,
        )

        macd_signal = st.number_input(
            "MACD Signal",
            value=0.5,
            step=0.1,
        )

    st.subheader("Price / Liquidity")

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        current_price = st.number_input(
            "Current Price",
            min_value=0.01,
            value=500.0,
            step=1.0,
        )

    with c2:

        short_strike = st.number_input(
            "Short Strike",
            min_value=0.01,
            value=490.0,
            step=1.0,
        )

    with c3:

        bid = st.number_input(
            "Short Option Bid",
            min_value=0.0,
            value=1.00,
            step=0.05,
        )

    with c4:

        ask = st.number_input(
            "Short Option Ask",
            min_value=0.0,
            value=1.10,
            step=0.05,
        )

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        support = st.number_input(
            "Support",
            min_value=0.0,
            value=480.0,
            step=1.0,
        )

    with c2:

        resistance = st.number_input(
            "Resistance",
            min_value=0.0,
            value=520.0,
            step=1.0,
        )

    with c3:

        open_interest = st.number_input(
            "Open Interest",
            min_value=0,
            value=1000,
            step=100,
        )

    with c4:

        volume = st.number_input(
            "Volume",
            min_value=0,
            value=500,
            step=100,
        )

    check_button = st.button(
        "Check Trade",
        type="primary",
        use_container_width=True,
    )

    if check_button:

        results = evaluate_trade(
            spread_type=spread_type,
            trend=trend,
            delta=delta,
            dte=dte,
            distance_atr=distance_atr,
            market_condition=market_condition.lower(),
            rsi=rsi,
            macd=macd,
            macd_signal=macd_signal,
            bid=bid,
            ask=ask,
            open_interest=open_interest,
            volume=volume,
            current_price=current_price,
            short_strike=short_strike,
            support=support,
            resistance=resistance,
        )

        overall_status = get_overall_status(
            results
        )

        st.divider()

        if overall_status == "PASS":

            st.success(
                "Overall Status: PASS"
            )

        elif overall_status == "REVIEW":

            st.warning(
                "Overall Status: REVIEW"
            )

        else:

            st.error(
                "Overall Status: FAIL"
            )

        for rule in results:

            status = rule["status"]

            if status == "PASS":
                icon = "🟢"

            elif status == "REVIEW":
                icon = "🟡"

            else:
                icon = "🔴"

            st.write(
                f"{icon} **{rule['rule']}** — {status}"
            )

            if rule.get("explanation"):
                st.caption(
                    rule["explanation"]
                )

    render_questionable_check(
        spread_type=spread_type,
        current_price=current_price,
        short_strike=short_strike,
        distance_atr=distance_atr,
        rsi=rsi,
        macd=macd,
        macd_signal=macd_signal,
    )


# =========================================================
# POSITION SIZING
# =========================================================

elif page == "Position Sizing":

    st.header("OTM Flex™ Position Sizing")

    st.write(
        "Calculate position size based on maximum theoretical spread loss."
    )

    c1, c2 = st.columns(2)

    with c1:

        account_size = st.number_input(
            "Account Size",
            min_value=100.0,
            value=20000.0,
            step=1000.0,
        )

        risk_percent = st.number_input(
            "Maximum Account Risk %",
            min_value=1.0,
            max_value=100.0,
            value=20.0,
            step=1.0,
        )

        spread_width = st.number_input(
            "Spread Width",
            min_value=0.50,
            max_value=100.0,
            value=5.0,
            step=0.50,
        )

    with c2:

        credit = st.number_input(
            "Credit Received",
            min_value=0.01,
            max_value=100.0,
            value=1.00,
            step=0.05,
        )

        contracts = st.number_input(
            "Contracts",
            min_value=1,
            max_value=1000,
            value=1,
            step=1,
        )

    analyze_button = st.button(
        "Calculate Position",
        type="primary",
        use_container_width=True,
    )

    if analyze_button:

        analysis = analyze_position(
            account_size=account_size,
            risk_percent=risk_percent,
            spread_width=spread_width,
            credit=credit,
            contracts=contracts,
        )

        st.divider()

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            st.metric(
                "Allowed Account Risk",
                f"${analysis['allowed_risk']:,.2f}",
            )

        with c2:

            st.metric(
                "Max Loss",
                f"${analysis['max_loss']:,.2f}",
            )

        with c3:

            st.metric(
                "Max Profit",
                f"${analysis['max_profit']:,.2f}",
            )

        with c4:

            st.metric(
                "Actual Risk",
                f"{analysis['actual_risk_percent']:.2f}%",
            )

        st.divider()

        c1, c2, c3 = st.columns(3)

        with c1:

            st.metric(
                "Max Contracts",
                analysis["max_contracts"],
            )

        with c2:

            st.metric(
                "Return on Risk",
                f"{analysis['return_on_risk']:.2f}%",
            )

        with c3:

            st.metric(
                "50% Profit Target",
                f"${analysis['profit_target']:,.2f}",
            )

        if analysis["within_risk_limit"]:

            st.success(
                "Position is within the selected account-risk limit."
            )

        else:

            st.error(
                "Position exceeds the selected account-risk limit."
            )

        st.subheader("Position Breakdown")

        breakdown = pd.DataFrame(
            {
                "Metric": [
                    "Account Size",
                    "Risk %",
                    "Allowed Risk",
                    "Spread Width",
                    "Credit",
                    "Contracts",
                    "Loss Per Contract",
                    "Maximum Loss",
                    "Maximum Profit",
                    "Actual Risk %",
                    "Return on Risk",
                    "Profit Target",
                    "Maximum Contracts",
                ],
                "Value": [
                    f"${analysis['account_size']:,.2f}",
                    f"{analysis['risk_percent']:.2f}%",
                    f"${analysis['allowed_risk']:,.2f}",
                    f"${analysis['spread_width']:.2f}",
                    f"${analysis['credit']:.2f}",
                    analysis["contracts"],
                    f"${analysis['loss_per_contract']:,.2f}",
                    f"${analysis['max_loss']:,.2f}",
                    f"${analysis['max_profit']:,.2f}",
                    f"{analysis['actual_risk_percent']:.2f}%",
                    f"{analysis['return_on_risk']:.2f}%",
                    f"${analysis['profit_target']:,.2f}",
                    analysis["max_contracts"],
                ],
            }
        )

        st.dataframe(
            breakdown,
            use_container_width=True,
            hide_index=True,
        )


# =========================================================
# TRADE JOURNAL
# =========================================================

elif page == "Trade Journal":

    st.header("Trade Journal")

    st.info(
        "Trade Journal storage will be added in the next development stage."
    )

    st.write(
        "Planned journal fields:"
    )

    journal_fields = [
        "Date",
        "Ticker",
        "Spread Type",
        "Expiration",
        "Short Strike",
        "Long Strike",
        "Credit",
        "Contracts",
        "Maximum Risk",
        "Profit Target",
        "Entry Reason",
        "Exit Reason",
        "P/L",
        "Notes",
    ]

    for field in journal_fields:

        st.write(
            f"• {field}"
        )


# =========================================================
# RULE BOOK
# =========================================================

elif page == "Rule Book":

    st.header("OTM Flex™ Rule Book")

    st.subheader("Mission")

    st.write(
        "Generate consistent option income by selling "
        "high-probability credit spreads while managing "
        "risk through distance from price rather than "
        "excessive trade filters."
    )

    st.divider()

    st.subheader("1. Trend Rule")

    st.write(
        "**Bull Put:** Preferred in a bullish trend."
    )

    st.write(
        "**Bear Call:** Preferred in a bearish trend."
    )

    st.divider()

    st.subheader("2. Delta")

    st.write(
        "Target short-leg delta: **0.10–0.18**"
    )

    st.write(
        "Default scanner target: **0.14**"
    )

    st.divider()

    st.subheader("3. OTM Flex™")

    st.write(
        "If the short strike feels too close, "
        "move it farther OTM and accept less premium."
    )

    st.divider()

    st.subheader("4. ATR Distance")

    st.write(
        "Strong trend: approximately 1–2 ATR"
    )

    st.write(
        "Average conditions: approximately 2 ATR"
    )

    st.write(
        "Choppy conditions: approximately 2–3 ATR"
    )

    st.divider()

    st.subheader("5. Support / Resistance")

    st.write(
        "Bull Put → short put preferably below support."
    )

    st.write(
        "Bear Call → short call preferably above resistance."
    )

    st.divider()

    st.subheader("6. DTE")

    st.write(
        "Typical target: **7–45 DTE**"
    )

    st.divider()

    st.subheader("7. Credit")

    st.write(
        "Distance comes first. Premium comes second."
    )

    st.divider()

    st.subheader("8. Liquidity")

    st.write(
        "Prefer liquid options with tight bid/ask spreads, "
        "good volume, and good open interest."
    )

    st.divider()

    st.subheader("9. Earnings")

    st.write(
        "Avoid opening individual-stock credit spreads "
        "through earnings."
    )

    st.divider()

    st.subheader("10. Profit Taking")

    st.write(
        "Target approximately **50% of maximum profit**."
    )

    st.divider()

    st.subheader("11. Threatened Trade")

    st.write(
        "Reassess trend, short-leg delta, and the original thesis."
    )

    st.write(
        "Consider reducing risk or rolling when appropriate."
    )

    st.divider()

    st.subheader("12. Position Sizing")

    st.write(
        "Size positions so that one loss is uncomfortable "
        "but not catastrophic."
    )

    st.divider()

    st.subheader("Golden Rule")

    st.success(
        "Choose the closest strike that still lets you sleep well at night."
    )

    st.write(
        "Stay out of the money. Stay flexible. Collect premium."
    )
