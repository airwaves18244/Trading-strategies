# Industry Momentum & Factor Momentum

Two related "momentum lives at the group level" findings, documented separately but sharing one implementation skeleton — treated in one doc, backtestable as two variants.

## 1. Classification

- **Category:** Momentum (cross-sectional, group-level)
- **Asset classes:** Equity industries (via sector indices/ETFs); equity factor portfolios
- **Style:** Long-short or long-only rotation
- **Horizon:** 1–12 month signals, monthly rebalance
- **Capacity:** High (trades liquid baskets)
- **Complexity:** Low; **Data burden:** sector index/ETF total returns; factor return series (published or self-built)

## 2. Economic rationale

**Industry momentum [M6]:** a large share of stock-level momentum is industry-driven: information about sector-wide fundamentals (oil price shifts, rate cycles, product cycles) diffuses slowly across investors and across stocks within the sector. Trading the industry basket captures this diffusion with far fewer names, lower idiosyncratic noise, and higher capacity. Counterparty: investors underreacting to sector-level news and mechanical style/sector allocators rebalancing against the move.

**Factor momentum [M7]:** factor portfolios themselves (value, quality, low-vol, etc.) exhibit return autocorrelation — a factor that did well recently tends to continue. Mechanism: factor flows are slow (institutional mandates chase factor performance over quarters) and arbitrage capital moves gradually across styles. Strikingly, Gupta-Kelly show factor momentum **subsumes much of stock-level momentum** — stock momentum is substantially a bet on recently-winning factors. Counterparty: slow institutional style rotation.

## 3. Signal & rules specification

**A. Industry momentum:**
- Universe: 20–50 industry groups (GICS level 2–3), tradable via sector ETFs or futures where available.
- Signal: past 6-month total return (range 3–12m; industry momentum is robust at shorter lookbacks than stock momentum and does *not* require the skip-month — test both).
- Portfolio: long top quartile industries / short bottom quartile, equal risk weights; long-only version = overweight top sectors.
- Rebalance monthly; vol-target the book.

**B. Factor momentum:**
- Inputs: return series for 10–50 long-short factors (published libraries or self-built from the equity pipeline: value, momentum, quality, low-vol, investment, accruals…).
- Signal: sign or z of each factor's trailing 1–12 month return (Gupta-Kelly: 1-month already works — factor returns are strongly autocorrelated; use average of 1/3/6/12 for robustness).
- Portfolio: long recent-winner factors, short recent-loser factors, scaled to equal vol per factor; or use it as a **tilt on an existing multi-factor book** (overweight factors with positive trailing return) — the practical deployment.
- Rebalance monthly.

## 4. Evidence & key research

- Moskowitz & Grinblatt (1999) [M6]: industry momentum ~0.4–0.5%/mo; explains a large fraction of stock momentum in their sample.
- Gupta & Kelly (2019) [M7]: factor momentum positive across 65 factors, robust internationally; 1-month factor autocorrelation especially strong; subsumes stock momentum better than the reverse.
- Ehsani & Linnainmaa (2022, *J. Finance*): confirms — momentum is largely "factor timing in disguise"; factor momentum earns Sharpe ~0.8 gross in long samples.
- **Decay status:** less studied post-publication than stock momentum; group-level versions are lower-turnover and large-cap, so cost-adjusted decay is smaller, but crowding monitoring is warranted — treat published Sharpe with a standard ~40% haircut [X1].

## 5. Expected performance profile

- Industry momentum: net Sharpe **0.3–0.5** standalone; factor momentum: **0.4–0.7** gross of the underlying factors' costs.
- Skew: negative (momentum family); factor momentum drawdowns cluster at sharp style rotations (Nov-2020 value snap, 2009-Q2).
- Turnover: low–medium (baskets, monthly). Cost sensitivity: low (ETFs/index instruments) — the family's most cost-friendly members.

## 6. Failure modes & risks

- Sharp style/sector rotations reverse group momentum violently (vaccine day Nov-2020: −10σ style rotation in a day).
- Factor momentum requires factor definitions stable over time; a "factor zoo" library invites overfitting — restrict to well-documented factors [X2].
- Overlap risk: industry momentum + stock momentum + factor momentum are correlated expressions of one phenomenon; counting them as three independent alphas overstates portfolio diversification (see critique doc).

## 7. Backtesting guidance

- Industry: use point-in-time sector classifications; sector ETFs only exist post-1998 — extend with index data before that; include ETF expense/spread.
- Factor: build factor returns from your own survivorship-free pipeline for full control, or use published series (Kenneth French library, AQR data sets) with the caveat that published series embed favorable conventions; costs of *trading the factors* must be layered on (a factor-momentum backtest gross of underlying turnover is fiction — factor momentum doubles the turnover of the underlying factors).
- The decisive experiment (per [M7]): regress stock-momentum returns on factor-momentum returns and vice versa on your data — determines which sleeve deserves capital.
- Minimum data: 20y+ factor/sector histories.

## 8. Recommendations for use

- **Backtest priority: medium-high.** Industry momentum is the cheapest live implementation of the momentum effect (few instruments, low cost) — good early production candidate. Factor momentum is most valuable as a *meta-layer* tilting an existing multi-factor allocation.
- Do not run stock, industry, and factor momentum as separate full-size sleeves — pick the layer(s) your infrastructure trades cheapest and treat the family as one risk allocation.
