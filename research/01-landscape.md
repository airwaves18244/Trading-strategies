---
title: "Landscape Scan — Source Log"
project: trading-strategies-research
flow: universal
phase: 1
date: 2026-07-04
---

# Phase 1 — Landscape Scan & Source Log

Credibility scale (per universal.md): **H** = primary / peer-reviewed / official (journal articles, NBER/Fed papers, exchange documentation); **M** = established secondary (top practitioner research — AQR, Man Institute, CFM, Robeco, Quantpedia summaries of papers; SSRN working papers with citation history); **L** = unverified / opinion (blogs, vendor marketing) — used only for color, never as sole support for a claim.

Gate check: **effort = deep requires ≥ 20 credible (H/M) sources** → satisfied (40+ H/M sources below).

## Cross-cutting (decay, methodology)

| ID | Source | Rating | Used for |
|----|--------|--------|----------|
| X1 | McLean & Pontiff (2016), "Does Academic Research Destroy Stock Return Predictability?", *Journal of Finance* — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2156623) | H | 26% out-of-sample / 58% post-publication decay across 97 predictors; decay worst for high in-sample return, high-liquidity anomalies |
| X2 | Harvey, Liu & Zhu (2016), "…and the Cross-Section of Expected Returns", *RFS* | H | Multiple-testing problem; t-stat > 3 hurdle for new factors |
| X3 | Bailey & López de Prado (2014), "The Deflated Sharpe Ratio", *J. Portfolio Mgmt* | H | Backtest overfitting corrections |
| X4 | Ilmanen (2011), *Expected Returns* (Wiley) | M | Taxonomy: risk premia vs mispricing; carry/trend/value/vol across assets |
| X5 | Arnott, Harvey et al. (2019), "A Backtesting Protocol in the Era of Machine Learning", *J. Financial Data Science* | H | Backtest design checklist |

## SQ1 — Arbitrage / relative value

| ID | Source | Rating | Used for |
|----|--------|--------|----------|
| A1 | Gatev, Goetzmann & Rouwenhorst (2006), "Pairs Trading: Performance of a Relative Value Arbitrage Rule", *RFS* | H | Distance-method pairs: ~11%/yr excess 1962–2002, decaying |
| A2 | Do & Faff (2010, 2012), *Financial Analysts Journal* / *JFR* | H | Pairs profitability decline post-1990s; net-of-cost attrition ([review](https://www.iwf.rw.fau.de/files/2016/03/09-2015.pdf)) |
| A3 | Krauss (2017), "Statistical arbitrage pairs trading strategies: Review and outlook", *J. Economic Surveys* | H | Taxonomy: distance, cointegration, copula, stochastic-spread methods |
| A4 | Avellaneda & Lee (2010), "Statistical arbitrage in the US equities market", *Quantitative Finance* | H | PCA/ETF-residual stat arb, s-score framework |
| A5 | Mitchell & Pulvino (2001), "Characteristics of Risk and Return in Risk Arbitrage", *J. Finance* | H | Merger arb ≈ short put on market; ~4% ann. excess after costs |
| A6 | Mitchell & Pulvino (2012), "Arbitrage crashes and the speed of capital", *JFE* | H | Convert arb 2008 dislocation; limits of arbitrage |
| A7 | Marshall, Nguyen & Visaltanachoti (2013), "ETF Arbitrage: Intraday Evidence", *JBF* | H | ETF–NAV deviations, speed of closure |
| A8 | CME/ICE contract specs & margin documentation (official) | H | Basis/calendar spread mechanics, margin offsets |
| A9 | Yale working paper, "Examining Pairs Trading Profitability" (2024) — [PDF](https://economics.yale.edu/sites/default/files/2024-05/Zhu_Pairs_Trading.pdf) | M | Recent out-of-sample pairs evidence |

## SQ2 — Momentum

| ID | Source | Rating | Used for |
|----|--------|--------|----------|
| M1 | Jegadeesh & Titman (1993), "Returns to Buying Winners and Selling Losers", *J. Finance* | H | Cross-sectional momentum 12-1; ~1%/mo gross |
| M2 | Asness, Moskowitz & Pedersen (2013), "Value and Momentum Everywhere", *J. Finance* | H | Momentum & value across 8 markets/asset classes; negative correlation |
| M3 | Moskowitz, Ooi & Pedersen (2012), "Time Series Momentum", *JFE* | H | TSMOM: 12-mo sign, vol-scaled, 58 futures; Sharpe ~1 pre-cost |
| M4 | Blitz, Huij & Martens (2011), "Residual momentum", *J. Empirical Finance* | H | Idiosyncratic momentum: similar return, ~half the vol/crash risk |
| M5 | George & Hwang (2004), "The 52-Week High and Momentum Investing", *J. Finance* | H | Anchoring-based 52w-high signal |
| M6 | Moskowitz & Grinblatt (1999), "Do Industries Explain Momentum?", *J. Finance* | H | Industry momentum |
| M7 | Gupta & Kelly (2019), "Factor Momentum Everywhere", *J. Portfolio Mgmt* (AQR) | M | Momentum in factor returns themselves |
| M8 | Antonacci (2014), *Dual Momentum Investing* + GEM papers (SSRN) | M | Relative + absolute momentum asset allocation |
| M9 | Daniel & Moskowitz (2016), "Momentum Crashes", *JFE* | H | Momentum crash dynamics; 1932/2009 episodes; vol-managed fix |
| M10 | Barroso & Santa-Clara (2015), "Momentum has its moments", *JFE* | H | Constant-vol momentum halves crash risk |
| M11 | Miffre & Rallis (2007), "Momentum strategies in commodity futures markets", *JBF* | H | Commodity CS momentum |

## SQ3 — Trend following

| ID | Source | Rating | Used for |
|----|--------|--------|----------|
| T1 | Hurst, Ooi & Pedersen (2017), "A Century of Evidence on Trend-Following Investing", *J. Portfolio Mgmt* (AQR) | M | Trend profitable in every decade since 1880; crisis alpha |
| T2 | Baltas & Kosowski (2013), "Momentum Strategies in Futures Markets and Trend-following Funds" — [PDF](https://www.naaim.org/wp-content/uploads/2013/10/00S_Momentum_Strategies_in_Futures_Markets_Nick_Baltas.pdf) | M | TSMOM explains CTA index returns; no capacity constraint found |
| T3 | AQR, "Demystifying Managed Futures" (Hurst, Ooi, Pedersen 2013) — [PDF](https://www.aqr.com/-/media/AQR/Documents/Insights/Journal-Article/Demystifying-Managed-Futures.pdf) | M | Replication of CTA returns with simple trend rules |
| T4 | Levine & Pedersen (2016), "Which Trend Is Your Friend?", *FAJ* | H | MA crossover ≈ TSMOM equivalence |
| T5 | Garleanu & Pedersen; hedging-pressure literature (Kang, Rouwenhorst & Tang 2020, *J. Finance*) | H | Who pays for trend/carry: hedgers' risk transfer |
| T6 | SG CTA / SG Trend Index performance data (Société Générale, official) + [Top Traders Unplugged reports](https://www.toptradersunplugged.com/trend-following-performance-report-april-2025/) | M | Live performance 2000–2025: +20.1% in 2022; weak 2023–2025 stretch |
| T7 | Hutchinson & O'Brien (2014), "Is This Time Different? Trend Following and Financial Crises", *JAI* | M | Post-crisis trend returns halve for ~4 years |

## SQ4 — Mean reversion / swing

| ID | Source | Rating | Used for |
|----|--------|--------|----------|
| R1 | Jegadeesh (1990) & Lehmann (1990) | H | 1-week/1-month cross-sectional reversal |
| R2 | Nagel (2012), "Evaporating Liquidity", *RFS* | H | Reversal returns = liquidity provision compensation; spike in stress |
| R3 | Lou, Polk & Skouras (2019), "A Tug of War: Overnight versus Intraday Expected Returns", *JFE* — [PDF](https://personal.lse.ac.uk/polk/research/TugOfWar.pdf) | H | Overnight/intraday return decomposition by anomaly |
| R4 | NY Fed, "The Overnight Drift" (Boyarchenko et al., Staff Report) | H | Overnight index drift concentrated in specific hours |
| R5 | Elm Wealth, "Night Moves" (2023) — [link](https://elmwealth.com/night-moves-overnight-drift/) | L→M | Post-publication waning of overnight effect (color; cross-checked vs R3/R4 rolling data) |
| R6 | Khandani & Lo (2007), "What Happened to the Quants in August 2007?" | H | Contrarian/stat-arb crowding crash |

## SQ5 — Carry

| ID | Source | Rating | Used for |
|----|--------|--------|----------|
| C1 | Koijen, Moskowitz, Pedersen & Vrugt (2018), "Carry", *JFE* | H | Universal carry definition across 9 asset classes; global carry Sharpe ~1.1 diversified (pre-cost, 1983–2012) |
| C2 | Brunnermeier, Nagel & Pedersen (2008), "Carry Trades and Currency Crashes", NBER — [PDF](https://www.nber.org/system/files/chapters/c7286/c7286.pdf) | H | FX carry crash risk, "up the stairs, down the elevator" |
| C3 | Daniel, Hodrick & Lu (2014), "The Carry Trade: Risks and Drawdowns", NBER w20433 | H | FX carry drawdown anatomy |
| C4 | Doskov & Swinkels / Filippou et al.; ScienceDirect (2021), "Currency carry trade: The decline in performance after the 2008 GFC" — [link](https://www.sciencedirect.com/science/article/abs/pii/S1042443121001670) | H | G10 carry Sharpe ~1.08 pre-GFC → ~0.25 post-GFC |
| C5 | Gorton & Rouwenhorst (2006) + Gorton, Hayashi & Rouwenhorst (2013), "The Fundamentals of Commodity Futures Returns", *Review of Finance* | H | Backwardation/inventory theory of commodity carry |
| C6 | Erb & Harvey (2006), "The Strategic and Tactical Value of Commodity Futures", *FAJ* | H | Roll yield as return driver |
| C7 | Cochrane & Piazzesi (2005); Ilmanen bond carry chapters | H/M | Bond carry & roll-down evidence |
| C8 | Macrosynergy, "Advanced FX carry strategies with valuation adjustment" — [link](https://macrosynergy.com/research/advanced-fx-carry-strategies-with-valuation-adjustment/) | M | Valuation-adjusted carry kept working in 2010s–2020s |

## SQ6 — Volatility

| ID | Source | Rating | Used for |
|----|--------|--------|----------|
| V1 | Carr & Wu (2009), "Variance Risk Premiums", *RFS* | H | VRP definition & magnitude across indices |
| V2 | Bakshi & Kapadia (2003), "Delta-Hedged Gains and the Negative Market Volatility Risk Premium", *RFS* | H | Delta-hedged short options returns |
| V3 | Bollerslev, Tauchen & Zhou (2009), "Expected Stock Returns and Variance Risk Premia", *RFS* | H | VRP predicts equity returns |
| V4 | Augustin, Cheng et al. / FAJ (2021), "Volmageddon and the Failure of Short Volatility Products" — [link](https://www.tandfonline.com/doi/abs/10.1080/0015198X.2021.1913040) | H | Feb-2018 XIV collapse mechanics; flow feedback |
| V5 | Simon & Campasano (2014), "The VIX Futures Basis: Evidence and Trading Strategies", *J. Derivatives* | H | VIX term-structure signal (contango/backwardation) |
| V6 | Barclays QIS, "Volatility Risk Premium" primer — [PDF](https://indices.cib.barclays/dms/Public%20marketing/Volatility_Risk_Premium.pdf) | M | VRP ~3–4 vol pts on SPX, positive ~85% of months |
| V7 | Moreira & Muir (2017), "Volatility-Managed Portfolios", *J. Finance* | H | Vol-timing improves Sharpe on factor portfolios |
| V8 | Driessen, Maenhout & Vilkov (2009), "The Price of Correlation Risk", *J. Finance* | H | Dispersion trade / correlation risk premium |

## SQ7 — Event-driven

| ID | Source | Rating | Used for |
|----|--------|--------|----------|
| E1 | Bernard & Thomas (1989/1990), *JAR/JAE* | H | PEAD original: ~18% ann. abnormal spread |
| E2 | Fink (2021), "A Review of the Post-Earnings-Announcement Drift", *J. Behavioral & Experimental Finance* — [WP PDF](https://static.uni-graz.at/fileadmin/sowi/Working_Paper/2020-04_Fink.pdf) | H | PEAD survey; US decay toward insignificance in large caps |
| E3 | Columbia CEASA, "Why Has PEAD Declined Over Time?" — [PDF](https://business.columbia.edu/sites/default/files-efs/imce-uploads/CEASA/Events%20Page/PEAD_Declined_over_time.pdf) | M | Earnings-news persistence explanation |
| E4 | Greenwood & Sammon (2024), "The Disappearing Index Effect", NBER w30748 / *J. Finance* — [PDF](https://www.nber.org/system/files/working_papers/w30748/w30748.pdf) | H | S&P add effect 7.4% (1990s) → ~0 (2010s–2020s) |
| E5 | Lucca & Moench (2015), "The Pre-FOMC Announcement Drift", *J. Finance* — [Fed SR512](https://www.newyorkfed.org/research/staff_reports/sr512.html) | H | 49bp/24h pre-FOMC 1994–2011 (~80% of ann. equity premium) |
| E6 | Kurov, Wolfe & Gilbert (2021), "The disappearing pre-FOMC announcement drift", *Finance Research Letters* — [link](https://www.sciencedirect.com/science/article/pii/S1544612320315956) | H | Drift gone after ~2015 |
| E7 | Ikenberry, Lakonishok & Vermaelen (1995, 2000) | H | Buyback announcement long-run drift |
| E8 | Field & Hanka (2001), "The Expiration of IPO Share Lockups", *J. Finance* | H | −1.5% abnormal return around lockup expiry, permanent volume rise |
| E9 | Cohen, Malloy & Pomorski (2012), "Decoding Inside Information", *J. Finance* | H | Opportunistic vs routine insider trades |

## SQ8 — Value / factor

| ID | Source | Rating | Used for |
|----|--------|--------|----------|
| F1 | Fama & French (1992, 1993, 2015) | H | Value/size/profitability/investment factors |
| F2 | Asness, Moskowitz & Pedersen (2013) [= M2] | H | Cross-asset value |
| F3 | Frazzini & Pedersen (2014), "Betting Against Beta", *JFE* | H | BAB: leverage-constraint premium |
| F4 | Novy-Marx (2013), "The Other Side of Value: The Gross Profitability Premium", *JFE* | H | Quality/profitability |
| F5 | Blitz & van Vliet (2007), "The Volatility Effect", *J. Portfolio Mgmt* | H | Low-vol anomaly |
| F6 | Arnott et al. (2021), "Reports of Value's Death May Be Greatly Exaggerated", *FAJ* | H | Value drawdown 2018–2020 decomposition; revaluation vs migration |
| F7 | Israel, Laursen & Richardson (2020), "Is (Systematic) Value Investing Dead?" (AQR) | M | Value spread evidence |

## SQ9 — Flows & seasonality

| ID | Source | Rating | Used for |
|----|--------|--------|----------|
| S1 | Lakonishok & Smidt (1988); McConnell & Xu (2008), "Equity Returns at the Turn of the Month", *FAJ* | H | TOM effect: bulk of equity return in ~4-day window |
| S2 | Etula, Rinne, Suominen & Vaittinen (2020), "Dash for Cash: Monthly Market Impact of Institutional Liquidity Needs", *RFS* | H | Month-end liquidity flows; predictable reversal |
| S3 | Mou (2011), "Limits to Arbitrage and Commodity Index Investment: Front-Running the Goldman Roll" (SSRN) | M | GSCI roll congestion strategy |
| S4 | Bouman & Jacobsen (2002), "The Halloween Indicator", *AER*; Jacobsen & Zhang updates | H | Sell-in-May: 65 markets, but weak US post-publication |
| S5 | Heston & Sadka (2008), "Seasonality in the Cross-Section of Stock Returns", *JFE* | H | Same-calendar-month return seasonality |
| S6 | Hartzmark & Solomon (2013), "The Dividend Month Premium", *JFE* | H | Predicted-dividend-month abnormal returns |

## SQ10 — Crypto-specific

| ID | Source | Rating | Used for |
|----|--------|--------|----------|
| K1 | Ackerer, Hugonnier & Jermann (2023+), "Perpetual Futures Pricing" — [Wharton PDF](https://finance.wharton.upenn.edu/~jermann/AHJ-main-10.pdf) | H | Perp funding mechanics & no-arbitrage pricing |
| K2 | Exchange documentation: Binance/Bybit/Deribit/dYdX funding-rate specs (official) | H | Funding formulas, intervals, clamps |
| K3 | ScienceDirect (2025), "Risk and Return Profiles of Funding Rate Arbitrage on CEX and DEX" — [link](https://www.sciencedirect.com/science/article/pii/S2096720925000818) | H | Live risk/return of funding arb; CEX price leadership |
| K4 | Makarov & Schoar (2020), "Trading and Arbitrage in Cryptocurrency Markets", *JFE* | H | Cross-exchange arb spreads, capital controls, kimchi premium |
| K5 | arXiv (2025), "Designing funding rates for perpetual futures" — [link](https://arxiv.org/html/2506.08573v1) | M | Funding design & basis behavior |

## Landscape conclusions feeding Phase 2

1. **Decay is the central fact.** Post-publication decay averages ~50% for equity cross-sectional anomalies (X1); several once-famous effects are now near zero (index effect E4, pre-FOMC E6, overnight drift R5, raw G10 FX carry C4). Every strategy doc must carry an explicit decay status.
2. **The most durable edges are macro-consistent risk premia** harvested across many markets (trend, carry, VRP, momentum) — they survive because they pay for bearing real risk (crash/skew/liquidity), not because they are secrets.
3. **Structural/flow edges persist while the flow persists** (index rebalancing died as flows got smarter; funding-rate arb lives while retail leverage demand lives).
4. **Costs decide viability at short horizons.** Weekly reversal, PEAD in small caps, and pairs trading are cost-dominated; the backtest design must treat costs as first-class.
