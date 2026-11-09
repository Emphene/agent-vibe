# /// script
# requires-python = ">=3.10"
# dependencies = ["marimo", "QuantLib", "numpy", "pandas", "matplotlib"]
# ///
# EXAMPLE UPSTREAM NOTEBOOK: European option, T2 QuantLib modeling.
# It demonstrates how the market and the contract are built, and PUBLISHES that code as
# @app.function / @app.class_definition so later notebooks import it instead of
# copying it. Publishing needs: a `with app.setup:` block, pure top-level functions,
# and an importable file name (lowercase, underscores, no leading digit).

import marimo

__generated_with = "0.0.0"
app = marimo.App(width="medium")

with app.setup:
    import sys
    from dataclasses import dataclass
    from pathlib import Path

    import marimo as mo
    import numpy as np
    import pandas as pd
    import QuantLib as ql

    _here = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
    for _p in (_here, _here.parent):  # notebooks/ (sibling imports) and project root (common/)
        if str(_p) not in sys.path:
            sys.path.insert(0, str(_p))
    from common.diagrams import diagram
    from common.plotting import payoff_figure


# ---- published code (importable without running any cell) ----
@app.class_definition
@dataclass
class FlatMarket:
    """Flat BSM market. Holds every QuantLib object so Python references stay alive."""
    today: object
    calendar: object
    day_counter: object
    spot_q: object
    rate_q: object
    div_q: object
    vol_q: object
    rf_curve: object
    div_curve: object
    vol_surface: object
    process: object


@app.function
def default_params() -> dict:
    """Synthetic market and contract parameters (NOT real data)."""
    return dict(spot=100.0, rate=0.03, div=0.01, vol=0.20, strike=100.0, years=1.0)


@app.function
def make_flat_market(spot, rate, div, vol) -> FlatMarket:
    """Build a flat BSM market and set the global evaluation date explicitly."""
    today, cal, dc = ql.Date(15, 1, 2026), ql.TARGET(), ql.Actual365Fixed()
    ql.Settings.instance().evaluationDate = today
    spot_q, rate_q, div_q, vol_q = (ql.SimpleQuote(x) for x in (spot, rate, div, vol))
    rf = ql.YieldTermStructureHandle(ql.FlatForward(today, ql.QuoteHandle(rate_q), dc))
    dv = ql.YieldTermStructureHandle(ql.FlatForward(today, ql.QuoteHandle(div_q), dc))
    vs = ql.BlackVolTermStructureHandle(
        ql.BlackConstantVol(today, cal, ql.QuoteHandle(vol_q), dc))
    process = ql.BlackScholesMertonProcess(ql.QuoteHandle(spot_q), dv, rf, vs)
    return FlatMarket(today, cal, dc, spot_q, rate_q, div_q, vol_q, rf, dv, vs, process)


@app.function
def make_european_option(strike, maturity, option_type=ql.Option.Call):
    payoff = ql.PlainVanillaPayoff(option_type, strike)
    return ql.VanillaOption(payoff, ql.EuropeanExercise(maturity))


# ---- the demonstration ----
@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # European option: T2 QuantLib modeling

    Later notebooks import `default_params`, `make_flat_market` and
    `make_european_option` from here. All market data is **synthetic**.
    """)
    return


@app.cell(hide_code=True)
def _():
    # T2's canonical diagram: the object dependency graph. Moving a quote reprices everything
    # downstream without rebuilding, because every link goes through a Handle.
    diagram("""
    flowchart LR
      Q1[(SimpleQuote: spot)]:::market --> H1[QuoteHandle]:::market
      Q2[(SimpleQuote: rate, div, vol)]:::market --> H2[Flat curves and vol<br/>via Handles]:::market
      H1 --> P[BlackScholesMertonProcess]:::model
      H2 --> P
      O[VanillaOption<br/>payoff + exercise]:::instrument -. engine added in T3 .-> E[[PricingEngine]]:::engine
      P --> E
      E ==> N([NPV]):::output
    """, caption="Every market input reaches the option through a Handle, so setValue reprices without rebuilding.")
    return


@app.cell
def _():
    params = default_params()
    market = make_flat_market(params["spot"], params["rate"], params["div"], params["vol"])
    maturity = market.today + ql.Period(int(round(params["years"] * 365)), ql.Days)
    option = make_european_option(params["strike"], maturity)
    return maturity, market, option, params


@app.cell
def _(maturity, market, params):
    pd.DataFrame({
        "layer": ["instrument", "market data", "model", "engine"],
        "object": ["VanillaOption", "FlatForward + BlackConstantVol (via Handles)",
                   "BlackScholesMertonProcess", "(assigned in T3)"],
        "detail": [f"call K={params['strike']:.0f}, expiry {maturity}",
                   f"eval date {market.today}, {market.calendar.name()}, "
                   f"{market.day_counter.name()}",
                   "GBM, flat vol, flat curves", ""],
    })
    return


@app.cell
def _(params):
    _k = params["strike"]
    _s = np.linspace(0.5 * _k, 1.5 * _k, 200)
    payoff_figure(_s, np.maximum(_s - _k, 0.0), strike=_k,
                  title="The contract object encodes this payoff, nothing else")
    return


if __name__ == "__main__":
    app.run()
