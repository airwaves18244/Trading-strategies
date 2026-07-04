# FX Carry

## 1. Classification

- **Category:** Carry (FX)
- **Asset classes:** Currency forwards/futures — G10 core; EM extension
- **Style:** Cross-sectional long-short (and TS variant)
- **Horizon:** Monthly rebalance; positions held months
- **Capacity:** Very high
- **Complexity:** Low; **Data burden:** spot + forward points (or futures) per currency; interest rates for validation

## 2. Economic rationale

Borrow low-yield currencies, lend high-yield ones. Uncovered interest parity says exchange-rate moves should offset the rate gap; empirically they don't (the *forward premium puzzle*) — high-rate currencies have historically not depreciated enough, leaving the carry as excess return. Why the premium exists: high rates typically compensate for **crash risk and funding fragility** — carry currencies do well in calm markets and crash together when global risk appetite breaks (Brunnermeier et al. [C2]: "up the stairs, down the elevator"; carry unwinds are self-reinforcing as levered positions hit funding constraints). Sellers of the premium: hedgers of high-yield-currency exposure and safe-haven demanders (institutions structurally long JPY/CHF assets paying for stability). The strategy is economically **selling global-risk-appetite insurance**.

## 3. Signal & rules specification

- **Universe:** G10 (9 pairs vs USD or all crosses); EM adds premium and adds crash/convertibility risk — separate sleeve if at all.
- **Carry measure:** annualized forward discount `(S − F)/F` per currency vs USD (equivalently short-rate differential; use forwards — they embed the true tradable carry including cross-currency basis).
- **Portfolio (cross-sectional):** rank by carry; long top 3, short bottom 3 (G10), equal risk (inverse ex-ante vol) weights, dollar-neutral. Rebalance monthly (carry moves slowly).
- **TS variant:** position each currency ∝ sign/size of its own carry vs USD — test both; CS is the literature standard.
- **Documented refinements (evidence-based, not decoration):**
  - **Valuation filter [C8]:** scale down long-carry positions in currencies expensive on long-run real-exchange-rate measures (PPP z-score) — valuation-adjusted carry retained positive returns post-GFC when raw carry flatlined.
  - **Risk-state throttle:** halve or cut exposure when global risk indicators (FX vol index, equity vol) spike — carry's losses concentrate in identifiable stress states [C2][C3]; even a crude vol filter historically cut the left tail materially.
- **Sizing:** portfolio vol target 6–10%; leverage kept modest (the tail is the constraint, not the vol).

## 4. Evidence & key research

- Koijen et al. [C1]: FX carry among the 9 asset classes; long-sample Sharpe ~0.6–0.9 gross pre-2012.
- Brunnermeier et al. [C2], Daniel et al. [C3]: crash anatomy, skewness ∝ carry level, funding-liquidity linkage.
- Post-GFC decay [C4]: G10 carry Sharpe ~1.08 pre-2008 → **~0.25 after** — rate compression (everyone at zero) removed dispersion, and the 2010s were a carry graveyard. Partial revival 2021–2024 as rate dispersion returned; the Aug-2024 yen unwind was a textbook crash reminder.
- Valuation-adjusted carry [C8] worked through the 2010s–2020s.
- **Decay status: substantial for raw G10 carry; conditional versions (valuation-adjusted, dispersion-aware, EM-inclusive) retain a modest premium.** Note the structural dependence: no rate dispersion → no strategy.

## 5. Expected performance profile

- Net Sharpe: raw G10 **0.2–0.4** in the modern era; valuation/risk-filtered **0.4–0.6**; EM adds ~0.1–0.2 with fatter tails.
- Skew: **strongly negative** — years of steady gains, then −10–20% weeks (1998, 2008, Aug-2024). This is the defining feature; any backtest not showing it is wrong.
- Turnover: very low; costs minimal in G10 forwards (~1–3bp) — among the cheapest strategies here.

## 6. Failure modes & risks

- **Global carry unwinds:** correlated across all carry pairs simultaneously; leverage + negative skew = ruin mechanics if oversized.
- Rate-compression regimes (2009–2020): the signal's raw material disappears.
- EM: convertibility, intervention, devaluation gaps (CHF Jan-2015 was G10-grade proof pegs break — a −20%+ single-print event for short-CHF carry).
- Crowding: carry is the most intuitive trade in macro; positioning data (CFTC) shows extremes before unwinds — usable as a throttle input.

## 7. Backtesting guidance

- **Use forward prices, not interest-rate differentials**, to compute returns (forwards embed cross-currency basis — the tradable carry differs from textbook rate gaps, especially post-2008).
- Total return per pair = spot return + carry accrual from forward roll; monthly forwards rolled properly; transaction costs on rolls too.
- Include 1998, 2008, 2015-CHF (if trading CHF), 2024-JPY; report skewness/max-drawdown per unit Sharpe.
- Test the pre/post-2008 split explicitly — the strategy's own literature says the regimes differ; a pooled average hides the live question.
- Validate valuation filter with point-in-time PPP/REER data (OECD/BIS series).
- Data: 25y+ of forwards for G10 (available from standard vendors).

## 8. Recommendations for use

- **Backtest priority: medium.** Cheap to build (few instruments), essential as the carry-family reference — but temper expectations on raw G10.
- Deploy only as part of the diversified carry composite (doc 05) and/or blended with trend (doc 03-03), never as a standalone levered book — the skew must be diluted across uncorrelated premia.
- Keep the valuation and risk-state filters; keep EM small if used.
