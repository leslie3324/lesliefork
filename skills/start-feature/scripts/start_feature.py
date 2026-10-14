#!/usr/bin/env python3
"""Create a feature worktree from origin/pro, optionally with requirement docs."""

import argparse
from datetime import date
from pathlib import Path
import subprocess
import sys


TEMPLATES = Path(__file__).resolve().parents[3] / "governance/docs/templates"


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True, capture_output=True, text=True,
    ).stdout.strip()


def init_docs(worktree, branch, include_parallel_plan=False):
    if not TEMPLATES.is_dir():
        raise ValueError("Documentation templates are missing from the skill repository.")
    worktree = worktree.resolve()
    docs = worktree / "docs" / branch
    if any(path.is_symlink() for path in (docs, *docs.parents)):
        raise ValueError("Documentation path must not use symlinks.")
    docs.mkdir(parents=True, exist_ok=True)
    for template in sorted(TEMPLATES.rglob("*")):
        if template.is_symlink():
            raise ValueError("Documentation templates must not be symlinks.")
        if template.name == "module-breakdown.md" and not include_parallel_plan:
            continue
        path = docs / template.relative_to(TEMPLATES)
        if any(parent.is_symlink() for parent in (path, *path.parents)):
            raise ValueError("Documentation entries must not be symlinks.")
        if template.is_dir():
            path.mkdir(exist_ok=True)
        elif template.name != ".gitkeep" and not path.exists():
            body = template.read_text(encoding="utf-8").replace("{{date}}", date.today().isoformat())
            with path.open("x", encoding="utf-8") as output:
                output.write(body)
    return docs


def is_registered_worktree(root, worktree, branch):
    """Require the target to be this repository's checked-out feature branch."""
    if worktree.is_symlink() or not worktree.is_dir():
        return False
    try:
        top = Path(git(worktree, "rev-parse", "--show-toplevel")).resolve()
        current_branch = git(worktree, "branch", "--show-current")
    except (OSError, subprocess.CalledProcessError):
        return False
    if top != worktree.resolve() or current_branch != branch:
        return False

    records = []
    current = None
    for line in git(root, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            if current:
                records.append(current)
            current = {"path": str(Path(line.removeprefix("worktree ")).resolve())}
        elif line.startswith("branch ") and current is not None:
            current["branch"] = line.removeprefix("branch ")
    if current:
        records.append(current)
    return any(
        record.get("path") == str(worktree.resolve())
        and record.get("branch") == f"refs/heads/{branch}"
        for record in records
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", type=Path)
    parser.add_argument("branch", help="New feat/... branch")
    parser.add_argument("worktree", type=Path, help="New worktree directory")
    parser.add_argument("--docs", action="store_true", help="Initialize docs while creating the worktree")
    parser.add_argument("--init-docs", action="store_true", help="Initialize docs in an existing feature worktree")
    parser.add_argument("--parallel", action="store_true", help="Include the optional parallel task template")
    args = parser.parse_args()

    try:
        if args.docs and args.init_docs:
            raise ValueError("Use either --docs or --init-docs, not both.")
        if args.parallel and not (args.docs or args.init_docs):
            raise ValueError("Use --parallel only with --docs or --init-docs.")
        root = Path(git(args.repo, "rev-parse", "--show-toplevel"))
        if not args.branch.startswith("feat/"):
            raise ValueError("Branch must start with feat/.")
        git(root, "check-ref-format", "--branch", args.branch)

        if args.init_docs:
            branches = git(root, "for-each-ref", "--format=%(refname)", "refs/heads")
            if f"refs/heads/{args.branch}" not in branches.splitlines():
                raise ValueError("Feature branch does not exist in this repository.")
            worktree = args.worktree
            if not is_registered_worktree(root, worktree, args.branch):
                raise ValueError("The path must be this repository's worktree on the requested feature branch.")
            if not TEMPLATES.is_dir():
                raise ValueError("Documentation templates are missing from the skill repository.")
            print(f"docs: {init_docs(worktree, args.branch, args.parallel)}")
            return 0

        branches = git(root, "for-each-ref", "--format=%(refname)", "refs/heads")
        if f"refs/heads/{args.branch}" in branches.splitlines():
            raise ValueError("Branch already exists; nothing will be overwritten.")
        if args.worktree.exists() or args.worktree.is_symlink():
            raise ValueError("Worktree path already exists; choose a new path.")
        worktree = args.worktree.resolve()
        if args.docs and not TEMPLATES.is_dir():
            raise ValueError("Documentation templates are missing from the skill repository.")
        if worktree.is_relative_to(root) and subprocess.run(
            ["git", "-C", str(root), "check-ignore", "-q", str(worktree)],
        ).returncode != 0:
            raise ValueError("A worktree inside the repository must be ignored.")

        # A fixed ref prevents using test or the current checkout as the base.
        git(root, "fetch", "--no-tags", "--no-prune", "--no-prune-tags",
            "origin", "+refs/heads/pro:refs/remotes/origin/pro")
        base = git(root, "rev-parse", "--verify", "refs/remotes/origin/pro^{commit}")
        git(root, "-c", "core.hooksPath=/dev/null", "worktree", "add",
            "--no-track", "-b", args.branch, str(worktree), base)
        print(f"branch: {args.branch}\nbase: origin/pro {base}\nworktree: {worktree}")
        if args.docs:
            print(f"docs: {init_docs(worktree, args.branch, args.parallel)}")
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        message = error.stderr.strip() if isinstance(error, subprocess.CalledProcessError) else str(error)
        print(f"Error: {message}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
