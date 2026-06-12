# CFBD 401 — Root-Cause Guide

Your code is **not** the problem. The client sends the correct header
(`Authorization: Bearer <key>`) against the correct host
(`https://api.collegefootballdata.com`), and your key loads cleanly from `.env`
(64 chars, no quotes, no whitespace). A 401 with this setup almost always comes
from the key itself or the access tier — not the request.

## First, run the diagnostic

```bash
python3 scripts/00_diagnose_cfbd.py
```

It tests, in order: key presence/shape → raw connectivity → a **free** endpoint
(`/games`) → a **paid-tier** endpoint (`/player/portal`), then prints one verdict.
Match its output to the cases below.

## The four causes, ranked by likelihood

1. **Invalid or regenerated key (most common).** If `/games` returns 401, the key
   is being rejected outright. Keys are invalidated when you regenerate one on the
   CFBD site — an older copy in `.env` stops working. Fix: get a fresh key from
   collegefootballdata.com and paste **only the key** into `.env` (no quotes, no
   `Bearer ` prefix).

2. **Key not activated yet.** New keys can require email verification before they
   work. Check for a verification email from CFBD.

3. **Paid-tier endpoint on a free key.** If `/games` works but `/player/portal`,
   `/stats/season/advanced`, `/player/returning`, or `/games/weather` return
   401/403, the key is valid but those endpoints need the CFBD Patreon tier. Either
   subscribe, or fill the manual CSV templates for those components (the model
   already prefers a manual CSV over the CFBD pull when both exist).

4. **Header/format issue (least likely here).** Already ruled out by inspection,
   but the diagnostic warns if a stray quote, whitespace, or a literal `Bearer`
   ever sneaks into the key value in `.env`.

## What the hardened client now does

- Classifies 401 vs 403 vs 429 vs 5xx with specific, actionable messages.
- Retries transient errors (429 / 5xx / network blips) with exponential backoff.
- Flags which endpoints are typically paid-tier so a tier-gated 401 is obvious.
- Exposes `check_auth()` for a one-call validity probe.

## Note on this environment

The data pull and the diagnostic must run **on your machine**. The assistant's
sandbox is network-restricted and cannot reach the CFBD API, so the key could not
be tested from there — only reviewed.
