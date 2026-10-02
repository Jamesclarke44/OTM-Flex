# OTM Flex™

OTM Flex™ is a Streamlit-based credit spread scanner designed around a simple principle:

> Stay out of the money. Stay flexible. Collect premium.

The application is designed to scan liquid ETFs for potential Bull Put and Bear Call credit spreads while considering:

- Trend
- EMA structure
- RSI
- MACD
- ATR distance
- Short-leg delta
- Support and resistance
- Days to expiration
- Bid/ask liquidity
- Spread width
- Credit received
- Maximum profit
- Maximum loss
- OTM Flex™ rule status

---

# Supported Underlyings

The initial supported ETFs are:

- SPY
- QQQ
- IWM
- VOO

---

# OTM Flex™ Rule Book

## Mission

Generate consistent option income by selling high-probability credit spreads while managing risk through distance from price rather than excessive trade filters.

---

## 1. Trend Rule

### Bull Put

Preferred when the underlying has a bullish trend.

### Bear Call

Preferred when the underlying has a bearish trend.

The scanner considers:

- Price vs EMA20
- EMA20 vs EMA50
- EMA50 vs EMA200

A fully aligned bullish structure is classified as:

`Bullish`

A fully aligned bearish structure is classified as:

`Bearish`

Anything between those conditions is:

`Neutral`

---

# 2. Delta Rule

Target short-leg delta:

`0.10 – 0.18`

Default scanner target:

`0.14`

Lower delta generally means the short strike is farther out of the money.

The OTM Flex™ philosophy is:

> If the trade feels too close, move the short strike farther OTM and accept less premium.

---

# 3. OTM Flex™ Rule

Distance from price comes before premium.

Do not move the short strike closer to price simply to collect additional credit.

If necessary:

1. Move the short strike farther OTM.
2. Reduce delta.
3. Increase distance from the current price.
4. Accept a smaller credit.

---

# 4. ATR Distance

ATR is used to measure the distance between the current price and the short strike.

### General framework

Strong trend:

`1–2 ATR`

Average conditions:

`~2 ATR`

Choppy or uncertain conditions:

`2–3 ATR`

Higher volatility should generally result in greater distance from the current price.

---

# 5. Support and Resistance

Support and resistance provide additional context.

### Bull Put

The short put should preferably be below support.

### Bear Call

The short call should preferably be above resistance.

Support and resistance are not treated as absolute guarantees.

The scanner currently uses the recent 20-day high and low as a simple technical reference.

---

# 6. DTE

Preferred expiration range:

`7–45 DTE`

The scanner searches available expirations inside this range.

---

# 7. Credit

Credit is important, but it comes after distance.

Do not chase premium by moving the short strike dangerously close to the current price.

The objective is:

> Distance first. Premium second.

---

# 8. Liquidity

Prefer liquid options with:

- Tight bid/ask spreads
- Good trading volume
- Good open interest

The scanner checks the short option's bid/ask spread.

---

# 9. Earnings

For individual stocks:

Avoid opening credit spreads through earnings.

The initial OTM Flex™ scanner focuses on ETFs:

- SPY
- QQQ
- IWM
- VOO

---

# 10. Profit Taking

Target approximately:

`50% of maximum profit`

For example:

A spread sold for:

`$1.00`

has a maximum profit of:

`$100`

per contract.

A 50% profit target would be approximately:

`$50`

per contract.

---

# 11. Threatened Trade

If the short strike becomes threatened:

1. Reassess the trend.
2. Reassess short-leg delta.
3. Reassess the original thesis.
4. Consider reducing risk.
5. Consider rolling when appropriate.
6. Do not blindly hold until maximum loss.

---

# 12. Position Sizing

Position size should be based on account size and the maximum loss of the spread.

The app allows the trader to choose a maximum account-risk percentage.

Example:

Account:

`$20,000`

Maximum risk:

`20%`

Maximum account risk:

`$4,000`

For a $5-wide spread receiving $1.00 credit:

Maximum loss per contract:

`($5.00 - $1.00) × 100`

`= $400`

Five contracts would have:

`$2,000`

maximum theoretical loss.

That represents:

`10%`

of the $20,000 account.

The position-sizing module calculates these values automatically.

---

# Scanner

The scanner combines:

1. Current market price
2. Historical market data
3. EMA20
4. EMA50
5. EMA200
6. RSI
7. MACD
8. ATR
9. Trend
10. Support
11. Resistance
12. Option expirations
13. Option chains
14. Estimated option delta
15. Credit
16. Maximum profit
17. Maximum loss
18. ATR distance
19. Liquidity
20. OTM Flex™ rule status

---

# Important: Option Greeks

Yahoo Finance option-chain data does not always provide reliable Greek values.

OTM Flex™ therefore calculates an estimated delta using the Black-Scholes model when necessary.

These are:

`ESTIMATED GREEKS`

They may differ from the Greeks displayed by a broker.

The scanner should therefore be used as a decision-support tool rather than as a guarantee of trade outcome.

---

# Installation

## 1. Install Python

Install Python 3.10 or newer.

---

## 2. Install the requirements

From the project folder:

```bash
pip install -r requirements.txt
