#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 3 ]]; then
  echo "用法: $0 <openapi.json|openapi.yaml> [collection.json] [environment.example.json]" >&2
  exit 2
fi

INPUT=$1
BASE_DIR=$(cd "$(dirname "$INPUT")" && pwd)
OUTPUT=${2:-"$BASE_DIR/postman/collection.json"}
ENV_OUTPUT=${3:-"$(dirname "$OUTPUT")/environment.example.json"}

python3 "$(dirname "$0")/generate-postman.py" "$INPUT" \
  --output "$OUTPUT" \
  --environment-output "$ENV_OUTPUT"
