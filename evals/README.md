# Behavior Evals

`run_evals.py` runs real, isolated Codex sessions against the cases in `cases.jsonl`. It records pass rate, token usage, elapsed time, whether the target `SKILL.md` was read, and cases whose results flip across repeated runs.

```bash
python3 evals/run_evals.py --dry-run
python3 evals/run_evals.py --repeat 1
python3 evals/run_evals.py --case prepare-commit-local-e2e-gate --repeat 3
python3 evals/run_evals.py --repeat 3 --output /tmp/lesliefork-evals.json
```

Each run uses a temporary `HOME`, `CODEX_HOME`, and workspace. Only this repository's Skills are linked into the temporary Agent Skill root; configuration is reduced to the active model provider, with memories, multi-agent, apps, plugins, project documents, MCP servers, and hooks excluded. The session runs read-only and ephemeral.

This first version grades deterministic text expectations. It is useful for regression and A/B comparisons on routing, gates, clarification, refusal of unsafe actions, pass rate, flips, and token cost. It does not replace real business E2E, an LLM judge, code-execution fixtures, or project-specific acceptance evidence.

`allow_implicit_invocation: false` makes a Skill intentionally absent from the model-visible automatic discovery list. The runner therefore gives the model the exact `SKILL.md` path and separately verifies that the file was read; hidden-by-policy is not treated as a discovery failure.
