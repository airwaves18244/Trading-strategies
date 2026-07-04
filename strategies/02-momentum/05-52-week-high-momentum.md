# 52-Week-High Momentum (Anchoring)

## 1. Classification

- **Category:** Momentum (cross-sectional, behavioral-anchor variant)
- **Asset classes:** Equities; works in industries too
- **Style:** Long-short ranking
- **Horizon:** Monthly rebalance; effective holding months
- **Capacity:** High
- **Complexity:** Low; **Data burden:** daily total-return prices (for highs), survivorship-free

## 2. Economic rationale

Rank stocks by **proximity of current price to their 52-week high** (not by past return). The mechanism is **anchoring**: traders use the 52-week high as a reference point and are reluctant to bid a stock through it ("it's already at its high"), so good news arriving near the high is underpriced — price then grinds through the anchor as the news is digested. Symmetrically, stocks far below their high are shunned ("falling knife") beyond what fundamentals justify... actually George-Hwang find the *nearness-to-high* long leg is where the effect concentrates. This is a distinct psychological mechanism from return-continuation momentum: a stock can be near its high with modest trailing returns (slow steady grinder) — and those are exactly the best performers. Counterparty: anchored traders who sell too early at reference-point prices (disposition effect at its purest).

## 3. Signal & rules specification

- **Universe:** standard equity universe (top 1000–3000, liquidity floors, point-in-time).
- **Signal:** `s = P_t / max(P over past 252 trading days)` using split/dividend-adjusted prices. s ∈ (0, 1].
- **Portfolio:** long top decile (nearest high), short bottom decile (furthest). Monthly rebalance; skip-month not required (the anchor is a level, not a return).
- Recommended refinements with evidence: exclude stocks within ±1 week of earnings; industry-neutral ranking (the effect exists within and across industries); combine with return-momentum — the *double sort* (high s AND positive 12-1 return) isolates the strongest continuation and the disagreement cells are diagnostic.
- **Sizing/risk:** as CS momentum (vol-target, value-weight); the short leg (deep-below-high names) is high-beta lottery territory — same crash mitigation as CS momentum applies (cut short leg in post-crash high-vol states).

## 4. Evidence & key research

- George & Hwang (2004) [M5]: 52w-high ranking earns ~0.45%/mo, comparable to JT momentum, and dominates it in head-to-head sorts in their sample (1963–2001); unlike JT momentum, returns do **not** reverse at 2–5y horizon — consistent with underreaction-only (no delayed-overreaction phase).
- Replications: effect confirmed internationally (weaker in some markets); industry-level 52w-high also works. Post-2000 US magnitude roughly halved (in line with momentum-family decay [X1]).
- Related anchor evidence: stocks crossing to *new* highs continue (breakout logic gets its respectability here — the anchor-breach is information).
- **Decay status: partial,** similar profile to CS momentum; crash risk of short leg identical in kind.

## 5. Expected performance profile

- Net Sharpe: **0.3–0.5** standalone long-short; correlation to CS momentum ~0.6–0.7 (sibling, not independent).
- Skew: negative (short-leg rebounds in recoveries); long leg alone (near-high names) is a surprisingly benign long-only tilt — low-beta quality-ish.
- Turnover: **lower than return momentum** (~50–80%/side/yr — the anchor moves slowly); best cost profile in the momentum family for single stocks.
- Cost sensitivity: medium-low.

## 6. Failure modes & risks

- Same family crashes (2009-Q2 type): far-below-high shorts rebound violently.
- Regime dependence: in V-shaped recoveries the *bottom* decile leads for quarters.
- The long leg concentrates in defensives/steady compounders — implicit quality/low-vol overlap; in junk rallies the long leg lags badly.
- Anchoring strength may weaken as algorithmic flow replaces retail anchor behavior (monitor rolling performance).

## 7. Backtesting guidance

- Adjusted-price discipline: the 52w high must be computed on the same adjustment basis as current price (raw-price highs against adjusted prices is a classic silent bug that fabricates signal after splits).
- Survivorship-free + delisting returns; standard momentum reporting (by decade, crash months, VW vs EW).
- Run the George-Hwang three-way horse race on your data: JT momentum vs 52w-high vs industry momentum, plus double-sorts — this determines whether it adds anything beyond your momentum sleeve *in your universe/period*, which is the actual decision.
- Check 2–5y post-formation returns: 52w-high winners should NOT show long-run reversal (validates you've isolated the anchor effect, not generic momentum).
- Minimum data: 20y+ daily.

## 8. Recommendations for use

- **Backtest priority: medium.** Cheap to add once CS momentum pipeline exists (one extra signal column). Its value is (a) lower turnover expression of momentum, (b) diagnostic variety within the family.
- Production use: as a component in a composite momentum score (e.g., average z of 12-1 return, residual IR, 52w-high proximity) rather than standalone — composites of correlated-but-distinct momentum measures are more robust than any single definition.
