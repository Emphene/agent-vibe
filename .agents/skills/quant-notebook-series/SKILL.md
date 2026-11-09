---
name: "quant-notebook-series"
description: Build exhaustive Marimo notebooks on QuantLib-Python and the front/middle-office applications of quantitative finance as one progressive series (one instrument x one theme per notebook, linear to multi-asset) with math, explicit QuantLib code, validation, matplotlib plots, Mermaid diagrams, desk applications (quoting, hedging, IPV, product control, risk, collateral, XVA, model validation), code shared by import from earlier notebooks or common/. Use to create, extend, plan or review a Marimo/QuantLib notebook or desk workflow on product anatomy, modeling, pricing, Greeks, hedging, P&L explain, risk factors, VaR/ES, CCR, netting, collateral, XVA, market data, calibration, valuation control, model risk, regulatory capital, margin (FRTB, SA-CCR) or diagrams — even if the user only says "next notebook in the series" or names an instrument and a theme.
---

# Quant notebook series

One instrument, modeled, priced and risk-managed in QuantLib under one theme, then used by front and middle office. Exhaustive working coverage, not a tutorial; reader = practitioner (quant, trader, structurer, risk manager, product controller, validator). Fixed order → N+1 stays familiar to readers of N in structure, notation and code.

## Hard rules

- **Data → matplotlib** (`common/plotting.py`); no plotly or interactive plotting libraries.
- **Mermaid → structure only:** layers, object graphs, pipelines, decision trees, who-pays-whom, life cycles, via `diagram()` (`common/diagrams.py`). Static plain-string source; 2–5 per notebook; one idea, ≤ ~12 nodes; real QuantLib and function names; series colour vocabulary; takeaway caption. A ```` ```mermaid ```` fence in `mo.md` does not render. Read `references/mermaid-diagrams.md`.
- **No interactive widgets:** no `mo.ui.*` (sliders, dropdowns, switches, buttons, tabs), no Mermaid `click`. Exploration static only: parameter sweeps, scenario tables, side-by-side plots. Display allowed: `mo.md`, `mo.callout`, `mo.accordion`, `mo.vstack`, `diagram()`.
- **No embedding, no shared state:** never `app.embed()`; each notebook runs alone; imports carry code, never state. `mo.embed`/`mo.notebook` do not exist — that request means reuse → imports.
- **Demonstrate, don't tutor:** no learning objectives, exercises, quizzes, level or time estimates. Prose = assumptions, why this object or engine, conventions, results; depth → mathematics, QuantLib coverage, validation, desk applications.
- **Import, don't copy:** reference implementations (builders, closed forms, pricers, Greek and exposure engines) stay in the notebook that defines them, imported via `@app.function`; one trusted implementation per piece of logic. `common/` = generic, instrument-agnostic helpers only. Read `references/code-reuse-by-import.md`.
- **Cell intros** (non-markdown cell = visible `@app.cell`, `diagram()`, `mo.accordion()`; markdown = pure `mo.md(...)`, `hide_code` irrelevant). Section with >1 non-markdown cell: immediately above each, `@app.cell(hide_code=True)` wrapping `mo.md(r"""…""")` = `###` title (sentence case, 2–6 words, ≠ cell's inner `**bold**` caption, ≠ diagram captions) + exactly one practitioner-voice sentence (what, why). Section with ≤1 (0 Header, 1 Setup, 6 Summary, 7 References, single-diagram section): exactly one such cell, bare sentence, no `###`, above the non-markdown cell if any else directly below the section heading — same voice, one sentence, same distinctness. No repeat of the section intro or a diagram caption; no cell with two intros.

## Inputs

Unit = **(instrument, theme)**; settle both before writing. Check the project first (`notebooks/`, `notebooks/README.md`, `common/`) and reuse its notation, parameters, published functions.

- Instrument only → next theme from `references/theme-ladder.md` given what exists, plus why; theme only → next instrument on the ladder.
- Programme → both matrices first (instrument x theme: `theme-ladder.md`; desk function x theme: `front-middle-office-applications.md`); confirm before building.
- ≤ 1–2 questions, only when the answer changes the work (single-curve vs OIS, primary desk or asset class); else state assumptions in one line, proceed.

## Workflow

1. **Prerequisites:** ladder → dependency notebooks; read their publishes (`@app.function` / `@app.class_definition`); two-line summary + link; no re-derivation.
2. **Scaffold if missing:** `assets/common/` (generic helpers incl. `diagrams.py`), `scripts/` (Mermaid checker; `cd scripts && npm install` once); new project → `assets/examples/european_option_t2_modeling.py` (publishing-upstream pattern) + `notebooks/README.md`.
3. **Template:** `assets/notebook_template.py` → `notebooks/<instrument>_<themecode>_<theme>.py` (importable name: lowercase, underscores, no leading digit); upstream import → right earlier notebook; fill `{{PLACEHOLDERS}}`; keep section order.
4. **Plan coverage, then write:** features, desk applications, validations, plots, diagrams ← `theme-ladder.md`; applicable rows ← `front-middle-office-applications.md`; header lists the demonstration. Read `marimo-quantlib-rules.md` before code cells, `front-middle-office-applications.md` before §5, `mermaid-diagrams.md` before drawing. Plan 2–5 diagrams up front, must-have first.
5. **Publish for successors:** reusable theme-specific logic → top-level pure `@app.function`s; later notebooks import, never copy.
6. **Verify by running:** `python notebook.py`, `marimo check notebook.py`, `marimo export html notebook.py` (running proves every QuantLib class in header and Summary exists); `python scripts/check_mermaid.py notebooks/<notebook>.py` (parses all diagrams; Mermaid errors otherwise browser-only); earlier notebooks still run alone. Unrun = unfinished. Report unrun checks (incl. unviewed diagram layout) and skipped desk applications.
7. **`notebooks/README.md`:** order, module, theme, code imported, code published + Mermaid import graph (node per module, arrows follow imports).

## Section skeleton (fixed order)

0. Header: title, instrument, theme, prerequisites, imported code, QuantLib features demonstrated, desk applications (front, middle office), Previously / Next.
1. Setup: imports; one plain `params` cell.
2. Theory: exhaustive LaTeX; framing diagram (valuation chain, cash flows) before the mathematics it organises; proofs in collapsible `mo.accordion`.
3. QuantLib implementation: architecture diagram first (instrument / market data / model / engine, imported vs new); per object — key arguments, exposures, the WHY (engine-choice tree before the engine is set, where relevant); layers visibly separate; imported builders → source notebook.
4. Validation: independent check (closed form vs engine, MC vs analytic, parity, finite differences vs analytic Greeks); tolerances displayed.
5. Front and middle office applications: desk use of the notebook's own functions, every applicable catalogue row (front: quoting, risk ladders, calibration, hedging policy, XVA quotes; middle: IPV, limits, P&L sign-off, market and credit risk reports, margin, model validation) — each with desk-grade output table, control and status, workflow diagram; closing coverage cell lists skips and reasons.
6. Summary: formulas, QuantLib objects (class, role), desk take-aways, code published for later notebooks, next link.
7. References.

## Principles

- **Math first, code second, validation always, desk use last**; each diagram precedes the text and code it organises.
- **Exhaustive QuantLib:** every object in the theme's feature list constructed, key arguments, exposures, behaviour check; only classes that exist, proved by running.
- **Desk-grade outputs:** blotter tables with units, sign conventions, as-of date, tolerances or limits (labelled illustrative parameters), OK / WARN / BREACH; every control shows threshold and status. Front and middle office both covered wherever the theme supports it.
- **Regulation = context, not authority:** no regulatory parameter from memory — cite current rule text or expose it as an illustrative parameter; title such work "simplified, illustrative, not for regulatory use".
- **No hidden magic:** calendars, day counters, schedules, handles, engine choice, each with the reason.
- **No unverified claim:** every one carries error and tolerance.
- **Notation once**, series-wide; assumptions stated (flat vol, single vs multi-curve, model risk).
- **Short cells, concrete numbers, synthetic but plausible labelled data**; comprehensive ≠ long — split by sub-theme, never cut coverage; Monte Carlo paths and grids capped via `params["high_precision"]`.

## Reference files

- `references/code-reuse-by-import.md` — notebook vs `common/` split, publishing and importing `@app.function`. **Before code.**
- `references/theme-ladder.md` — T1–T14 content, instrument ladder, coverage matrix, notation, naming.
- `references/front-middle-office-applications.md` — desk map, per-theme catalogue, output and control patterns, regulatory rule, desk x theme matrix (§6), how to write the applications section (§7). **Before §5.**
- `references/marimo-quantlib-rules.md` — reactivity, static exploration, reproducibility, QuantLib conventions and pitfalls.
- `references/quantlib-144-api-notes.md` — verified 1.44 signatures and traps: dates and enums, bond risk functions, handles, SwaptionHelper calibration, simulation, RiskStatistics.
- `references/mermaid-diagrams.md` — rules, vocabulary, diagram type per job, T1–T14 menu, patterns, import graph. **Before any diagram.**
- `assets/notebook_template.py` — runnable T3 European option, publishing functions, front (quoting) and middle (IPV) examples.
- `assets/examples/european_option_t2_modeling.py` — upstream publishing market/instrument builders.
- `assets/common/` — `bump.py`, `sim.py`, `plotting.py`, `diagrams.py`.
- `scripts/check_mermaid.py` — parses recorded diagrams with the real Mermaid parser (Node; `npm install` once in `scripts/`).

## Output when delivering

Notebook path(s), prerequisites, imports from, publishes, QuantLib features and desk applications covered or skipped (reasons), diagrams, validated/how, unrun (incl. Mermaid parsing, visual review), next (instrument, theme). Short; the notebook is the deliverable.
