#!/usr/bin/env python3
"""
Upload Question CLI Tool
========================
Uploads or updates a DSA problem along with visible and hidden test cases
directly to the AI-Assisted DSA Platform backend via the admin endpoint.

Usage:
    python scripts/upload_problem.py problems/sample_two_sum_ii.json
    python scripts/upload_problem.py problems/sample_two_sum_ii.json --url http://production-dsa-alb-209746966.ap-southeast-2.elb.amazonaws.com
    python scripts/upload_problem.py problems/sample_two_sum_ii.json --key my_custom_admin_key
"""

import sys
import json
import argparse
import urllib.request
import urllib.error
import os

DEFAULT_URL = os.environ.get(
    "API_URL",
    "http://production-dsa-alb-209746966.ap-southeast-2.elb.amazonaws.com"
)
DEFAULT_KEY = os.environ.get(
    "ADMIN_API_KEY",
    "dsa_admin_secret_key_change_in_prod"
)

def parse_args():
    parser = argparse.ArgumentParser(description="Upload DSA Question JSON to Platform")
    parser.add_argument("file", help="Path to problem JSON file (e.g. problems/sample_two_sum_ii.json)")
    parser.add_argument("--url", default=DEFAULT_URL, help=f"Base backend API URL (default: {DEFAULT_URL})")
    parser.add_argument("--key", default=DEFAULT_KEY, help="Admin API Key for X-Admin-Key header")
    return parser.parse_args()

def main():
    args = parse_args()
    file_path = args.file

    if not os.path.exists(file_path):
        print(f"[-] Error: File not found at '{file_path}'")
        sys.exit(1)

    print(f"[*] Reading problem file: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[-] Invalid JSON in '{file_path}': {e}")
        sys.exit(1)

    # Basic schema checks
    required_fields = ["title", "slug", "difficulty", "description", "test_cases"]
    for rf in required_fields:
        if rf not in data:
            print(f"[-] Error: Missing required field '{rf}' in JSON.")
            sys.exit(1)

    title = data.get("title")
    slug = data.get("slug")
    difficulty = data.get("difficulty")
    test_cases = data.get("test_cases", [])
    public_tc = sum(1 for tc in test_cases if not tc.get("is_hidden", False))
    hidden_tc = sum(1 for tc in test_cases if tc.get("is_hidden", False))

    print(f"[*] Preparing to upload:")
    print(f"    - Title:        {title}")
    print(f"    - Slug:         {slug}")
    print(f"    - Difficulty:   {difficulty.upper()}")
    print(f"    - Public Tests: {public_tc}")
    print(f"    - Hidden Tests: {hidden_tc}")
    print(f"    - Target URL:   {args.url}/api/v1/questions")

    endpoint = f"{args.url.rstrip('/')}/api/v1/questions"
    headers = {
        "Content-Type": "application/json",
        "X-Admin-Key": args.key,
        "User-Agent": "DSA-Admin-CLI/1.0"
    }

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(data).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            status_code = resp.getcode()
            response_body = resp.read().decode("utf-8")
            result = json.loads(response_body)

            print("\n[+] SUCCESS! Question uploaded successfully.")
            print(f"    - HTTP Status:     {status_code}")
            print(f"    - Question ID:     {result.get('id')}")
            print(f"    - Catalog Slug:    {result.get('slug')}")
            print(f"    - Visible Cases:   {len(result.get('test_cases', []))}")
            print(f"\n[+] View in browser: {args.url}/problems/{slug}")

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"\n[-] HTTP Error {e.code}: {e.reason}")
        print(f"    Details: {error_body}")
        if e.code == 403:
            print("    [Hint] Admin key rejected. Check --key argument or ADMIN_API_KEY environment variable.")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"\n[-] Network Connection Error: {e.reason}")
        print(f"    Could not reach {args.url}. Ensure the server is online and reachable.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[-] Unexpected Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
