#!/usr/bin/env bash
# Clean-clone verification: clones the committed repo into a temp dir, builds a fresh Python 3.11 venv from
# requirements.txt only (no .env, no API keys, no network access needed at runtime), then checks the repo
# hygiene, README links/images, tests, the offline replay stream, and all analyze presets.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMP_DIR="$(mktemp -d -t s2s_clean_clone_XXXXXX)"
PYTHON_BIN="${PYTHON_BIN:-python3.11}"
MAX_CLONE_MB="${MAX_CLONE_MB:-20}"
TEST_PORT="$("$PYTHON_BIN" -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1]); s.close()')"

cleanup() {
  if [ -n "${SERVER_PID:-}" ] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
  rm -rf "$TEMP_DIR"
}
trap cleanup EXIT INT TERM

fail() { echo "[-] FAILED: $*"; exit 1; }

echo "=================================================================="
echo "  SIGNAL-TO-SHOCK: CLEAN-CLONE OFFLINE VERIFICATION"
echo "=================================================================="

echo "[1/8] Cloning committed files into $TEMP_DIR/clone"
git clone --quiet "$REPO_ROOT" "$TEMP_DIR/clone"
cd "$TEMP_DIR/clone"
[ ! -f .env ] || fail ".env is tracked"

echo "[2/8] Repository hygiene"
CLONE_MB=$(du -sm . | cut -f1)
echo "  -> clone size (working tree + .git): ${CLONE_MB} MB (limit ${MAX_CLONE_MB} MB)"
[ "$CLONE_MB" -le "$MAX_CLONE_MB" ] || fail "clone exceeds ${MAX_CLONE_MB} MB"
BAD=$(git ls-files | grep -E '(^|/)(node_modules|\.venv|__pycache__|\.pytest_cache|\.idea|\.vscode|\.gemini)(/|$)|\.DS_Store$|\.pyc$|(^|/)\.env$|\.log$|\.map$' || true)
[ -z "$BAD" ] || fail "junk files are tracked: $BAD"
[ -f ui/dist/index.html ] || fail "ui/dist/index.html missing (compiled UI must be committed)"
for asset in $(grep -oE '(src|href)="/assets/[^"]+"' ui/dist/index.html | sed -E 's/.*"\/(assets\/[^"]+)"/\1/'); do
  [ -f "ui/dist/$asset" ] || fail "ui/dist/index.html references missing $asset"
done
echo "  -> no junk tracked; ui/dist present with all referenced assets"

echo "[3/8] Fresh venv ($PYTHON_BIN) from requirements.txt only"
PY_VER="$("$PYTHON_BIN" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
[ "$PY_VER" = "3.11" ] || fail "Python 3.11 required, found $PY_VER"
"$PYTHON_BIN" -m venv "$TEMP_DIR/venv"
"$TEMP_DIR/venv/bin/pip" install --quiet -r requirements.txt
PY="$TEMP_DIR/venv/bin/python"
echo "  -> installed $("$TEMP_DIR/venv/bin/pip" list 2>/dev/null | tail -n +3 | wc -l | tr -d ' ') packages"

echo "[4/8] README links and images resolve (docs/presentation.pdf may be absent)"
"$PY" - <<'PYEOF'
import re, sys
from pathlib import Path
text = Path("README.md").read_text(encoding="utf-8")
text = re.sub(r"```.*?```", "", text, flags=re.S)  # ignore fenced code
missing = []
for target in re.findall(r"!?\[[^\]]*\]\(([^)\s]+)\)", text):
    if re.match(r"^(https?:|mailto:|#)", target):
        continue
    path = target.split("#")[0]
    if path == "docs/presentation.pdf":
        continue
    if path and not Path(path).exists():
        missing.append(target)
if missing:
    print("  -> broken README links:", missing)
    sys.exit(1)
print("  -> all relative README links and images resolve")
PYEOF

echo "[5/8] pytest (offline)"
env -u LLM_API_KEY -u GEMINI_API_KEY -u OPENAI_API_KEY -u NEWSAPI_KEY "$TEMP_DIR/venv/bin/python" -m pytest -q 2>&1 | tail -3

echo "[6/8] Starting demo server on port $TEST_PORT (offline)"
"$PY" run_demo.py --port "$TEST_PORT" --no-browser > "$TEMP_DIR/server.log" 2>&1 &
SERVER_PID=$!
for _ in $(seq 1 120); do
  if curl -sf "http://127.0.0.1:$TEST_PORT/health" > /dev/null 2>&1; then break; fi
  kill -0 "$SERVER_PID" 2>/dev/null || { cat "$TEMP_DIR/server.log"; fail "server died during startup"; }
  sleep 0.5
done
curl -sf "http://127.0.0.1:$TEST_PORT/health" > /dev/null || fail "server not ready"
BASE="http://127.0.0.1:$TEST_PORT"

echo "[7/8] Probing API, replay stream and presets"
HEALTH=$(curl -s "$BASE/health")
echo "$HEALTH" | grep -q '"offline_mode":true' || fail "demo is not in offline mode: $HEALTH"
echo "$HEALTH" | grep -q '"rules-fallback":0' || fail "replay signals fell back to rules extractor (cache miss): $HEALTH"
echo "  -> /health ok, offline mode, 0 replay cache misses"
[ "$(curl -s -o /dev/null -w '%{http_code}' "$BASE/")" = "200" ] || fail "GET / did not return 200"
echo "  -> GET / serves compiled UI"
N_SIG=$(curl -s "$BASE/signals" | grep -o '"signal_id"' | wc -l | tr -d ' ')
[ "$N_SIG" -ge 14 ] || fail "expected >=14 signals, got $N_SIG"
echo "  -> GET /signals: $N_SIG signals"
curl -s "$BASE/portfolio" | grep -q '"total_market_value"' || fail "/portfolio failed"
echo "  -> GET /portfolio ok"
CUSTOM=$(curl -s -X POST "$BASE/stress/custom" -H 'Content-Type: application/json' -d '{"theme":"shipping_disruption","severity":8.5}')
echo "$CUSTOM" | grep -q '"pnl_abs"' || fail "/stress/custom failed: $CUSTOM"
echo "  -> POST /stress/custom ok"
STREAM=$( (curl -N -s --max-time 4 "$BASE/replay/stream?speed=50" || true) | head -n 4 )
echo "$STREAM" | grep -q '^data: ' || fail "SSE replay stream produced no events"
echo "  -> GET /replay/stream streams events"
"$PY" - "$BASE" <<'PYEOF'
import json, sys, urllib.request
base = sys.argv[1]
presets = json.load(urllib.request.urlopen(f"{base}/presets"))
assert len(presets) == 5, f"expected 5 presets, got {len(presets)}"
for p in presets:
    req = urllib.request.Request(f"{base}/analyze", data=json.dumps({"text": p["text"], "source": p["source"], "source_type": p["source_type"]}).encode(), headers={"Content-Type": "application/json"})
    out = json.load(urllib.request.urlopen(req))
    assert "rules-fallback" not in json.dumps(out.get("model_versions", out)), f"preset {p['id']} fell back to rules extractor (cache miss)"
print("  -> all 5 presets answered from cache (no rules fallback)")
PYEOF

echo "[8/8] Done"
echo "=================================================================="
echo "  [SUCCESS] CLEAN-CLONE VERIFICATION PASSED"
echo "=================================================================="
