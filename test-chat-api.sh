#!/bin/bash

# Test script for chat API endpoint
# Usage: ./test-chat-api.sh [port]

PORT=${1:-5001}
BASE_URL="http://localhost:${PORT}"

echo "Testing Chat API on ${BASE_URL}/api/chat"
echo "========================================"
echo ""

# Test OPTIONS (CORS preflight)
echo "1. Testing OPTIONS (CORS preflight)..."
OPTIONS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X OPTIONS \
  -H "Origin: http://localhost:${PORT}" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  "${BASE_URL}/api/chat")

if [ "$OPTIONS_RESPONSE" = "204" ] || [ "$OPTIONS_RESPONSE" = "200" ]; then
    echo "✅ OPTIONS request successful (${OPTIONS_RESPONSE})"
else
    echo "❌ OPTIONS request failed (${OPTIONS_RESPONSE})"
fi

echo ""

# Test POST
echo "2. Testing POST request..."
POST_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:${PORT}" \
  -d '{"message": "Bu hafta hangi etkinlikler var?"}' \
  "${BASE_URL}/api/chat")

HTTP_CODE=$(curl -s -o /tmp/response.json -w "%{http_code}" -X POST \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:${PORT}" \
  -d '{"message": "Bu hafta hangi etkinlikler var?"}' \
  "${BASE_URL}/api/chat")

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ POST request successful (${HTTP_CODE})"
    echo "Response:"
    cat /tmp/response.json | python3 -m json.tool 2>/dev/null || cat /tmp/response.json
else
    echo "❌ POST request failed (${HTTP_CODE})"
    echo "Response:"
    cat /tmp/response.json
fi

echo ""
echo "========================================"
echo "Test completed!"

