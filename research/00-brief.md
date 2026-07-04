---
title: "Non-HFT Trading Strategies — Research Brief"
project: trading-strategies-research
flow: universal
effort: deep
date: 2026-07-04
status: final
---

# Phase 0 — Research Brief

## Main research question

**Which non-HFT trading strategies have a credible economic rationale and sufficient documented evidence to justify a high-quality backtest, and what exactly must be specified (signals, rules, data, pitfalls) to backtest each one properly?**

## Scope

- **In scope:** systematic and semi-systematic strategies tradable at horizons from ~1 day to ~12 months, across equities, futures, FX, rates/bonds, commodities, crypto, and options/volatility.
- **Out of scope:**
  - HFT / latency-sensitive strategies (sub-second edge, queue position, co-location).
  - Strategies defined *only* by technical indicators with no market logic (e.g., "buy when RSI < 30" as the entire thesis). Indicator-like constructs are allowed only as *measurement tools* for an underlying economic effect (e.g., a moving average as a trend estimator where the edge is the documented trend premium).
  - Pure discretionary/fundamental stock picking (not specifiable for backtest).
- **Deliverable style:** logic, rationale, signal specification at pseudocode level, evidence, expected performance, failure modes, backtesting guidance, use recommendations. **No implementation code.**

## Sub-questions (one per strategy category)

| SQ | Category | Question |
|----|----------|----------|
| SQ1 | Arbitrage / relative value | Which arbitrage and RV approaches remain viable for a non-HFT participant, and what drives their spread convergence? |
| SQ2 | Momentum | Which distinct momentum formulations exist, how do they differ economically, and how much do they overlap? |
| SQ3 | Trend following | Why does trend following persist across a century of data, and what are robust non-indicator-worship implementations? |
| SQ4 | Mean reversion / swing | Where does short-horizon reversal come from (liquidity provision) and at what horizon/universe does it survive costs? |
| SQ5 | Carry | How does carry generalize across asset classes and what is the common risk being compensated? |
| SQ6 | Volatility | What is the variance risk premium, how is it harvested, and what data does that require? |
| SQ7 | Event-driven | Which announcement/flow events produce exploitable drift or pressure, and how has each decayed post-publication? |
| SQ8 | Value / factor | Which fundamental cross-sectional premia are robust enough to trade, and at what horizon? |
| SQ9 | Flows & seasonality | Which calendar/flow effects have a structural (not data-mined) cause? |
| SQ10 | Crypto-specific | Which crypto market structure edges (funding, fragmentation) are accessible without HFT infrastructure? |

## Success criteria (gate for Phase 5)

1. ≥ 40 strategy documents, ≥ 25 genuinely independent underlying approaches (independence judged by economic rationale, not implementation).
2. Every strategy has an explicit economic rationale naming the counterparty/source of edge — none justified by indicator mechanics alone.
3. Every strategy document is specific enough that a competent quant can build a backtest without further design decisions on signals, universe, or rebalancing (parameter *ranges* given, not tuned values).
4. Performance claims cite identifiable sources (paper, dataset, practitioner publication) logged in `research/01-landscape.md`.
5. `SUMMARY.md` compares all strategies on a common set of axes and gives a prioritized backtesting order.
6. Critique pass (`research/04-critique.md`) completed: decay honesty, single-source chains, overlap audit.

## Inclusion criteria per strategy

- Documented in at least one credible primary/secondary source (peer-reviewed paper, SSRN working paper with citations, or a first-tier practitioner publication — AQR, Man Institute, CFM, NBER, Fed).
- Economic rationale classifiable as: **risk premium**, **behavioral**, **structural/flow**, or **constraint/friction-based**.
- Tradable with daily OHLCV data plus, where necessary, standard add-ons (futures chains, fundamentals, corporate events, options surface — flagged per strategy).
- Realistic for a small fund / sophisticated individual (no balance-sheet-intensive strategies without a flagged caveat).

## Effort & flow notes

Effort dial: **deep** (per ROADMAP.md this requires ≥ 20 credible sources at the Phase 1 gate). Flow: `universal` — no flow switch expected; the topic is stable.
