# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "QuantLib",
#     "numpy",
#     "scipy",
#     "pandas",
#     "matplotlib",
# ]
# ///
# TEMPLATE NOTES (delete when filling in):
#   * SECTION ORDER = the Section skeleton in SKILL.md, numbered the same way:
#     0 Header, 1 Setup, 2 Theory, 3 QuantLib implementation, 4 Validation,
#     5 Front and middle office applications,
#     6 Summary, 7 References.
#     Do not add, drop, renumber or reorder sections: put extra material inside the closest one.
#   * Sub-sections (rule in SKILL.md Hard rules): a section with more than one
#     code/diagram/accordion cell gets a `###` intro markdown cell directly above
#     each of them — keep them. A section with at most one such cell gets ONE
#     titleless one-sentence intro instead: directly above that cell (Setup and
#     Validation here), or directly below the heading cell (Header, Summary,
#     References) as a section intro (unless it already has one). Add matching intros 
#     if you add cells.
#   * This is a demonstration notebook, not a tutorial: no learning objectives, exercises or
#     level/time estimates. Coverage goes into QuantLib features (header + section 3) and desk
#     applications (section 6, catalogue in references/front-middle-office-applications.md).
#   * Placeholder content: European option, T3 Pricing. Replace every {{PLACEHOLDER}}
#     (they appear only inside strings/comments so the file stays runnable as-is).
#   * Code reuse = IMPORTS, never embedding. Instrument/theme-specific code is imported
#     from the earlier notebook that defines it (here european_option_t2_modeling.py,
#     shipped in assets/examples/). Generic helpers come from common/.
#   * File name must be an importable module name (lowercase, underscores, no leading
#     digit): <instrument>_<themeCode>_<theme>.py. Order is kept in notebooks/README.md.
#   * No interactive widgets: exploration is static (sweeps, scenario tables, plots).
#   * Structure diagrams: Mermaid via common.diagrams.diagram() (never an f-string, never a
#     ```mermaid fence inside mo.md). Diagram text is concrete here because the lint rejects
#     '{{'; edit module names and captions by hand. See references/mermaid-diagrams.md.
#   * Pin exact dependency versions after the first successful run. Do not guess them.
#   * Verify: python this_file.py ; marimo check this_file.py ; marimo export html this_file.py ;
#     python scripts/check_mermaid.py this_file.py

import marimo

__generated_with = "0.0.0"  # marimo rewrites this on save
app = marimo.App(width="medium")

with app.setup:
    # ---------------------------------------------------------------------
    # IMPORTS. Everything an @app.function below needs must be imported here,
    # because published functions may only use setup-block names.
    # ---------------------------------------------------------------------
    import sys
    from pathlib import Path

    import marimo as mo
    import numpy as np
    import pandas as pd
    import QuantLib as ql
    from scipy.stats import norm

    _here = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
    for _p in (_here, _here.parent):  # notebooks/ (sibling notebooks) and project root (common/)
        if str(_p) not in sys.path:
            sys.path.insert(0, str(_p))

    # Code from EARLIER NOTEBOOKS (preferred home for instrument/theme-specific logic):
    from european_option_t2_modeling import (          # {{UPSTREAM_NOTEBOOK_MODULE}}
        default_params, make_european_option, make_flat_market,
    )
    # Generic, instrument-agnostic helpers only:
    from common.bump import bump_and_reval
    from common.diagrams import diagram
    from common.plotting import line_figure

    SEED = 42
    TOL = 1e-6  # tolerance for deterministic checks


# ---------------------------------------------------------------------------
# CODE THIS NOTEBOOK PUBLISHES for later notebooks to import
# (top-level, pure, only setup-block names or other @app.function).
# ---------------------------------------------------------------------------
@app.function
def black_scholes_closed_form(spot, strike, years, rate, div, vol) -> float:
    d1 = (np.log(spot / strike) + (rate - div + 0.5 * vol**2) * years) / (vol * np.sqrt(years))
    d2 = d1 - vol * np.sqrt(years)
    return (spot * np.exp(-div * years) * norm.cdf(d1)
            - strike * np.exp(-rate * years) * norm.cdf(d2))


@app.function
def price_european(spot, strike, years, rate, div, vol, engine="analytic",
                   mc_paths=20_000, seed=42, option_type=ql.Option.Call, fd_grid=200) -> dict:
    """Build everything from scratch and price: cheap to call in a loop.

    engine: "analytic" (closed form, with Greeks), "mc" (Monte Carlo, with standard error) or
    "fd" (finite-difference PDE: the independent numerical method used for IPV in section 6).
    """
    market = make_flat_market(spot, rate, div, vol)
    maturity = market.today + ql.Period(int(round(years * 365)), ql.Days)
    opt = make_european_option(strike, maturity, option_type)
    if engine == "analytic":
        opt.setPricingEngine(ql.AnalyticEuropeanEngine(market.process))
        return {"npv": opt.NPV(), "delta": opt.delta(), "gamma": opt.gamma(),
                "vega": opt.vega(), "theta": opt.theta(), "rho": opt.rho()}
    if engine == "fd":
        opt.setPricingEngine(ql.FdBlackScholesVanillaEngine(
            market.process, int(fd_grid), int(fd_grid)))
        return {"npv": opt.NPV()}
    opt.setPricingEngine(ql.MCEuropeanEngine(
        market.process, "PseudoRandom", timeSteps=1,
        requiredSamples=int(mc_paths), seed=int(seed)))
    return {"npv": opt.NPV(), "std_error": opt.errorEstimate()}


@app.function
def implied_vol_european(price, spot, strike, years, rate, div,
                         option_type=ql.Option.Call, guess_vol=0.20) -> float:
    """Black-Scholes implied vol by QuantLib's root finder: the market quoting convention."""
    market = make_flat_market(spot, rate, div, guess_vol)
    maturity = market.today + ql.Period(int(round(years * 365)), ql.Days)
    opt = make_european_option(strike, maturity, option_type)
    return opt.impliedVolatility(price, market.process, 1e-10, 200, 1e-4, 4.0)


@app.function
def tolerance_check(diff, reference, abs_tol, rel_tol):
    """Desk control: tolerance = max(abs_tol, rel_tol * |reference|). Returns (tolerance, status).

    Reused by later notebooks (P&L explain thresholds, valuation control, capital checks).
    """
    tol = max(abs_tol, rel_tol * abs(reference))
    return tol, ("OK" if abs(diff) <= tol else "BREACH")


# ---------------------------------------------------------------------------
# 0. HEADER
# ---------------------------------------------------------------------------
@app.cell(hide_code=True)
def _():
    mo.md(r"""
    States what the demonstration notebook covers, what it imports from upstream, and which desk applications it shows, before any code runs.
    """)
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # {{INSTRUMENT}}: {{THEME_CODE}} {{THEME_NAME}}

    | | |
    |---|---|
    | **Instrument** | {{INSTRUMENT}} |
    | **Theme** | {{THEME_CODE}} {{THEME_NAME}} |
    | **Prerequisites** | {{PREREQUISITE_NOTEBOOKS_AND_CONCEPTS}} |
    | **Code imported from** | `{{UPSTREAM_NOTEBOOK_MODULE}}` |
    | **QuantLib features demonstrated** | {{QUANTLIB_FEATURES}} |
    | **Desk applications** | Front office: {{FRONT_OFFICE_APPLICATIONS}}. Middle office: {{MIDDLE_OFFICE_APPLICATIONS}} |
    | **Previously / Next** | {{LINK_TO_PREVIOUS}} / {{LINK_TO_NEXT}} |

    **Scope.** {{SCOPE_IN_TWO_OR_THREE_SENTENCES}}

    > All market data, marks, tolerances and limits below are **synthetic and illustrative**:
    > they demonstrate the method and are not production figures or policy.
    """)
    return


# ---------------------------------------------------------------------------
# 1. SETUP: imports are in the setup block above; parameters in ONE plain cell (no widgets)
# ---------------------------------------------------------------------------
@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## 1. Setup

    Imports sit in the setup block (code from earlier notebooks and `common/`). Every
    parameter lives in the single `params` cell below: plain values, no widgets.
    """)
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    Bundles the imported contract terms with the Monte Carlo budget and IPV tolerances every validation below reads.
    """)
    return


@app.cell
def _():
    params = {**default_params(), "mc_paths": 20_000, "high_precision": False,
              # desk controls (section 6): illustrative parameters, not policy
              "ipv_rel_tol": 1e-3, "ipv_abs_tol": 0.005, "ipv_grid": 200}
    return (params,)


# ---------------------------------------------------------------------------
# 2. THEORY: framing diagram, then the mathematics, then proofs in accordions
# ---------------------------------------------------------------------------
@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## 2. Theory
    """)
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ### Valuation chain

    The framing diagram before the mathematics: payoff, risk-neutral expectation and discounting as the three steps to the call price.
    """)
    return


@app.cell(hide_code=True)
def _():
    # Framing diagram BEFORE the mathematics it organises: the valuation chain.
    diagram("""
    flowchart LR
      P["Payoff at T<br/>max(S_T - K, 0)"]:::instrument --> X["Expectation under Q<br/>S follows GBM"]:::model
      X --> D["Discount<br/>exp(-rT)"]:::market
      D ==> V(["V(0): the call price"]):::output
    """, caption="Risk-neutral valuation is three steps: payoff, expectation under Q, discounting.")
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    **Setting.** {{ASSUMPTIONS}} (e.g. under $\mathbb{Q}$,
    $dS_t = (r-q)S_t\,dt + \sigma S_t\,dW_t$).

    **Result.** {{KEY_RESULT}} For the European call:

    $$
    C = S_0 e^{-qT}\,\Phi(d_1) - K e^{-rT}\,\Phi(d_2),\qquad
    d_{1,2} = \frac{\ln(S_0/K) + (r - q \pm \tfrac12\sigma^2)T}{\sigma\sqrt{T}}
    $$
    """)
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ### Payoff intuition

    Plots the closed-form value against intrinsic value across spot so the formula's shape is visible before any engine runs.
    """)
    return


@app.cell
def _(params):
    # Intuition third: what the formula looks like (static plot, takeaway in the title).
    _k = params["strike"]
    _s = np.linspace(0.5 * _k, 1.5 * _k, 200)
    _value = [black_scholes_closed_form(x, _k, params["years"], params["rate"],
                                        params["div"], params["vol"]) for x in _s]
    line_figure(_s, {"Intrinsic (payoff now)": np.maximum(_s - _k, 0.0), "Option value": _value},
                title="{{TAKEAWAY_TITLE}}: value sits above intrinsic, most at the strike",
                xlabel="Spot", ylabel="Value", vlines={"Spot": params["spot"]})
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ### Derivation details

    The derivation of the closed form, collapsed out of the main flow until the reader wants it.
    """)
    return


@app.cell(hide_code=True)
def _():
    mo.accordion({"Deep dive: {{PROOF_TITLE}}": mo.md(r"{{PROOF_OR_DERIVATION}}")})
    return


# ---------------------------------------------------------------------------
# 3. QUANTLIB IMPLEMENTATION: architecture diagram first, then one layer per cell with the "why"
# ---------------------------------------------------------------------------
@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## 3. QuantLib implementation

    Four layers stay separate: **instrument**, **market data**, **model**, **engine**.
    The first two are built with code imported from `{{UPSTREAM_NOTEBOOK_MODULE}}`
    (see that notebook for how and why); this notebook adds the model-to-engine layer.
    """)
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ### Layer architecture

    What this notebook imports from the upstream module and what it builds here, before any of the code runs.
    """)
    return


@app.cell(hide_code=True)
def _():
    # Architecture with provenance: imported code vs what is new here. Edit the subgraph title
    # to the real upstream module and the nodes to the real classes.
    diagram("""
    flowchart LR
      subgraph IMP["imported from european_option_t2_modeling"]
        direction TB
        I[VanillaOption<br/>payoff + exercise]:::instrument
        M[(FlatForward +<br/>BlackConstantVol)]:::market
      end
      subgraph NEW["new in this notebook"]
        direction TB
        P[BlackScholesMertonProcess]:::model
        E[[AnalyticEuropeanEngine]]:::engine
      end
      M --> P --> E
      I -- setPricingEngine --> E
      E ==> V([NPV and Greeks]):::output
    """, caption="Instrument and market data come from T2; this notebook adds the model and engine.")
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ### Instrument construction

    Builds the market and option from the imported builders and shows the evaluation date, calendar and day counter they pin.
    """)
    return


@app.cell
def _(params):
    market = make_flat_market(params["spot"], params["rate"], params["div"], params["vol"])
    maturity = market.today + ql.Period(int(round(params["years"] * 365)), ql.Days)
    option = make_european_option(params["strike"], maturity, ql.Option.Call)
    mo.md(f"Evaluation date **{ql.Settings.instance().evaluationDate}**, "
          f"calendar **{market.calendar.name()}**, day counter **{market.day_counter.name()}**")
    return market, option


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ### Engine choice

    The decision tree applied just before the engine is attached: exact closed form first, PDE or Monte Carlo only when the payoff demands it.
    """)
    return


@app.cell(hide_code=True)
def _():
    # Engine choice as a decision tree: the reader sees WHY before the next cell picks one.
    diagram("""
    flowchart TB
      S{Payoff path-dependent?}
      S -- no --> C{Closed form under the model?}
      C -- yes --> A[[AnalyticEuropeanEngine]]:::engine
      C -- no --> F[[PDE or tree engine]]:::engine
      S -- yes --> D{Early exercise?}
      D -- no --> M[[Monte Carlo engine]]:::engine
      D -- yes --> L[[Least-squares MC or PDE]]:::engine
    """, caption="Pick the cheapest engine that is exact for this payoff and model: here, analytic.")
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ### Attaching the engine

    Sets the analytic engine on the option and reads off the NPV that the validation section will independently check.
    """)
    return


@app.cell
def _(market, option):
    # NEW layer: model + engine. Analytic is exact for flat-vol BSM European payoffs.
    option.setPricingEngine(ql.AnalyticEuropeanEngine(market.process))
    npv_ql = option.NPV()
    npv_ql
    return (npv_ql,)


# ---------------------------------------------------------------------------
# 4. VALIDATION: independent checks, tolerances displayed
# ---------------------------------------------------------------------------
@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## 4. Validation

    Every claim gets an independent check, with the error and the tolerance shown.
    """)
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    Recomputes the option value by closed form and Monte Carlo and diffs both against the QuantLib analytic price, with the tolerances displayed.
    """)
    return


@app.cell
def _(npv_ql, params):
    _args = (params["spot"], params["strike"], params["years"], params["rate"],
             params["div"], params["vol"])
    npv_closed = black_scholes_closed_form(*_args)
    _paths = 200_000 if params["high_precision"] else params["mc_paths"]
    _mc = price_european(*_args, engine="mc", mc_paths=_paths, seed=SEED)
    _e1, _e2 = abs(npv_closed - npv_ql), abs(_mc["npv"] - npv_ql)
    _ok = _e1 < TOL and _e2 < 3 * _mc["std_error"]
    mo.callout(mo.md(
        f"closed form {npv_closed:.6f} | QuantLib analytic {npv_ql:.6f} "
        f"(|err| {_e1:.1e}, tol {TOL:.0e}) | MC {_mc['npv']:.4f} +/- {_mc['std_error']:.4f} "
        f"(|err| {_e2:.4f} < 3 SE) -> **{'PASS' if _ok else 'CHECK'}**"),
        kind="success" if _ok else "warn")
    return (npv_closed,)


# ---------------------------------------------------------------------------
# 5. FRONT AND MIDDLE OFFICE APPLICATIONS: what the desks do with the functions above
# (catalogue, outputs and controls: references/front-middle-office-applications.md)
# ---------------------------------------------------------------------------
@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## 6. Front and middle office applications

    The same published functions, used the way the desks use them. **Front office** quotes,
    trades and hedges; **middle office** verifies prices, monitors risk and escalates breaks.
    Tolerances are illustrative parameters in `params`.
    """)
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ### Desk workflow

    How a quoted vol becomes a desk mark and how the middle office re-prices it with an independent engine before accepting it.
    """)
    return


@app.cell(hide_code=True)
def _():
    # Workflow diagram: who produces and who consumes each output, where the control sits.
    diagram("""
    flowchart LR
      subgraph FO["Front office"]
        direction TB
        Q[(Quoted vol)]:::market --> P[[price_european<br/>analytic engine]]:::engine
        P --> M([Desk mark]):::output
      end
      subgraph MO["Middle office: IPV"]
        direction TB
        I[[price_european<br/>fd engine]]:::engine --> C{"Within tolerance?"}
        C -- yes --> A([Mark accepted]):::output
        C -- no --> B([Breach: escalate for re-mark]):::risk
      end
      M --> C
    """, caption="The desk marks with one engine; the middle office re-prices with an independent one and escalates breaks.")
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ### Vol round-trip check

    Converts quoted vol to price and back with QuantLib's root finder, checking the round trip to machine precision.
    """)
    return


@app.cell
def _(params):
    # FRONT OFFICE, quoting: options trade in volatility and are marked in price, so desks
    # convert both ways. Round trip: vol -> price (engine) -> vol (QuantLib root finder).
    _smile = {90.0: 0.24, 100.0: 0.20, 110.0: 0.18}  # synthetic skew
    _rows = []
    for _k, _quoted in _smile.items():
        _a = (params["spot"], _k, params["years"], params["rate"], params["div"])
        _px = price_european(*_a, _quoted)["npv"]
        _iv = implied_vol_european(_px, *_a)
        _rows.append({"strike": _k, "quoted vol": _quoted, "price": _px,
                      "implied vol (QuantLib)": _iv, "|vol error|": abs(_iv - _quoted)})
    _sheet = pd.DataFrame(_rows)
    _ok = _sheet["|vol error|"].max() < 1e-8
    mo.vstack([
        mo.md("**Quote sheet** (as-of " + str(ql.Settings.instance().evaluationDate) + ", synthetic skew)"),
        _sheet.round(6),
        mo.callout(mo.md(f"Round trip max |vol error| {_sheet['|vol error|'].max():.1e} "
                         f"-> **{'PASS' if _ok else 'CHECK'}**"), kind="success" if _ok else "warn"),
    ])
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ### Independent price verification

    Re-prices every desk mark with the finite-difference engine and flags a planted mis-mark against the illustrative tolerance.
    """)
    return


@app.cell
def _(params):
    # MIDDLE OFFICE, independent price verification (IPV): re-price every desk mark with an
    # independent numerical method (PDE vs the desk's closed form) and flag breaks.
    _rng = np.random.default_rng(SEED)
    _book = [("T001", ql.Option.Call, 100.0, 1.00), ("T002", ql.Option.Put, 90.0, 0.50),
             ("T003", ql.Option.Call, 110.0, 2.00), ("T004", ql.Option.Put, 100.0, 0.25),
             ("T005", ql.Option.Call, 95.0, 1.50), ("T006", ql.Option.Put, 105.0, 3.00)]
    _rows = []
    for _id, _typ, _k, _t in _book:
        _a = (params["spot"], _k, _t, params["rate"], params["div"], params["vol"])
        _mark = price_european(*_a, option_type=_typ)["npv"] * (1 + _rng.normal(0, 2e-4))
        if _id == "T005":
            _mark *= 1.03  # PLANTED mis-mark, to show the control firing
        _indep = price_european(*_a, engine="fd", option_type=_typ,
                                fd_grid=params["ipv_grid"])["npv"]
        _diff = _mark - _indep
        _tol, _status = tolerance_check(_diff, _indep, params["ipv_abs_tol"], params["ipv_rel_tol"])
        _rows.append({"trade": _id, "type": "Call" if _typ == ql.Option.Call else "Put",
                      "strike": _k, "years": _t, "desk mark": _mark, "independent (FD)": _indep,
                      "diff": _diff, "tolerance": _tol,
                      "status": _status})
    _blotter = pd.DataFrame(_rows)
    _n = int((_blotter["status"] == "BREACH").sum())
    mo.vstack([
        mo.md("**IPV blotter** (unit: price per option; desk marks synthetic, T005 mis-marked on purpose)"),
        _blotter.round(4),
        mo.callout(mo.md(f"{_n} breach(es) of {len(_blotter)} marks"
                         + (": escalate to the desk for re-mark." if _n else ": all marks accepted.")),
                   kind="warn" if _n else "success"),
    ])
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    **Coverage of desk applications for this (instrument, theme).** Catalogue:
    `references/front-middle-office-applications.md`.

    | Desk | Application | Status |
    |---|---|---|
    | Front office | Quoting: price and implied vol, both directions | Covered above |
    | Front office | Pricing ladders and what-if pricing | Covered in section 5 (sweeps) |
    | Middle office | IPV against an independent engine | Covered above |
    | Middle office | {{OTHER_APPLICATION}} | {{COVERED_OR_SKIPPED_WITH_REASON}} |
    """)
    return


# ---------------------------------------------------------------------------
# 6. SUMMARY and 7. REFERENCES
# ---------------------------------------------------------------------------
@app.cell(hide_code=True)
def _():
    mo.md(r"""
    Gathers the formulas, the QuantLib objects, the desk take-aways and the functions published for later notebooks into one closing page.
    """)
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## 8. Summary

    **Key formulas.** {{KEY_FORMULAS}}

    **QuantLib objects demonstrated.**

    | Class | Role here |
    |---|---|
    | {{QUANTLIB_CLASS}} | {{ROLE}} |

    **Desk take-aways.** {{DESK_TAKEAWAYS}}

    **Code published for later notebooks:** `black_scholes_closed_form`, `price_european`
    (engines `analytic`, `mc`, `fd`), `implied_vol_european`, `tolerance_check`.

    **Next:** {{LINK_TO_NEXT}}
    """)
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## 9. References

    Lists the pricing reference and the QuantLib documentation behind the classes demonstrated above.

    - {{REFERENCE_1}}
    - QuantLib documentation: https://www.quantlib.org/
    """)
    return


if __name__ == "__main__":
    app.run()
