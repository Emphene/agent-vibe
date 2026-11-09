"""Generic, instrument-agnostic helpers only (plotting, diagrams, simulation, bump-and-reval).

Instrument- or theme-specific code (market builders, pricers, closed forms, exposure
engines) does NOT belong here. It lives in the notebook that defines it, as
@app.function / @app.class_definition, and later notebooks import it from there.
See references/code-reuse-by-import.md.
"""
