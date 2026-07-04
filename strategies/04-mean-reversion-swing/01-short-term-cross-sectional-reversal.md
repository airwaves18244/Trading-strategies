# Short-Term Cross-Sectional Equity Reversal

## 1. Classification

- **Category:** Mean reversion (cross-sectional, short horizon)
- **Asset classes:** Equities
- **Style:** Market-neutral long-short
- **Horizon:** Formation 1–5 days to 1 month; holding days–weeks
- **Capacity:** Low–medium (cost-constrained)
- **Complexity:** Medium; **Data burden:** daily OHLCV survivorship-free; intraday helpful

## 2. Economic rationale

Stocks with the worst returns over the past week/month outperform recent winners over the following days–weeks. This is **liquidity provision, priced**: short-horizon losers are disproportionately names hit by uninformed sell flow (fund redemptions, margin calls, tax selling, retail capitulation); buyers who absorb that flow demand a price concession that subsequently reverses. Nagel [R2] shows reversal-strategy returns behave like market-making revenue — they spike when volatility/VIX is high (liquidity scarce, concessions wide) and shrink when capital is plentiful. Counterparty: whoever demands immediacy. This is the *same economic engine* as stat-arb (doc 01-02) with the factor-hygiene layer removed — the two docs should be read and budgeted as one family.

## 3. Signal & rules specification

- **Universe:** liquid mid/large caps (top 500–1500 ADV); exclude < $5, earnings windows (±1–2 days), M&A targets, and news-driven moves where identifiable (adverse selection filters are the difference between profit and loss here).
- **Signal (baseline):** past 5-day return (range 3–10 days; the classic monthly version — past 1-month return — is weaker and largely subsumed by industry effects).
- **Refinement with strong evidence:** *industry-relative* reversal — rank on `r_stock − r_industry` (isolates idiosyncratic flow; raw reversal shorts winners in trending sectors, which momentum says is wrong). Additional quality filter: require the losing move to have occurred on **high volume without news** (flow signature) — test as variant.
- **Portfolio:** long bottom decile / short top decile of the residual return; equal- or inverse-vol weights; 50–200 names/side.
- **Holding/rebalance:** rebalance every 1–5 days (staggered cohorts to smooth); positions effectively held ~1 week.
- **Sizing:** vol-target book at 6–10%; per-name ≤ 1%; conditional scaling by trailing VIX percentile (Nagel result: expected return is higher post-vol-spikes — scale up then, or at minimum don't de-risk mechanically at the wrong time).

## 4. Evidence & key research

- Jegadeesh (1990), Lehmann (1990) [R1]: monthly/weekly reversal ~1.7–2%/mo gross in early samples — the oldest documented anomalies; universally acknowledged to be substantially a **bid-ask bounce and microstructure artifact at raw prices** (see §7).
- Nagel (2012) [R2]: reversal P&L ∝ liquidity-provision compensation; returns forecastable by VIX; near-zero in calm 2000s mid-decade, huge in 2008-Q4.
- Avellaneda-Lee [A4] and the stat-arb literature: the industrial implementation (with factor hedging) of this same effect.
- Post-2000 evidence: raw weekly reversal in large caps ≈ dead net of costs in normal regimes; **survives in**: mid-caps, high-vol regimes, industry-relative residual form, and intraday-to-close variants.
- **Decay status: heavy in raw form; alive as a conditional, residualized, cost-engineered strategy.**

## 5. Expected performance profile

- Net Sharpe: **0.3–0.7** for the residualized, filtered, conditionally-scaled version at realistic costs; near zero for the naive version.
- Skew: negative (short-vol-like); big up-months cluster in crisis quarters (paid liquidity provision) — 2008-Q4, 2020-Q1/Q2 were historically the best months, *if* you survived to provide liquidity.
- Turnover: extreme (20–50x/yr per side). **Cost sensitivity: the binding constraint** — half-spread assumptions decide the sign of net returns.

## 6. Failure modes & risks

- **Adverse selection:** losers that keep losing because the move was informed (earnings leaks, fraud, downgrades). News/earnings filters and diversification are the defense; expect to lose on the informed subset structurally.
- **Deleveraging cascades:** Aug 2007 [R6] — when other liquidity providers pull back, marks go against the whole book at once; the strategy's worst weeks precede its best months (capital survival is the game).
- Regime starvation: long calm periods offer nothing net of costs; discipline to downsize then (or the conditional scaling does it).
- Short-side frictions: hard-to-borrow recent winners (squeeze candidates on the short side).

## 7. Backtesting guidance

- **Bid-ask bounce is the #1 fake-alpha source:** signals computed on last-trade prices mechanically "buy at bid, sell at ask." Mandatory: compute signals on midquotes or closing auction prices, and apply the one-day-wait / next-open execution test — expect a large chunk of gross alpha to vanish; what remains is real.
- Survivorship-free + delisting returns; point-in-time industry tags for residualization.
- Cost model per name: half effective spread + impact by (size/ADV); rerun at 2x costs. Report net-of-cost by universe-liquidity tercile.
- Validate the Nagel conditioning (returns vs trailing VIX buckets) — mechanism check.
- Include earnings-filter on/off to measure adverse-selection cost explicitly.
- Data: 15y+ daily (with reliable closing auction prices); midquote data if attainable.

## 8. Recommendations for use

- **Backtest priority: medium-high** — as the *validation ground* for your cost model and the entry point to the stat-arb family; deploy only the residualized conditional version.
- Budget jointly with stat-arb (doc 01-02) — same factor, one allocation.
- Realistic role for an independent quant: small, mid-cap-tilted, vol-conditional book that scales up after volatility events; not an always-on large allocation.
