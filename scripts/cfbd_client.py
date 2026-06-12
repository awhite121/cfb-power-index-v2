from __future__ import annotations

import time
from typing import Any

import pandas as pd
import requests

from config import CFBD_API_KEY

BASE_URL = "https://api.collegefootballdata.com"

# Endpoints that commonly require a paid CFBD (Patreon) tier. A 401/403 on ONLY
# these — while free endpoints like /games succeed — points to a tier issue, not
# a bad key.
TIERED_ENDPOINTS = {
    "/stats/season/advanced",
    "/stats/game/advanced",
    "/player/returning",
    "/player/portal",
    "/games/weather",
    "/ratings/sp",
    "/ratings/elo",
}


class CFBDApiError(RuntimeError):
    """Raised for any non-success CFBD response, with the status code attached."""

    def __init__(self, message: str, status_code: int | None = None, endpoint: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.endpoint = endpoint


def _auth_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {CFBD_API_KEY}",
        "Accept": "application/json",
    }


def _explain_status(status_code: int, endpoint: str, body: str) -> str:
    """Human-readable guidance for the most common failure codes."""
    if status_code == 401:
        return (
            f"401 Unauthorized for {endpoint}. The key was rejected. Most likely causes, in order:\n"
            "  1. The API key is invalid, mistyped, or was regenerated (old key no longer works).\n"
            "  2. The key has not been activated yet (check the verification email from CFBD).\n"
            "  3. The Authorization header is malformed (must be exactly 'Bearer <key>').\n"
            "Run scripts/00_diagnose_cfbd.py for a definitive answer."
        )
    if status_code == 403:
        tier_note = " This endpoint typically requires a paid CFBD (Patreon) tier." if endpoint in TIERED_ENDPOINTS else ""
        return f"403 Forbidden for {endpoint}. The key is valid but not allowed here.{tier_note}"
    if status_code == 429:
        return f"429 Too Many Requests for {endpoint}. You are being rate limited; slow down or add longer sleeps."
    return f"{status_code} error for {endpoint}: {body[:300]}"


def cfbd_get(
    endpoint: str,
    params: dict[str, Any] | None = None,
    sleep_seconds: float = 0.25,
    max_retries: int = 3,
) -> list[dict[str, Any]]:
    """Call CollegeFootballData and return JSON rows.

    endpoint example: "/games"
    params example: {"year": 2026, "seasonType": "regular"}

    Retries transient errors (429 and 5xx) with exponential backoff. Raises a
    CFBDApiError with a descriptive, code-specific message on hard failures.
    """
    if not CFBD_API_KEY or CFBD_API_KEY == "your_key_here":
        raise CFBDApiError(
            "Missing CFBD_API_KEY. Copy .env.example to .env and add your key.", status_code=None, endpoint=endpoint
        )

    url = f"{BASE_URL}{endpoint}"
    clean_params = {k: v for k, v in (params or {}).items() if v is not None}

    last_exc: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=_auth_headers(), params=clean_params, timeout=45)
        except requests.RequestException as exc:
            last_exc = exc
            wait = sleep_seconds * (2 ** attempt)
            print(f"  network error on {endpoint} (attempt {attempt}/{max_retries}): {exc} -> retry in {wait:.1f}s")
            time.sleep(wait)
            continue

        # Retry transient server-side / rate-limit issues.
        if response.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
            wait = sleep_seconds * (2 ** attempt)
            print(f"  transient {response.status_code} on {endpoint} (attempt {attempt}/{max_retries}) -> retry in {wait:.1f}s")
            time.sleep(wait)
            continue

        time.sleep(sleep_seconds)

        if response.status_code >= 400:
            raise CFBDApiError(
                _explain_status(response.status_code, endpoint, response.text),
                status_code=response.status_code,
                endpoint=endpoint,
            )

        payload = response.json()
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            return [payload]
        return []

    raise CFBDApiError(
        f"Network failure for {endpoint} after {max_retries} attempts: {last_exc}", status_code=None, endpoint=endpoint
    )


def cfbd_to_csv(endpoint: str, params: dict[str, Any], output_path) -> pd.DataFrame:
    rows = cfbd_get(endpoint, params=params)
    df = pd.json_normalize(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df):,} rows -> {output_path}")
    return df


def check_auth() -> tuple[bool, int | None, str]:
    """Lightweight auth probe against a known free endpoint.

    Returns (ok, status_code, message). Does not raise.
    """
    if not CFBD_API_KEY or CFBD_API_KEY == "your_key_here":
        return False, None, "No CFBD_API_KEY found in environment / .env."
    try:
        resp = requests.get(
            f"{BASE_URL}/games",
            headers=_auth_headers(),
            params={"year": 2024, "seasonType": "regular", "week": 1},
            timeout=45,
        )
    except requests.RequestException as exc:
        return False, None, f"Could not reach CFBD at all (network/DNS/proxy issue): {exc}"

    if resp.status_code == 200:
        n = len(resp.json()) if isinstance(resp.json(), list) else 1
        return True, 200, f"Key works. /games returned {n} rows for 2024 week 1."
    return False, resp.status_code, _explain_status(resp.status_code, "/games", resp.text)
