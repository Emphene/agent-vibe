# Code reuse by importing from earlier notebooks

Notebooks never embed each other and never carry state between them. They share **code**, in two ways:

1. **`common/`**: generic, instrument-agnostic helpers (plot styling, RNG and path generators, bump-and-reval, formatting).
2. **Importing from an earlier notebook**: instrument- or theme-specific code that an earlier notebook defines (market and instrument builders, closed forms, pricers, Greek calculators, exposure engines, XVA formulas).

Marimo supports (2) natively: functions and classes marked `@app.function` / `@app.class_definition` in a notebook can be imported by any Python code, including other notebooks, **without running the notebook's cells**. (Verified on marimo 0.25.x: importing a notebook runs only its `with app.setup:` block, so nothing is built until you call a function.)

> Terminology: Marimo has no `mo.embed` or `mo.notebook`. In this skill, do not embed notebooks (`app.embed()`) at all. If a user asks to "reuse a notebook", it means this import mechanism.

## Which home for which code

Prefer importing from the earlier notebook when **the code is that notebook's reference implementation**:

| Code | Home | Why |
|---|---|---|
| `make_flat_market`, `make_european_option` | notebook T2 | T2 explains the objects; readers can jump to the source and the commentary |
| `black_scholes_closed_form`, `price_european` | notebook T3 | derived and validated in T3; T4-T9 reuse the same trusted version |
| `delta_by_bump`, `dv01_ladder` | notebook T4 | belongs with the sensitivities notebook |
| `exposure_profile`, `eepe` | notebook T9 | CCR logic defined there, reused by T10 and T11 |
| `tolerance_check` | notebook T3 | first needed for IPV; reused by T6 (explain thresholds), T13 and T14 |
| `build_snapshot`, `calibration_report` | notebook T12 | market-data and calibration logic defined there, reused by T13 and T14 |
| `valuation_reserve` | notebook T13 | reserve methodology defined there |
| `aggregate_charge`, `pla_test` | notebook T14 | regulatory aggregation (illustrative parameters) defined there |
| `okabe_ito_palette`, `line_figure`, `gbm_paths`, `bump_and_reval` | `common/` | no financial content, used everywhere |

Decision rule: **would a reader of notebook N+1 benefit from knowing where this code is explained?** Yes: import it from the notebook that explains it. No financial content, or used from the first notebook: `common/`.

A function starts in `common/` only if it is generic from day one. Do not duplicate: if code exists in an earlier notebook, import it; if two themes of different instruments need the same generic piece, promote it to `common/`.

## How: publishing code

In the earlier notebook:

```python
with app.setup:                       # runs on import; keep it to imports and constants
    import numpy as np
    import QuantLib as ql

@app.function                         # top-level, pure
def black_scholes_closed_form(spot, strike, years, rate, div, vol) -> float:
    ...

@app.class_definition                 # use with @dataclass for shared containers
@dataclass
class FlatMarket: ...
```

Rules for published code:
- **Top-level and pure.** It may use only names from the `with app.setup:` block, its own arguments, and other `@app.function`s. A function that reads a cell variable cannot be imported.
- **Build inside, return values.** Functions create their QuantLib objects themselves (market, instrument, engine) and return results, so they are safe to call in loops and from any notebook.
- **Set the QuantLib evaluation date explicitly** inside builders that create curves.
- **Everything such functions need is imported in the setup block**, including upstream imports.

## How: importing

In the later notebook, imports of notebook code go in the setup block when published functions depend on them, otherwise a normal import cell is fine:

```python
with app.setup:
    import sys
    from pathlib import Path
    _here = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
    for _p in (_here, _here.parent):          # notebooks/ and project root (common/)
        if str(_p) not in sys.path:
            sys.path.insert(0, str(_p))
    from european_option_t2_modeling import make_flat_market, make_european_option
    from common.plotting import line_figure
```

Then mention it in the header (`Code imported from: ...`) and, in section 4, point to the source notebook for the explanation instead of repeating it.

## Constraints

- **Importable file names**: lowercase, underscores, no leading digit, no dashes (`european_option_t3_pricing.py`, not `04_european_option_T3.py`). Keep the order in `notebooks/README.md`.
- **Import only from earlier notebooks.** No cycles; the dependency graph follows the theme ladder.
- **Import each name from the notebook that defines it**, not via a notebook that re-imports it (it works, but hides provenance).
- **Sibling imports need `notebooks/` on `sys.path`** (the setup block above does it). They also work with `marimo edit` and `python nb.py`.
- **Only code is shared, not state.** Each notebook builds its own objects by calling the imported functions with its own parameters. This keeps every notebook runnable alone, and avoids hidden coupling and re-execution costs.
- **Setup blocks run on import**: keep them to imports and constants, with no heavy work.
- **Published functions are an API**: do not rename or change their meaning once other notebooks import them; add new functions or keyword arguments instead.
- **Verify** by running the downstream notebook (`python nb.py`, `marimo check`, `marimo export html`), and the upstream notebook still runs alone.
