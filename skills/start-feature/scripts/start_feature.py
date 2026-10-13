#!/usr/bin/env python3
"""Create a feature branch and worktree from the latest origin/pro."""

import argparse
from pathlib import Path
import subprocess
import sys


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True, capture_output=True, text=True,
    ).stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", type=Path)
    parser.add_argument("branch", help="New feat/... branch")
    parser.add_argument("worktree", type=Path, help="New worktree directory")
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
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        message = error.stderr.strip() if isinstance(error, subprocess.CalledProcessError) else str(error)
        print(f"Error: {message}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
