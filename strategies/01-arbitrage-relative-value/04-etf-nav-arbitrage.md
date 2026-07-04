# ETF–NAV / Index Arbitrage (Creation–Redemption Logic)

## 1. Classification

- **Category:** Arbitrage / relative value (structural)
- **Asset classes:** ETFs vs their baskets — equities, fixed income, country funds; closed-end funds (cousin trade)
- **Style:** Market-neutral premium/discount capture
- **Horizon:** Intraday–weeks (equity ETFs); weeks–months (bond/country ETFs, CEFs)
- **Capacity:** Low–medium for non-AP participants
- **Complexity:** Medium; **Data burden:** daily (ideally intraday) ETF prices + iNAV/NAV, basket compositions

## 2. Economic rationale

Authorized participants (APs) can create/redeem ETF shares at NAV, so ETF price is arbitraged to basket value. The mechanism breaks — leaving premiums/discounts — when: (a) the basket is **hard to trade** (high-yield bonds, EM local markets, closed foreign markets), (b) **stress makes APs step back** (March 2020: bond ETFs at 3–5% discounts to stale NAVs), (c) **flow is one-sided** (retail piling into a niche ETF faster than APs recycle). A non-HFT trader cannot compete on the tight intraday arb (that *is* HFT), but can trade the **slower, wider dislocations**: stress discounts in bond ETFs, persistent country-fund premia, and pair-level divergence between ETFs holding near-identical baskets. Compensation: providing liquidity when APs won't — i.e., bearing exactly the liquidity risk that scared the APs. Counterparty: panicked sellers (discounts) or exuberant buyers (premiums).

Note on "stale NAV": part of any measured discount is the NAV being stale, not free money — the ETF price is often the *correct* price. The trade is that stress discounts **overshoot** fair value, which is why they revert.

## 3. Signal & rules specification

Three tradable expressions:

**A. Stress-discount reversion (bond/credit ETFs):**
- Universe: large credit ETFs (LQD/HYG-class) and their peers.
- Signal: `d_t = P/NAV − 1`. Compute rolling 1y mean/std of d (these funds have structurally nonzero average d). Enter long when `z(d) < −2.5` (range 2–3) *and* discount < −1% absolute; this fires only in genuine stress.
- Exit: z back to 0 or discount > −0.25%; time stop 1–3 months. Optional hedge: short duration/credit proxy (treasury futures / CDX-tracking instrument) if you want pure-dislocation exposure; unhedged, the trade doubles as buying credit at panic prices.

**B. Twin-ETF relative value:**
- Pairs of ETFs on near-identical exposure (same index different issuer, or 90%+ overlapping baskets). Trade the price ratio with the pairs-trading machinery (doc 01), z-entry 2, half-life filter ≤ 10 days. Cleaner than stock pairs because the fundamental linkage is contractual, not statistical.

**C. Closed-end fund discount harvesting (slow cousin):**
- Long CEFs at z-scored extreme discounts vs own history (z < −2, absolute discount < −10%), diversified 20+ funds, horizon months; activism/liquidation events are the realization catalyst.

- **Sizing:** per-position 2–5% NAV (A/C), pairs-book sizing for B. These are episodic strategies — capital is deployed opportunistically.

## 4. Evidence & key research

- Marshall, Nguyen & Visaltanachoti (2013) [A7]: ETF–NAV deviations revert within hours-days in liquid funds; wider and slower in illiquid baskets.
- March 2020 episode: investment-grade bond ETFs traded 3–5% below NAV, reverting within days once the Fed backstopped credit — the canonical stress-discount trade (documented in Fed/BIS post-mortems; [A7]-adjacent literature).
- CEF discount literature (Lee, Shleifer & Thaler 1991 onward): discounts mean-revert; extreme-discount portfolios earn abnormal returns of several % annually.
- **Decay status:** intraday arb fully professionalized (not our trade); stress-discount and CEF versions persist because they require warehousing risk at the worst times — structurally hard to crowd out.

## 5. Expected performance profile

- Episodic: years of nothing, then 2–5% NAV contributions in stress windows (A); pairs version (B) small steady Sharpe ~0.5–0.8; CEF sleeve ~mid-single-digit annual excess with equity-like drawdowns in crashes.
- Skew: positive-ish for A (buying panic, defined catalyst), negative for C (discounts widen in crashes before narrowing).
- Turnover: low (A, C), medium (B). Cost sensitivity: medium — the instruments are liquid, but stress spreads are wide (use limit orders; the width is your friend on entry).

## 6. Failure modes & risks

- **The discount is right:** in a true credit event, NAV falls to meet price — buying HY ETF discounts in a default wave loses on the basket, not the basis. Hedge or size accordingly.
- Discounts can persist/widen far longer in CEFs (no creation/redemption); catalyst-free positions decay into value traps.
- Stale-NAV illusion in backtests (see §7) — the #1 source of fake alpha in this strategy.
- Regulatory/plumbing changes (e.g., ETFs granted direct Fed support in 2020 — helped the trade then, but future policy is a wildcard).

## 7. Backtesting guidance

- **Stale-NAV bias:** for international/bond ETFs, published NAV uses stale or model prices; a naive backtest "buys the discount" that only exists on paper. Mitigate: trade signals only on z-scores of the *deviation from that fund's own typical premium/discount pattern*, lag execution one day, and validate on funds with same-time-zone baskets.
- Use primary-market data where possible (issuer NAV files); intraday iNAV only for context, not fills.
- Fill realism: assume you cross a stress-widened spread (10–50bp+ in March-2020-type days); test with fills at bid (for buys at the offer, etc.) worst-case.
- For B, all pairs-backtest hygiene from doc 01 applies (survivorship of ETF closures — many small ETFs delist).
- Data: daily P and NAV per fund (issuer/vendor), 10y+; basket overlap data for B.

## 8. Recommendations for use

- **Backtest priority: medium.** Variant A is one of the best crisis-deployment playbooks available to a non-AP participant; validating it is mostly about measuring historical dislocation depth/duration.
- Keep as a pre-researched **opportunistic playbook** with alert thresholds rather than an always-on system; combine with the cash-and-carry sleeve as "deploy in dislocations" capital.
- Variant B is a low-drama continuous strategy that reuses the pairs infrastructure.
