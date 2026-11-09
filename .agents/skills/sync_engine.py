"""
sync_engine.py — synchronization engine for the Centralized AI Skills Architecture.

Topology
--------
Central Brain: https://github.com/Emphene/central-brain.git
  * branch ``main``          — the whole project (notebooks/, docs/, .agents/skills/, ...)
  * directory ``.agents/skills/`` — the shared, cross-agent skills (SKILL.md folders)
  * branch ``skills-split``  — an orphan branch containing ONLY the skills tree.

    ``skills-split`` is the canonical publishing line. It exists so ``git
    subtree push/pull`` stays fast-forward in both directions: pushing agent
    changes directly onto ``main`` would be a non-fast-forward push (``main``
    contains the entire project) and GitHub would reject it.

Agent repos (agent-oc, agent-cc, agent-omp, agent-mimo,
agent-pi, ...)
  * directory ``<skills-dir>/`` — a git subtree fed from ``skills-split``,
    where ``<skills-dir>`` is the agent CLI's NATIVE skill-discovery
    directory, so synced skills are loaded by the agent running in that
    workspace:
        agent-oc   ->  .agents/skills/    (OpenCode)
        agent-cc   ->  .claude/skills/    (Claude Code)
        agent-omp  ->  .agents/skills/    (Oh My Pi)
        agent-mimo ->  .agents/skills/    (MiMo Code)
        agent-pi   ->  .agents/skills/    (Pi)
    The engine derives the prefix from its own location (see
    ``resolve_agent_prefix``); override with ``AGENT_SKILLS_DIR`` or
    ``--prefix``.

CRITICAL RULE: NEVER use --squash with subtree pull/add in this architecture.
A squash pull severs the link to ``skills-split`` history, and every later
``subtree push`` builds a new root commit that GitHub rejects as
non-fast-forward. New agents MUST add the subtree with:

    git subtree add --prefix=<skills-dir>/ <central-url> skills-split

(omitting --squash). The skills history is tiny, so keeping it is cheap.

Workflow
--------
  1. On startup    -> auto_pull_latest_skills(...)         # absorb skills from other agents
  2. Agent learns  -> writes/edits files under <skills-dir>/
  3. After a task  -> auto_push_skills(...)                # publish skill edits to skills-split
  4. Skill edits made INSIDE the Central Brain (main branch)
       -> push_central_skills_edit(...)                    # publish to skills-split
  5. Periodically  -> promote_skills_split_to_main(...)    # fold skills-split back
                                                             into main at .agents/skills/
  6. Agent docs    -> render_agent_docs(...) / `sync-docs`  # root AGENTS.md + README.md
                       are rendered from <skills-dir>/templates/*.tmpl so every
                       agent's docs stay aligned; runs automatically on every pull.
  7. Env sync      -> export_requirements(...) (Central Brain: uv export from its
                       uv.lock into templates/requirements.txt.tmpl) and sync_env(...)
                       (agents: uv pip sync -r requirements.txt; Central Brain: uv sync)
                       so every venv reflects the same pinned dependency set —
                       e.g. after a quantlib upgrade in the Central Brain.
"""

import os
import shutil
import subprocess

from git import GitCommandError, Repo

# --------------------------------------------------------------------------
# Defaults
# --------------------------------------------------------------------------
CENTRAL_BRAIN_URL = "https://github.com/Emphene/central-brain.git"
SPLIT_BRANCH = "skills-split"           # branch carrying ONLY the skills tree
FALLBACK_AGENT_PREFIX = "shared_skills/"  # used only when no enclosing repo is found
CENTRAL_PREFIX = ".agents/skills/"      # where skills live in the Central Brain's main


def resolve_agent_prefix(prefix: str | None = None) -> str:
    """Resolve the agent-side skills subtree prefix (always ``.../``-suffixed).

    The prefix doubles as the agent CLI's skill-discovery directory, so the
    synced skills are picked up by the agent working in that workspace:
    ``.agents/skills/`` for an OpenCode, Oh My Pi, MiMo Code or Pi agent,
    ``.claude/skills/`` for a Claude Code agent.  Resolution order:

      1. an explicit ``prefix`` argument / ``--prefix`` CLI flag;
      2. the ``AGENT_SKILLS_DIR`` environment variable;
      3. this engine file's own directory relative to the enclosing git
         repository — agents run the engine *from inside the subtree*, so
         where the engine lives IS the prefix
         (``.agents/skills/sync_engine.py`` -> ``.agents/skills/``);
      4. ``shared_skills/`` as a last resort when the engine's location cannot
         be tied to a repository.

    Key property: the same engine file works unchanged in every agent repo —
    each repo's prefix follows its CLI's discovery convention automatically.
    """
    if prefix:
        return prefix if prefix.endswith("/") else f"{prefix}/"
    env = os.environ.get("AGENT_SKILLS_DIR")
    if env:
        return env.rstrip("/") + "/"
    here = os.path.dirname(os.path.abspath(__file__))
    node = here
    while True:
        if os.path.exists(os.path.join(node, ".git")):
            rel = os.path.relpath(here, node)
            if rel in (".", os.curdir):
                break  # engine at repo root: fall through to the fallback
            return rel.replace(os.sep, "/").rstrip("/") + "/"
        parent = os.path.dirname(node)
        if parent == node:
            break  # walked past the filesystem root: no .git found
        node = parent
    return FALLBACK_AGENT_PREFIX


def auto_push_skills(
    agent_repo_path: str,
    central_repo_url: str,
    commit_message: str,
    prefix: str | None = None,
    split_branch: str = SPLIT_BRANCH,
) -> str:
    """Stage, commit and publish a shared-skill update to the Central Brain.

    Commits any changes under ``prefix`` (default: this engine file's own
    directory, i.e. the agent CLI's skill-discovery dir), pushes them to the
    agent repo's own origin, then subtree-pushes to the Central Brain's
    ``skills-split`` branch. Run ``promote_skills_split_to_main`` in the
    Central Brain afterwards to fold the update into ``main``.
    """
    prefix = resolve_agent_prefix(prefix)
    try:
        repo = Repo(agent_repo_path)
        if repo.bare:
            return "❌ Error: Invalid repository."

        status = repo.git.status("--porcelain", prefix)
        if not status:
            return f"ℹ️ No changes detected in '{prefix}'. Nothing to sync."

        print(f"🔍 Changes detected in '{prefix}'. Committing locally...")
        repo.git.add(prefix)
        repo.index.commit(commit_message)

        print("🚀 Pushing to Agent's repository...")
        repo.remote(name="origin").push()

        print(f"🚀 Pushing subtree to Central Brain branch '{split_branch}'...")
        repo.git.subtree("push", f"--prefix={prefix}", central_repo_url, split_branch)

        return (
            f"🎉 Success! Skill edits pushed to the Central Brain "
            f"(branch '{split_branch}'). Run promote_skills_split_to_main() in "
            f"the Central Brain to fold them into 'main'."
        )
    except GitCommandError as e:
        if "non-fast-forward" in str(e) or "fetch first" in str(e):
            return (
                "❌ Git Push Error: another agent published to skills-split "
                f"since our last pull. Run auto_pull_latest_skills() first, "
                f"resolve any conflicts, then retry. Details: {e}"
            )
        return f"❌ Git Push Error: {str(e)}"


def auto_pull_latest_skills(
    agent_repo_path: str,
    central_repo_url: str,
    prefix: str | None = None,
    split_branch: str = SPLIT_BRANCH,
) -> str:
    """Pull the latest global skills from the Central Brain into the agent workspace.

    Deliberately NOT squashed: the merge keeps the ``skills-split`` commits in
    this repo's history, which is what makes later ``subtree push`` calls
    fast-forward instead of rejected.
    """
    prefix = resolve_agent_prefix(prefix)
    try:
        repo = Repo(agent_repo_path)
        if repo.is_dirty(untracked_files=True):
            return "⚠️ Warning: Please commit or stash local agent changes first."

        print(f"🔄 Pulling latest shared skills from Central Brain ('{split_branch}')...")
        repo.git.subtree(
            "pull",
            f"--prefix={prefix}",
            central_repo_url,
            split_branch,
            "-m",
            "merge: sync central skills",
        )

        # Keep the root docs aligned with the central templates on every pull.
        _render_and_commit_docs(
            repo, prefix, f"chore: re-render root files from central templates ({split_branch})"
        )

        repo.remote(name="origin").push()
        return "🎉 Success! Agent skills are now completely up to date."
    except GitCommandError as e:
        return f"❌ Git Pull Error: {str(e)}"


def _link_split_into_main(
    repo: Repo, central_repo_url: str, split_branch: str, message: str
) -> bool:
    """Fetch ``skills-split`` and record it as a merge parent of HEAD (ours tree).

    Makes ``main`` a descendant of ``skills-split`` WITHOUT touching any
    content — the hard requirement for a later ``subtree push --prefix`` to be
    a fast-forward. Returns True if a linking merge commit was created.
    """
    repo.git.fetch(central_repo_url, f"{split_branch}:{split_branch}")
    # Commits reachable from skills-split but not from HEAD:
    missing = repo.git.rev_list(f"HEAD..{split_branch}").strip()
    if not missing:
        return False  # HEAD already contains every skills-split commit
    print(f"🔗 Linking '{split_branch}' into main (ours tree kept)...")
    # skills-split is an orphan branch, so the very first link in a fresh
    # Central Brain has no common ancestor — git needs explicit permission.
    repo.git.merge(
        "-s", "ours", "--allow-unrelated-histories", split_branch, "-m", message
    )
    return True


def promote_skills_split_to_main(
    central_repo_path: str,
    central_repo_url: str,
    commit_message: str = "skills: sync agent skill edits into main",
    prefix: str = CENTRAL_PREFIX,
    split_branch: str = SPLIT_BRANCH,
) -> str:
    """Fold the Central Brain's ``skills-split`` branch back into ``main``.

    Must be run INSIDE the Central Brain checkout (or with --repo pointing at
    it). Procedure:
      1. fetch skills-split;
      2. record it as a merge parent with the 'ours' strategy (links history);
      3. overlay the skills tree at ``.agents/skills/`` with a prefixed
         read-tree, then commit (amending the fresh merge commit).
    Refuses to run when nothing is waiting on ``skills-split`` and main's
    prefix diverged from the published tree — that means unpublished
    central-side edits which the overlay would overwrite (publish those with
    ``push_central_skills_edit`` instead).
    Afterwards ``main`` is a descendant of ``skills-split``, so skill edits
    made on ``main`` can themselves be subtree-pushed back with
    ``push_central_skills_edit``.
    """
    try:
        repo = Repo(central_repo_path)
        if repo.is_dirty(untracked_files=True):
            return "⚠️ Warning: Please commit or stash Central Brain changes first."

        print(f"🔄 Fetching '{split_branch}' from {central_repo_url}...")
        linked = _link_split_into_main(repo, central_repo_url, split_branch, commit_message)

        # Safety guard: promote FOLDS agent-side skill changes back into main; it
        # must never be the path that (re)writes main's prefix. If no new split
        # commits are waiting AND main's prefix diverged from the published
        # tree, the only way the overlay could "change" anything is by
        # OVERWRITING unpublished central-side edits — refuse instead.
        prefix_tree = repo.git.rev_parse(f"HEAD:{prefix.rstrip('/')}").strip()
        split_tree = repo.git.rev_parse(f"{split_branch}^{{tree}}").strip()
        if not linked and prefix_tree != split_tree:
            return (
                f"⚠️ Nothing to promote from '{split_branch}', but {prefix} on "
                "'main' contains edits that were never published (they are not "
                f"on '{split_branch}'). Promote would OVERWRITE them with the "
                "published tree — publish them first with "
                "`central-push -m \"...\"`, then re-run promote if needed."
            )

        print(f"🔀 Overlaying skills tree at {prefix}...")
        # `read-tree --prefix` can only bind NEW paths ("Cannot bind" on
        # anything already in the index), so clear the prefix first. The tree
        # is guaranteed clean here (checked above), so nothing is lost.
        repo.git.rm("-r", "--quiet", "--ignore-unmatch", prefix)
        repo.git.read_tree(f"--prefix={prefix}", "-u", split_branch)
        if repo.is_dirty(index=True, working_tree=False):
            if linked:
                repo.git.commit("--amend", "-m", commit_message)
            else:
                repo.index.commit(commit_message)
            changed = True
        else:
            changed = False

        repo.remote(name="origin").push()
        if changed:
            return f"🎉 Success! '{split_branch}' has been merged into 'main' at {prefix}."
        return f"ℹ️ '{split_branch}' already up to date in 'main' (no content changes)."
    except GitCommandError as e:
        return f"❌ Git Promote Error: {str(e)}"


def _publish_prefix_tree(
    repo: Repo,
    central_repo_url: str,
    prefix: str,
    split_branch: str,
    commit_message: str,
) -> bool:
    """Commit main's ``<prefix>`` tree directly onto ``skills-split`` (snapshot
    commit: tree = main's prefix, parent = current split tip) and push it.

    Returns False when the split tip already mirrors main's prefix.

    This replaces ``git subtree push`` for Central-Brain publishing: subtree
    split rebuilds main's *entire* prefix history (main-side commits are not
    part of the split lineage) and the resulting chain is never a descendant
    of ``skills-split``, so GitHub rejects it as non-fast-forward. A single
    snapshot commit parented on the tip is always a fast-forward and keeps
    agent pulls/merges working unchanged.
    """
    prefix = prefix.rstrip("/")
    prefix_tree = repo.git.rev_parse(f"HEAD:{prefix}").strip()
    split_tree = repo.git.rev_parse(f"{split_branch}^{{tree}}").strip()
    if prefix_tree == split_tree:
        return False
    tip = repo.commit(split_branch).hexsha
    new = repo.git.commit_tree(
        prefix_tree, "-p", tip, "-m", commit_message
    ).strip()
    print(f"🚀 Pushing skills snapshot {new[:7]} onto '{split_branch}' (fast-forward)...")
    repo.git.push(central_repo_url, f"{new}:refs/heads/{split_branch}")
    return True


def push_central_skills_edit(
    central_repo_path: str,
    central_repo_url: str,
    commit_message: str,
    prefix: str = CENTRAL_PREFIX,
    split_branch: str = SPLIT_BRANCH,
) -> str:
    """Publish skill edits made directly in the Central Brain's ``main`` branch.

    Steps: fetch ``skills-split`` (refusing to publish if agents have skill
    edits you haven't promoted yet), commit pending changes under ``prefix``, push
    main's prefix tree as a snapshot commit onto ``skills-split``, then record
    that tip in ``main`` with a history-linking merge so both lines stay
    ancestry-synced.
    """
    try:
        repo = Repo(central_repo_path)
        print(f"🔄 Fetching '{split_branch}' from {central_repo_url}...")
        repo.git.fetch(central_repo_url, f"{split_branch}:{split_branch}")
        missing = repo.git.rev_list(f"HEAD..{split_branch}").strip()
        if missing:
            return (
                "⚠️ Agents published to skills-split since your last promote. "
                "Commit (or stash) your edits, run `promote`, then re-run "
                "central-push — otherwise their changes would be overwritten."
            )

        status = repo.git.status("--porcelain", prefix)
        if status:
            print(f"🔍 Changes detected in '{prefix}'. Committing locally...")
            repo.git.add(prefix)
            repo.index.commit(commit_message)

        if not _publish_prefix_tree(
            repo, central_repo_url, prefix, split_branch, commit_message
        ):
            return f"ℹ️ '{split_branch}' already mirrors {prefix} — nothing to publish."

        print("🔗 Recording the published tip in main...")
        repo.git.fetch(central_repo_url, f"{split_branch}:{split_branch}")
        repo.git.merge("-s", "ours", split_branch, "-m",
                       f"merge: record published {split_branch} tip")
        repo.remote(name="origin").push()
        return (
            f"🎉 Success! Central Brain skills published to '{split_branch}'. "
            f"Other agents absorb them via auto_pull_latest_skills()."
        )
    except GitCommandError as e:
        return f"❌ Git Push Error: {str(e)}"


DOC_TEMPLATE_DIR = "templates"  # lives at <skills-dir>/templates/

REQUIREMENTS_HEADER = """\
# GENERATED FILE — do not edit by hand.
#
# Source of truth: the Central Brain (`central-brain`) pyproject.toml
# + uv.lock — that is the only place humans edit dependencies. This file is
# their exact-pin transport to the agents, exported by
# `sync_engine.py export-requirements` (uv export) and rendered into each
# agent's root by `sync-docs` (automatic on every `pull`).
#
# Dependency change workflow:
#   1. In the Central Brain, edit pyproject.toml (or: uv lock --upgrade-package
#      <pkg>), then `uv sync`
#   2. <engine> export-requirements
#   3. <engine> central-push -m "deps: <what changed>"
#   4. In every agent: <engine> pull && <engine> sync-env
#
"""


def _find_uv() -> str | None:
    """Locate the uv binary (PATH, then the common ~/.local/bin install)."""
    uv = shutil.which("uv")
    if uv:
        return uv
    candidate = os.path.expanduser("~/.local/bin/uv")
    return candidate if os.path.exists(candidate) else None


def _uv_env(root: str) -> dict[str, str]:
    """Environment for uv subprocesses, pinned to *this* repo's venv.

    ``uv pip`` honours ``VIRTUAL_ENV`` from the caller's shell, so an engine
    run from a shell that has another project's venv active would sync — and
    prune — THAT environment instead of this repo's (an agent's ``sync-env``
    could strip the Central Brain's dev dependencies, for instance). Pin the
    variable to ``<root>/.venv``, or drop it when that venv does not exist
    yet (so ``uv venv`` creates it in the repo, not at the stale path).
    """
    env = dict(os.environ)
    venv = os.path.join(root, ".venv")
    if os.path.isdir(venv):
        env["VIRTUAL_ENV"] = venv
    else:
        env.pop("VIRTUAL_ENV", None)
    return env


def sync_env(repo_path: str) -> str:
    """Make the local ``.venv`` reflect the repo's dependency manifest.

    * Central Brain (``pyproject.toml`` + ``uv.lock`` present) -> ``uv sync``
    * Agents (``requirements.txt`` present, created from the template export)
      -> ``uv venv`` if needed, then ``uv pip sync -r requirements.txt`` so the
      venv matches the file exactly (installs, upgrades AND removes strays).

    uv is always invoked with ``VIRTUAL_ENV`` pinned to this repo's own venv
    (see ``_uv_env``), so a foreign venv active in the caller's shell can
    never be the environment that gets synced.

    Run this after ``pull`` — especially after the Central Brain publishes a
    dependency upgrade (e.g. a new quantlib).
    """
    uv = _find_uv()
    if not uv:
        return "❌ uv not found on PATH (install: https://docs.astral.sh/uv/)."
    root = os.path.abspath(repo_path)

    if os.path.exists(os.path.join(root, "pyproject.toml")) and os.path.exists(
        os.path.join(root, "uv.lock")
    ):
        cmd, described = [uv, "sync"], "uv sync (pyproject.toml + uv.lock)"
    elif os.path.exists(os.path.join(root, "requirements.txt")):
        if not os.path.exists(os.path.join(root, ".venv", "bin", "python")):
            print("🆕 Creating .venv ...")
            made = subprocess.run(
                [uv, "venv"], cwd=root, capture_output=True, text=True,
                env=_uv_env(root),
            )
            if made.returncode != 0:
                return f"❌ uv venv failed: {made.stderr.strip()}"
        cmd = [uv, "pip", "sync", "requirements.txt"]  # SRC_FILE is positional in uv pip sync
        described = "uv pip sync requirements.txt"
    else:
        return "❌ No pyproject.toml + uv.lock and no requirements.txt found — nothing to sync."

    print(f"📦 Syncing venv with: {described}")
    run = subprocess.run(cmd, cwd=root, capture_output=True, text=True, env=_uv_env(root))
    if run.stdout.strip():
        print(run.stdout.strip())
    if run.returncode != 0:
        return f"❌ Dependency sync failed: {run.stderr.strip()}"
    return "🎉 venv is in sync with the dependency manifest."


def export_requirements(
    central_repo_path: str, prefix: str = CENTRAL_PREFIX
) -> str:
    """Central Brain only: regenerate ``<prefix>templates/requirements.txt.tmpl``
    from ``uv.lock`` so every agent inherits the exact pinned dependency set.

    Publish the result with ``push_central_skills_edit`` (``central-push``);
    agents absorb it on their next ``pull`` (which re-renders the root
    ``requirements.txt``) followed by ``sync_env``.
    """
    root = os.path.abspath(central_repo_path)
    if not (
        os.path.exists(os.path.join(root, "pyproject.toml"))
        and os.path.exists(os.path.join(root, "uv.lock"))
    ):
        return (
            "❌ export-requirements must run in the Central Brain "
            "(pyproject.toml + uv.lock required)."
        )
    out_dir = os.path.join(root, prefix, DOC_TEMPLATE_DIR)
    if not os.path.isdir(out_dir):
        return f"❌ Templates directory not found: {out_dir}"
    out_file = os.path.join(out_dir, "requirements.txt.tmpl")
    uv = _find_uv()
    if not uv:
        return "❌ uv not found on PATH (install: https://docs.astral.sh/uv/)."

    print("📦 Exporting uv.lock → requirements template ...")
    run = subprocess.run(
        [
            uv, "export",
            "--format", "requirements.txt",
            "--no-hashes",
            "--no-emit-project",
            "--no-dev",
            "--no-header",
            "-o", out_file,
        ],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if run.returncode != 0:
        return f"❌ uv export failed: {run.stderr.strip()}"

    with open(out_file, encoding="utf-8") as f:
        body = f.read()
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(REQUIREMENTS_HEADER + "\n" + body)

    rel = os.path.relpath(out_file, root)
    return (
        f"🎉 Exported uv.lock → {rel}. Next: run `central-push -m "
        f'"deps: <what was upgraded>"` to publish it to all agents.'
    )


def _agent_identity(repo: Repo) -> tuple[str, str]:
    """Resolve (agent_name, agent_id): env overrides, else derived from origin."""
    name = os.environ.get("AGENT_NAME")
    if not name:
        try:
            url = repo.remote(name="origin").url
            tail = url.rstrip("/").split("/")[-1].split(":")[-1]
            name = tail[:-4] if tail.endswith(".git") else tail
        except Exception:
            name = "agent"
    agent_id = os.environ.get("AGENT_ID")
    if not agent_id:
        agent_id = name.rsplit("-", 1)[-1] if "-" in name else name
    return name, agent_id


def render_agent_docs(agent_repo_path: str, prefix: str | None = None) -> list[str]:
    """Render ``<prefix>templates/*.tmpl`` into ``AGENTS.md``/``README.md`` at the
    repo root, substituting ``{{AGENT_NAME}}``, ``{{AGENT_ID}}`` and
    ``{{SKILLS_DIR}}`` (the agent-side subtree prefix).

    Returns the list of root files that were actually changed (empty if
    everything already matches the templates).
    """
    repo = Repo(agent_repo_path)
    prefix = resolve_agent_prefix(prefix)
    tmpl_dir = os.path.join(repo.working_dir, prefix, DOC_TEMPLATE_DIR)
    if not os.path.isdir(tmpl_dir):
        return []
    name, agent_id = _agent_identity(repo)
    written: list[str] = []
    for fname in sorted(os.listdir(tmpl_dir)):
        if not fname.endswith(".tmpl"):
            continue
        with open(os.path.join(tmpl_dir, fname), encoding="utf-8") as f:
            content = f.read()
        content = (
            content.replace("{{AGENT_NAME}}", name)
            .replace("{{AGENT_ID}}", agent_id)
            .replace("{{SKILLS_DIR}}", prefix.rstrip("/"))
        )
        out_name = fname[: -len(".tmpl")]
        out_path = os.path.join(repo.working_dir, out_name)
        if os.path.exists(out_path):
            with open(out_path, encoding="utf-8") as f:
                if f.read() == content:
                    continue  # already aligned
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
        written.append(out_name)
    return written


def _render_and_commit_docs(repo: Repo, prefix: str, message: str) -> bool:
    """Render root docs from templates and commit them if anything changed."""
    changed = render_agent_docs(repo.working_dir, prefix)
    if not changed:
        return False
    print(f"📄 Rendered agent docs from central templates: {', '.join(changed)}")
    repo.git.add(*changed)
    repo.index.commit(message)
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Synchronize an agent's skills directory with the Central Brain."
    )
    default_central = os.environ.get("CENTRAL_SKILLS_REPO", CENTRAL_BRAIN_URL)
    sub = parser.add_subparsers(dest="command", required=True)

    def _add_prefix(p):
        p.add_argument(
            "--prefix",
            default=None,
            help="Agent-side skills dir (default: auto-detected from this "
                 "engine's location, or $AGENT_SKILLS_DIR)",
        )

    p_pull = sub.add_parser("pull", help="Pull latest skills from the Central Brain")
    p_pull.add_argument("--repo", default=os.getcwd(), help="Agent repo path")
    p_pull.add_argument("--central", default=default_central)
    _add_prefix(p_pull)

    p_push = sub.add_parser("push", help="Publish local skills-dir changes (agent)")
    p_push.add_argument("--repo", default=os.getcwd(), help="Agent repo path")
    p_push.add_argument("--central", default=default_central)
    p_push.add_argument("-m", "--message", required=True, help="Commit message")
    _add_prefix(p_push)

    p_cpush = sub.add_parser(
        "central-push", help="Publish skill edits made on main in the Central Brain"
    )
    p_cpush.add_argument("--repo", default=os.getcwd(), help="Central Brain repo path")
    p_cpush.add_argument("--central", default=default_central)
    p_cpush.add_argument("-m", "--message", required=True, help="Commit message")

    p_docs = sub.add_parser(
        "sync-docs",
        help="Render root AGENTS.md/README.md from <skills-dir>/templates/",
    )
    p_docs.add_argument("--repo", default=os.getcwd(), help="Agent repo path")
    p_docs.add_argument("-m", "--message", default="docs: render agent docs from central templates")
    p_docs.add_argument("--push", action="store_true", help="Also push the agent's main to origin")
    _add_prefix(p_docs)

    p_env = sub.add_parser(
        "sync-env", help="Make .venv reflect requirements.txt (agents) or uv.lock (Central Brain)"
    )
    p_env.add_argument("--repo", default=os.getcwd(), help="Repo path")

    p_exp = sub.add_parser(
        "export-requirements",
        help="Central Brain only: regenerate templates/requirements.txt.tmpl from uv.lock",
    )
    p_exp.add_argument("--repo", default=os.getcwd(), help="Central Brain repo path")

    p_prom = sub.add_parser("promote", help="Merge skills-split into main (Central Brain only)")
    p_prom.add_argument("--repo", default=os.getcwd(), help="Central Brain repo path")
    p_prom.add_argument("--central", default=default_central)
    p_prom.add_argument("-m", "--message", default="skills: sync agent skill edits into main")

    args = parser.parse_args()
    if args.command == "pull":
        print(auto_pull_latest_skills(args.repo, args.central, prefix=args.prefix))
    elif args.command == "push":
        print(auto_push_skills(args.repo, args.central, args.message, prefix=args.prefix))
    elif args.command == "central-push":
        print(push_central_skills_edit(args.repo, args.central, args.message))
    elif args.command == "sync-docs":
        repo = Repo(args.repo)
        if repo.is_dirty(untracked_files=True):
            print("⚠️ Warning: Please commit or stash local changes first.")
        elif _render_and_commit_docs(
            repo, resolve_agent_prefix(args.prefix), args.message
        ):
            if args.push:
                repo.remote(name="origin").push()
            print("🎉 Agent docs rendered from central templates and committed.")
        else:
            print("ℹ️ Agent docs already aligned with the central templates.")
    elif args.command == "sync-env":
        print(sync_env(args.repo))
    elif args.command == "export-requirements":
        print(export_requirements(args.repo))
    elif args.command == "promote":
        print(promote_skills_split_to_main(args.repo, args.central, args.message))
