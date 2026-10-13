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


def init_docs(worktree, branch):
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", type=Path)
    parser.add_argument("branch", help="New feat/... branch")
    parser.add_argument("worktree", type=Path, help="New worktree directory")
    parser.add_argument("--docs", action="store_true", help="Initialize requirement documents")
    args = parser.parse_args()

    try:
        root = Path(git(args.repo, "rev-parse", "--show-toplevel"))
        if not args.branch.startswith("feat/"):
            raise ValueError("Branch must start with feat/.")
        git(root, "check-ref-format", "--branch", args.branch)
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
            print(f"docs: {init_docs(worktree, args.branch)}")
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        message = error.stderr.strip() if isinstance(error, subprocess.CalledProcessError) else str(error)
        print(f"Error: {message}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
