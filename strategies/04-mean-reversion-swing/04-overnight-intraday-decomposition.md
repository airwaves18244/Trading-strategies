# Overnight vs Intraday Return Decomposition — ⚠ flagged: decayed core, useful residuals

## 1. Classification

- **Category:** Mean reversion / market structure (session-level seasonality)
- **Asset classes:** Equity indices & single stocks (US primarily); index futures
- **Style:** Session-conditional exposure timing
- **Horizon:** Overnight (close→open) vs intraday (open→close) legs
- **Capacity:** High at index level; **Data burden:** requires reliable open *and* close prices (or intraday data); daily-only OHLC with good opens suffices

## 2. Economic rationale

Historically, virtually all US equity index total return accrued **overnight** (close→open); intraday (open→close) averaged ≈ 0 or negative over multi-decade windows [R3, R4]. Candidate mechanisms — none fully settled:

1. **News timing:** earnings and macro news release outside RTH; overnight bears the news risk and earns its premium.
2. **Inventory risk transfer:** market makers/liquidity providers reduce inventory into the close and re-establish at the open, paying a concession (NY Fed documents the drift concentrating in specific overnight hours [R4]).
3. **Flow structure:** retail/401(k) flows execute at or near opens; MOC/opening auction imbalances.
4. At single-stock level [R3]: a "tug of war" — momentum profits accrue overnight, while several other anomalies (value, profitability) earn intraday — implying *which* factor you run should shape *when* you carry exposure.

Counterparty: intraday liquidity demanders and auction-flow participants. **Critical caveat:** the aggregate overnight-drift trade waned notably in the last ~10 years after heavy publication [R5] — the naive version is not recommended; the surviving content is conditional/structural (see §3, §4).

## 3. Signal & rules specification

Testable expressions, ordered by expected residual value:

**A. Factor-session alignment (the LPS result [R3]):** if running momentum sleeves, concentrate exposure overnight; if running value/quality, intraday — implemented via MOC/MOO order pairs on the sleeve's rebalance flow. This is an *overlay* on existing strategies, not a standalone book.
**B. Conditional overnight index drift:** long index futures close→open only in favorable states — documented conditioners: after down intraday sessions (reversal into the overnight), high-vol states, and specific overnight windows [R4]. Entry at cash close / exit at next open (futures execution).
**C. Event-overnight harvesting:** hold overnight through scheduled pre-open information (the earnings-announcement premium — a separate literature showing average positive drift into announcements; links to doc 07-01).
**D. Naive full overnight drift (long every close→open):** benchmark only — expected ≈ flat net of costs today.

- **Sizing:** these are timing overlays; risk lives in the underlying exposure. For B: vol-scaled index position, portfolio share small (≤ 5–10% risk), 2 trades/day cost reality.

## 4. Evidence & key research

- Lou, Polk & Skouras (2019) [R3]: decomposition by anomaly, US 1993–2013 — the tug-of-war evidence; robust in their sample.
- NY Fed "Overnight Drift" [R4]: index drift concentrated in specific hours (notably around European open), consistent with inventory-risk-transfer pricing.
- French & Roll (1986): the ancient root — return variance and mean differ radically by session.
- Elm Wealth analysis [R5, cross-checked]: rolling 5-year overnight-minus-intraday spread collapsed in the ~2015–2025 window post-publication — decay evidence for the naive trade.
- **Decay status: naive version heavily decayed; conditional/factor-session variants under-tested publicly (opportunity and risk).**

## 5. Expected performance profile

- Naive (D): ≈ 0 net today. Conditional (B): modest — Sharpe **0.2–0.5** as a small overlay in the states where it fires. Factor-session alignment (A): worth single-digit bps/month of implementation alpha on existing sleeves — meaningful at scale, invisible at small size.
- Skew: overnight legs carry gap/news risk (negative tails you cannot stop out of — you're holding precisely when the market is closed).
- Cost sensitivity: **extreme** — two executions per day; only index futures (sub-bp) or auction-native equity flow make sense; spreads kill everything else.

## 6. Failure modes & risks

- Gap risk concentration: the strategy is *deliberately* exposed to the session with the fat tails (overnight news shocks) and flat when hedging/exit is possible.
- Structural change: 24h futures trading, overnight equity venues, and global books are eroding the session boundary the effect depends on — the mechanism's substrate is dissolving (part of why decay is credible).
- Backtest fragility: results hinge on open-print quality (see §7) — many published magnitudes were partly auction-artifact.

## 7. Backtesting guidance

- **Open prices are the minefield:** consolidated "open" prints differ from tradable auction prices; pre-2000s opens especially unreliable. Use primary-exchange auction prices or index futures quotes at cash open; discard results that don't survive switching price sources.
- Execute in futures for B/D (cash-index arithmetic with futures fills); include roll and financing.
- Report rolling 5-year windows — the entire question is the post-2015 sample; a full-history average is misleading by construction.
- For A: implement as paired-order simulation on your actual momentum/value sleeve rebalances (MOO vs MOC), measure implementation-shortfall difference.
- Data: 20y+ with verified auction opens; NY Fed hour-level results need intraday futures data to replicate (optional).

## 8. Recommendations for use

- **Backtest priority: low-medium as standalone; medium as overlay research** once momentum/value sleeves exist (variant A is nearly free to test on your own rebalance flow).
- Do not deploy naive overnight drift; treat variant B as a small opportunistic overlay only if your post-2015 out-of-sample confirms.
- Included in the corpus because the session decomposition itself (which sessions pay for which factors) is a structural fact every equity strategy here should be checked against — it's diagnostic infrastructure as much as a strategy.
