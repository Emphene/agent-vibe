# Theme ladder, instrument ladder, coverage matrix

## Contents
1. Theme ladder (T1-T14)
2. Instrument ladder
3. Coverage matrix
4. Notation
5. Naming and numbering

Each theme lists its dependencies and assumes those. T12 to T14 are the desk-process themes (market data and calibration, valuation control and model risk, regulatory capital and margin): they consume the outputs of the earlier themes. A notebook for (instrument, theme Tk) may reuse any earlier theme's code for the same or a simpler instrument, so link back instead of repeating. Each theme lists its **QuantLib features** (the objects to demonstrate; names verified against QuantLib-Python 1.44, re-check on other versions by running) and its **Desk applications** (front office FO, middle office MO; the full catalogue with outputs and controls is in `front-middle-office-applications.md`), alongside its recommended **Diagrams** (Mermaid, for structure; details in `mermaid-diagrams.md`), alongside its matplotlib **Plots**. Reuse is by **importing code** (never embedding): from the earlier notebook that defines it when the code is instrument- or theme-specific, from `common/` when it is generic (see `code-reuse-by-import.md`).

---

## 1. Theme ladder

### T1 Product anatomy
**Scope:** the contract fully specified without any pricing model: terms, cash flows, payoff, conventions, life-cycle events.
**Content:** term sheet fields, legs, notional, dates, conventions, payoff formula, payoff/cash-flow diagram, who pays what and when.
**QuantLib features:** `Date`, `Period`, `Calendar` (e.g. `TARGET`), `DayCounter`, business-day conventions, `Schedule` / `MakeSchedule`, `FixedRateLeg` / `IborLeg`, `CashFlows` (`accruedAmount`, `nextCashFlowDate`), `PlainVanillaPayoff`, exercise classes (`EuropeanExercise`, `AmericanExercise`, `BermudanExercise`).
**Desk applications:** FO: term-sheet capture, client payoff scenarios. MO: trade validation (independent cash-flow projection vs booked schedule).
**Validation:** hand-computed cash flows for a small example match a schedule table.
**Plots:** payoff at maturity, cash-flow timeline.
**Diagrams:** parties and legs, who pays what to whom (`sequenceDiagram`); optional contract life cycle (`timeline`).
**Depends on:** none.

### T2 QuantLib modeling
**Scope:** the instrument, market data and term structures built and inspected in QuantLib, every component visible.
**Content:** `Calendar`, `DayCounter`, `BusinessDayConvention`, `Schedule`, `Date`, term structures and `Handle`/`Quote`, instrument classes, leg construction, printing cash flows.
**QuantLib features:** `Settings` (evaluation date), `SimpleQuote` / `QuoteHandle` / `RelinkableYieldTermStructureHandle`, `FlatForward`, curve bootstrapping (`DepositRateHelper`, `FraRateHelper`, `SwapRateHelper`, `OISRateHelper` with `PiecewiseLogLinearDiscount`, `PiecewiseLinearZero`, `PiecewiseCubicZero`, `PiecewiseFlatForward`), indices (`Euribor6M`, `Sofr`, `Estr`), `BlackConstantVol`, `BlackVarianceSurface`, instruments (`VanillaOption`, `MakeVanillaSwap`, `FixedRateBond`, `ZeroCouponBond`, `ForwardRateAgreement`, `FxForward`; availability depends on the QuantLib-Python version, check by running).
**Desk applications:** FO: curve and surface build for marking, single vs OIS impact. MO: market-data validation (curve reprices its inputs, independent rebuild, stale or outlier quotes; full pipeline in T12).
**Validation:** QuantLib cash-flow table equals the T1 hand computation.
**Plots:** schedule/cash-flow chart, curve plot.
**Diagrams:** object dependency graph Quote -> Handle -> TermStructure -> Process (`flowchart LR`); optional four-layer stack, instrument class hierarchy.
**Depends on:** T1.

### T3 Pricing
**Scope:** valuation with a justified model and engine, cross-checked against independent numerical methods.
**Content:** mathematical framework (risk-neutral valuation, numeraire, measure), payoff and cash-flow valuation, model choice, engine choice, QuantLib NPV, comparison of at least two numerical methods where relevant (analytic, MC, PDE/tree).
**QuantLib features:** equity/FX engines `AnalyticEuropeanEngine`, `MCEuropeanEngine`, `FdBlackScholesVanillaEngine`, `BinomialVanillaEngine`; American `BaroneAdesiWhaleyApproximationEngine`, `BjerksundStenslandApproximationEngine`, `MCAmericanEngine`; barrier `AnalyticBarrierEngine`; rates `DiscountingBondEngine`, `DiscountingSwapEngine`, `BlackSwaptionEngine`, `BachelierSwaptionEngine`, `BlackCapFloorEngine`, `BachelierCapFloorEngine`; smile `HestonProcess` + `HestonModel` + `AnalyticHestonEngine` (characteristic-function pricing); `impliedVolatility`.
**Desk applications:** FO: quote sheet (price and implied vol, both directions), pricing ladders, what-if pricing. MO: IPV against an independent engine, tolerance bands, first valuation-reserve estimate from the model spread (full framework in T13).
**Validation:** closed form vs engine vs MC (with standard error), put-call parity or par-rate consistency, tolerances shown.
**Plots:** price vs spot/strike/vol, convergence of MC or tree, price decomposition (intrinsic vs time value).
**Diagrams:** contract-to-NPV pipeline with imported vs new layers; engine-choice decision tree; optional valuation chain (payoff -> expectation under Q -> discounting).
**Depends on:** T1, T2.

### T4 Sensitivities
**Scope:** first- and second-order risk, analytic and bump-and-reval, with documented bump conventions.
**Content:** analytic vs bump-and-reval Greeks, bump size and scheme (forward/central, absolute/relative), DV01 and key-rate durations, vega and vega surface, cross-gamma for multi-asset, bumping through `Handle`s.
**QuantLib features:** engine Greeks (`delta`, `gamma`, `vega`, `theta`, `rho`), bump-and-reval through `SimpleQuote`, `CashFlows.bps`, `BondFunctions` (`duration`, `convexity`, `basisPointValue`), key-rate bumps through rate-helper quotes on a re-bootstrapped curve, vol bumps through the `BlackConstantVol` quote handle, `ZeroSpreadedTermStructure` for parallel shifts.
**Desk applications:** FO: trader risk ladders, hedge ratios. MO: sensitivity limits and utilisation, reconciliation of desk vs independent risk (bump conventions).
**Validation:** analytic vs finite-difference Greeks across bump sizes (stability plot).
**Plots:** Greek profiles vs spot and time, bucketed rate risk, vega surface.
**Diagrams:** Greek family map (what each differentiates with respect to; analytic vs bumped); optional bump-and-reval workflow with restore.
**Depends on:** T3.

### T5 Hedging
**Scope:** hedge construction, discrete-rebalancing simulation and residual risk.
**Content:** delta, gamma and vega hedges, hedge instruments, discrete rebalancing simulation, transaction costs (optional), hedge error distribution, dependence on rebalancing frequency and volatility mismatch.
**QuantLib features:** `GeometricBrownianMotionProcess`, `TimeGrid`, `GaussianRandomSequenceGenerator` / `UniformRandomSequenceGenerator`, `GaussianPathGenerator`, `SobolRsg`; repricing along a path by moving `Settings` evaluation date and market quotes.
**Desk applications:** FO: hedging policy design (rebalancing rule vs cost, slippage vs the client price). MO: residual-risk and hedge-slippage monitoring.
**Validation:** hedge error shrinks with rebalancing frequency at the expected rate; zero error in the degenerate case.
**Plots:** one simulated hedge path, hedge-error histogram, error vs frequency.
**Diagrams:** rebalancing loop (`stateDiagram-v2`); optional hedge-instrument ladder (delta, + gamma, + vega).
**Depends on:** T3, T4, `common/sim.py`.

### T6 Daily P&L attribution
**Scope:** two-date revaluation and attribution of the daily P&L move by risk factor, with the unexplained residual.
**Content:** two-date revaluation, Taylor attribution (theta/carry, delta, gamma, vega, rho, cross terms), full-revaluation vs sensitivity-based attribution, unexplained residual and what drives it.
**QuantLib features:** evaluation-date roll with `Settings`, full revaluation across two market snapshots (`SimpleQuote.setValue`), engine Greeks for the Taylor terms, curve re-bootstrap or `ZeroSpreadedTermStructure`, `CashFlows` events (fixings, payments) between the two dates.
**Desk applications:** FO: P&L explain for the trader. MO (product control): P&L sign-off, unexplained thresholds, event and new-trade P&L.
**Validation:** components sum to total P&L; residual shown and discussed.
**Plots:** P&L waterfall, residual vs size of market move.
**Diagrams:** attribution pipeline, two-date revaluation -> Taylor terms -> residual; optional full-revaluation vs sensitivity-based comparison.
**Depends on:** T4.

### T7 Risk factors
**Scope:** risk-factor models, calibration to market instruments, correlation structure and path generation.
**Content:** factor choice per asset class (GBM, Heston, SABR for equity/FX/vol; Hull-White, CIR for rates; credit intensity), calibration to market instruments, correlation structure, path generation, sanity checks on simulated marginals.
**QuantLib features:** `HestonProcess` / `HestonModel` / `HestonModelHelper`; `HullWhite` / `HullWhiteProcess` / `SwaptionHelper` / `JamshidianSwaptionEngine`; `G2`, `Gsr`, `CoxIngersollRoss`; calibration (`calibrate` with `LevenbergMarquardt` and `EndCriteria`); smiles and surfaces (`sabrVolatility`, `SabrSmileSection`, `BlackVarianceSurface`, `LocalVolSurface`, `SwaptionVolatilityMatrix`); simulation (`StochasticProcessArray`, `GaussianMultiPathGenerator`, `GaussianPathGenerator`, `SobolRsg`).
**Desk applications:** FO: daily calibration, parameter stability, model choice by payoff. MO: model validation (calibration error vs tolerance, benchmark against a second model, out-of-sample check; full framework in T13).
**Validation:** simulated moments and zero-coupon prices match analytic values; calibration error table.
**Plots:** fan charts, marginal distributions, correlation heatmap, calibrated vs market vols.
**Diagrams:** factor hierarchy, asset class -> model -> calibration instruments; optional model-choice tree, simulation pipeline.
**Depends on:** T3 (models), `common/sim.py`.

### T8 Market risk
**Scope:** VaR and ES by historical and Monte Carlo methods, full revaluation vs approximation, backtesting.
**Content:** historical vs Monte Carlo VaR, full revaluation vs delta-gamma approximation, horizon scaling, ES, backtesting (exceptions, traffic-light), limits of each approach.
**QuantLib features:** `RiskStatistics` (`valueAtRisk`, `expectedShortfall`), `IncrementalStatistics`; full revaluation of scenarios vs delta-gamma from engine Greeks; scenario paths from `GaussianMultiPathGenerator`.
**Desk applications:** FO: pre-trade what-if risk (incremental VaR). MO: VaR/ES reporting, stress tests, backtesting, risk decomposition, limit monitoring.
**Validation:** MC VaR converges to a known closed form for a linear position; backtest exception count vs expectation.
**Plots:** P&L distribution with VaR/ES marked, rolling VaR vs realised P&L, exception chart.
**Diagrams:** VaR pipeline, scenarios -> revaluation -> P&L distribution -> VaR/ES; optional historical / MC / delta-gamma choice tree.
**Depends on:** T4, T6, T7.

### T9 Counterparty credit risk
**Scope:** forward exposure simulation and the CCR metrics EE, PFE, EPE, EEPE.
**Content:** simulate risk factors forward, reprice on a time grid, exposure `max(V,0)`, EE, PFE at a quantile, EPE, EEPE (effective, non-decreasing EE), exposure for linear vs optional products, wrong-way risk (conceptual).
**QuantLib features:** `HullWhite` (`discountBond`) with `HullWhiteProcess` for state simulation, `TimeGrid`, revaluation on grid dates by moving `Settings` evaluation date and building a `ZeroCurve` / `DiscountCurve` per path and date, `DiscountingSwapEngine`, `Calendar.advance`.
**Desk applications:** FO: pre-trade counterparty limit check. MO: exposure reporting, PFE vs limit utilisation, EEPE (regulatory EAD benchmarks in T14).
**Validation:** forward example against analytic exposure (e.g. FX forward EE), convergence in paths, EEPE from EE per regulatory definition.
**Plots:** EE/PFE profiles, exposure fan, EPE vs EEPE.
**Diagrams:** exposure pipeline, simulate -> reprice on time grid -> max(V,0) -> EE/PFE/EPE/EEPE; optional linear vs optional product exposure, wrong-way risk links.
**Depends on:** T3, T7.

### T10 Netting and collateral
**Scope:** netting sets, CSA terms, margin period of risk and the exposure benefit of netting and collateral.
**Content:** netting sets, portfolio exposure `max(sum V_i, 0)` vs `sum max(V_i,0)`, CSA terms (threshold, MTA, independent amount), margin period of risk, collateralised exposure simulation, residual exposure.
**QuantLib features:** shared market objects across trades (one set of handles), portfolio repricing on a common `TimeGrid`, `Calendar.advance` / `businessDaysBetween` for call dates and margin period of risk, CSA discounting by passing a different discount curve to `DiscountingSwapEngine`.
**Desk applications:** FO: effect of CSA terms and collateral funding on price. MO: margin call calculation, dispute analysis, netting-benefit reporting.
**Validation:** netted exposure <= gross; fully collateralised, zero-MPoR limit gives zero exposure.
**Plots:** gross vs net vs collateralised EE/PFE, netting benefit vs correlation, threshold sensitivity.
**Diagrams:** netting-set hierarchy with and without agreement; optional margin call lifecycle (`sequenceDiagram`), margin period of risk (`timeline`).
**Depends on:** T9.

### T11 XVA
**Scope:** CVA, DVA, FVA, MVA, KVA with credit and funding inputs, netting-set and incremental XVA.
**Content:** CVA, DVA, bilateral CVA, FVA, MVA, KVA (conceptual plus numerical where tractable), credit curves and recovery, discounting exposure profiles, netting-set level XVA and incremental/marginal XVA, model risk and double counting.
**QuantLib features:** `FlatHazardRate`, `PiecewiseFlatHazardRate` bootstrapped from `SpreadCdsHelper`, `CreditDefaultSwap` priced with `MidPointCdsEngine` / `IsdaCdsEngine`, `DefaultProbabilityTermStructureHandle` (`survivalProbability`, `defaultProbability`, `hazardRate`), discount curves from T2.
**Desk applications:** FO (XVA desk): pre-trade XVA quote, XVA hedges (CS01, rate delta). MO: XVA P&L explain, reserve review, double-counting checks (CVA capital benchmark in T14).
**Validation:** unilateral CVA against a closed form for a simple profile; XVA monotone in spread and recovery.
**Plots:** CVA integrand, XVA stack, sensitivity to CDS spread.
**Diagrams:** XVA stack and what each adjustment prices; optional cash-flow sequence between bank, counterparty and funding desk.
**Depends on:** T9, T10.

### T12 Market data and calibration management
**Scope:** building, validating, versioning and stressing the market data desks mark against: curves, surfaces, correlations and calibrated model parameters.
**Content:** quote ingestion and cleaning (stale, outlier and missing quotes, fallbacks); curve construction choices (instrument set, interpolation, single vs multi-curve) and their effect on forwards and risk; volatility surface construction and static-arbitrage checks (calendar, butterfly); calibration workflow (initial guess, constraints, optimiser, end criteria, warm start from the previous day); calibration quality and parameter stability across days; market-data snapshots (as-of date, snapshot id, relinking) and reproducibility; shocked snapshots handed to risk (T4, T8).
**QuantLib features:** `RelinkableYieldTermStructureHandle`, `RelinkableQuoteHandle`, `RelinkableBlackVolTermStructureHandle`; helpers (`DepositRateHelper`, `FraRateHelper`, `FuturesRateHelper`, `SwapRateHelper`, `OISRateHelper`, `FixedRateBondHelper`) with `PiecewiseLogLinearDiscount`, `PiecewiseLinearZero`, `PiecewiseCubicZero`, `PiecewiseFlatForward`; `ZeroCurve`, `DiscountCurve`, `ForwardCurve`; bond curve fitting (`FittedBondDiscountCurve` with `NelsonSiegelFitting` or `SvenssonFitting`); surfaces (`BlackVarianceCurve`, `BlackVarianceSurface`, `LocalVolSurface`, `SabrSmileSection`, `sabrVolatility`, `SwaptionVolatilityMatrix`); calibration (`HestonModelHelper`, `SwaptionHelper`, `calibrate`, `LevenbergMarquardt`, `Simplex`, `EndCriteria`, `PositiveConstraint`, `BoundaryConstraint`, `params` to read parameters back); shocked and rolled curves (`ZeroSpreadedTermStructure`, `ForwardSpreadedTermStructure`, `ImpliedTermStructure`).
**Desk applications:** FO: daily curve and surface build for marking, interpolation choice and its effect on forwards and risk, calibration run with warm start and parameter-stability alerts. MO: independent market-data rebuild compared with the front-office build (difference in bp), data-quality controls (stale, outlier, arbitrage), snapshot versioning and reproducibility, shocked snapshots for risk.
**Validation:** each curve reprices its input instruments within tolerance; the surface has non-decreasing total variance in maturity and non-negative butterfly on the grid; calibration recovers known parameters from model-generated synthetic quotes; the same snapshot gives an identical NPV on rebuild.
**Plots:** zero and forward curves by interpolation; vol surface slices; calibration fit (market vs model vols); parameter history.
**Diagrams:** market-data pipeline, raw quotes -> cleaning -> helpers -> curve or surface -> calibrated model -> snapshot (`flowchart LR`); optional calibration loop (`stateDiagram-v2`).
**Depends on:** T2, T7.

### T13 Valuation control and model risk
**Scope:** independent price verification, valuation reserves and the model-risk lifecycle: benchmarking, replication, model and parameter uncertainty, limitations.
**Content:** IPV framework (price-source hierarchy, tolerance by product and liquidity, escalation); alternative engines and models on the same instrument and the price range they imply; valuation reserves (model uncertainty, parameter uncertainty, bid-offer or close-out); day-one P&L (transaction price vs model value) and the fair-value hierarchy by input observability (conceptual); model validation tests (replication of calibration instruments, convergence, limit cases, static-arbitrage and parity checks, Greek stability); model change impact on a book; model inventory and limitation register (structure only).
**QuantLib features:** several engines on one instrument (`AnalyticEuropeanEngine`, `FdBlackScholesVanillaEngine`, `BinomialVanillaEngine`, `MCEuropeanEngine`; barrier `AnalyticBarrierEngine`, `FdBlackScholesBarrierEngine`, `BinomialBarrierEngine`, `MCBarrierEngine`, `FdHestonBarrierEngine`); alternative models (`HestonModel` with `AnalyticHestonEngine` or `FdHestonVanillaEngine`; local volatility from `BlackVarianceSurface` / `LocalVolSurface` through the `localVol` option of the finite-difference Black-Scholes engines); `BarrierOption` with `Barrier` types for in/out parity; `impliedVolatility`; bid and ask inputs as paired `SimpleQuote`s; re-running `calibrate` under shifted inputs for parameter uncertainty.
**Desk applications:** FO: model-choice defence for exotics, day-one P&L and bid-offer view. MO (valuation control): IPV with escalation, valuation reserves (model, parameter, bid-offer), model validation (benchmark, limit cases, arbitrage checks), model change impact on a book, model inventory and limitation register.
**Validation:** put-call parity; call price convex in strike; knock-in plus knock-out equals the vanilla for zero rebate (agrees to machine precision with `AnalyticBarrierEngine`); limit cases (maturity to 0 gives intrinsic, vol to 0 gives the discounted forward intrinsic); independent engines agree within shown tolerances; PDE grid and MC path convergence.
**Plots:** price by model across strikes with the spread (reserve band); PDE and MC convergence; in/out parity error; reserve by trade.
**Diagrams:** valuation-control workflow, price-source hierarchy -> tolerance -> escalate -> reserve (`flowchart`); optional model lifecycle (`stateDiagram-v2`: development, validation, approval, monitoring, recalibration or retirement).
**Depends on:** T3, T4, T7, T12.

### T14 Regulatory capital and margin
**Scope:** capital and margin metrics built from earlier risk outputs, with the regulatory aggregation written out explicitly and titled simplified, illustrative, not for regulatory use.
**Content:** market-risk capital (sensitivities-based aggregation: risk classes, buckets, risk weights, within- and across-bucket correlation, delta, vega and curvature; expected-shortfall charges and liquidity-horizon scaling, conceptual; P&L attribution test comparing hypothetical and risk-theoretical P&L with a rank-correlation and a distribution-distance statistic, and desk-eligibility zones); counterparty capital (SA-CCR EAD for a netting set: replacement cost, add-on, multiplier, shown next to the T9 EEPE; CVA capital, simplified); margin (initial margin by a sensitivity-based method in the style of SIMM and by simulated margin-period-of-risk P&L; variation margin; IM and VM call forecasts). Every risk weight, correlation, supervisory factor, threshold and confidence level is an **illustrative parameter** or cited from the current rule text, never taken from memory (`front-middle-office-applications.md`, section 5).
**QuantLib features:** QuantLib has no regulatory-capital engine; it supplies the inputs: sensitivities (engine Greeks, `CashFlows.bps`, bump-and-reval through `SimpleQuote`), scenario revaluation, `RiskStatistics.expectedShortfall`, exposure profiles from T9 (`HullWhite`, `DiscountingSwapEngine`), `Calendar.advance` for margin-period-of-risk dates, `FlatHazardRate` / `CreditDefaultSwap` for CVA inputs. The regulatory aggregation is explicit numpy code, published as `@app.function`.
**Desk applications:** FO: capital and margin cost in pricing (capital per trade, incremental capital feeding KVA, IM funding feeding MVA), clearing vs bilateral and compression what-ifs. MO: market-risk capital report by risk class, P&L attribution test status per desk, SA-CCR EAD vs IMM EEPE, CVA capital benchmark, IM calculation and IM/VM call forecast, netting-set and desk capital reports with data lineage.
**Validation:** aggregation limits (correlation 1 gives the sum of the charges, correlation 0 the root of the sum of squares, diversification benefit never negative); charge monotone in sensitivities; SA-CCR EAD reproduces a hand computation on a one-trade netting set; IM from scaled sensitivities close to IM from the simulated margin-period-of-risk P&L tail (difference explained); PLA statistics against a hand computation.
**Plots:** capital by risk class; diversification benefit vs correlation; HPL vs RTPL scatter with test statistics; IM profile over time; EAD comparison (SA-CCR vs EEPE).
**Diagrams:** capital data flow, sensitivities and scenarios (T4, T8) and exposures (T9) -> methods -> reports (`flowchart LR`); optional P&L attribution decision flow, HPL and RTPL -> tests -> zone -> desk eligibility (`flowchart TB`).
**Depends on:** T4, T6, T8; T9, T10, T11 for the counterparty and margin parts, when they exist for the instrument.

---

## 2. Instrument ladder

Ordered by increasing nonlinearity and dimension. Adjust only with a stated reason.

1. Zero-coupon bond, FX forward
2. Fixed-rate bond
3. Vanilla interest-rate swap (single curve first, then OIS/SOFR/ESTR multi-curve)
4. European equity or FX option
5. Cap/floor, swaption
6. Barrier, American, Bermudan options
7. Multi-asset: basket, quanto, rainbow, autocallable

## 3. Coverage matrix

Not every pair is worth a notebook. Mark skipped pairs with the reason.

| Instrument | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 | T9 | T10 | T11 | T12 | T13 | T14 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ZCB / FX forward | x | x | x | x | x | x | x | x | x | | | | | |
| Fixed-rate bond | x | x | x | x | | x | | x | | | | x | | |
| Vanilla IR swap | x | x | x | x | x | x | x | x | x | x | x | x | x | x |
| European option | x | x | x | x | x | x | x | x | x | x | | x | x | x |
| Cap/floor, swaption | x | x | x | x | x | x | x | x | x | | | x | x | x |
| Barrier/American/Bermudan | x | x | x | x | x | x | | x | | | | | x | x |
| Multi-asset | x | x | x | x | x | x | x | x | x | x | x | x | x | x |

Rationale: T10 and T11 are most instructive on portfolios, so they sit on the swap (the canonical netting-set product) and on multi-asset books. T7 is introduced once per asset class and reused after that. T12 sits where a new kind of market data first appears: bootstrapped curves on the swap, bond-implied curves on the fixed-rate bond, the vol surface on the European option, calibration on cap/floor and swaption, correlation on multi-asset; the other instruments reuse it (ZCB and FX forward use the swap and bond curve work, barrier and American options use the European surface). T13 sits where model uncertainty is material: European option with smile, cap/floor and swaption, barrier/American/Bermudan, multi-asset, and the swap for curve and discounting choices. T14 sits on the swap (SA-CCR, margin, CVA capital) and on options (market-risk capital, using whichever of T9 to T11 exist for the instrument).

Recommended build order: T1-T4 for the first three instruments, then instrument by instrument through T6, then the risk themes (T7-T11) on the swap and European option before extending. Build T12 right after T7 for each asset class (curves on the swap, the surface on the European option), then T13, and T14 last, because it consumes the sensitivity, market-risk, exposure and XVA outputs.

## 4. Notation (use throughout, never redefine)

| Symbol | Meaning |
|---|---|
| `t`, `T` | valuation date, maturity (year fractions) |
| `S_t` | spot of an equity/FX underlying |
| `K` | strike |
| `r`, `q`, `sigma` | risk-free rate, dividend/foreign yield, volatility |
| `P(t,T)` | discount factor |
| `V_t` | present value of the product at `t` |
| `N`, `tau_i` | notional, accrual fraction |
| `E[.]`, `Q` | expectation, risk-neutral measure |
| `EE(t)`, `PFE_alpha(t)` | expected exposure, potential future exposure at quantile alpha |
| `lambda`, `R` | default intensity, recovery rate |
| `EAD`, `MPoR` | exposure at default, margin period of risk |
| `IM`, `VM` | initial margin, variation margin |
| `HPL`, `RTPL` | hypothetical and risk-theoretical P&L (P&L attribution test) |

## 5. Naming and numbering

Notebooks are imported by later notebooks, so file names must be valid module names: `<instrument>_<themecode>_<theme>.py`, lowercase, underscores, **no leading digit**, e.g. `european_option_t3_pricing.py`, `vanilla_swap_t9_ccr.py`, `vanilla_swap_t12_market_data.py`, `european_option_t13_valuation_control.py`, `vanilla_swap_t14_capital_margin.py`. Keep the reading order in `notebooks/README.md` (a table: order, module, theme, code it imports, code it publishes, followed by a Mermaid `flowchart LR` import graph with one node per module and arrows following imports).
