# Pairs Trading (Distance & Cointegration Methods)

## 1. Classification

- **Category:** Arbitrage / relative value (statistical)
- **Asset classes:** Equities (primary), ETFs, futures, crypto
- **Style:** Market-neutral, cross-sectional relative value
- **Horizon:** Days to ~2 months per trade
- **Capacity:** Low–medium (edge concentrated in less liquid names)
- **Complexity:** Medium; **Data burden:** daily OHLCV + corporate actions (splits/dividends adjusted), borrow availability

## 2. Economic rationale

Two claims on near-identical cash flows or risk exposures (dual listings, same-sector close substitutes, parent/subsidiary) should move together. Temporary divergence is caused by **uninformed idiosyncratic order flow** (a fund liquidating one name, index flows hitting one twin, retail attention) that price-pressure moves one leg without new information. The pairs trader is a **liquidity provider enforcing the law of one price**; the compensation is a premium for absorbing inventory risk and bearing *divergence risk* — the spread can widen further before converging (limits of arbitrage, Shleifer-Vishny). The counterparty is the impatient flow that caused the divergence.

Important honesty point: for non-identical pairs (two banks, two miners), "convergence" is a statistical regularity, not a hard arbitrage. The edge is proportional to how structurally linked the two businesses are.

## 3. Signal & rules specification

Two canonical variants (backtest both; they disagree usefully):

**A. Distance method (Gatev-Goetzmann-Rouwenhorst):**
- Universe: liquid share universe (e.g., top 1000 US by dollar volume), exclude stocks <$5, ADV < $5M.
- **Formation window:** 12 months (range: 6–18m). Normalize each stock's total-return index to 1 at window start. For every pair, compute sum of squared differences (SSD) of normalized prices.
- Select top N pairs by smallest SSD (N = 5–20 traded; form from top 20–100). Optionally restrict pairs to same GICS industry — strongly recommended: raises convergence rates and gives the statistical link an economic backbone.
- **Trading window:** next 6 months. Open when spread |z| > 2σ of formation-window spread std (range 1.5–2.5σ): short the winner, long the loser, equal dollar legs. Close at spread crossing 0 (or |z| < 0.5), or at trading-window end, or stop at |z| > 4σ (divergence stop).
- **Rebalance:** overlapping cohorts — start a new formation/trading cycle monthly.

**B. Cointegration method:**
- For candidate same-industry pairs, test log-price cointegration over 1–3y (Engle-Granger; hedge ratio β from the cointegrating regression, or Johansen). Keep pairs with p < 0.05 **and** spread half-life (from AR(1)/Ornstein-Uhlenbeck fit) between ~5 and ~40 trading days — too short is untradeable noise, too long ties up capital.
- Spread: `s_t = ln P1_t − β·ln P2_t`. Trade z-score of s on rolling window ≈ 3–5 half-lives. Entry |z| > 2, exit z ≈ 0, hard stop |z| > 3.5–4 **or** re-test failure (cointegration breaks on rolling re-estimation → close immediately).
- Position size per pair: risk-budgeted so a 4σ adverse move costs ≤ 0.5–1% of NAV; β-weighted legs (not equal dollar).

## 4. Evidence & key research

- Gatev et al. (2006, *RFS*) [A1]: ~11%/yr excess return 1962–2002 on top-20 distance pairs, near-zero market beta, Sharpe above contemporaneous market.
- Do & Faff (2010, 2012) [A2]: profitability declines sharply after 1990s; after realistic commissions, impact, and short fees, mean excess return of the classic recipe drops to roughly breakeven — **surviving profitability concentrates in same-industry pairs and in high-divergence episodes** (2000–02, 2008–09).
- Krauss (2017) [A3]: survey; cointegration variants and copula/O-U refinements outperform raw distance out-of-sample in most studies.
- Recent evidence [A9]: modest but positive net returns persist in mid/small caps and outside the US; near zero in US large caps.
- **Decay status: significant.** Treat US large-cap pairs as a validity check for your pipeline, not a source of alpha.

## 5. Expected performance profile

- Realistic net Sharpe today: **0.3–0.7** standalone (portfolio of 20+ pairs, mid-cap tilt, industry-matched); higher in stress years — the strategy is *long volatility of cross-sectional dislocation*.
- Return profile: many small wins, occasional large loss when a "pair" structurally breaks (fraud, M&A on one leg, thesis change). Mildly negative skew per pair, diversifiable across pairs.
- Turnover: high (200–400% per leg annually). Cost sensitivity: **decisive** — this strategy lives or dies on borrow fees + slippage.

## 6. Failure modes & risks

- **Structural breaks:** one leg gets acquired, delisted, or re-rated permanently (the spread never converges). This is the dominant loss source — divergence stops and re-test exits are not optional.
- **Crowding/deleveraging:** August 2007 quant crash [R6] — when levered stat-arb books unwind simultaneously, spreads widen violently before converging; leverage above ~3–4x turns a survivable event into ruin.
- **Short leg risks:** borrow recalls, squeeze dynamics (short leg rallying on flow, not fundamentals).
- Regime: underperforms in quiet, trending, low-dispersion markets; earns most after volatility spikes.

## 7. Backtesting guidance

- **Survivorship bias is fatal here:** delisted/acquired stocks are precisely the pairs-breaking events. Use a survivorship-bias-free universe with delisting returns (CRSP-style handling); without it, results are inflated massively.
- Use total-return prices (dividends), point-in-time industry classification, and apply the **one-day-wait rule** (signal on close t, trade at t+1) to kill bid-ask bounce, which otherwise fabricates most of the distance-method profit — Gatev et al. show waiting one day cuts returns ~⅓; your backtest must show the same sensitivity or it's broken.
- Costs: model commissions + half-spread + impact ≥ 10–20bp round trip per leg (mid-caps), plus borrow fee (30–300bp/yr; hard-to-borrow names much more; ideally use actual borrow data or exclude high-fee names).
- Walk-forward only: form pairs strictly on past data; re-select monthly. Report results by year and by market-cap bucket — a good pipeline shows decay over time and better results in smaller caps; if not, suspect look-ahead.
- Minimum data: 10+ years daily, survivorship-free, with industry tags.

## 8. Recommendations for use

- **Backtest priority: medium-high** — not for the raw alpha, but because the pipeline (spread modeling, O-U half-life estimation, cost realism, delisting handling) is reusable infrastructure for every other RV strategy in this corpus.
- Best current expression: same-industry mid-caps, non-US markets, ETF pairs (see ETF–NAV doc), and crisis-conditional deployment (scale up when cross-sectional dispersion spikes).
- Portfolio role: market-neutral diversifier; correlates with short-vol/liquidity-provision strategies (Nagel [R2]) — don't treat it as independent of the short-term reversal sleeve.
