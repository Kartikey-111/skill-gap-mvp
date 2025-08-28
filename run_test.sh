#!/usr/bin/env bash
set -euo pipefail
if ! command -v jq >/dev/null 2>&1; then
  echo "Warning: jq not found; output will be raw JSON"
fi
curl -s -X POST http://127.0.0.1:8080/diagnostics/generate -H "Content-Type: application/json" -d @sample_payload.json | jq . || true
