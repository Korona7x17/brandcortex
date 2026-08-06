#!/usr/bin/env bash
# Run the API and the dashboard together for local development.
set -euo pipefail

cd "$(dirname "$0")/.."
[[ -f .env ]] || { echo "no .env — copy .env.example and fill it in"; exit 1; }

(cd apps/api && uv run uvicorn brandcortex.main:app --reload --port 8000) &
API_PID=$!
trap 'kill $API_PID 2>/dev/null || true' EXIT

cd apps/web && npm run dev
