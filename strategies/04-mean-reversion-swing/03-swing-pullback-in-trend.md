# Swing Trading: Pullback-in-Trend (Structure-Based)

## 1. Classification

- **Category:** Swing trading (hybrid: trend context + reversion entry)
- **Asset classes:** Equities, index futures, FX, crypto — anything liquid with trending behavior
- **Style:** Directional, discrete trades with defined risk
- **Horizon:** Holds 2–20 days
- **Capacity:** Medium–high (instrument-dependent)
- **Complexity:** Low–medium; **Data burden:** daily OHLCV (intraday improves entries)

## 2. Economic rationale

The trade: in an established uptrend, buy the retracement; exit into strength (mirror for downtrends). Why this has market logic rather than being chart mysticism — it stacks **two documented premia with compatible signs**:

1. **Medium-horizon continuation** (the trend/momentum premium, docs 02-02/03-01): the trend state raises the probability the next multi-week move is up.
2. **Short-horizon reversal** (docs 04-01/04-02): the pullback itself is often uninformed flow — profit-taking, stop-runs, index-level de-risking hitting a strong name — that concedes price to liquidity providers.

Buying pullbacks in trends is *harvesting short-term reversal conditional on positive medium-term drift* — both legs of the position have documented positive expectancy, whereas buying every dip (no trend filter) or chasing every rally (no reversion entry) each fight one of the premia. Counterparty: short-horizon impatient sellers inside a longer accumulation. Lou-Polk-Skouras [R3] adds supporting structure: momentum profits accrue overnight while intraday flow reverses — consistent with pullbacks being intraday-flow phenomena inside overnight-driven trends.

## 3. Signal & rules specification

Fully mechanical spec (no discretion required):

- **Trend state (context):** price > 100–200d MA **and** medium-term return positive (e.g., 6m return > 0) — either alone suffices; both = stricter. (MA here is a trend *estimator*, per brief rules.)
- **Pullback trigger:** retracement of 3–10 days losing 1–2·ATR(20) from the swing high, **without** trend-state violation; optional quality condition: pullback on *declining* volume (flow, not news — test).
- **Entry:** limit near prior support / fixed 1.5–2 ATR below swing high, or on first strength resumption (close > previous high) — test both entry styles: limit entries earn the concession but catch more knives; resumption entries pay more but filter.
- **Initial stop:** 1–1.5·ATR below entry (or below the pullback low). **Target/exit:** prior swing high or 2–3R; or trail once 1R in profit; time stop 15–20 days.
- **Sizing:** fixed fractional risk 0.25–0.75% NAV per trade at stop; concurrent positions capped by correlation groups.
- **Universe (equities):** liquid names already ranked by the momentum pipeline (top momentum decile = candidate pool) — reuses cross-sectional infrastructure and aligns the trade with the documented factor.

## 4. Evidence & key research

- Component evidence: trend/momentum [M1][M3][T1] + short-term reversal [R1][R2] — this doc's claim is the *composition*, which is directly testable (see §7) rather than separately published; academic proxies exist (e.g., studies of momentum-with-reversal-timing overlays showing improved entry pricing reduces momentum's turnover cost drag).
- Lou-Polk-Skouras [R3]: overnight/intraday split consistent with the mechanism.
- Practitioner provenance: this is the codified core of classical swing methodology (O'Neil/Minervini-style pullback buys, stripped of discretionary pattern layers) — treated here as hypothesis, not authority.
- **Decay status:** inherits components (momentum partial decay; conditional reversal alive). No independent post-publication history since the composition isn't a single published anomaly. **Confidence: medium** — must earn its keep in your backtest vs its components.

## 5. Expected performance profile

- Expected: win rate 45–60%, payoff ~1.5–2R, net Sharpe **0.3–0.6** standalone; the honest benchmark is whether it beats *simple momentum holding* on the same names after costs (better entries vs missed moves).
- Skew: mildly positive (stops truncate losses; targets cap wins — roughly symmetric per trade, portfolio skew depends on trail vs target choice).
- Turnover: moderate; cost sensitivity medium (limit entries help materially).

## 6. Failure modes & risks

- **Trend break disguised as pullback:** the stop is the only defense; expect clustered stop-outs at trend turns (give-back of several R in a week).
- Strong trends that never pull back to the limit → participation gap vs pure momentum (opportunity cost is the hidden fee of entry selectivity).
- Chop regimes: trend filter passes marginal trends whose pullbacks don't resume; the 6m-return condition tightens this.
- In single stocks: pullbacks caused by real news (filter earnings/major events windows).

## 7. Backtesting guidance

- **The decisive experiment is A/B:** identical universe/costs — (A) momentum buy-and-rebalance, (B) pullback-entry version, (C) pullback entry with no trend filter, (D) trend filter with immediate entry. B must beat A net-of-costs *and* C, D on risk-adjusted terms, else the composition adds nothing — kill it without sentiment.
- Fill realism for limit entries: a limit at support fills preferentially when price trades *through* it (adverse selection of fills) — simulate fills only when price trades strictly below limit, and test fill-rate sensitivity.
- Path-dependent rules (stops/targets/trails) need intrabar assumptions: use conservative ordering (stop hit before target when both touch in one bar) or intraday data.
- Report trade-level distribution (R-multiples), by trend-strength tercile and by regime; parameter surfaces for ATR multiples and time stops.
- Data: 15y+ daily OHLCV across ≥ 3 asset classes (composition should generalize if real).

## 8. Recommendations for use

- **Backtest priority: medium.** It's the corpus's representative of classical swing trading, deliberately specified to be testable; its value is likely execution-layer improvement of momentum sleeves (better entry pricing, defined risk) rather than an independent alpha.
- If validated: best used in markets where you already run momentum/trend and want per-trade risk definition (crypto, concentrated equity books).
- If it fails the A/B: keep the stop/sizing discipline (portable), discard the entry timing.
