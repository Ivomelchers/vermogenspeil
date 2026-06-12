#!/usr/bin/env python3
"""
Test Saxo Bank API endpoints to verify they work.

Usage:
    python test_saxo_endpoints.py YOUR_SAXO_ACCESS_TOKEN

Or on Render shell:
    python manage.py shell < test_saxo_endpoints.py
"""

import sys
import json
import requests
from datetime import datetime
from typing import Optional, Tuple

BASE_URL = "https://gateway.saxobank.com/sim/openapi"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*50}{Colors.RESET}")
    print(f"{Colors.BOLD}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*50}{Colors.RESET}\n")


def print_success(text: str):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text: str):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_test(test_num: int, name: str, endpoint: str):
    print(f"\n{Colors.BOLD}TEST {test_num}: {name}{Colors.RESET}")
    print(f"Endpoint: {endpoint}")
    print("-" * 50)


def make_request(method: str, endpoint: str, token: str, params: dict = None) -> Tuple[int, dict]:
    """Make HTTP request to Saxo API and return (status_code, response_json)."""
    url = f"{BASE_URL}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=10)
        else:
            response = requests.post(url, headers=headers, json=params, timeout=10)

        try:
            return response.status_code, response.json()
        except:
            return response.status_code, {"raw_response": response.text[:200]}
    except Exception as e:
        return 0, {"error": str(e)}


def test_saxo_endpoints(token: str):
    """Run all endpoint tests."""
    print_header(f"Saxo Bank API Endpoint Test")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Token: {token[:20]}...")
    print(f"Base URL: {BASE_URL}\n")

    # Test 1: Get Client Info
    print_test(1, "Get Current Client", "GET /port/v1/clients/me")
    status, data = make_request("GET", "port/v1/clients/me", token)
    print(f"HTTP Status: {status}")
    print(f"Response: {json.dumps(data, indent=2)[:500]}")

    if status != 200:
        print_error("Failed to get client info")
        print(f"  Status {status}: Check if token is valid and not expired")
        return False

    client_key = data.get("ClientKey")
    if not client_key:
        print_error("Response missing ClientKey field")
        return False

    print_success(f"Got ClientKey: {client_key}")

    # Test 2: Get Accounts
    print_test(2, "Get Accounts", f"GET /port/v1/accounts?ClientKey={client_key}")
    status, data = make_request("GET", f"port/v1/accounts", token, {"ClientKey": client_key})
    print(f"HTTP Status: {status}")
    print(f"Response: {json.dumps(data, indent=2)[:500]}")

    if status != 200:
        print_error(f"Failed to get accounts (HTTP {status})")
        return False

    accounts = data.get("Data", [])
    if not accounts:
        print(f"{Colors.YELLOW}! No accounts found (may be OK if test account is empty){Colors.RESET}")
        account_key = None
    else:
        account_key = accounts[0].get("AccountKey")
        account_id = accounts[0].get("AccountId")
        print_success(f"Got {len(accounts)} account(s)")
        print(f"  Account: {account_id} (Key: {account_key})")

    # Test 3: Get Balances (if we have account)
    if account_key:
        print_test(3, "Get Balances", f"GET /port/v1/balances?AccountKey={account_key}")
        status, data = make_request("GET", "port/v1/balances", token, {"AccountKey": account_key})
        print(f"HTTP Status: {status}")
        print(f"Response: {json.dumps(data, indent=2)[:500]}")

        if status == 200:
            print_success("Balances endpoint works")
            cash_balance = data.get("CashBalance")
            total_value = data.get("TotalValue")
            if cash_balance is not None:
                print(f"  Cash Balance: {cash_balance}")
            if total_value is not None:
                print(f"  Total Value: {total_value}")
        else:
            print_error(f"Failed to get balances (HTTP {status})")

    # Test 4: Get Positions
    if account_key:
        print_test(4, "Get Positions", f"GET /port/v1/positions/{account_key}")
        status, data = make_request("GET", f"port/v1/positions/{account_key}", token)
        print(f"HTTP Status: {status}")
        print(f"Response: {json.dumps(data, indent=2)[:500]}")

        if status == 200:
            positions = data.get("Data", [])
            print_success(f"Positions endpoint works ({len(positions)} positions)")
            if positions:
                pos = positions[0]
                print(f"  First position: {pos.get('Identifier')} - {pos.get('NetPosition')} units")
        elif status == 404:
            print_error("Positions endpoint not found (404)")
            print(f"  May need different path, e.g.: /port/v2/positions/{account_key}")
        else:
            print_error(f"Failed to get positions (HTTP {status})")

    # Test 5: Get Trades
    if account_key:
        print_test(5, "Get Trades", f"GET /trade/v1/trades/{account_key}")
        status, data = make_request("GET", f"trade/v1/trades/{account_key}", token, {"count": 10})
        print(f"HTTP Status: {status}")
        print(f"Response: {json.dumps(data, indent=2)[:500]}")

        if status == 200:
            trades = data.get("Data", [])
            print_success(f"Trades endpoint works ({len(trades)} trades)")
            if trades:
                trade = trades[0]
                print(f"  First trade: {trade.get('Uic')} - {trade.get('BuySell')} {trade.get('Amount')} units")
        elif status == 404:
            print_error("Trades endpoint not found (404)")
            print(f"  May need different path:")
            print(f"    Try: /trade/v2/trades/{account_key}")
            print(f"    Try: /trade/v1/trades/me")
        else:
            print_error(f"Failed to get trades (HTTP {status})")

    # Summary
    print_header("Test Summary")
    print("If all tests passed (✓), the endpoints are correct!")
    print("\nIf you got ✗ errors:")
    print("  - 401/403: Token is invalid or expired")
    print("  - 404: Endpoint path is wrong")
    print("  - Other: Share the error message with me")
    print("")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_saxo_endpoints.py YOUR_SAXO_ACCESS_TOKEN")
        print("")
        print("Get your access token:")
        print("  1. Go to https://developer.saxobank.com")
        print("  2. Create an app or use sandbox")
        print("  3. Get OAuth2 access token")
        print("  4. Run: python test_saxo_endpoints.py 'your_token_here'")
        sys.exit(1)

    token = sys.argv[1]
    test_saxo_endpoints(token)
