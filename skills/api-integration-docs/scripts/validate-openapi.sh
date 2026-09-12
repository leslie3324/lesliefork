#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "用法: $0 <openapi.json|openapi.yaml>" >&2
  exit 2
fi

INPUT=$1
if [[ ! -f "$INPUT" ]]; then
  echo "文件不存在: $INPUT" >&2
  exit 2
fi

python3 - "$INPUT" <<'PY'
import json
import pathlib
import shutil
import subprocess
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

try:
    document = json.loads(text)
except json.JSONDecodeError:
    if shutil.which("yq") is None:
        print("JSON 解析失败；校验 YAML 需要安装 yq。", file=sys.stderr)
        raise SystemExit(1)
    try:
        converted = subprocess.run(
            ["yq", "-o=json", ".", str(path)],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        document = json.loads(converted)
    except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(f"YAML 解析失败: {exc}", file=sys.stderr)
        raise SystemExit(1)

if not isinstance(document, dict):
    print("OpenAPI 根节点必须是对象。", file=sys.stderr)
    raise SystemExit(1)

version = document.get("openapi")
if not isinstance(version, str) or not version.startswith("3."):
    print("只接受 OpenAPI 3.x 文档，缺少或错误的 openapi 字段。", file=sys.stderr)
    raise SystemExit(1)

info = document.get("info")
paths = document.get("paths")
if not isinstance(info, dict) or not info.get("title") or not info.get("version"):
    print("info.title 和 info.version 均为必填。", file=sys.stderr)
    raise SystemExit(1)
if not isinstance(paths, dict) or not paths:
    print("paths 必须是非空对象。", file=sys.stderr)
    raise SystemExit(1)

methods = {"get", "put", "post", "delete", "patch", "head", "options", "trace"}
operations = []
for route, path_item in paths.items():
    if not isinstance(route, str) or not route.startswith("/"):
        print(f"路径必须以 / 开头: {route}", file=sys.stderr)
        raise SystemExit(1)
    if not isinstance(path_item, dict):
        print(f"路径项必须是对象: {route}", file=sys.stderr)
        raise SystemExit(1)
    for method, operation in path_item.items():
        if method.lower() not in methods:
            continue
        if not isinstance(operation, dict):
            print(f"操作必须是对象: {method.upper()} {route}", file=sys.stderr)
            raise SystemExit(1)
        if not isinstance(operation.get("responses"), dict) or not operation["responses"]:
            print(f"缺少 responses: {method.upper()} {route}", file=sys.stderr)
            raise SystemExit(1)
        operations.append((method.upper(), route))

if not operations:
    print("paths 中没有 HTTP 操作。", file=sys.stderr)
    raise SystemExit(1)

print(f"OpenAPI {version} 校验通过: {len(operations)} 个接口")
for method, route in operations:
    print(f"- {method} {route}")
PY
