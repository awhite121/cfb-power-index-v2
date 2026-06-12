"""CFBD authentication diagnostic.

Run this FIRST when CFBD requests fail. It isolates the exact cause of a 401 by
testing the key, the header format, raw connectivity, a free endpoint, and a
paid-tier endpoint, then prints a single verdict.

    python scripts/00_diagnose_cfbd.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import requests

from config import CFBD_API_KEY, PROJECT_ROOT

BASE_URL = "https://api.collegefootballdata.com"
ENV_PATH = PROJECT_ROOT / ".env"


def line(char: str = "-") -> None:
    print(char * 64)


def step_env_key() -> bool:
    line("=")
    print("STEP 1  Key presence & shape")
    line()
    if not CFBD_API_KEY:
        print("FAIL  No CFBD_API_KEY loaded.")
        print(f"      Expected it in: {ENV_PATH}")
        print("      Fix: create .env with a line like  CFBD_API_KEY=your_real_key")
        return False
    if CFBD_API_KEY == "your_key_here":
        print("FAIL  Key is still the placeholder 'your_key_here'.")
        return False

    has_ws = CFBD_API_KEY != CFBD_API_KEY.strip()
    has_quotes = CFBD_API_KEY[:1] in {'"', "'"} or CFBD_API_KEY[-1:] in {'"', "'"}
    print(f"OK    Key loaded. length={len(CFBD_API_KEY)}  prefix={CFBD_API_KEY[:3]}...  suffix=...{CFBD_API_KEY[-2:]}")
    if has_ws:
        print("WARN  Key has leading/trailing whitespace. Remove it in .env.")
    if has_quotes:
        print("WARN  Key appears wrapped in quotes. Remove the quotes in .env (CFBD_API_KEY=abc, not \"abc\").")
    if "Bearer" in CFBD_API_KEY:
        print("WARN  Key text contains 'Bearer'. Put ONLY the key in .env; the code adds 'Bearer ' itself.")
    return not (has_ws or has_quotes)


def step_connectivity() -> bool:
    line("=")
    print("STEP 2  Raw connectivity (no auth)")
    line()
    try:
        # Hitting a real path without a key should yield 401 (reached server),
        # which still proves connectivity. A network error proves it did not.
        resp = requests.get(f"{BASE_URL}/games", params={"year": 2024, "week": 1}, timeout=30)
        print(f"OK    Reached CFBD. Unauthenticated status: {resp.status_code} (a 401 here is expected).")
        return True
    except requests.RequestException as exc:
        print(f"FAIL  Could not reach CFBD at all: {exc}")
        print("      This is a network/DNS/proxy/firewall problem, NOT an API key problem.")
        return False


def probe(endpoint: str, params: dict) -> int | None:
    headers = {"Authorization": f"Bearer {CFBD_API_KEY}", "Accept": "application/json"}
    try:
        resp = requests.get(f"{BASE_URL}{endpoint}", headers=headers, params=params, timeout=45)
    except requests.RequestException as exc:
        print(f"  {endpoint:<28} network error: {exc}")
        return None
    body = resp.text[:160].replace("\n", " ")
    print(f"  {endpoint:<28} HTTP {resp.status_code}  {body}")
    return resp.status_code


def step_free_endpoint() -> int | None:
    line("=")
    print("STEP 3  Authenticated call to a FREE endpoint (/games)")
    line()
    return probe("/games", {"year": 2024, "seasonType": "regular", "week": 1})


def step_tier_endpoint() -> int | None:
    line("=")
    print("STEP 4  Authenticated call to a PAID-TIER endpoint (/player/portal)")
    line()
    return probe("/player/portal", {"year": 2025})


def verdict(free: int | None, tier: int | None) -> None:
    line("=")
    print("VERDICT")
    line()
    if free == 200 and tier == 200:
        print("Key is valid AND has paid-tier access. Everything should work. Run 01_pull_cfbd_data.py.")
    elif free == 200 and tier in (401, 403):
        print("Key is VALID. Free endpoints work; paid-tier endpoints are gated.")
        print("Your 401s are coming from tier-locked endpoints (advanced stats, portal, returning, weather).")
        print("Options: subscribe to the CFBD Patreon tier, OR rely on the manual CSV templates for those.")
    elif free == 200:
        print("Key is valid (free endpoint works). Investigate the specific failing endpoint individually.")
    elif free in (401, 403):
        print("Key is being REJECTED on a free endpoint -> the key itself is the problem.")
        print("Most likely: invalid/regenerated key, or not yet activated. Regenerate at collegefootballdata.com")
        print("and paste the new key into .env (key only, no quotes, no 'Bearer ').")
    else:
        print("Could not get a clean signal. See the network errors above (likely connectivity, not the key).")
    line("=")


def main() -> None:
    key_ok = step_env_key()
    if not key_ok and not CFBD_API_KEY:
        return
    if not step_connectivity():
        return
    free = step_free_endpoint()
    tier = step_tier_endpoint()
    verdict(free, tier)


if __name__ == "__main__":
    main()
