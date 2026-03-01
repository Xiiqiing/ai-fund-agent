#!/usr/bin/env bash
# ──────────────────────────────────────────────────────
# Smoke test for AI Fund Operations Agent
# Usage: ./scripts/smoke_test.sh <BASE_URL>
# ──────────────────────────────────────────────────────
set -euo pipefail

BASE_URL="${1:?Usage: smoke_test.sh <BASE_URL>}"
PASSED=0
TOTAL=0

echo "🔍 Smoke testing: ${BASE_URL}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── Test 1: Homepage loads ──
TOTAL=$((TOTAL + 1))
echo -n "  [1/3] Homepage returns HTTP 200... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}" --max-time 30)
if [ "$STATUS" = "200" ]; then
    echo "✅"
    PASSED=$((PASSED + 1))
else
    echo "❌ (HTTP ${STATUS})"
fi

# ── Test 2: Streamlit health endpoint ──
TOTAL=$((TOTAL + 1))
echo -n "  [2/3] Streamlit health endpoint... "
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/_stcore/health" --max-time 10)
if [ "$HEALTH_STATUS" = "200" ]; then
    echo "✅"
    PASSED=$((PASSED + 1))
else
    echo "❌ (HTTP ${HEALTH_STATUS})"
fi

# ── Test 3: Page contains expected content ──
TOTAL=$((TOTAL + 1))
echo -n "  [3/3] Page contains 'Fund Assistant'... "
BODY=$(curl -s "${BASE_URL}" --max-time 30)
if echo "$BODY" | grep -qi "Fund Assistant"; then
    echo "✅"
    PASSED=$((PASSED + 1))
else
    echo "❌ (content not found)"
fi

# ── Summary ──
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🏁 Smoke test: ${PASSED}/${TOTAL} passed"

if [ "$PASSED" -lt "$TOTAL" ]; then
    echo "❌ FAILED — some checks did not pass"
    exit 1
fi

echo "✅ ALL PASSED"
