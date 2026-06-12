#!/usr/bin/env python3
"""
Test Saxo integration with both OAuth token and API key methods.

Usage:
    # Test with OAuth token:
    python test_saxo_both_methods.py --method oauth --token "your_oauth_token"

    # Test with API key:
    python test_saxo_both_methods.py --method apikey --key "your_api_key"
"""

import sys
import argparse
import json

BASE_URL = "https://gateway.saxobank.com/sim/openapi"


def test_endpoint(method, credential, endpoint, params=None):
    """Test a single endpoint."""
    try:
        import requests
    except ImportError:
        print("ERROR: requests library not found. Install with: pip install requests")
        return None

    headers = {
        "Content-Type": "application/json",
    }

    if method == "oauth":
        headers["Authorization"] = f"Bearer {credential}"
    elif method == "apikey":
        headers["Authorization"] = f"Bearer {credential}"

    url = f"{BASE_URL}/{endpoint}"

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        return response.status_code, response.text[:500]
    except Exception as e:
        return None, str(e)


def test_saxo(method, credential):
    """Test Saxo API with given method and credential."""
    print("=" * 70)
    print(f"SAXO API TEST — {method.upper()} Method")
    print("=" * 70)
    print(f"Credential: {credential[:30]}...\n")

    tests = [
        ("TEST 1: Get Client Info", "port/v1/clients/me", None),
        ("TEST 2: Get Accounts", "port/v1/accounts", {"ClientKey": "test"}),
        ("TEST 3: Get Balances", "port/v1/balances", {"ClientKey": "test"}),
        ("TEST 4: Get Positions", "port/v1/positions/test", None),
        ("TEST 5: Get Transactions", "hist/v1/transactions", {"ClientKey": "test"}),
    ]

    results = {"method": method, "tests": []}

    for name, endpoint, params in tests:
        print(f"\n{name}")
        print(f"  Endpoint: {endpoint}")
        status, response = test_endpoint(method, credential, endpoint, params)

        if status is None:
            print(f"  ❌ ERROR: {response}")
            results["tests"].append({"name": name, "status": "error", "error": response})
        else:
            print(f"  Status: {status}")
            if status == 200:
                print(f"  ✅ SUCCESS")
                results["tests"].append({"name": name, "status": "success"})
            elif status == 401:
                print(f"  ❌ UNAUTHORIZED — Check credential")
                results["tests"].append({"name": name, "status": "unauthorized"})
            elif status == 404:
                print(f"  ⚠️  NOT FOUND (404)")
                results["tests"].append({"name": name, "status": "not_found"})
            else:
                print(f"  ❌ FAILED — {response[:100]}")
                results["tests"].append({"name": name, "status": f"error_{status}"})

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    success_count = sum(1 for t in results["tests"] if t["status"] == "success")
    print(f"Passed: {success_count}/{len(results['tests'])}")

    if success_count == len(results["tests"]):
        print("✅ ALL TESTS PASSED — Integration is working!")
    elif success_count > 0:
        print("⚠️  PARTIAL SUCCESS — Some endpoints work, some don't")
    else:
        print("❌ NO TESTS PASSED — Check your credential")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test Saxo API with OAuth token or API key"
    )
    parser.add_argument(
        "--method",
        choices=["oauth", "apikey"],
        required=True,
        help="Authentication method",
    )
    parser.add_argument(
        "--token", help="OAuth2 access token (for --method oauth)"
    )
    parser.add_argument(
        "--key", help="API key (for --method apikey)"
    )

    args = parser.parse_args()

    credential = None
    if args.method == "oauth" and args.token:
        credential = args.token
    elif args.method == "apikey" and args.key:
        credential = args.key

    if not credential:
        print(f"ERROR: --{args.method == 'oauth' and 'token' or 'key'} is required for --method {args.method}")
        sys.exit(1)

    results = test_saxo(args.method, credential)

    print("\n📋 JSON Results:")
    print(json.dumps(results, indent=2))
