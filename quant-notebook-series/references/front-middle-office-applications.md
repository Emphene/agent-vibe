# Front and middle office applications

Read before writing section 6 of any notebook. The series does not stop at "QuantLib returns a number": every notebook shows what a desk does with that number. A QuantLib object that never reaches a desk-consumable output is only half demonstrated. The reader is a practitioner (quant, trader, structurer, risk manager, product controller, validator) who wants to see how it is done, what each object exposes, and what the output is used for.

## Contents
1. Desk map
2. Catalogue by theme
3. Desk-grade outputs
4. Control patterns
5. Frameworks and regulatory context
6. Desk function x theme matrix
7. Writing section 6

---

## 1. Desk map

| Desk | What it decides | Typical outputs consumed | Cadence |
|---|---|---|---|
| **Front office** | | | |
| Trading and market making | quote, trade, hedge | prices, implied vols, risk ladders, hedge ratios, intraday P&L | intraday |
| Structuring and sales | what to offer a client and at what margin | fair value, payoff scenarios, indicative prices | per deal |
| Quant strats | which model, numerics and calibration are used | calibrated parameters, pricing library, convergence studies | ongoing |
| XVA and funding desk | what charge and hedge cover credit, funding and capital | XVA stack, XVA sensitivities, exposure profiles | intraday to daily |
| **Middle office** | | | |
| Market risk | is risk within appetite | VaR/ES, stress results, sensitivity limits, backtests | daily |
| Counterparty credit risk | can we trade with this counterparty | exposure profiles, PFE vs limit, pre-deal checks | daily, per deal |
| Product and valuation control | are the marks and the P&L right | IPV results, P&L explain, reserves, breaks | daily, monthly |
| Model risk and validation | can the model be relied upon | benchmarks, replication tests, parameter stability, limitations | per model, periodic |
| Collateral and margin | how much collateral moves | margin calls, disputes, netting-set statements | daily |
| Risk reporting and limits | who is told what, when | limit utilisation, escalations, aggregated reports | daily |

Out of scope unless the user asks: back office (confirmation, settlement, accounting entries) and treasury / ALM.

## 2. Catalogue by theme

For each (instrument, theme) build **every applicable row**, or list the skipped ones with a reason in the coverage cell of section 6. Pick the QuantLib features from `theme-ladder.md` so the application is also a feature demonstration.

| Theme | Front office application | Middle office application | Desk output | Control |
|---|---|---|---|---|
| T1 Product anatomy | term-sheet capture; client payoff scenario table | trade validation: independent cash-flow projection vs booked schedule | cash-flow table; payoff scenarios | schedule equality; date and calendar breaks |
| T2 QuantLib modeling | curve and surface build for marking; single vs OIS curve impact | market-data validation: curve reprices its inputs, independent rebuild, stale or outlier quote detection (full pipeline in T12) | curve difference table (bp); instrument repricing errors | tolerance in bp; outlier threshold |
| T3 Pricing | quote sheet (price and implied vol, both directions); pricing ladders; what-if pricing | IPV against an independent engine or method; first valuation-reserve estimate from model spread (full framework in T13) | blotter: desk mark, independent price, difference, tolerance, status | relative and absolute tolerance; breach flag |
| T4 Sensitivities | trader risk ladder (delta, gamma, vega by bucket); hedge ratios | sensitivity limits and utilisation; reconciliation of desk vs independent risk (bump conventions) | risk ladder; limit table | limit utilisation; reconciliation tolerance |
| T5 Hedging | hedging policy design: rebalancing rule vs cost; slippage vs the price quoted to the client | residual-risk and hedge-slippage monitoring | hedge P&L distribution summary; cost vs frequency table | slippage limit; frequency policy |
| T6 P&L attribution | P&L explain to the trader (theta, delta, gamma, vega, rho, residual) | product control sign-off; unexplained P&L thresholds; event and new-trade P&L | P&L explain by driver; unexplained as % of total | explain threshold; escalation |
| T7 Risk factors | daily calibration; parameter stability; model choice by payoff | model validation: calibration error vs tolerance, benchmark vs a second model, out-of-sample check (full framework in T13) | calibration report (market vs model vols); parameter history | RMSE tolerance; parameter bounds |
| T8 Market risk | pre-trade what-if risk (incremental VaR) | daily VaR/ES by desk and factor; stress tests; backtesting; risk decomposition; limit monitor | VaR/ES table; stress table; exception chart | limits; exception count vs expectation |
| T9 Counterparty credit risk | pre-trade counterparty limit check (incremental PFE) | exposure reporting; PFE vs limit; EEPE (regulatory EAD benchmarks in T14) | EE/PFE table by date; limit utilisation | PFE vs limit; EEPE monotonicity |
| T10 Netting and collateral | effect of CSA terms and collateral funding on price | margin call calculation; dispute analysis; netting-benefit reporting | margin call statement; netting-benefit table | threshold, MTA and rounding rules; dispute tolerance |
| T11 XVA | pre-trade XVA quote (charge on top of fair value); XVA sensitivities for hedging (CS01, rate delta) | XVA P&L explain; reserve review; double-counting checks (CVA capital benchmark in T14) | XVA stack; sensitivity ladder | monotonicity in spread and recovery; reconciliation |
| T12 Market data and calibration | daily curve and surface build for marking; interpolation choice and its effect on forwards and risk; calibration with warm start and parameter-stability alerts | independent market-data rebuild vs front office; data-quality controls (stale, outlier, arbitrage); snapshot versioning; shocked snapshots for risk | curve and surface difference tables (bp, vol points); calibration report; data-quality exceptions | tolerance in bp and vol points; arbitrage flags; parameter bounds |
| T13 Valuation control and model risk | model-choice defence for exotics; day-one P&L and bid-offer view | IPV with escalation; valuation reserves (model, parameter, bid-offer); model validation tests; model change impact on a book; limitation register | IPV blotter; reserve table by trade; model-comparison table; model change impact table | tolerance bands by product; parity and limit-case checks; reserve methodology stated |
| T14 Regulatory capital and margin | capital and margin cost in pricing (capital per trade, KVA and MVA inputs); clearing vs bilateral and compression what-ifs | market-risk capital by risk class; P&L attribution test by desk; SA-CCR EAD vs EEPE; CVA capital benchmark; IM and VM calls and forecasts | capital by risk class; PLA test table with zone; EAD comparison; margin call statement | aggregation limit checks; test statistics vs illustrative thresholds; illustrative-parameter labels |

## 3. Desk-grade outputs

A desk output is a table or plot someone could act on. Conventions:

- **Blotter style:** one row per trade, or per risk factor, or per date. Always show trade or factor id, currency, units, sign convention (long/short, pay/receive), as-of date and a market-data label.
- **Numbers:** stated units (price, vol in %, bp, base-currency amount), consistent decimals, signs explained once.
- **Status column** for every control: `OK`, `WARN`, `BREACH`, with the threshold shown next to the value, and a `mo.callout` summarising counts and the action ("escalate to desk for re-mark").
- **Parameters, not magic numbers:** tolerances, limits and warning levels are entries in `params`, labelled **illustrative**, never presented as policy.
- **Synthetic and simplified, said plainly:** data is synthetic; methodologies are simplified; results are not production risk figures. Planted breaks (to show a control firing) are labelled as planted.
- **One call, published functions:** compute with the functions published by this and earlier notebooks, never with re-implemented copies.

## 4. Control patterns

| Pattern | Rule of thumb |
|---|---|
| Tolerance band | `abs(diff) <= max(abs_tol, rel_tol * abs(reference))`; show both parts. A relative-only tolerance misbehaves near zero. |
| Limit utilisation | `usage = metric / limit`; `OK` below the warning level, `WARN` above it, `BREACH` above 100%. |
| Reconciliation break | list only items outside tolerance, with a hand-reasoned likely cause (bump size, day count, curve, calendar). |
| Independent calculation | a different engine, method or implementation. Say how independent it is (same library, different engine is weaker than a different library). |
| Escalation | each status maps to an action in the callout text; no silent pass. |
| Reproducibility | print the as-of date, seed and market-data label next to every desk output. |

## 5. Frameworks and regulatory context

Use framework names to place the output in a desk workflow, not as authority.

| Term | Meaning | Use in notebooks |
|---|---|---|
| IPV | independent price verification of desk marks | T3 blotter; T13 full framework |
| Valuation adjustments / prudent valuation | reserves and adjustments to fair value for model, market-price and other uncertainty | T13: spread across engines or models, bid-offer and parameter uncertainty as reserve estimates (conceptual) |
| FRTB | market-risk capital framework: sensitivities-based method, internal models with expected shortfall, P&L attribution test | T4 and T8 inputs; T6 hypothetical vs risk-theoretical P&L; T14 aggregation and P&L attribution test |
| SA-CCR, IMM | standardised and internal-model approaches to counterparty exposure; EEPE | T9 EEPE vs T14 SA-CCR EAD |
| CVA capital | basic and standardised CVA approaches | T11 inputs, T14 benchmark |
| CSA, VM, IM, MTA, MPoR | collateral agreement terms and margin mechanics | T10 |
| SIMM | standard initial margin model for uncleared derivatives | T4 sensitivities, T14 simplified IM, T10 margin mechanics |
| Fair-value hierarchy, day-one P&L | classification of valuations by observability of inputs; treatment of the gap between transaction price and model value | T13 (conceptual) |
| Model risk management | model inventory, validation, ongoing monitoring, limitations | T13 (structure only) |

**Rule:** do not hard-code regulatory parameters (multipliers, supervisory factors, risk weights, confidence levels, add-ons) from memory. Either take them from the current rule text (web search, or a source the user provides) and cite it, or expose them as parameters labelled illustrative. Every regulatory-flavoured computation is titled "simplified, illustrative, not for regulatory use".

## 6. Desk function x theme matrix

| Desk | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 | T9 | T10 | T11 | T12 | T13 | T14 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trading and market making |  | x | x | x | x | x |  |  |  |  |  | x |  | x |
| Structuring and sales | x |  | x |  | x |  |  |  |  | x | x |  |  | x |
| Quant strats |  | x | x |  |  |  | x |  |  |  |  | x | x |  |
| XVA and funding desk |  |  |  |  |  |  |  |  | x | x | x |  |  | x |
| Market risk |  |  |  | x |  | x | x | x |  |  |  | x |  | x |
| Counterparty credit risk |  |  |  |  |  |  |  |  | x | x | x |  |  | x |
| Product and valuation control | x | x | x |  |  | x |  |  |  |  | x | x | x |  |
| Model risk and validation |  |  | x | x |  |  | x | x | x |  |  | x | x |  |
| Collateral and margin |  |  |  |  |  |  |  |  |  | x |  |  |  | x |

When asked for a whole programme, produce this matrix next to the instrument x theme matrix and confirm both before building.

## 7. Writing section 6

1. **Select** the applicable rows of the catalogue for this (instrument, theme). Be exhaustive: cover each, or list it as skipped with a reason.
2. **One block per application:** one or two lines of context (who uses it, when, why), the computation with published functions, the desk output (table or plot), the control and status, and a one-line "what the desk does next".
3. **Draw the workflow once:** a Mermaid diagram with subgraphs "Front office" and "Middle office" showing who produces and who consumes each output, where the control sits and where breaches go (`mermaid-diagrams.md`).
4. **Close with a coverage cell:** desk, application, status (covered above, covered in another section, skipped with reason).
5. **Size:** about 8 cells per application at most. If the notebook grows past roughly 45 cells or runs slowly, split by sub-theme with a letter suffix in the theme code (`vanilla_swap_t9a_exposure.py`, `vanilla_swap_t9b_limits.py`) and record both in `notebooks/README.md`, instead of cutting coverage.
6. **Publish** reusable desk logic (tolerance check, limit utilisation, margin call calculation) as `@app.function` in the notebook that first needs it; promote to `common/` only when it is instrument-agnostic and used from several notebooks.
