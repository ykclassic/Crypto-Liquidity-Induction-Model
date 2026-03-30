# 🤖 Omni-Manipulation Bot (Institutional Liquidity Model)

A high-probability cryptocurrency signaling bot designed to identify **Institutional Liquidity Raids** and **Market Structure Shifts**. 

Instead of chasing breakouts or using lagging indicators, this bot identifies the 4-phase sequence where retail traders are "baited" into the market before a major reversal occurs.

## 2. Core Ideology: The 4-Phase Sequence
The bot only triggers when a specific market process is completed:
1. **The Build:** Price engineers "Clean" levels (Equal Highs or Lows) to attract retail stop-losses.
2. **Induction:** Price trends slowly to encourage retail participation in the wrong direction.
3. **The Raid:** A fast, aggressive move that "sweeps" the engineered liquidity (triggers stops).
4. **Displacement:** A high-volume reversal that confirms the "Smart Money" has entered.

## 🛠 Features
* **Multi-Asset:** BTC, ETH, SOL, BNB, XRP, ADA, DOGE, LINK, SUI, POL.
* **Multi-Timeframe:** 1H, 4H, and 1D analysis for macro-confluence.
* **Smart Filters:** Volume Confirmation and Session Killzones (London/NY Opens).
* **Automated Trade Plans:** Generates Entry, Stop Loss, and Take Profit levels based on market structure.
* **Multi-Exchange Failover:** Scans Bybit, Bitget, Gate.io, and Kraken to bypass regional API restrictions.

## 🚀 Setup
1. **Fork this repository.**
2. **Add Discord Webhook:** Go to `Settings > Secrets and Variables > Actions` and add `DISCORD_WEBHOOK`.
3. **Enable Actions:** The bot will automatically run every hour via GitHub Actions.
