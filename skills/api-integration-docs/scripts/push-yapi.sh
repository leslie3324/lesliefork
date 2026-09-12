#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "用法: $0 --openapi <file> --base-url <url> [--endpoint <path>] [--token-env VAR] [--execute]" >&2
}

OPENAPI=
BASE_URL=
ENDPOINT=/api/open/import_data
TOKEN_ENV=YAPI_PROJECT_TOKEN
EXECUTE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --openapi) OPENAPI=${2:-}; shift 2 ;;
    --base-url) BASE_URL=${2:-}; shift 2 ;;
    --endpoint) ENDPOINT=${2:-}; shift 2 ;;
    --token-env) TOKEN_ENV=${2:-}; shift 2 ;;
    --execute) EXECUTE=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "未知参数: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "$OPENAPI" || -z "$BASE_URL" ]]; then usage; exit 2; fi
if [[ ! -f "$OPENAPI" ]]; then echo "OpenAPI 文件不存在: $OPENAPI" >&2; exit 2; fi
if [[ ! "$TOKEN_ENV" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
  echo "--token-env 必须是合法的环境变量名。" >&2
  exit 2
fi
if [[ "$ENDPOINT" != /* ]]; then ENDPOINT=/$ENDPOINT; fi
if [[ "$BASE_URL" == *\?* || "$BASE_URL" == *\#* ]]; then
  echo "--base-url 不应包含 query 或 fragment。" >&2
  exit 2
fi

"$(dirname "$0")/validate-openapi.sh" "$OPENAPI" >/dev/null

if [[ -z "${!TOKEN_ENV+x}" ]]; then
  if [[ "$EXECUTE" == true ]]; then
    echo "执行推送前必须设置环境变量 $TOKEN_ENV；脚本不会接受命令行明文 Token。" >&2
    exit 2
  fi
  TOKEN_PRESENT=false
else
  TOKEN_PRESENT=true
fi

if [[ "$EXECUTE" != true ]]; then
  echo "YApi dry-run："
  echo "- OpenAPI: $OPENAPI"
  echo "- Endpoint: ${BASE_URL%/}$ENDPOINT"
  echo "- Import type: swagger_json"
  echo "- Token env: $TOKEN_ENV (present=$TOKEN_PRESENT)"
  echo "- 未发送远程请求；增加 --execute 且设置 $TOKEN_ENV 后才会推送。"
  exit 0
fi

TEMP_RESPONSE=$(mktemp)
trap 'rm -f "$TEMP_RESPONSE"' EXIT
TOKEN=${!TOKEN_ENV}
HTTP_CODE=$(curl --silent --show-error --fail-with-body \
  --output "$TEMP_RESPONSE" --write-out '%{http_code}' \
  --request POST "${BASE_URL%/}$ENDPOINT?type=swagger_json&token=$TOKEN" \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode "json@${OPENAPI}") || {
    echo "YApi 推送失败，HTTP 状态: ${HTTP_CODE:-unknown}。未输出响应体。" >&2
    exit 1
  }
echo "YApi 推送完成，HTTP 状态: $HTTP_CODE。响应体已省略。"
