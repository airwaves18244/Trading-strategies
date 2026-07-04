# Cross-Sectional Equity Momentum (12-1)

## 1. Classification

- **Category:** Momentum (cross-sectional)
- **Asset classes:** Equities (global)
- **Style:** Long-short (or long-only tilt), relative ranking
- **Horizon:** Signal 3–12 months; monthly rebalance; positions held ~3–6 months effective
- **Capacity:** High (large-cap versions)
- **Complexity:** Low–medium; **Data burden:** daily/monthly total-return prices, survivorship-free universe

## 2. Economic rationale

Stocks that outperformed peers over the past ~year continue outperforming for months. Behavioral mechanism (dominant explanation): **investor underreaction** — information diffuses slowly (anchoring on old prices, disposition effect: winners sold too early keep prices below fair value, losers held too long stay above), then **delayed overreaction** as trend-chasers pile in. The counterparty is the disposition-effect investor and the slow-moving institution. A risk-based component exists (momentum crashes = payment for crash risk), but the premium is too large and too universal to be fully risk. It is one of the most replicated findings in finance — and per McLean-Pontiff [X1] also one of the most arbitraged post-publication.

## 3. Signal & rules specification

- **Universe:** all listed stocks above liquidity/price floors (e.g., top 1000–3000 by cap; exclude < $5, ADV < $2M). Point-in-time membership.
- **Signal:** total return from t−12 months to t−1 month (**skip the most recent month** — it reverses; see short-term reversal doc). Range: formation 6–12m, skip 0–1m (keep the skip).
- **Portfolio:** rank; long top decile, short bottom decile (long-only: overweight top quintile/decile). Value-weighted within deciles reduces cost & small-cap dependence; equal-weighted shows bigger gross returns (a red flag for costs, not a feature).
- **Rebalance:** monthly; overlapping-cohorts (hold 3 monthly-formed sub-portfolios, e.g.) reduces turnover and timing luck.
- **Risk overlay (strongly recommended, evidence-based):** volatility-managed momentum — scale exposure by target_vol/realized_vol of the momentum portfolio (Barroso-Santa-Clara [M10]) and/or reduce the short-losers leg after market crashes when losers become high-beta lottery tickets (Daniel-Moskowitz [M9]). This is not indicator decoration; it addresses the documented crash mechanism.
- Sector-neutral variant: rank within sectors — cuts factor bets, improves Sharpe consistency, lowers crash severity.

## 4. Evidence & key research

- Jegadeesh & Titman (1993) [M1]: ~1%/month gross long-short spread, US 1965–1989; replicated out-of-sample in later decades and pre-1965 data.
- Asness, Moskowitz & Pedersen (2013) [M2]: momentum works in every equity market examined and in FX, commodities, bonds — the universality is the strongest anti-data-mining evidence in the factor literature.
- Daniel & Moskowitz (2016) [M9]: crashes — 1932, 2009: short-leg rebounds destroyed −70%+ in months; crash is forecastable (bear market + high vol states).
- Barroso & Santa-Clara (2015) [M10]: constant-vol scaling roughly doubles net Sharpe and cuts max drawdown from −96% to −45% (long history).
- McLean & Pontiff [X1] + post-2000 US evidence: gross US long-short momentum weaker post-publication (2000s–2010s ≈ half the pre-1993 rate; 2009 crash within that). International and vol-managed versions held up better.
- **Decay status: partial** (~30–50% of gross premium), crash risk fully intact.

## 5. Expected performance profile

- Long-short net Sharpe today: **0.3–0.6 raw; 0.5–0.8 vol-managed, sector-neutral**; long-only tilt adds ~1–2% over index with tracking error ~4–6%.
- Skew: **strongly negative raw** (crash risk); vol management mitigates. Correlation to value: negative (~−0.4) — the classic pairing.
- Turnover: ~70–150% per side annually (overlapping construction at the low end). Cost sensitivity: medium — viable in large caps at ~10–20bp costs; equal-weighted small-cap versions are cost-fiction.

## 6. Failure modes & risks

- **Momentum crashes:** sharp market reversals after downtrends (2009-Q2: losers +80% in 3 months). Mitigation is built into §3.
- Factor concentration: momentum piles into whatever theme led (tech 2000, energy 2008, AI 2024) — theme unwind = drawdown; sector-neutrality halves this.
- Crowding: the most-cited factor; expect episodic factor-level unwinds (momentum-specific deleveraging weeks).
- Long dry spells (2010s US had a decade of weak raw momentum) — position it as a sleeve, never the whole book.

## 7. Backtesting guidance

- Survivorship-free universe with delisting returns is mandatory (losers delist; without delisting returns the short leg is fantasy). Total-return prices.
- Point-in-time universe membership and sector tags; skip-month convention exactly as specified; signal from month-end t−1 data, execute at month-start t.
- Model costs per trade with turnover accounting; test value-weighted vs equal-weighted — report both; if your alpha lives only in equal-weighted small caps, it's a cost artifact.
- Reproduce known results as validation: your 1965–1990 US backtest should land near ~1%/mo gross — calibrates the pipeline before you trust any variation.
- Report: by decade, crash episodes isolated, vol-managed vs raw, sector-neutral vs raw.
- Minimum data: 20y+ (ideally CRSP-style full history) to include multiple regimes and both crashes.

## 8. Recommendations for use

- **Backtest priority: high** — cornerstone factor, cheap infrastructure, and the reference implementation for every other cross-sectional doc in this corpus.
- Deploy vol-managed + sector-neutral; consider long-only tilt if shorting infrastructure is a constraint.
- Pair with value (negative correlation) and trend (crash behavior differs — trend tends to profit in the drawn-out bear that precedes momentum's crash).
