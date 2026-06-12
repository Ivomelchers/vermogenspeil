#!/bin/bash
# Test Saxo Bank API endpoints
# Usage: ./test_saxo_endpoints.sh YOUR_SAXO_ACCESS_TOKEN

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <SAXO_ACCESS_TOKEN>"
    echo ""
    echo "Get your access token from Saxo Bank OpenAPI:"
    echo "1. Go to https://developer.saxobank.com"
    echo "2. Get your OAuth2 token"
    echo "3. Pass it as argument: $0 'your_token_here'"
    exit 1
fi

TOKEN="$1"
BASE_URL="https://gateway.saxobank.com/sim/openapi"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "=========================================="
echo "Saxo Bank API Endpoint Test"
echo "=========================================="
echo "Timestamp: $TIMESTAMP"
echo "Token: ${TOKEN:0:20}..."
echo ""

# Test 1: Get Client Info
echo "TEST 1: Get Current Client"
echo "Endpoint: GET $BASE_URL/port/v1/clients/me"
echo "---"
RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  "$BASE_URL/port/v1/clients/me")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')
echo "HTTP Status: $HTTP_CODE"
echo "Response:"
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
echo ""

if [ "$HTTP_CODE" == "200" ]; then
    CLIENT_KEY=$(echo "$BODY" | jq -r '.ClientKey' 2>/dev/null)
    echo "✓ SUCCESS - Got ClientKey: $CLIENT_KEY"
    echo ""
else
    echo "✗ FAILED - Check token and endpoint"
    echo ""
    exit 1
fi

# Test 2: Get Accounts
echo "TEST 2: Get Accounts"
echo "Endpoint: GET $BASE_URL/port/v1/accounts?ClientKey=$CLIENT_KEY"
echo "---"
RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  "$BASE_URL/port/v1/accounts?ClientKey=$CLIENT_KEY")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')
echo "HTTP Status: $HTTP_CODE"
echo "Response:"
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
echo ""

if [ "$HTTP_CODE" == "200" ]; then
    ACCOUNT_KEY=$(echo "$BODY" | jq -r '.Data[0].AccountKey' 2>/dev/null)
    echo "✓ SUCCESS - Got AccountKey: $ACCOUNT_KEY"
    echo ""
else
    echo "✗ FAILED - Check ClientKey or endpoint"
    echo ""
fi

# Test 3: Get Balances
if [ ! -z "$ACCOUNT_KEY" ]; then
    echo "TEST 3: Get Balances"
    echo "Endpoint: GET $BASE_URL/port/v1/balances?AccountKey=$ACCOUNT_KEY"
    echo "---"
    RESPONSE=$(curl -s -w "\n%{http_code}" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      "$BASE_URL/port/v1/balances?AccountKey=$ACCOUNT_KEY")

    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    echo "HTTP Status: $HTTP_CODE"
    echo "Response (first 500 chars):"
    echo "$BODY" | jq '.' 2>/dev/null | head -20 || echo "$BODY" | head -20
    echo ""

    if [ "$HTTP_CODE" == "200" ]; then
        echo "✓ SUCCESS - Balances endpoint works"
    else
        echo "✗ FAILED - Check AccountKey or endpoint"
    fi
fi

# Test 4: Get Positions
if [ ! -z "$ACCOUNT_KEY" ]; then
    echo ""
    echo "TEST 4: Get Positions"
    echo "Endpoint: GET $BASE_URL/port/v1/positions/$ACCOUNT_KEY"
    echo "---"
    RESPONSE=$(curl -s -w "\n%{http_code}" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      "$BASE_URL/port/v1/positions/$ACCOUNT_KEY")

    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    echo "HTTP Status: $HTTP_CODE"
    echo "Response (first 500 chars):"
    echo "$BODY" | jq '.' 2>/dev/null | head -20 || echo "$BODY" | head -20
    echo ""

    if [ "$HTTP_CODE" == "200" ]; then
        echo "✓ SUCCESS - Positions endpoint works"
    else
        echo "✗ FAILED - Check endpoint path"
    fi
fi

# Test 5: Get Trades
if [ ! -z "$ACCOUNT_KEY" ]; then
    echo ""
    echo "TEST 5: Get Trades"
    echo "Endpoint: GET $BASE_URL/trade/v1/trades/$ACCOUNT_KEY"
    echo "---"
    RESPONSE=$(curl -s -w "\n%{http_code}" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      "$BASE_URL/trade/v1/trades/$ACCOUNT_KEY?count=10")

    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    echo "HTTP Status: $HTTP_CODE"
    echo "Response (first 500 chars):"
    echo "$BODY" | jq '.' 2>/dev/null | head -20 || echo "$BODY" | head -20
    echo ""

    if [ "$HTTP_CODE" == "200" ]; then
        echo "✓ SUCCESS - Trades endpoint works"
    elif [ "$HTTP_CODE" == "404" ]; then
        echo "✗ NOT FOUND - Endpoint path may be wrong"
        echo "   Try: /trade/v2/trades/$ACCOUNT_KEY"
    else
        echo "✗ FAILED - Check endpoint"
    fi
fi

echo ""
echo "=========================================="
echo "Test Complete"
echo "=========================================="
echo ""
echo "If you got ✓ for all tests, the endpoints are correct!"
echo "If you got ✗ errors:"
echo "  - Check your token is valid and not expired"
echo "  - Check the endpoint paths in the script"
echo "  - Share the HTTP error messages with me"
