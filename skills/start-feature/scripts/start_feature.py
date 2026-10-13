#!/usr/bin/env python3
"""Create a feature worktree from origin/pro, optionally with requirement docs."""

import argparse
from datetime import date
from pathlib import Path
import subprocess
import sys


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True, capture_output=True, text=True,
    ).stdout.strip()


def init_docs(worktree, branch):
    worktree = worktree.resolve()
    docs = worktree / "docs" / branch
    if any(path.is_symlink() for path in (docs, *docs.parents)):
        raise ValueError("Documentation path must not use symlinks.")
    docs.mkdir(parents=True, exist_ok=True)
    header = f"状态: 草稿    最后更新: {date.today().isoformat()}\n\n"
    documents = {
        "index.md": "# 需求文档入口\n\n职责：阅读顺序、文档职责和当前阶段。\n\n"
        "当前阶段：需求对齐。\n\n| 文档 | 职责 | 状态 |\n|---|---|---|\n"
        "| overview.md | 需求总览与待确认问题 | 已建 |\n"
        "| design.md | 设计与实现口径 | 已建 |\n"
        "| decisions.md | 决策与问题流水 | 已建 |\n"
        "| _scratch/ | 未定稿草稿 | 已建 |\n",
        "overview.md": "# 需求总览\n\n职责：记录已确认需求、范围和阶段边界。\n\n"
        "## 已确认结论\n\n## 待确认问题\n",
        "design.md": "# 设计\n\n职责：维护接口、数据和业务链路的权威设计。\n\n"
        "## 接口\n\n## 数据\n\n## 业务链路与实现\n",
        "decisions.md": "# 决策与问题\n\n职责：按背景、决定、理由记录决策。\n\n"
        "## 待处理\n\n## 已确认\n",
    }
    if any((docs / name).is_symlink() for name in (*documents, "_scratch")):
        raise ValueError("Documentation entries must not be symlinks.")
    for name, body in documents.items():
        path = docs / name
        if not path.exists():
            with path.open("x", encoding="utf-8") as output:
                output.write(header + body)
    (docs / "_scratch").mkdir(exist_ok=True)
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
