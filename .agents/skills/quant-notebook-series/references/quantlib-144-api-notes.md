# QuantLib 1.44 API notes (verified by running)

Python-specific traps hit and re-verified while building the zero-coupon bond series
(T1–T9). Every line was executed against QuantLib 1.44; re-verify on any upgrade.

## Dates, enums, bonds

- `ql.Date` uses methods: `dayOfMonth()`, `month()`, `year()` — attribute access yields
  bound methods, and `.day` does not exist.
- `ql.Following` etc. are enum *values*: pass directly (`paymentConvention=ql.Following`);
  never call them — they are not classes.
- `ZeroCouponBond(...)` takes `faceAmount=`, not `nominal=`.
- `BondPrice(price, BondPrice.Clean)` — types are class attributes (`Clean` / `Dirty`);
  there is no `BondPrice.Type` namespace.
- `BondFunctions.dirtyPrice` has no yield-based overload — use
  `cleanPrice(bond, y, dc, comp, freq, settlement)` + `accruedAmount`.
- Price → yield: `BondFunctions.bondYield(bond, BondPrice(...), dc, comp, freq,
  settlement)`; the reverse: `cleanPrice(bond, y, ...)`.
- `BondFunctions.zSpread` takes the *raw curve object*, not a `YieldTermStructureHandle`.
- `BondFunctions.basisPointValue` is the **exact one-sided +1bp move**, not the
  derivative: it equals `-P·D·1bp + ½·convexity·(1bp)²`. Reconcile it against
  `-dirty×duration×1bp` by *showing the half-convexity identity* — never by widening a
  tolerance (EUR-scale gap on a 10m face; the identity closes to machine precision).
- `CashFlows.bps` returned 0 for a zero-coupon leg in 1.44 — prefer
  `BondFunctions.basisPointValue`.

## Handles and curves

- `RelinkableYieldTermStructureHandle.linkTo(curve)` — the method is `linkTo`, not
  `relinkTo`.
- Hold every curve-chain object (quotes, helpers, curve, handle) in one container:
  a garbage-collected link inside a `Handle` fails silently with stale or wrong prices.

## Hull-White and swaption calibration

- `HullWhiteProcess(termStructureHandle, a, sigma)` — takes the handle and parameters,
  not a `HullWhite` model instance.
- `SwaptionHelper(expiry, length, volQuote, iborIndex, fixedLegTenor, fixedDC, floatDC,
  discountHandle, errorType, strike, nominal, type)`: Python has no `Null[Real]`; the
  `sys.float_info.max` sentinel backfires (`-inf forward` in the option pricer) —
  compute and pass an explicit ATM strike; `type=ql.Normal` sits after strike/nominal.
- The index needs a curve: `ql.Euribor6M(handle)` in single-curve setups; a bare
  `Euribor6M()` dies at calibration with "null term structure ... 2nd leg".
- Engines are never set automatically:
  `helper.setPricingEngine(ql.JamshidianSwaptionEngine(model))` before
  `model.calibrate(...)`, else "null pricing engine". The engine takes only `(model)` or
  `(model, discountHandle)` — no vol-type or shift arguments.
- `EndCriteria(maxIter, maxStationaryIters, rootEps, funcEps, gradientEps)` — five args,
  second is `Size` (int). `ql.Constraint()` is abstract → pass `ql.NoConstraint()`.
- Fix parameters positionally:
  `model.calibrate(hs, method, ec, ql.NoConstraint(), [], [True, False])` — fix `a`,
  fit `sigma` only (the benchmark row model validation asks for).
- `helper.impliedVolatility(...)` needs all five Python args
  `(targetValue, accuracy, maxEvaluations, minVol, maxVol)`; pass `helper.modelValue()`
  as the target for the model's implied vol — or skip the solver and report
  `marketValue()` / `modelValue()` / `calibrationError()`.
- Weak identification is real: 3–4 swaptions often drive `a → 0` regardless of starting
  point. Fix `a`, bound it, or state the collapse — never present a drifting `a` as a
  calibrated fact.

## Simulation and statistics

- `process.evolve(t, x, dt, z)` with `z ~ N(0,1)` drawn from `numpy.default_rng`
  produced the σ²·dt step variance (matched `process.variance(t, x, dt)`); draw outside
  QuantLib for reproducible seeds.
- Sample moments on a `(paths, times)` array: variance **per time** is `axis=0`;
  `axis=1` silently computes per-path time variance and quietly destroys the check.
- Cross-path-deterministic grid dates (t=0, maturity) have spread that is pure
  floating-point noise — exclude them from z-score checks (threshold the standard error,
  not the date).
- `RiskStatistics.valueAtRisk(p)` / `expectedShortfall(p)` return **positive losses** at
  percentile `p` (verified against numpy quantiles). Size VaR tolerances from the
  estimator's own error `σ·sqrt(α(1-α)/n)/φ(z_α)`, not from a round percent.
