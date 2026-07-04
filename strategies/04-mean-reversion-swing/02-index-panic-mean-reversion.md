# Index Panic Mean-Reversion (Liquidity Provision at the Index Level)

## 1. Classification

- **Category:** Mean reversion (time-series, index level)
- **Asset classes:** Equity index futures/ETFs (primary); works on liquid single markets and crypto majors with adjustments
- **Style:** Directional long-bias, episodic
- **Horizon:** Entries after multi-day selloffs; holds 2–15 trading days
- **Capacity:** Very high
- **Complexity:** Low; **Data burden:** daily index OHLCV + a volatility measure (realized or VIX)

## 2. Economic rationale

Equity indices exhibit **negative short-horizon autocorrelation after sharp, volatility-spiking declines**: multi-day panics overshoot because selling is dominated by *forced* flow — margin calls, vol-target deleveraging, risk-limit breaches, redemption sales — that is price-insensitive by construction. Whoever buys from forced sellers earns a concession. The effect is state-dependent: in calm markets index returns are ~unpredictable (or mildly trending); the reversal premium exists specifically in the high-vol, post-cascade state — which is also why it's not arbitraged flat: catching falling knives requires capital and mandate freedom exactly when both are scarce (limits of arbitrage). Counterparty: the forced sellers. This is Nagel's liquidity-provision logic [R2] applied at the index level, where costs are tiny and capacity huge — the trade-off is no cross-sectional diversification: it's a handful of fat episodes per year.

Note: at multi-month horizons this shades into "buy the dip within secular uptrends" — a different (equity-risk-premium) justification. This doc is strictly the days-scale liquidity trade.

## 3. Signal & rules specification

Baseline spec (define precisely, then vary within ranges):

- **Panic state definition:** index return over past 3–5 days < −1.5σ (σ = trailing 60d vol) **AND** vol spike: realized 5d vol > 1.5× trailing 60d vol (or VIX > 1.3× its 60d mean). Both legs required — the vol condition separates forced-flow selloffs from orderly repricing.
- **Entry:** long index futures/ETF at next close (or scale in thirds over 1–3 days — panics cluster; averaging into the state is part of the design, with a hard cap).
- **Exit:** first of — (a) return to pre-panic 5–10d price level or vol normalization (5d vol < 1.1× 60d), (b) time stop 10–15 trading days, (c) **disaster stop:** additional −2σ move after full position → exit (this is the 2008-continuation protection; it will occasionally sell lows — that's the insurance premium you pay).
- **Sizing:** per-episode risk 1–3% NAV at the disaster stop; position vol-scaled (higher vol → fewer contracts).
- **Frequency:** state triggers ~2–6× per year; strategy is flat most of the time (capital reusable elsewhere).
- Variants to test: RSI-type oscillators are *not* the spec — the spec is return-threshold + vol-state (economic definition); intraday version (buy final-hour capitulation) if intraday data available.

## 4. Evidence & key research

- Nagel (2012) [R2]: reversal premium scales with VIX — the state-dependence evidence.
- Documented index short-horizon autocorrelation flip: positive (momentum) pre-1990s → negative post-2000 in US large-cap indices (widely replicated; related to rise of index arbitrage and fast liquidity); the negative autocorrelation concentrates in high-vol states.
- Practitioner literature on "crash then rally" statistics: majority of 5-day −3σ index moves since 1990 mean-reverted ≥ half the fall within 2 weeks (US); the exceptions (Sep-2008, Feb/Mar-2020 first leg) are exactly why the disaster stop and sizing rules exist.
- **Decay status: mild.** The forced-flow mechanism regenerates (vol-target AUM grew, retail leverage grew); each episode differs, but the state-conditional edge has persisted out-of-sample (post-2012: Aug-2015, Feb-2018, Dec-2018, Mar-2020 second leg, 2022 bear rallies, Aug-2024 all reverted per pattern).

## 5. Expected performance profile

- Episodic: hit rate ~65–75% of episodes, average win ≈ 1.5–2× average loss *excluding* disasters; one -full-risk disaster per several years.
- Net Sharpe standalone: **0.4–0.7** (low trade count keeps statistical confidence modest — accept wide error bars); costs negligible (index futures).
- Skew: negative (the disaster case), truncated by the stop; correlation to equities positive-in-crashes — **this strategy adds to portfolio drawdowns**; size it as risk-seeking capital, not diversifier.

## 6. Failure modes & risks

- **Regime misread:** buying a liquidity cascade that is actually the start of a solvency crisis (2008): the state definition can't distinguish; the disaster stop + sizing must carry the strategy through being wrong.
- Averaging-in discipline: uncapped adds turn a bounded trade into ruin — cap is structural.
- Overnight/weekend gaps through stops (futures close, crypto never does — crypto version needs wider stops/smaller size).
- Correlation with the rest of your book: fires exactly when stat-arb/carry books are drawing down — portfolio-level cash planning matters (this is a strategy you must have dry powder for).

## 7. Backtesting guidance

- Low trade count → **episode-level analysis, not just aggregate stats:** list every historical trigger with entry/exit/path; eyeball the losers (the 2008 sequence is the design case).
- No look-ahead in σ estimates (trailing windows end t−1); execution next close after trigger; include overnight gap risk in fills.
- Long history essential: 1987, 1998, 2008, 2011, 2015, 2018, 2020, 2022, 2024 — daily index data to 1980s minimum (this is available; use futures-era data for realistic costs, index data for episode census).
- Report: per-episode table, sensitivity surface over (return threshold σ, vol multiple, time stop), and results with the disaster stop disabled (to price the insurance you're buying).
- Cross-market validation: run identical spec on 5–10 developed indices — a real mechanism should appear everywhere (with varying strength), a curve-fit won't.

## 8. Recommendations for use

- **Backtest priority: high** — cheap to test, high capacity, and the episode playbook doubles as portfolio crisis-management doctrine (when to deploy dry powder).
- Deploy as an opportunistic overlay (0 exposure most of the time) with pre-committed sizing rules written *before* the panic — the entire edge is doing mechanically what discretionary traders can't do emotionally in the state.
- Pairs structurally with trend following: trend gets short/flat in extended bears while this harvests the bounces — the combination covers both crash shapes (grind vs V).
