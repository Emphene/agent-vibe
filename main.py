"""
main.py — Vibe (agent-vibe) orchestrator loop wired to the Centralized AI
Skills Architecture.

On startup it absorbs the latest shared skills from the Central Brain
(central-brain), runs its task, and publishes skill updates back to
the Central Brain for every other agent to pick up.
"""

import importlib.util
import os
from pathlib import Path

# Load the sync engine BY PATH from this repo's skill-discovery directory —
# the directory the agent CLI itself scans for skills (OpenCode, Oh My Pi,
# MiMo Code and Pi scan `.agents/skills/`; Claude Code scans
# `.claude/skills/`), which is also where the git subtree from the Central
# Brain lands. The name is a dotted directory that no `import` statement can
# express, hence importlib. This is the only line to adjust when onboarding
# a new agent CLI.
SKILLS_DIR = Path(__file__).resolve().parent / ".agents" / "skills"

_spec = importlib.util.spec_from_file_location(
    "sync_engine", SKILLS_DIR / "sync_engine.py"
)
engine = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(engine)

# Setup environment details
LOCAL_WORKSPACE = os.getcwd()
# PAT is never hardcoded: credentials come from git's credential helper
# (`git config --global credential.helper store`, fed once with a repo-scoped PAT).
AUTHENTICATED_CENTRAL_REPO = os.environ.get("CENTRAL_SKILLS_REPO", engine.CENTRAL_BRAIN_URL)

print("--- AGENT INITIALIZATION ---")
# 1. Pull the latest skills from other agents on startup
sync_status = engine.auto_pull_latest_skills(LOCAL_WORKSPACE, AUTHENTICATED_CENTRAL_REPO)
print(sync_status)

# 1b. Make the venv reflect the shared requirements.txt (e.g. after the
#     Central Brain published a quantlib upgrade)
print(engine.sync_env(LOCAL_WORKSPACE))

print("\n--- AGENT RUNNING WORKSPACE TASK ---")
# 2. Simulate the agent completing its task and improving a shared skill.
#    In a real agent this is where the task runs; when reusable knowledge is
#    discovered, add it to the relevant skill folder:
note = (
    "- Pin the QuantLib evaluation date explicitly before pricing "
    "instruments."
)
skills_file_path = SKILLS_DIR / "quantlib-paper" / "references" / "quantlib-notes.md"
known_notes = skills_file_path.read_text() if skills_file_path.exists() else ""
if note in known_notes:
    print("ℹ️ Skill note already recorded — nothing new to publish this run.")
else:
    skills_file_path.parent.mkdir(parents=True, exist_ok=True)
    with skills_file_path.open("a") as f:
        f.write(f"\n{note}\n")
    print(f"📝 Agent updated {skills_file_path.relative_to(LOCAL_WORKSPACE)}.")

print("\n--- AUTOMATED UPSTREAM SYNC ---")
# 3. Trigger the automatic push back to the Central Brain
push_status = engine.auto_push_skills(
    agent_repo_path=LOCAL_WORKSPACE,
    central_repo_url=AUTHENTICATED_CENTRAL_REPO,
    commit_message="agent-vibe-sync: documented QuantLib evaluation-date rule.",
)
print(push_status)
