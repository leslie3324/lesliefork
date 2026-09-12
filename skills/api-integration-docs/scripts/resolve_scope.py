#!/usr/bin/env python3
"""Resolve an explicitly requested API documentation scope to JSON."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable


IGNORED_DIRS = {".git", "node_modules", "target", "build", "dist", ".gradle", ".idea"}


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "-c", "core.quotePath=false", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def repo_root(start: Path) -> Path:
    try:
        return Path(run_git(start, "rev-parse", "--show-toplevel").strip()).resolve()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"无法确定 Git 仓库根目录: {exc}") from exc


def relative_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError as exc:
        raise SystemExit(f"路径不在仓库内: {path}") from exc


def walk_explicit_directory(directory: Path, root: Path) -> list[str]:
    files: list[str] = []
    for current, dirs, names in os.walk(directory):
        dirs[:] = sorted(name for name in dirs if name not in IGNORED_DIRS)
        for name in sorted(names):
            path = Path(current) / name
            if path.is_file():
                files.append(relative_path(path, root))
    return files


def resolve_paths(root: Path, paths: Iterable[str]) -> dict:
    selected: set[str] = set()
    missing: list[str] = []
    for raw_path in paths:
        candidate = Path(raw_path)
        if not candidate.is_absolute():
            candidate = root / candidate
        candidate = candidate.resolve()
        if not candidate.exists():
            missing.append(raw_path)
            continue
        if candidate.is_dir():
            selected.update(walk_explicit_directory(candidate, root))
        else:
            selected.add(relative_path(candidate, root))
    return {
        "repository": str(root),
        "mode": "paths",
        "files": sorted(selected),
        "missing": missing,
    }


def changed_files(root: Path, base: str, head: str) -> list[dict[str, str]]:
    output = run_git(root, "diff", "--name-status", "--find-renames", f"{base}..{head}")
    entries: list[dict[str, str]] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        fields = line.split("\t")
        status = fields[0]
        if status.startswith(("R", "C")) and len(fields) >= 3:
            entries.append({"status": status, "path": fields[2], "previous_path": fields[1]})
        elif len(fields) >= 2:
            entries.append({"status": status, "path": fields[1]})
    return entries


def working_tree_files(root: Path) -> list[dict[str, str]]:
    output = run_git(root, "status", "--short", "--untracked-files=all")
    entries: list[dict[str, str]] = []
    for line in output.splitlines():
        if len(line) < 4:
            continue
        status = line[:2]
        path = line[3:]
        if " -> " in path:
            old_path, new_path = path.split(" -> ", 1)
            entries.append({"status": status, "path": new_path, "previous_path": old_path})
        else:
            entries.append({"status": status, "path": path})
    return entries


def resolve_git(root: Path, args: argparse.Namespace) -> dict:
    try:
        entries = changed_files(root, args.base, args.head)
    except subprocess.CalledProcessError as exc:
        if args.include_working_tree and args.base == "HEAD" and args.head == "HEAD":
            entries = []
        else:
            raise SystemExit(
                f"Git 范围解析失败，请确认引用存在: {args.base}..{args.head}"
            ) from exc
    if args.include_working_tree:
        existing = {(item["status"], item["path"]) for item in entries}
        for item in working_tree_files(root):
            if (item["status"], item["path"]) not in existing:
                entries.append(item)
    return {
        "repository": str(root),
        "mode": "git",
        "base": args.base,
        "head": args.head,
        "include_working_tree": args.include_working_tree,
        "files": sorted({item["path"] for item in entries}),
        "changes": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="解析接口文档本次需求范围，不扫描全项目")
    parser.add_argument("--repo", type=Path, help="仓库路径，默认使用当前目录")
    subparsers = parser.add_subparsers(dest="command", required=True)

    paths_parser = subparsers.add_parser("paths", help="使用明确文件或目录")
    paths_parser.add_argument("--path", action="append", required=True, help="可重复指定路径")

    git_parser = subparsers.add_parser("git", help="使用两个 Git 引用之间的变更")
    git_parser.add_argument("--base", required=True, help="基准引用，例如 origin/main")
    git_parser.add_argument("--head", default="HEAD", help="目标引用，默认 HEAD")
    git_parser.add_argument("--include-working-tree", action="store_true")

    args = parser.parse_args()
    root = repo_root((args.repo or Path.cwd()).resolve())
    result = resolve_paths(root, args.path) if args.command == "paths" else resolve_git(root, args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("missing"):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
