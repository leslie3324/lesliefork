# Behavior Evals

`run_evals.py` runs real, isolated Codex sessions against the cases in `cases.jsonl`. It records pass rate, token usage, elapsed time, whether the target `SKILL.md` was read, and cases whose results flip across repeated runs.

```bash
python3 evals/run_evals.py --dry-run
python3 evals/run_evals.py --repeat 1
python3 evals/run_evals.py --case prepare-commit-local-e2e-gate --repeat 3
python3 evals/run_evals.py --repeat 3 --output /tmp/lesliefork-evals.json
python3 evals/run_evals.py --cases evals/cases-router.jsonl --repeat 3
python3 evals/run_evals.py --cases evals/cases-router.jsonl --repeat 3 --unassisted
```

Each run uses a temporary `HOME`, `CODEX_HOME`, and workspace. Only this repository's Skills are linked into the temporary Agent Skill root; configuration is reduced to the active model provider, with memories, multi-agent, apps, plugins, project documents, MCP servers, and hooks excluded. The session runs read-only and ephemeral.

This first version grades deterministic text expectations. It is useful for regression and A/B comparisons on routing, gates, clarification, refusal of unsafe actions, pass rate, flips, and token cost. It does not replace real business E2E, an LLM judge, code-execution fixtures, or project-specific acceptance evidence.

`allow_implicit_invocation: false` makes a Skill intentionally absent from the model-visible automatic discovery list. The runner therefore gives the model the exact `SKILL.md` path and separately verifies that the file was read; hidden-by-policy is not treated as a discovery failure.

`--unassisted` keeps the same task cases but removes the exact `SKILL.md` path from the prompt, so the model must rely on automatic Skill discovery. Compare it with the normal run to measure whether a router improves stage selection without changing the task.

Cases may also declare `read` and `avoid_read` Skill names. The runner checks completed command executions and requires the command output to contain the Skill's frontmatter name, so a path mentioned in the prompt is not counted as a read. This is used to verify that `dev-router` loads only the current stage and that `auto` does not preload future stages.

`behavior_expect` is a separate, semantic checklist. The normal `expect` checks the router's exact output contract, while `passed` additionally checks required `read`/`avoid_read` evidence and rejects; `behavior_expect` checks whether the reply still identifies the right stage and gate when formatting differs. The JSON includes both `passed` and `behavior_passed`, allowing a strict comparison and a behavior-level comparison without hiding real gate failures.
