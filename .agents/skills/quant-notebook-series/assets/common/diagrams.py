"""Mermaid helpers: one shared visual vocabulary for static structure diagrams.

Use Mermaid for STRUCTURE (layers, object graphs, pipelines, decision trees, who pays
whom and when). Use matplotlib (`plotting.py`) for anything with quantities on axes.
See references/mermaid-diagrams.md.

`diagram()` renders with `mo.mermaid` (a ```mermaid fence inside `mo.md` does NOT render
in marimo), applies the series colour classes, and fails loudly on the mistakes that
would otherwise only show up in the reader's browser. Static only: no `click`, no widgets.

Set the environment variable MERMAID_DUMP=<file> and every diagram source is appended to
that file as JSON lines; `scripts/check_mermaid.py` uses this to parse them headlessly.
"""
from __future__ import annotations

import json
import os
import re
import textwrap

import marimo as mo

# Series colour vocabulary: the same Okabe-Ito hues as plotting.PALETTE, always with explicit
# dark text so nodes stay readable in light and dark mode. One meaning per colour, series-wide.
CLASSDEFS = """\
classDef instrument fill:#56B4E9,stroke:#0072B2,stroke-width:1.5px,color:#000
classDef market fill:#E69F00,stroke:#8A5F00,stroke-width:1.5px,color:#000
classDef model fill:#CC79A7,stroke:#7A3D62,stroke-width:1.5px,color:#000
classDef engine fill:#009E73,stroke:#00573F,stroke-width:1.5px,color:#000
classDef output fill:#F0E442,stroke:#8C8500,stroke-width:1.5px,color:#000
classDef risk fill:#D55E00,stroke:#7A3600,stroke-width:1.5px,color:#000
classDef neutral fill:#E5E7EB,stroke:#6B7280,stroke-width:1.5px,color:#000"""

# classDef is understood by these diagram types only.
_STYLED = ("flowchart", "graph", "stateDiagram", "stateDiagram-v2")
# Stable diagram types. The *-beta types depend on the Mermaid version bundled with marimo.
_ALLOWED = _STYLED + ("sequenceDiagram", "classDiagram", "timeline", "mindmap",
                      "erDiagram", "gantt")


def _body_lines(src: str) -> list[str]:
    """Diagram lines without front matter and %% comment/directive lines."""
    lines = src.splitlines()
    if lines and lines[0].strip() == "---":  # YAML front matter
        end = next((i for i, ln in enumerate(lines[1:], 1) if ln.strip() == "---"), 0)
        lines = lines[end + 1:]
    return [ln for ln in lines if ln.strip() and not ln.strip().startswith("%%")]


def lint(src: str) -> list[str]:
    """Cheap structural problems that break rendering. Empty list = nothing found.

    This is NOT a full parser. `scripts/check_mermaid.py` runs the real Mermaid parser.
    """
    problems: list[str] = []
    lines = _body_lines(src)
    if not lines:
        return ["empty diagram"]
    kind = lines[0].split()[0]
    if kind.endswith("-beta"):
        problems.append(f"'{kind}' is version-dependent; use matplotlib or a stable type")
    elif kind not in _ALLOWED:
        problems.append(f"unknown or unsupported diagram type '{kind}'")
    code = "\n".join(lines)  # without front matter and %% lines (init directives contain '}}')
    if re.search(r"^\s*(click|callback|link)\s", code, flags=re.M):
        problems.append("interactive directives (click/callback/link) are not allowed")
    if "{{" in code or "}}" in code:
        problems.append("'{{' or '}}' found: unresolved placeholder or f-string artefact")
    if re.search(r"\$\{?[A-Za-z_]\w*", code):
        problems.append("unresolved $name from string.Template (use .substitute)")
    unquoted = re.sub(r'"[^"\n]*"', "", code)  # brackets inside quoted labels are fine
    for open_, close in ("[]", "()", "{}"):
        if unquoted.count(open_) != unquoted.count(close):
            problems.append(f"unbalanced '{open_}{close}'")
    return problems


def _record(src: str, caption: str | None) -> None:
    path = os.environ.get("MERMAID_DUMP")
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"source": src, "caption": caption}) + "\n")


def diagram(body: str, caption: str | None = None, styled: bool = True):
    """Render a static Mermaid diagram, with the takeaway as an italic caption below.

    body    Mermaid source. Use a plain string (NOT an f-string: Mermaid uses braces); to
            insert values use `string.Template(...).substitute(...)` or concatenation.
    caption One sentence stating what the reader should conclude (like a plot title).
            The caption must carry the message on its own: the diagram is drawn by the
            browser, so text and script exports do not show it.
    styled  Append the series colour classes (flowchart / graph / stateDiagram only);
            then tag nodes with `class A,B instrument` or `A:::instrument`.
    """
    src = textwrap.dedent(body).strip()
    problems = lint(src)
    if problems:
        raise ValueError("Mermaid diagram problems: " + "; ".join(problems))
    if styled and _body_lines(src)[0].split()[0] in _STYLED:
        src = src + "\n" + CLASSDEFS
    _record(src, caption)
    figure = mo.mermaid(src)
    return mo.vstack([figure, mo.md("*" + caption + "*")]) if caption else figure
