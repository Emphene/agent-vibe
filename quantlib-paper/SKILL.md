---
name: quantlib-paper
description: Implement a quantitative finance research paper as an interactive marimo notebook together with the user. Start by understanding what the user wants to explore, fetch the paper via alphaxiv or a local PDF, then build, validate, and reproduce a focused notebook.
---

# Implement Paper

Turn a quantitative finance research paper into an interactive marimo notebook. For general marimo notebook conventions (cell structure, PEP 723 metadata, output rendering, `marimo check`, variable naming, etc.), refer to the `marimo-notebook` skill.

## Step 1: Understand what the user wants

Before fetching or reading anything, have a short conversation to scope the work. Ask the user:

- **Which part of the paper interests you most?** A paper may have multiple contributions — the user likely cares about one or two. Don't implement the whole thing.
- **What's the goal?** Are they trying to understand the method, reproduce a result, adapt it to their own data, or teach it to someone else? This changes the notebook's tone and depth.
- **Do they want to use a specific dataset?** If it's relevant, ask. Otherwise, suggest simulating data.

Only move on once you have a clear picture of what to build.

## Step 2: Fetch the paper

1. Parse the ID from whatever the user provides (`https://arxiv.org/abs/2401.12345` → `2401.12345`). Keep any `v2` suffix.
2. Fetch the AI-generated overview first: `curl -sL "https://alphaxiv.org/overview/{ID}.md"`. Always pass `-L`.
3. If the overview lacks needed detail (a specific equation, table, proof), fetch full text: `curl -sL "https://alphaxiv.org/abs/{ID}.md"`.
4. On 404 for both, or if the user supplies a local PDF / non-Arxiv URL, use the `pdftotext` path: download first if needed, then extract selectively (`pdftotext -f 3 -l 6 paper.pdf -`).

Do not pass a PDF to `read_files` directly — extract text with `pdftotext` first. See [references/fetching-papers.md](references/fetching-papers.md) for ID parsing, selective extraction, and error handling.

## Step 3: Plan the notebook

After reading the paper, outline the notebook structure for the user before writing code.

Prefer QuantLib engines where they exist (vanilla pricing, curves, schedules, calendars/day-counts). Otherwise use numpy/scipy directly and cross-check against QuantLib where possible. State in the outline which path each section uses.

A typical arc:

| Section | Purpose | Typical elements |
|---------|---------|------------------|
| Title & context | Orient the reader | `mo.md()` with paper title, authors, link |
| Background | Set up prerequisites | Markdown + equations |
| Method | Core algorithm step-by-step | Code + markdown interleaved |
| Experiments | Reproduce key results | Interactive widgets + plots |
| Conclusion | Summarize takeaways | `mo.md()` |

Not every notebook needs all sections. Share the outline with the user and **wait for approval before writing code** — do not start the notebook until the outline is settled.

## Step 4: Build the notebook

Create the marimo notebook following the `marimo-notebook` skill conventions. For QuantLib pricing conventions, day counts, calendar handling, and SWIG bindings gotchas, consult the [QuantLib-Python docs](https://quantlib-python-docs.readthedocs.io/en/latest/) and verify each binding against the pinned version (`dir(ql)`, exact constructor overloads) rather than assuming the C++ API is wrapped.

Work in two stages, in order (validation is Step 5):

### 4a. Model
- **Never assume the dataset.** Use whatever the user specified in Step 1. If they didn't specify one, simulate data.
- **Make it self-contained.** A reader should understand the notebook without reading the full paper.
- **Use KaTeX for equations.** Render key equations with `mo.md(r"""$...$""")` so the notebook mirrors the paper's notation. Keep notation consistent with the paper.
- **If the paper uses heavy notation**, include a small "notation reference" cell with a markdown table mapping symbols to descriptions.
- **Set up market plumbing as its own stage** — calendars, day-count conventions, currencies, and quote types — before any model code.

### 4b. Implementation
- **Every model/pricing cell carries a comment naming the equation(s) it implements** (e.g., `# Eq. (12): stochastic variance process`). Plumbing, widget, and plot-only cells are exempt. The reader should be able to move between the markdown and the code without hunting.
- **Use paper notation for locals, descriptive names for marimo globals.** Paper-notation globals (`alpha`, `X`, `W`) collide across cells in marimo's reactive DAG — keep them local inside a cell, and expose shared values with descriptive names (e.g. `kappa_meanrev` for $\kappa$) or bundle a model in one cell returning a dict/dataclass.
- **Bracket process-wide QuantLib state.** Re-running a cell re-executes `ql.Settings.instance().evaluationDate = ...` and `index.addFixing(...)`. Set the evaluation date at the top of the plumbing cell, and guard duplicate fixings (e.g. `ql.IndexManager.instance().clearHistories()` or add only if not already recorded), so re-running one cell doesn't poison or crash the rest.
- **Fix all random seeds** and expose the seed as a variable where Monte Carlo is involved, so results are reproducible.
- **Show, don't just tell.** Prefer a plot or table over a paragraph of explanation.
- **Iterate visually.** Build up figures incrementally (show data → show model fit → show residuals) rather than dumping everything into one plot.

## Step 5: Validate the reproduction

Before presenting the notebook as done:

- **Reproduce at least one headline number from the paper** and place your result next to the paper's reported value.
- **Add at least one assertion cell** so the notebook fails loudly instead of silently drifting. Pick the tolerance for the method: ~`1e-6` for analytic vs. QuantLib (e.g. `assert abs(price - paper_value) < 1e-6`), wider for simulation (e.g. 2–3x Monte Carlo std-err) with the seed fixed and noted.
- **Cross-check against an independent implementation when one exists** — the paper's method vs. a QuantLib engine, or Monte Carlo vs. an analytic formula. Agreement between two independent paths is the strongest evidence the implementation is right.
- **Report deviations honestly.** If the numbers don't match, show the gap and the likely cause; do not tune parameters until they agree.
- **Re-run the notebook end to end** to confirm it works from a fresh kernel: `uvx marimo check <notebook.py>` lints statically but does not execute cells — actually execute with script mode (`uv run <notebook.py>`). In script mode keep all widgets displayed and only swap the data source to synthetic/defaults — follow the `is_script_mode` pattern in the `marimo-notebook` skill, don't gate widgets behind conditionals.

## Conventions

- **Save to** `notebooks/<arxiv-id>-<slug>.py` (e.g. `notebooks/2401-12345-heston-smile.py`). If the paper has no arxiv ID (local PDF), use `notebooks/<slug>.py`.
- **PEP 723 deps** must include `marimo`, `QuantLib` (the repo floor is `>=1.44` — match it with `>=` rather than hard-pinning; re-verify SWIG bindings against the pinned version on upgrade), plus `numpy`/`matplotlib` as needed.
- **Cite, don't paste.** Title cell carries paper title, authors, and link. Do not paste large excerpts or figures from the paper.

## Tips

- **If no headline number exists, reproduce a figure shape qualitatively** (smile skew, term-structure slope) and assert on the shape property, not the level.
- **For UI elements** (`mo.ui.slider`, tables) see `marimo-notebook/references/UI.md` — Experiments sections should stay interactive in `marimo run` and still pass in script mode.

