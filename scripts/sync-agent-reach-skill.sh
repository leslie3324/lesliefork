#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCE_DIR="$REPO_ROOT/skills/agent-reach"
VALIDATOR="${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py"

if ! command -v pipx >/dev/null 2>&1; then
  echo "pipx is required to locate the installed agent-reach package" >&2
  exit 1
fi

VENV_ROOT="$(pipx environment --value PIPX_LOCAL_VENVS)"
PYTHON="$VENV_ROOT/agent-reach/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "agent-reach is not installed in the pipx venv: $VENV_ROOT/agent-reach" >&2
  exit 1
fi

UPSTREAM_SKILL="$("$PYTHON" - <<'PY'
from pathlib import Path

import agent_reach

print(Path(agent_reach.__file__).resolve().parent / "skill")
PY
)"

if [[ ! -f "$UPSTREAM_SKILL/SKILL.md" ]]; then
  echo "Installed agent-reach skill not found: $UPSTREAM_SKILL" >&2
  exit 1
fi

mkdir -p "$SOURCE_DIR"
rsync -a --delete "$UPSTREAM_SKILL/" "$SOURCE_DIR/"

link_skill() {
  local link_path="$1"

  case "$link_path" in
    "$HOME/.agents/skills/agent-reach"|\
    "$HOME/.claude/skills/agent-reach"|\
    "$HOME/.config/opencode/skills/agent-reach"|\
    "$HOME/.openclaw/skills/agent-reach")
      ;;
    *)
      echo "Refusing to manage unexpected link path: $link_path" >&2
      exit 1
      ;;
  esac

  mkdir -p "$(dirname "$link_path")"

  if [[ -L "$link_path" ]]; then
    if [[ "$(readlink "$link_path")" == "$SOURCE_DIR" ]]; then
      return
    fi
    rm "$link_path"
  elif [[ -e "$link_path" ]]; then
    # agent-reach install replaces managed symlinks with real directories.
    rm -rf "$link_path"
  fi

  ln -s "$SOURCE_DIR" "$link_path"
  echo "Linked $link_path -> $SOURCE_DIR"
}

link_skill "$HOME/.agents/skills/agent-reach"
link_skill "$HOME/.claude/skills/agent-reach"
link_skill "$HOME/.config/opencode/skills/agent-reach"

if [[ -d "$HOME/.openclaw/skills" ]]; then
  link_skill "$HOME/.openclaw/skills/agent-reach"
fi

if [[ -f "$VALIDATOR" ]]; then
  "$PYTHON" "$VALIDATOR" "$SOURCE_DIR"
fi

echo "Agent Reach skill synced to $SOURCE_DIR"
