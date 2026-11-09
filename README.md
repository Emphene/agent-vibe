# agent-vibe

agent-vibe — agent workspace wired into the **Centralized AI Skills
Architecture**: this repo mirrors the shared QuantLib/marimo skills from the
Central Brain
([`Emphene/central-brain`](https://github.com/Emphene/central-brain))
in a `.agents/skills/` git subtree, and can publish everything it learns back
so every other agent absorbs it. The subtree sits in **this agent CLI's
native skill-discovery directory** (`.agents/skills/` for OpenCode, Oh My Pi,
MiMo Code, Pi and Vibe, `.claude/skills/` for Claude Code), so the agent
itself loads the synced skills directly — no manual registration step.

> **Generated file.** Rendered from `.agents/skills/templates/README.md.tmpl`
> by `sync-docs` (runs automatically on every skills-sync `pull`).

## Architecture

```
central-brain (Central Brain)
 ├─ main .............. whole project; .agents/skills/ = mirror of the skills line
 └─ skills-split ...... skills-only publishing line (canonical, orphan branch)
        ▲            ▲
   subtree push   subtree pull (NEVER squashed)
        │            │
agent-oc            agent-cc            agent-omp           agent-mimo          agent-pi            agent-vibe        (future agents: same pattern)
```

- **`skills-split`** carries *only* the skills tree, so subtree push/pull stays
  fast-forward in both directions. Pushing agent changes directly onto the
  Central Brain's `main` would be non-fast-forward (`main` holds the whole
  project) and GitHub would reject it.
- **`main` in the Central Brain** is a *mirror* of `skills-split` under
  `.agents/skills/`, updated by `promote` (a history-linked, ours-strategy
  merge), so the skills stay browsable and editable there.
- Both branches are kept ancestry-linked, which is what makes every
  `git subtree push` a fast-forward instead of a rejection.

## Repository layout

| Path | Purpose |
|---|---|
| `.agents/skills/` | Subtree mirrored from `skills-split`: skill folders (each with a `SKILL.md`), `sync_engine.py`, `templates/` |
| `main.py` | Orchestrator demo: pull → run task → publish skill edits |
| `AGENTS.md` | Agent instructions — **rendered** from `.agents/skills/templates/AGENTS.md.tmpl` |
| `README.md` | This file — **rendered** from `.agents/skills/templates/README.md.tmpl` |
| `requirements.txt` | **Rendered** from the Central Brain's `uv.lock` export; drives `sync-env` |
| [`AI Skills Architecture.md`](https://github.com/Emphene/central-brain/blob/main/AI%20Skills%20Architecture.md) | As-built setup guide — hosted in the Central Brain, never copied into agent repos |
| `.venv/` | Python environment (gitignored), kept in sync by `sync-env` |

## Quickstart

```bash
# absorb the latest skills + rendered docs (also re-renders this file),
# then make the venv match the shared requirements.txt
.venv/bin/python .agents/skills/sync_engine.py pull
.venv/bin/python .agents/skills/sync_engine.py sync-env

# run the demo cycle (pull -> update a skill -> publish)
.venv/bin/python main.py
```

## Sync commands

```bash
# agent side (run from an agent repo root)
.venv/bin/python .agents/skills/sync_engine.py pull                    # absorb skills + re-render root files
.venv/bin/python .agents/skills/sync_engine.py sync-env                # .venv ← requirements.txt (uv pip sync)
.venv/bin/python .agents/skills/sync_engine.py push -m "agent-vibe-sync: <what/why>"   # publish skill edits
.venv/bin/python .agents/skills/sync_engine.py sync-docs --push       # render AGENTS.md/README.md only

# central side (run from central-brain)
python .agents/skills/sync_engine.py promote                          # fold skills-split back into main
python .agents/skills/sync_engine.py central-push -m "..."            # publish skill edits made on main
python .agents/skills/sync_engine.py export-requirements              # uv.lock -> templates/requirements.txt.tmpl
```

When to sync: **pull at session start**, **`sync-env` right after (or whenever
the Central Brain published a dependency upgrade)**, **push after updating a
skill** (see [AGENTS.md](AGENTS.md)), and ask the user to run **`promote`**
periodically — skill edits only reach the Central Brain's `main` after a
promote.

### Dependency upgrades (e.g. quantlib)

Dependencies flow one way, from the Central Brain's `uv.lock`:

```bash
# in central-brain
uv lock --upgrade-package quantlib && uv sync
python .agents/skills/sync_engine.py export-requirements
python .agents/skills/sync_engine.py central-push -m "deps: upgrade quantlib to <version>"

# in every agent
.venv/bin/python .agents/skills/sync_engine.py pull
.venv/bin/python .agents/skills/sync_engine.py sync-env
```

## Hard rules

1. **Never `git subtree pull/add ... --squash`** here. A squash pull severs
   the link to `skills-split` history and every later subtree push is rejected
   as non-fast-forward. This repo's subtree was added with:

   ```bash
   git subtree add --prefix=.agents/skills/ https://github.com/Emphene/central-brain.git skills-split
   ```

2. Never `git push --force` to `skills-split`.
3. Don't commit `.agents/skills/` changes without publishing them via `push`.
4. If `push` is rejected non-fast-forward, another agent published meanwhile:
   run `pull`, resolve, retry.
5. Don't hand-edit root `AGENTS.md`/`README.md` — they are generated from
   `.agents/skills/templates/`; change the template and republish instead.
6. Don't hand-edit root `requirements.txt` — it is exported from the Central
   Brain's `uv.lock`; upgrade via `export-requirements` + `central-push`
   there, then `pull` + `sync-env` here.

## Authentication

Pushes are unattended: the PAT (repo scope) is stored once via

```bash
git config --global credential.helper store
printf 'protocol=https\nhost=github.com\nusername=Emphene\npassword=<PAT>\n' | git credential approve
```

No token is embedded in any file or remote URL. See the
[AI Skills Architecture guide](https://github.com/Emphene/central-brain/blob/main/AI%20Skills%20Architecture.md)
Phase 2.
