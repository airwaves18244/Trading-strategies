# Residual (Idiosyncratic) Momentum

## 1. Classification

- **Category:** Momentum (cross-sectional, factor-hedged)
- **Asset classes:** Equities
- **Style:** Long-short market/factor-neutral
- **Horizon:** 12-1 formation, monthly rebalance
- **Capacity:** High
- **Complexity:** Medium; **Data burden:** daily/monthly total returns + factor returns (market, size, value or a factor library)

## 2. Economic rationale

Standard momentum ranks on total returns, so its winners/losers are substantially **factor bets in disguise** (high-beta stocks after rallies, sector concentrations). Residual momentum ranks on the *stock-specific* component of returns — performance net of factor exposure. The behavioral engine (underreaction to firm-specific news: earnings, products, management) is the same as CS momentum, but the construction removes the part of momentum that is factor-timing luck. Because factor exposures drive momentum crashes (short leg = high-beta losers rebounding), stripping them cuts crash risk roughly in half while keeping the underreaction alpha. Counterparty: same slow-reacting/disposition-prone investors — but the bet is purified to firm-level news diffusion.

## 3. Signal & rules specification

- **Universe:** same as CS momentum (top 1000–3000, liquidity floors, point-in-time).
- **Residual estimation:** rolling regression of each stock's monthly (or daily) returns on factor returns — minimum: market; standard: Fama-French 3 (Mkt, SMB, HML). Window 36 months (range 24–60).
- **Signal (Blitz-Huij-Martens [M4]):** mean of residuals over t−12 to t−2, **scaled by the std of those residuals** (an information-ratio, not a raw return): `s = mean(ε_{−12..−2}) / std(ε_{−12..−2})`.
- **Portfolio:** decile long-short on s; sector-neutral optional (residualization already removes much sector effect if sector factors included). Value-weight or liquidity-weight.
- **Rebalance:** monthly, overlapping cohorts as in CS momentum.
- **Sizing:** the resulting portfolio is near-zero beta by construction; vol-target the book to 8–12%.

## 4. Evidence & key research

- Blitz, Huij & Martens (2011) [M4]: US 1930–2009 — similar raw return to standard momentum with roughly **half the volatility**, doubling the Sharpe (~0.5 → ~0.9 gross in their sample); dramatically smaller 1932/2009-style crashes.
- Blitz, Hanauer & Vidojevic (2020, follow-up): idiosyncratic momentum works internationally and survives factor-model changes; weaker post-2000 in the US like all momentum, but degrades less.
- Consistent with Daniel-Moskowitz [M9] diagnosis: crashes live in the factor component — removing it removes most crash.
- **Decay status: partial** (inherits general momentum decay [X1]) but the *relative* advantage over raw momentum is stable across samples.

## 5. Expected performance profile

- Net Sharpe: **0.5–0.8** long-short (better than raw CS momentum per unit of drama).
- Skew: mildly negative (vs strongly negative raw momentum); max drawdowns historically ~⅓–½ of raw momentum's.
- Turnover: similar to CS momentum (~100% per side annually); cost sensitivity medium.
- Correlations: high to raw momentum (~0.7 — they are siblings, not independent strategies), low to market/value.

## 6. Failure modes & risks

- Factor-model misspecification: residuals still contain unmodeled factors (crypto-beta, AI-theme); refresh factor sets or add statistical factors, else "idiosyncratic" drifts thematic.
- Momentum-wide unwind events still bite (Aug 2007-style quant deleveraging hits every momentum flavor).
- Estimation noise: 36-month betas on volatile stocks are noisy; the IR-scaling in the signal partially self-corrects, but garbage-beta names should be filtered (min R² or min observations).

## 7. Backtesting guidance

- All CS-momentum hygiene applies (survivorship-free + delisting returns, point-in-time, skip month, next-period execution, cost model).
- Factor returns must be **point-in-time computable** (use standard published factor series or build from the same universe — don't regress on factors that embed future universe knowledge).
- The key report: side-by-side vs raw CS momentum on identical universe/costs — Sharpe, max DD, crash-month table (2009-Q2, 2020-Q2, Nov-2020 vaccine rotation). The claim to validate is *better risk-adjusted, smaller crashes*, not higher raw return.
- Sensitivity: factor set (CAPM vs FF3 vs FF5), estimation window, IR-scaling on/off.
- Minimum data: 20y+ with factor histories.

## 8. Recommendations for use

- **Backtest priority: high, conditional on CS momentum being built first** (it's a variant with one added estimation layer, and the comparison is the deliverable).
- If running one equity momentum sleeve, residual momentum is the better production choice (same idea, less crash); if capacity for both, they don't count as two independent bets — treat as one allocation.
- Pairs well with value and quality sleeves in a factor-neutral multi-factor book.
