# Statistical Arbitrage via Mean-Reverting Residual Portfolios

## 1. Classification

- **Category:** Arbitrage / relative value (statistical, portfolio-level)
- **Asset classes:** Equities (primary); extensible to futures and liquid crypto
- **Style:** Market/factor-neutral, cross-sectional
- **Horizon:** 1–20 trading days per position
- **Capacity:** Medium
- **Complexity:** High; **Data burden:** daily OHLCV (intraday helpful), factor model or sector ETF data

## 2. Economic rationale

Generalization of pairs trading: instead of one partner stock, each stock is hedged against a **systematic factor replication** (PCA factors, or its sector ETF). The residual — the stock's return unexplained by common factors — mean-reverts because most idiosyncratic price moves are **liquidity events, not information**: fund flows, rebalancing, retail bursts. Providing liquidity against these flows earns a spread. The counterparty is anyone demanding immediacy in a single name. Compensation is for (a) inventory/divergence risk, (b) adverse selection — sometimes the move *is* information (earnings leak, analyst move), and the stat-arb trader loses to informed flow.

This is the institutional core of "quant equity market-neutral" (Avellaneda-Lee) and the same economic engine as short-term reversal [R1, R2], implemented with factor hygiene.

## 3. Signal & rules specification

- **Universe:** top 500–1500 US stocks by ADV; exclude earnings-announcement days (±1 day) — this removes most adverse-selection losses.
- **Factor model:** either (a) PCA on 1y of daily returns, keep k = 10–15 components (or components explaining ~55% of variance), or (b) regress each stock on its sector ETF (simpler, more stable). Re-estimate monthly (PCA) / quarterly (ETF betas).
- **Residual process:** cumulative residual `X_t = Σ ε` per stock; fit O-U:
  `dX = κ(m − X)dt + σ dW` via AR(1) on 60 days (range 40–90).
  Keep names with mean-reversion speed κ giving **half-life ≤ ~15 days** (τ = ln2/κ).
- **Signal (s-score):** `s = (X_t − m) / σ_eq` where σ_eq = σ/√(2κ) is the equilibrium std of the O-U process.
- **Rules (Avellaneda-Lee baseline, tune within ranges):** open short residual at s > +1.25, open long at s < −1.25, close long at s > −0.5, close short at s < +0.75 (asymmetry reflects short costs). Ranges: entry 1.0–1.5, exit 0.25–0.75.
- **Portfolio construction:** dollar-neutral and beta/factor-neutral by construction (each position hedged with its factor replication or netted across the book). Position cap 1–2% NAV per name; 50–200 concurrent names. Gross leverage 2–4x typical institutional; ≤ 2x recommended for independent operation.
- **Rebalance:** daily at close (or next open with the one-day-wait rule).

## 4. Evidence & key research

- Avellaneda & Lee (2010) [A4]: Sharpe ~1.4 (1997–2007) for ETF-residual version before the 2007 quant quake; PCA version similar. Post-2002 returns visibly lower than the 1990s.
- Khandani & Lo (2007) [R6]: the same construction, run at high leverage industry-wide, lost 20–30% in three days in August 2007 and mostly recovered by week's end — canonical crowding evidence.
- Nagel (2012) [R2]: reversal/liquidity-provision returns track VIX — expected returns to this strategy are state-dependent and highest right after volatility spikes.
- **Decay status: substantial but not terminal.** US large-cap gross Sharpe from simple versions is a fraction of the 1990s level; edge survives via better universes (mid-cap), faster signals (intraday), earnings hygiene, and cost control.

## 5. Expected performance profile

- Realistic net Sharpe: **0.5–1.0** at modest leverage with disciplined costs (higher for sophisticated implementations; the published 1.4+ numbers predate crowding).
- Return profile: steady small gains; sharp drawdowns during systematic deleveraging events (Aug 2007, Mar 2020, Jan 2021 short squeeze). Negative skew at the book level.
- Turnover: very high (5–20x annual per side). **Cost sensitivity: extreme** — 5bp vs 15bp per trade is the difference between viable and not.

## 6. Failure modes & risks

- **Crowding cascade:** losses come precisely when other liquidity providers de-lever; correlations across "market-neutral" books → simultaneous spread widening. Leverage discipline and a drawdown-triggered gross reduction rule are structural requirements.
- **Adverse selection:** residual moves driven by real information (pre-announcement drift, activist stakes). Earnings exclusion and news filters mitigate.
- **Factor model misspecification:** a "residual" that still contains a factor (e.g., crypto-exposure in 2021, AI-exposure in 2024) turns the book directional without you knowing. Monitor residual cross-correlation.
- Short-side frictions: borrow fees/recalls; squeeze regimes (2021 meme episode was a factor-model failure + short crowding event).

## 7. Backtesting guidance

- Same non-negotiables as pairs trading: survivorship-free universe with delisting returns, total-return prices, one-day-wait execution test, point-in-time sector data.
- **Cost model is the backtest.** Use per-name cost = half-spread + impact scaled by (trade size / ADV); rerun at 2x assumed costs — if Sharpe doesn't survive, the strategy doesn't exist for you.
- Exclude earnings windows in one variant and include them in another; the spread between the two isolates adverse-selection cost and validates the mechanism.
- Test the Nagel conditioning: expected returns should be higher when trailing VIX is elevated. A backtest not showing this pattern likely has a bug or look-ahead.
- Stress-replay August 2007 and March 2020 with your actual leverage rule.
- Minimum data: 10y+ daily survivorship-free; sector ETFs history.

## 8. Recommendations for use

- **Backtest priority: high** — this is the flagship of the market-neutral sleeve, and its residual/O-U machinery generalizes (pairs, ETF arb, crypto RV).
- Run at conservative leverage with a hard de-grossing rule; treat the strategy as short liquidity-vol and pair it with long-vol allocations (trend, long tails) at the portfolio level.
- For an independent quant: the ETF-residual variant on the top-1000 universe with earnings exclusion is the recommended first implementation — fewer moving parts than PCA, nearly the same economics.
