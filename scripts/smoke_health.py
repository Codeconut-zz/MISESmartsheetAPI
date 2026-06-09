"""Simple local smoke test for the FastAPI health endpoint."""

from __future__ import annotations

import json
import sys
import urllib.request


def main() -> int:
    base_url = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    with urllib.request.urlopen(f"{base_url}/health", timeout=5) as response:
        payload = json.loads(response.read().decode("utf-8"))

    if payload != {"status": "ok"}:
        print(f"Unexpected health payload: {payload}", file=sys.stderr)
        return 1

    print("health ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
