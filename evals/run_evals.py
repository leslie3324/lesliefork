#!/usr/bin/env python3
"""Run small, repeatable behavior evaluations against isolated Codex Skills."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = Path(__file__).with_name("cases.jsonl")


@dataclass(frozen=True)
class Case:
    id: str
    skill: str
    prompt: str
    expect: tuple[tuple[str, ...], ...]
    behavior_expect: tuple[tuple[str, ...], ...]
    reject: tuple[str, ...]
    read: tuple[str, ...]
    avoid_read: tuple[str, ...]


def load_cases(path: Path) -> list[Case]:
    cases: list[Case] = []
    seen: set[str] = set()
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            item = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc

        case_id = item.get("id")
        skill = item.get("skill")
        prompt = item.get("prompt")
        expect = item.get("expect")
        behavior_expect = item.get("behavior_expect", expect)
        reject = item.get("reject", [])
        read = item.get("read", [])
        avoid_read = item.get("avoid_read", [])
        if not isinstance(case_id, str) or not case_id:
            raise ValueError(f"{path}:{line_no}: id must be a non-empty string")
        if case_id in seen:
            raise ValueError(f"{path}:{line_no}: duplicate id {case_id!r}")
        if not isinstance(skill, str) or not (REPO_ROOT / "skills" / skill / "SKILL.md").is_file():
            raise ValueError(f"{path}:{line_no}: unknown skill {skill!r}")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError(f"{path}:{line_no}: prompt must be a non-empty string")
        if not isinstance(expect, list) or not expect:
            raise ValueError(f"{path}:{line_no}: expect must be a non-empty list")
        if not all(isinstance(group, list) and group for group in expect):
            raise ValueError(f"{path}:{line_no}: every expect group must be a non-empty list")
        if not all(isinstance(pattern, str) and pattern for group in expect for pattern in group):
            raise ValueError(f"{path}:{line_no}: expect patterns must be non-empty strings")
        if not isinstance(behavior_expect, list) or not behavior_expect:
            raise ValueError(f"{path}:{line_no}: behavior_expect must be a non-empty list")
        if not all(isinstance(group, list) and group for group in behavior_expect):
            raise ValueError(f"{path}:{line_no}: every behavior_expect group must be a non-empty list")
        if not all(isinstance(pattern, str) and pattern for group in behavior_expect for pattern in group):
            raise ValueError(f"{path}:{line_no}: behavior_expect patterns must be non-empty strings")
        if not isinstance(reject, list) or not all(isinstance(pattern, str) and pattern for pattern in reject):
            raise ValueError(f"{path}:{line_no}: reject must be a list of non-empty strings")
        if not isinstance(read, list) or not all(
            isinstance(skill_name, str) and (REPO_ROOT / "skills" / skill_name / "SKILL.md").is_file()
            for skill_name in read
        ):
            raise ValueError(f"{path}:{line_no}: read must be a list of known skill names")
        if not isinstance(avoid_read, list) or not all(
            isinstance(skill_name, str) and (REPO_ROOT / "skills" / skill_name / "SKILL.md").is_file()
            for skill_name in avoid_read
        ):
            raise ValueError(f"{path}:{line_no}: avoid_read must be a list of known skill names")
        for pattern in [p for group in expect for p in group] + [
            p for group in behavior_expect for p in group
        ] + reject:
            try:
                re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            except re.error as exc:
                raise ValueError(f"{path}:{line_no}: invalid regex {pattern!r}: {exc}") from exc

        seen.add(case_id)
        cases.append(
            Case(
                id=case_id,
                skill=skill,
                prompt=prompt,
                expect=tuple(tuple(group) for group in expect),
                behavior_expect=tuple(tuple(group) for group in behavior_expect),
                reject=tuple(reject),
                read=tuple(read),
                avoid_read=tuple(avoid_read),
            )
        )
    if not cases:
        raise ValueError(f"{path}: no cases")
    return cases


def toml_value(value: Any) -> str:
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(toml_value(item) for item in value) + "]"
    if isinstance(value, dict):
        pairs = ", ".join(f"{json.dumps(str(k), ensure_ascii=False)} = {toml_value(v)}" for k, v in value.items())
        return "{ " + pairs + " }"
    raise TypeError(f"unsupported TOML value: {type(value).__name__}")


def write_isolated_config(source: Path, target: Path, reasoning: str | None) -> None:
    with source.open("rb") as handle:
        data = tomllib.load(handle)

    provider_name = data.get("model_provider", "openai")
    provider = data.get("model_providers", {}).get(provider_name, {})
    selected = {
        key: data[key]
        for key in ("model", "model_provider", "model_catalog_json", "openai_base_url")
        if key in data
    }
    selected["model_reasoning_effort"] = reasoning or data.get("model_reasoning_effort", "medium")
    selected["project_doc_max_bytes"] = 0

    lines = [f"{key} = {toml_value(value)}" for key, value in selected.items()]
    lines.extend(
        [
            "",
            "[features]",
            "memories = false",
            "multi_agent = false",
            "apps = false",
            "plugins = false",
            "",
        ]
    )
    if provider:
        provider_key = json.dumps(str(provider_name), ensure_ascii=False)
        lines.append(f"[model_providers.{provider_key}]")
        lines.extend(f"{key} = {toml_value(value)}" for key, value in provider.items())
        lines.append("")
    target.write_text("\n".join(lines), encoding="utf-8")
    target.chmod(0o600)


def parse_events(stdout: str) -> tuple[str, dict[str, int], list[dict[str, Any]]]:
    messages: list[str] = []
    usage = {
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "cache_write_input_tokens": 0,
        "output_tokens": 0,
        "reasoning_output_tokens": 0,
    }
    events: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        events.append(event)
        if event.get("type") == "item.completed":
            item = event.get("item", {})
            if item.get("type") == "agent_message" and item.get("text"):
                messages.append(item["text"])
        elif event.get("type") == "turn.completed":
            for key in usage:
                usage[key] += int(event.get("usage", {}).get(key, 0) or 0)
    return "\n".join(messages).strip(), usage, events


def skill_reads_from_events(events: list[dict[str, Any]]) -> list[str]:
    reads: set[str] = set()
    for event in events:
        if event.get("type") != "item.completed":
            continue
        item = event.get("item", {})
        if item.get("type") != "command_execution":
            continue
        command = item.get("command", "")
        output = item.get("aggregated_output", "")
        for match in re.finditer(r'''(?:^|[\s'"=/])skills/([A-Za-z0-9_-]+)/SKILL\.md(?=$|[\s'"\\])''', command):
            if f"name: {match.group(1)}" in output:
                reads.add(match.group(1))
    return sorted(reads)


def evaluate_output(
    case: Case,
    text: str,
    events: list[dict[str, Any]],
    require_skill_read: bool,
) -> dict[str, Any]:
    expect_results = []
    for group in case.expect:
        matched = next((pattern for pattern in group if re.search(pattern, text, re.IGNORECASE | re.MULTILINE)), None)
        expect_results.append({"patterns": list(group), "matched": matched})

    behavior_results = []
    for group in case.behavior_expect:
        matched = next((pattern for pattern in group if re.search(pattern, text, re.IGNORECASE | re.MULTILINE)), None)
        behavior_results.append({"patterns": list(group), "matched": matched})

    reject_results = []
    for pattern in case.reject:
        matched = bool(re.search(pattern, text, re.IGNORECASE | re.MULTILINE))
        reject_results.append({"pattern": pattern, "matched": matched})

    skill_reads = skill_reads_from_events(events)
    skill_read = case.skill in skill_reads
    required_reads = [{"skill": name, "matched": name in skill_reads} for name in case.read]
    avoided_reads = [{"skill": name, "matched": name in skill_reads} for name in case.avoid_read]
    reject_failed = any(item["matched"] for item in reject_results)
    behavior_passed = all(item["matched"] for item in behavior_results) and not reject_failed
    passed = (
        (not require_skill_read or skill_read)
        and all(item["matched"] for item in expect_results)
        and not reject_failed
        and all(item["matched"] for item in required_reads)
        and not any(item["matched"] for item in avoided_reads)
    )
    return {
        "passed": passed,
        "behavior_passed": behavior_passed,
        "skill_read": skill_read,
        "skill_reads": skill_reads,
        "expect": expect_results,
        "behavior_expect": behavior_results,
        "reject": reject_results,
        "read": required_reads,
        "avoid_read": avoided_reads,
    }


def run_once(case: Case, timeout: int, reasoning: str | None, unassisted: bool) -> dict[str, Any]:
    real_codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    source_config = real_codex_home / "config.toml"
    if not source_config.is_file():
        raise FileNotFoundError(f"Codex config not found: {source_config}")

    root = Path(tempfile.mkdtemp(prefix="lesliefork-eval-"))
    home = root / "home"
    codex_home = root / "codex"
    workspace = root / "workspace"
    (home / ".agents" / "skills").mkdir(parents=True)
    codex_home.mkdir()
    workspace.mkdir()
    (home / ".agents" / "skills" / "skills").symlink_to(REPO_ROOT / "skills", target_is_directory=True)
    write_isolated_config(source_config, codex_home / "config.toml", reasoning)
    auth = real_codex_home / "auth.json"
    if auth.exists():
        (codex_home / "auth.json").symlink_to(auth)

    if unassisted:
        prompt = (
            "这是隔离的行为评测。不要修改文件，不要执行有副作用的操作。"
            "只返回任务要求的判断、计划或澄清问题。\n\n"
            f"{case.prompt}"
        )
    else:
        skill_path = home / ".agents" / "skills" / "skills" / case.skill / "SKILL.md"
        prompt = (
            "这是隔离的行为评测。先读取并遵守这个精确的 Skill 文件，再回答下面的任务：\n"
            f"{skill_path}\n\n"
            "不要修改文件，不要执行有副作用的操作。只返回任务要求的判断、计划或澄清问题。\n\n"
            f"$ {case.skill}\n{case.prompt}"
        )
    command = [
        "codex",
        "exec",
        "--json",
        "--ephemeral",
        "--skip-git-repo-check",
        "--ignore-rules",
        "-C",
        str(workspace),
        "-s",
        "read-only",
        "--color",
        "never",
        prompt,
    ]
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["CODEX_HOME"] = str(codex_home)

    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        elapsed = time.monotonic() - started
        text, usage, events = parse_events(completed.stdout)
        checks = evaluate_output(case, text, events, require_skill_read=not unassisted)
        return {
            "case": case.id,
            "skill": case.skill,
            "status": "completed" if completed.returncode == 0 else "codex_error",
            "exit_code": completed.returncode,
            "elapsed_seconds": round(elapsed, 2),
            "output": text,
            "stderr_tail": completed.stderr[-2000:],
            "usage": usage,
            "events_count": len(events),
            "unassisted": unassisted,
            **checks,
        }
    except subprocess.TimeoutExpired as exc:
        elapsed = time.monotonic() - started
        return {
            "case": case.id,
            "skill": case.skill,
            "status": "timeout",
            "exit_code": None,
            "elapsed_seconds": round(elapsed, 2),
            "output": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": (exc.stderr or "")[-2000:] if isinstance(exc.stderr, str) else "",
            "usage": {},
            "events_count": 0,
            "unassisted": unassisted,
            "passed": False,
            "behavior_passed": False,
            "skill_read": False,
            "skill_reads": [],
            "expect": [],
            "behavior_expect": [],
            "reject": [],
            "read": [],
            "avoid_read": [],
        }
    finally:
        shutil.rmtree(root, ignore_errors=True)


def summarize(results: list[dict[str, Any]], repeat: int) -> dict[str, Any]:
    by_case: dict[str, list[dict[str, Any]]] = {}
    for result in results:
        by_case.setdefault(result["case"], []).append(result)

    cases = []
    for case_id, runs in by_case.items():
        passed = sum(1 for run in runs if run["passed"])
        cases.append(
            {
                "case": case_id,
                "skill": runs[0]["skill"],
                "runs": len(runs),
                "passed": passed,
                "pass_rate": round(passed / len(runs), 3),
                "flipped": 0 < passed < len(runs),
            }
        )

    total = len(results)
    passed = sum(1 for result in results if result["passed"])
    behavior_passed = sum(1 for result in results if result.get("behavior_passed", result["passed"]))
    usage = {
        key: sum(int(result.get("usage", {}).get(key, 0) or 0) for result in results)
        for key in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens")
    }
    return {
        "repeat": repeat,
        "total_runs": total,
        "passed_runs": passed,
        "pass_rate": round(passed / total, 3) if total else 0,
        "behavior_passed_runs": behavior_passed,
        "behavior_pass_rate": round(behavior_passed / total, 3) if total else 0,
        "flipped_cases": [case["case"] for case in cases if case["flipped"]],
        "usage": usage,
        "cases": cases,
    }


def print_summary(summary: dict[str, Any]) -> None:
    print("\ncase                              runs  passed  rate   flip")
    print("--------------------------------  ----  ------  -----  ----")
    for case in summary["cases"]:
        print(
            f"{case['case'][:32]:32}  {case['runs']:4}  {case['passed']:6}  "
            f"{case['pass_rate']:5.0%}  {'yes' if case['flipped'] else 'no'}"
        )
    print(
        f"\nTotal: {summary['passed_runs']}/{summary['total_runs']} "
        f"({summary['pass_rate']:.0%}), flips={summary['flipped_cases'] or 'none'}"
    )
    print(
        f"Behavior: {summary['behavior_passed_runs']}/{summary['total_runs']} "
        f"({summary['behavior_pass_rate']:.0%})"
    )
    print(f"Tokens: {json.dumps(summary['usage'], ensure_ascii=False)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--case", action="append", default=[], help="run only this case id; repeatable")
    parser.add_argument("--repeat", type=int, default=3, help="runs per case (default: 3)")
    parser.add_argument("--timeout", type=int, default=180, help="timeout per run in seconds")
    parser.add_argument("--reasoning", choices=("none", "minimal", "low", "medium", "high"), help="override reasoning")
    parser.add_argument(
        "--unassisted",
        action="store_true",
        help="do not provide the target SKILL.md path; measure automatic Skill discovery for the same cases",
    )
    parser.add_argument("--output", type=Path, help="write full JSON results to this path")
    parser.add_argument("--dry-run", action="store_true", help="validate cases without invoking Codex")
    args = parser.parse_args()

    if args.repeat < 1:
        parser.error("--repeat must be >= 1")
    cases = load_cases(args.cases)
    if args.case:
        selected = set(args.case)
        unknown = selected - {case.id for case in cases}
        if unknown:
            parser.error(f"unknown case id(s): {', '.join(sorted(unknown))}")
        cases = [case for case in cases if case.id in selected]

    if args.dry_run:
        for case in cases:
            print(f"{case.id}: skill={case.skill}, repeats={args.repeat}")
        print(f"Validated {len(cases)} case(s); no Codex runs executed.")
        return 0

    all_results: list[dict[str, Any]] = []
    for case in cases:
        for run_index in range(1, args.repeat + 1):
            print(f"[{case.id}] run {run_index}/{args.repeat}", flush=True)
            result = run_once(case, args.timeout, args.reasoning, args.unassisted)
            result["run"] = run_index
            all_results.append(result)
            print(
                f"  {'PASS' if result['passed'] else 'FAIL'} "
                f"({result['elapsed_seconds']}s, skill_read={result['skill_read']})",
                flush=True,
            )

    summary = summarize(all_results, args.repeat)
    print_summary(summary)
    document = {"summary": summary, "results": all_results}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Results: {args.output}")
    return 0 if summary["passed_runs"] == summary["total_runs"] else 1


if __name__ == "__main__":
    sys.exit(main())
