# Marimo and QuantLib rules

Read before writing code cells. Most failures in this kind of notebook come from the two areas below. Code sharing between notebooks is covered in `code-reuse-by-import.md`.

## Contents
1. Marimo reactivity
2. No interactive widgets
3. Reproducibility and dependencies
4. QuantLib conventions
5. QuantLib pitfalls
6. Visualization standards
7. Mermaid diagrams (summary)

---

## 1. Marimo reactivity

Marimo builds a dependency graph from variable names, so cell order on the page does not matter but name discipline does.

- **Define each global name in exactly one cell.** Redefining a name in two cells is an error. Use leading underscores (`_tmp`, `_fig`) for cell-local variables that must not leak.
- **Do not mutate shared state across cells.** Marimo cannot see mutation, so downstream cells will not re-run. For QuantLib: `quote.setValue(x)` in one cell will *not* trigger repricing in another. Write a pure function `price(spot, vol, ...)` that builds the market objects inside it, and call it wherever needed.
- **Bumps happen inside one cell or helper** with restore in `try/finally` (`common/bump.py`). Never leave a bumped quote behind.
- **Logic lives in functions** (`@app.function` in the notebook that defines it, or `common/` if generic). Cells narrate, call and plot.
- **Setup block** (`with app.setup:`): imports and constants. Names defined there are available in every cell without being listed as arguments, and published `@app.function`s can use them.
- **Output is the last expression** of a cell. Return needed names as a tuple.
- **Raw strings for LaTeX:** `mo.md(r"""...""")`. Do not put `{{PLACEHOLDER}}` inside f-strings.
- **Guards:** `mo.stop(condition, mo.md("..."))` to skip expensive cells.
- **Layout (static, not input):** `mo.md` with LaTeX, `mo.callout`, `mo.accordion` for proofs and solutions, `mo.vstack` / `mo.hstack` to arrange results, `diagram()` (Mermaid) for structure.

## 2. No interactive widgets

Notebooks in this series do not use `mo.ui.*` input elements (sliders, dropdowns, switches, buttons, tabs), and Mermaid diagrams carry no `click` handlers. Exploration is static and code-driven so that results are reproducible, reviewable as plain text, and identical when run as a script.

- Parameters are plain values in one `params` cell. Heavy computation is gated by a plain flag such as `params["high_precision"]`.
- **Sweeps:** loop an imported or published pricing function over a grid and plot the curves (e.g. price vs spot for three vols).
- **Scenario tables:** a `pandas` DataFrame over a few parameter combinations (vol x maturity) showing price and Greeks.
- **Side-by-side comparison** plots instead of toggles: show the variants together.
- Choose a few instructive values, and state the takeaway in each plot title.

## 3. Reproducibility and dependencies

- PEP 723 block at the top of every notebook (marimo, QuantLib, numpy, scipy, pandas, matplotlib). Pin exact versions only after the notebook has run; never guess a version.
- Fixed seeds everywhere (`numpy.random.default_rng(seed)`; QuantLib engines take `seed`).
- Must work as `marimo edit --sandbox`, `marimo run`, and `python notebook.py`. The last is the cheapest end-to-end verification.
- File names are importable module names: lowercase, underscores, no leading digit. Order is tracked in `notebooks/README.md`.

## 4. QuantLib conventions

- **Set the evaluation date explicitly** in market-building code and show it. Never rely on the system date. It is process-global.
- **Four layers, visibly separated:** instrument (what), market data (curves, vols, quotes), model/process (dynamics), engine (numerics). Imported builders usually provide the first two; the notebook adds and justifies the rest.
- **Handles and quotes:** `ql.SimpleQuote` in `ql.QuoteHandle`; term structures in `ql.YieldTermStructureHandle` / `ql.BlackVolTermStructureHandle`. Show once that moving a quote reprices without rebuilding, inside one cell.
- **Keep Python references alive** (dataclass or dict holding curves, quotes, handles). A garbage-collected curve behind a Handle gives wrong results or crashes.
- **Conventions shown, not implied:** calendar, day counter, business-day convention, settlement days, schedule rule.
- **Engines:** state why this engine for this product; compare two where meaningful (analytic, MC, PDE/tree).
- **Flat vol and single curve** are simplifications; label them. Move to surfaces or OIS multi-curve when the theme needs it and say what changed.
- **Check API details by running.** QuantLib-Python signatures differ across versions (e.g. `option.payoff()` returns the base `Payoff`, which has no `strike()`; keep the strike in your own parameters).

## 5. QuantLib pitfalls to surface in "Pitfalls"

- Evaluation date set after objects are built
- Day-count mismatch between curve, vol surface and the time used in a closed form
- Settlement days and holiday calendars shifting cash-flow dates
- Greeks not provided by an engine (`RuntimeError`): fall back to bump-and-reval
- Bump too small (round-off) or too large (convexity bias): show a stability plot
- MC error: always report the standard error (`errorEstimate()`)
- FX: dividend yield vs foreign rate (Garman-Kohlhagen is BSM with `q = r_f`)

## 6. Visualization standards
7. Mermaid diagrams (summary)

- **matplotlib only**, through the shared helpers in `common/plotting.py` (`line_figure`, `payoff_figure`, `distribution_figure`, `fan_figure`, `waterfall_figure`); colorblind-safe Okabe-Ito palette.
- Build figures with the object-oriented API (`matplotlib.figure.Figure`, or `fig, ax = plt.subplots()` for custom plots), not implicit `plt.plot` state, and return the figure as the last expression of the cell. Never call `plt.show()`.
- If a custom figure is created with pyplot, close it (`plt.close(fig)`) after returning/using it so figures do not accumulate.
- Static images only: no hover tooltips, so annotate key values directly on the plot.
- Axis labels with units; titles state the takeaway, not just the quantity.
- Mark key quantities (strike, VaR/ES, PFE quantile, EEPE).
- Every conceptual claim gets a figure: payoffs, curves, price and Greek profiles, exposure profiles, P&L waterfalls, loss distributions.

## 7. Mermaid diagrams (summary; full rules in `mermaid-diagrams.md`)

- Structure (layers, object graphs, pipelines, decision trees, cash-flow sequences, life cycles) is drawn in Mermaid with `diagram()` from `common/diagrams.py`; quantities on axes stay matplotlib.
- Output is the last expression of a cell, like a figure. Diagram cells use `hide_code=True` (the code is Mermaid source, not the content).
- Plain strings only: Mermaid braces clash with f-strings, and marimo's `mo.md` does not render ```` ```mermaid ```` fences. Interpolate with `string.Template` if truly needed.
- The diagram is drawn in the browser: it does not appear in `python notebook.py` output or text exports, and syntax errors do not fail `marimo check`. Give every diagram a caption that states the takeaway, and run `scripts/check_mermaid.py`.
- Diagram names must match the code (real QuantLib classes and published function names), and colours follow the series vocabulary (instrument, market, model, engine, output, risk, neutral).
