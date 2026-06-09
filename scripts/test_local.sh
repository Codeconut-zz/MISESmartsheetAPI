#!/usr/bin/env bash
set -euo pipefail

docker compose config >/dev/null
pytest
python scripts/smoke_health.py "${MISE_API_URL:-http://127.0.0.1:8000}"
