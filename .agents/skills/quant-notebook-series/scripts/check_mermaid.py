#!/usr/bin/env python3
"""Validate the Mermaid diagrams of one or more notebooks without opening a browser.

usage: python scripts/check_mermaid.py notebooks/european_option_t3_pricing.py [...]

1. Runs each notebook as a script with MERMAID_DUMP set, so every `diagram(...)` call
   appends its source to a temp file. (`common/diagrams.py` already lints on the way.)
2. Parses each recorded diagram with the real Mermaid parser (Node, one-time setup:
   `cd scripts && npm install`). Without Node/Mermaid it says so and exits 2 instead of
   pretending the syntax was checked.

Not covered: layout quality (overlapping labels, unreadable size). Look at the rendered
notebook (`marimo run` or `marimo export html`) for that, or report it as not reviewed.
Exit codes: 0 all good, 1 a notebook or diagram failed, 2 parser unavailable (only linted).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run_notebook(nb: Path, dump: Path) -> bool:
    env = {**os.environ, "MERMAID_DUMP": str(dump)}
    proc = subprocess.run([sys.executable, nb.name], cwd=nb.parent, env=env,
                          capture_output=True, text=True)
    if proc.returncode:
        print(f"  FAIL  notebook did not run (a diagram lint error also stops it):\n"
              + "\n".join("        " + ln for ln in proc.stderr.strip().splitlines()[-8:]))
    return proc.returncode == 0


def main(paths: list[str]) -> int:
    if not paths:
        print(__doc__)
        return 1
    parser_ready = shutil.which("node") and (HERE / "node_modules" / "mermaid").exists()
    status = 0
    for name in paths:
        nb = Path(name).resolve()
        print(nb.name)
        with tempfile.TemporaryDirectory() as tmp:
            dump = Path(tmp) / "diagrams.jsonl"
            if not run_notebook(nb, dump):
                status = 1
                continue
            count = len(dump.read_text().splitlines()) if dump.exists() else 0
            if count == 0:
                print("  note  no diagrams recorded (none in this notebook, or not via diagram())")
                continue
            if not parser_ready:
                print(f"  lint only: {count} diagram(s) passed the structural lint; Mermaid "
                      f"parser unavailable (cd scripts && npm install)")
                status = status or 2
                continue
            rc = subprocess.run(["node", str(HERE / "mermaid_parse.mjs"), str(dump)]).returncode
            status = 1 if rc else status
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
