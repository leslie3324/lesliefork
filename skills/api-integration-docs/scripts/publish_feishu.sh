#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
用法:
  publish_feishu.sh create-markdown --file <relative.md> --name <name.md> [--execute]
  publish_feishu.sh create-doc --file <relative.md> --title <title> [--execute]
  publish_feishu.sh update-doc --doc <url-or-token> --file <relative.md> [--command overwrite|append] [--execute]
EOF
}

if [[ $# -lt 1 ]]; then usage; exit 2; fi
COMMAND=$1
shift
FILE=
NAME=
TITLE=
DOC=
DOC_COMMAND=overwrite
EXECUTE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --file) FILE=${2:-}; shift 2 ;;
    --name) NAME=${2:-}; shift 2 ;;
    --title) TITLE=${2:-}; shift 2 ;;
    --doc) DOC=${2:-}; shift 2 ;;
    --command) DOC_COMMAND=${2:-}; shift 2 ;;
    --execute) EXECUTE=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "未知参数: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "$FILE" ]]; then echo "必须指定 --file。" >&2; exit 2; fi
if [[ "$FILE" = /* || "$FILE" == *../* || "$FILE" == ../* ]]; then
  echo "--file 必须是当前工作目录下的相对 Markdown 路径。" >&2
  exit 2
fi
if [[ "$FILE" != *.md || ! -f "$FILE" ]]; then
  echo "--file 必须是存在的 .md 文件。" >&2
  exit 2
fi

LARK_CLI=${LARK_CLI:-lark-cli}
if ! command -v "$LARK_CLI" >/dev/null 2>&1; then
  echo "找不到 lark-cli: $LARK_CLI" >&2
  exit 2
fi

case "$COMMAND" in
  create-markdown)
    [[ -n "$NAME" ]] || NAME=$(basename "$FILE")
    [[ "$NAME" == *.md ]] || { echo "--name 必须以 .md 结尾。" >&2; exit 2; }
    args=(markdown +create --file "$FILE" --name "$NAME")
    ;;
  create-doc)
    [[ -n "$TITLE" ]] || { echo "create-doc 必须指定 --title。" >&2; exit 2; }
    "$LARK_CLI" skills read lark-doc references/lark-doc-md.md >/dev/null
    args=(docs +create --content "@$FILE" --doc-format markdown --title "$TITLE")
    ;;
  update-doc)
    [[ -n "$DOC" ]] || { echo "update-doc 必须指定 --doc。" >&2; exit 2; }
    [[ "$DOC_COMMAND" == overwrite || "$DOC_COMMAND" == append ]] || { echo "--command 只能是 overwrite 或 append。" >&2; exit 2; }
    "$LARK_CLI" skills read lark-doc references/lark-doc-md.md >/dev/null
    args=(docs +update --doc "$DOC" --content "@$FILE" --doc-format markdown --command "$DOC_COMMAND")
    ;;
  *) echo "未知操作: $COMMAND" >&2; usage; exit 2 ;;
esac

if [[ "$EXECUTE" != true ]]; then
  args+=(--dry-run)
  echo "飞书 CLI dry-run：未写入飞书。"
else
  echo "正在通过 lark-cli 执行显式写入: $COMMAND"
fi
"$LARK_CLI" "${args[@]}"
