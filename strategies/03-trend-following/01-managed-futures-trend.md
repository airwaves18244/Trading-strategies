# Classic Managed-Futures Trend Following (Multi-Signal, Vol-Targeted)

## 1. Classification

- **Category:** Trend following (the institutional CTA core)
- **Asset classes:** 40–80 futures/forwards: equity indices, bonds/rates, FX, commodities
- **Style:** Directional per-market, diversified, systematic
- **Horizon:** Signals spanning ~1–12 months; daily monitoring, effective holding weeks–months
- **Capacity:** Very high (hundreds of $bn industry)
- **Complexity:** Medium; **Data burden:** roll-adjusted futures for many markets, decades of history

## 2. Economic rationale

The production-grade superset of TSMOM (doc `02-momentum/02` — read together). Why trends exist and persist:

1. **Slow reaction chain:** news → early-informed investors → institutional committees → retail; large allocators take quarters to move. Prices adjust to big shifts (rate cycles, inflation regimes, recessions) over months, not days.
2. **Risk transfer / hedging pressure [T5]:** hedgers systematically sell into rising markets and buy into falling ones (locking in prices), paying trend followers to take the other side — a genuine insurance premium.
3. **Reflexive flows:** vol-targeting funds, margin calls, and stop-losses create sustained one-directional flow in drawn-out moves.

The strategy's signature property is **crisis convexity**: extended bear markets and macro dislocations are exactly the environments generating strong trends (short equities, long bonds in deflationary crises; short bonds, long commodities in 2022's inflation). Counterparty: hedgers and rebalancers, plus investors who anchor and average down against regime changes.

## 3. Signal & rules specification

Institutional-replication baseline (AQR "Demystifying" [T3] / Levine-Pedersen [T4]):

- **Universe:** ≥ 40 markets balanced across the 4 asset classes (risk-balanced, e.g., ~25% each).
- **Signal per market:** ensemble across speeds. Standard: EWMA crossover pairs (fast, slow) ∈ {(8,24), (16,48), (32,96)} days (equivalently 1m/3m/12m return signs [T4] — MA crossovers and TS momentum are the same estimator family). Signal per speed: `x = (EWMA_f − EWMA_s) / σ_price`; squash to [−1, 1] (e.g., x/|x|·min(|x|,2)/2 or tanh); average across speeds → composite signal s_i.
- **Sizing:** `w_i ∝ s_i · σ_target_i / σ_i` (ex-ante EWMA vol, 20–60d); risk-balance across asset classes; **portfolio vol target 10–15%** with gross-exposure caps.
- **Rebalance:** daily signal update, trade on meaningful changes (threshold/buffer rebalancing cuts turnover ~30–50% at negligible signal cost).
- **Optional documented enhancements:** long-gamma overlay at position level (trim after parabolic extension); correlation-adjusted risk allocation (don't count 6 correlated rate markets as 6 bets); carry tilt (see doc 03).

## 4. Evidence & key research

- Hurst, Ooi & Pedersen (2017) [T1]: 1880–2016, gross Sharpe ~0.8–1.0 in *every decade*; performs best in the 10 worst equity drawdowns ("crisis alpha").
- AQR [T3] + Baltas-Kosowski [T2]: simple 1/3/12-month trend replicates CTA indices (alpha of CTAs over the replication ≈ 0); no capacity ceiling found in-sample.
- Live: SG Trend Index [T6] — 2008 +20%+, 2022 +20.1% (both crisis years), but 2011–2019 flat stretch and 2023–2025 weakness; net live Sharpe over 2000–2025 ≈ 0.4–0.5 with near-zero equity correlation and positive skew at monthly+ horizons.
- Hutchinson & O'Brien [T7]: returns halve for ~4y after financial crises (rates pinned → fewer macro trends).
- **Decay status: modest;** the premium is cyclical with macro-trend supply. The 2022 result out-of-sample confirmed the core property post-publication.

## 5. Expected performance profile

- Net Sharpe: **0.4–0.7** through-cycle; near-zero long-run correlation to equities, **negative correlation conditional on equity drawdowns** — the portfolio property that justifies it even at Sharpe 0.4.
- Skew: positive at monthly/quarterly horizon; daily P&L is unremarkable; multi-year flat stretches are the norm, punctuated by outsized crisis years.
- Turnover: moderate; costs 1–3bp/trade in liquid markets — at 40+ markets, execution infrastructure matters but is not HFT.

## 6. Failure modes & risks

- **Trendless chop** (2012–2017 QE-suppressed macro): death by whipsaw for years — investor patience is the scarce resource.
- **Sharp reversals at position extremes:** trend is maximally long right before V-tops (and short before V-bottoms, March→April 2020). Vol targeting + signal squashing + optional trimming address, never eliminate.
- Correlated-market illusion: rates trades across 10 markets = 1 trade; 2022-style success means 2023-style give-back when the same macro trend reverses.
- Crowding at signal flips of the big CTAs (billions move on similar triggers) — slippage clusters; being small is an advantage here.

## 7. Backtesting guidance

- Everything in TSMOM doc §7 applies (roll-adjusted excess returns, ex-ante vol, cost per market, published-result validation).
- Ensemble honesty: fix the speed set *a priori* (1/3/12m is the literature standard); do not grid-search speeds per market — per-market optimization is the leading cause of fake CTA backtests.
- Test buffer/threshold rebalancing explicitly (report turnover vs Sharpe frontier).
- Report: performance in the 10 worst equity quarters (crisis-alpha table), skewness at daily/monthly/quarterly aggregation, per-asset-class attribution, correlation-adjusted risk usage.
- Include 2011–2019 in full — a backtest that looks smooth through that window is wrong.
- Data: 25y+ × 40+ markets minimum; longer if extending with cash-market proxies.

## 8. Recommendations for use

- **Backtest priority: highest (tied with TSMOM — build as one project).** This is the recommended permanent core sleeve of a diversified book: 15–30% of portfolio risk, held through the flat years, precisely for its crisis convexity.
- Implementation choice for smaller capital: reduced universe (~20 most liquid markets) retains most of the Sharpe; ETF-based versions lose the shorting/leverage efficiency and much of the value.
- Combine at the signal level with carry (doc 03) rather than running separate books — cross-signal netting cuts costs.
