"""
Live ESPN data layer for the CFB Power Index.

Everything here is fetched at runtime from ESPN's public JSON API and cached with
short TTLs, so the deployed app stays current (live AP poll, scoreboard, records,
FPI, per-team schedule/stats/roster) without committing stale snapshots. Every
public function is wrapped so a network hiccup degrades gracefully (empty frame /
None) instead of crashing a tab. Call clear_live_cache() to force a refresh.
"""
from __future__ import annotations

import math
import requests
import pandas as pd


def win_prob(spread: float, sigma: float = 16.5) -> float:
    """Win probability for a team favored by `spread` points (normal model)."""
    try:
        return 0.5 * (1 + math.erf(spread / (sigma * math.sqrt(2))))
    except Exception:
        return 0.5

try:
    import streamlit as st
    _cache = st.cache_data
except Exception:  # allow standalone import/testing without streamlit
    def _cache(*a, **k):
        def deco(fn): return fn
        return (deco if not a else deco(a[0]))
    class _Dummy:
        def cache_data(self, *a, **k): return _cache(*a, **k)
    st = _Dummy()  # type: ignore

import re
SEASON = 2026
SITE = "https://site.api.espn.com/apis/site/v2/sports/football/college-football"
SITE_V2 = "https://site.api.espn.com/apis/v2/sports/football/college-football"
FITT = "https://site.web.api.espn.com/apis/fitt/v3/sports/football/college-football"
CORE = "https://sports.core.api.espn.com/v2/sports/football/leagues/college-football"
# NOTE: ESPN's API returns 403 for browser-like User-Agents on these hosts but
# serves clean JSON to the default requests/curl agent, so we deliberately do NOT
# spoof a browser UA here.
HDRS = {"Accept": "application/json"}


def _get(url, params=None, timeout=12):
    r = requests.get(url, params=params, headers=HDRS, timeout=timeout)
    r.raise_for_status()
    return r.json()


def logo_url(team_id) -> str:
    return f"https://a.espncdn.com/i/teamlogos/ncaa/500/{team_id}.png"


def clear_live_cache():
    """Drop all cached ESPN responses so the next call refetches live."""
    try:
        st.cache_data.clear()
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Bulk endpoints (fast — load on tab open)
# ─────────────────────────────────────────────────────────────────────────────
@_cache(ttl=600, show_spinner=False)
def get_ap_top25() -> pd.DataFrame:
    """AP Top 25: rank, team, record, points, first-place votes, weekly trend."""
    try:
        d = _get(f"{SITE}/rankings")
        polls = d.get("rankings", [])
        ap = next((p for p in polls if "AP" in p.get("name", "")), polls[0] if polls else None)
        if not ap:
            return pd.DataFrame()
        rows = []
        for t in ap.get("ranks", []):
            tm = t.get("team", {})
            rows.append({
                "rank": t.get("current"),
                "prev": t.get("previous"),
                "team": tm.get("location") or tm.get("nickname"),
                "team_id": tm.get("id"),
                "nickname": tm.get("nickname"),
                "record": t.get("recordSummary", ""),
                "points": t.get("points"),
                "fpv": t.get("firstPlaceVotes", 0),
                "trend": t.get("trend", "-"),
                "logo": logo_url(tm.get("id")),
                "color": "#" + (tm.get("color") or "555555"),
            })
        meta = ap.get("occurrence", {})
        df = pd.DataFrame(rows)
        df.attrs["headline"] = ap.get("headline", "")
        df.attrs["week"] = meta.get("displayName", "")
        return df
    except Exception:
        return pd.DataFrame()


@_cache(ttl=300, show_spinner=False)
def get_scoreboard(week: int | None = None) -> pd.DataFrame:
    """This week's games: matchup, ranks, records, status/score, spread, TV, venue."""
    try:
        params = {"limit": 400}
        if week:
            params["week"] = week
        d = _get(f"{SITE}/scoreboard", params=params)
        rows = []
        wk = d.get("week", {}).get("number")
        for e in d.get("events", []):
            comp = (e.get("competitions") or [{}])[0]
            cs = comp.get("competitors", [])
            home = next((c for c in cs if c.get("homeAway") == "home"), {})
            away = next((c for c in cs if c.get("homeAway") == "away"), {})
            if not home or not away:
                continue
            status = e.get("status", {}).get("type", {})
            odds = (comp.get("odds") or [{}])[0]

            def _rk(c):
                r = (c.get("curatedRank") or {}).get("current", 99)
                return r if r and r <= 25 else None

            def _rec(c):
                recs = c.get("records") or []
                return recs[0].get("summary", "") if recs else ""

            rows.append({
                "id": e.get("id"),
                "week": wk,
                "date": e.get("date"),
                "home": home.get("team", {}).get("location"),
                "home_id": home.get("team", {}).get("id"),
                "home_abbr": home.get("team", {}).get("abbreviation"),
                "home_logo": logo_url(home.get("team", {}).get("id")),
                "home_color": "#" + (home.get("team", {}).get("color") or "555555"),
                "home_rank": _rk(home),
                "home_rec": _rec(home),
                "home_score": home.get("score"),
                "away": away.get("team", {}).get("location"),
                "away_id": away.get("team", {}).get("id"),
                "away_abbr": away.get("team", {}).get("abbreviation"),
                "away_logo": logo_url(away.get("team", {}).get("id")),
                "away_color": "#" + (away.get("team", {}).get("color") or "555555"),
                "away_rank": _rk(away),
                "away_rec": _rec(away),
                "away_score": away.get("score"),
                "state": status.get("state"),          # pre / in / post
                "status": status.get("shortDetail", ""),
                "completed": status.get("completed", False),
                "spread": odds.get("details", ""),
                "ou": odds.get("overUnder"),
                "tv": ", ".join(sorted({n for b in comp.get("broadcasts", [])
                                        for n in b.get("names", [])})),
                "venue": (comp.get("venue") or {}).get("fullName", ""),
                "neutral": comp.get("neutralSite", False),
            })
        df = pd.DataFrame(rows)
        df.attrs["week"] = wk
        return df
    except Exception:
        return pd.DataFrame()


def best_matchups(sb: pd.DataFrame, n: int = 6) -> pd.DataFrame:
    """Rank this week's games by buzz: both-ranked > combined rank > tight spread."""
    if sb is None or sb.empty:
        return pd.DataFrame()
    df = sb.copy()

    def buzz(r):
        hr, ar = r.get("home_rank"), r.get("away_rank")
        both = hr is not None and ar is not None
        one = (hr is not None) ^ (ar is not None)
        # lower score = better matchup
        if both:
            base = (hr + ar)          # e.g. #1 vs #2 -> 3 (best)
        elif one:
            base = 60 + (hr or ar)    # ranked vs unranked
        else:
            base = 200
        # tighten by spread magnitude (closer games score better)
        try:
            import re
            m = re.search(r"-?\d+\.?\d*", str(r.get("spread", "")))
            sp = abs(float(m.group())) if m else 25
        except Exception:
            sp = 25
        return base + sp * 0.4

    df["_buzz"] = df.apply(buzz, axis=1)
    return df.sort_values("_buzz").head(n).drop(columns="_buzz")


def _parse_record(rec: str):
    """'2-1' or '2-1-0' -> (wins, losses, win_pct). Returns (None, None, None)."""
    try:
        parts = [int(x) for x in str(rec).split("-")]
        w = parts[0]
        losses = parts[1]
        ties = parts[2] if len(parts) > 2 else 0
        games = w + losses + ties
        return w, losses, (round((w + 0.5 * ties) / games, 4) if games else None)
    except Exception:
        return None, None, None


@_cache(ttl=900, show_spinner=False)
def get_standings() -> pd.DataFrame:
    """Every FBS team with conference, overall + conference record, win%.

    ESPN's standings payload only reliably carries the overall record STRING at
    type=total, so wins/losses/win% are parsed from it.
    """
    try:
        d = _get(f"{SITE_V2}/standings", params={"season": SEASON, "level": 80})
        rows = []
        for conf in d.get("children", []):
            cname = conf.get("shortName") or conf.get("name")
            for e in conf.get("standings", {}).get("entries", []):
                tm = e.get("team", {})

                def disp(name, typ=None):
                    for s in e.get("stats", []):
                        if s.get("name") == name and (typ is None or s.get("type") == typ):
                            return s.get("displayValue")
                    return None

                overall = disp("overall", "total")
                w, losses, wp = _parse_record(overall)
                rows.append({
                    "team_id": tm.get("id"),
                    "team": tm.get("location") or tm.get("displayName"),
                    "conf": cname,
                    "logo": logo_url(tm.get("id")),
                    "overall": overall,
                    "conf_rec": disp("vs. Conf.", "vsconf"),
                    "wins": w,
                    "losses": losses,
                    "win_pct": wp,
                })
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()


@_cache(ttl=1800, show_spinner=False)
def get_fpi() -> pd.DataFrame:
    """ESPN Football Power Index: rating + rank + projected record where available."""
    try:
        d = _get(f"{FITT}/powerindex", params={"region": "us", "lang": "en",
                                               "season": SEASON, "limit": 250})
        # value-name order for each category
        order = {c.get("name"): c.get("names", []) for c in d.get("categories", [])}
        rows = []
        for t in d.get("teams", []):
            tm = t.get("team", {})
            rec = {"team_id": tm.get("id"),
                   "team": tm.get("location") or tm.get("displayName"),
                   "logo": logo_url(tm.get("id"))}
            for cat in t.get("categories", []):
                names = order.get(cat.get("name"), [])
                for i, val in enumerate(cat.get("values", [])):
                    key = names[i] if i < len(names) else f"{cat.get('name')}_{i}"
                    rec[key] = val
            rows.append(rec)
        df = pd.DataFrame(rows)
        return df
    except Exception:
        return pd.DataFrame()


@_cache(ttl=900, show_spinner=False)
def get_stat_leaders() -> list:
    """Live 2026 individual leaders (top player per key category) with team + value.
    Resolves only the #1 athlete per category to stay cheap (a handful of calls)."""
    labels = {"passingYards": "Passing Yds", "rushingYards": "Rushing Yds",
              "receivingYards": "Receiving Yds", "sacks": "Sacks",
              "interceptions": "INTs", "passingTouchdowns": "Pass TDs"}
    try:
        d = _get(f"{CORE}/seasons/{SEASON}/types/2/leaders")
        out = []
        by = {c.get("name"): c for c in d.get("categories", [])}
        for key, lbl in labels.items():
            c = by.get(key)
            if not c or not c.get("leaders"):
                continue
            top = c["leaders"][0]
            name = "?"
            aref = (top.get("athlete") or {}).get("$ref")
            if aref:
                try:
                    a = _get(aref); name = a.get("displayName") or a.get("fullName", "?")
                except Exception:
                    pass
            tref = (top.get("team") or {}).get("$ref", "")
            m = re.search(r"/teams/(\d+)", tref)
            tid = m.group(1) if m else None
            out.append({"cat": lbl, "player": name, "value": top.get("displayValue"),
                        "team_id": tid, "logo": logo_url(tid) if tid else ""})
        return out
    except Exception:
        return []


@_cache(ttl=900, show_spinner=False)
def get_fbs_teams() -> pd.DataFrame:
    """FBS team directory for pickers: id, name, conf, logo (from standings)."""
    s = get_standings()
    if s is not None and not s.empty:
        return s[["team_id", "team", "conf", "logo"]].sort_values("team").reset_index(drop=True)
    return pd.DataFrame()


# ─────────────────────────────────────────────────────────────────────────────
# Per-team detail (on-demand — fetched when a team is selected)
# ─────────────────────────────────────────────────────────────────────────────
@_cache(ttl=1800, show_spinner=False)
def get_team_schedule(team_id) -> pd.DataFrame:
    """Full 2026 schedule: opponent, home/away, result or upcoming, score."""
    try:
        d = _get(f"{SITE}/teams/{team_id}/schedule")
        tid = str(team_id)
        rows = []
        for e in d.get("events", []):
            comp = (e.get("competitions") or [{}])[0]
            cs = comp.get("competitors", [])
            me = next((c for c in cs if str(c.get("id")) == tid
                       or str(c.get("team", {}).get("id")) == tid), {})
            opp = next((c for c in cs if c is not me), {})
            st_type = comp.get("status", {}).get("type", {})
            completed = st_type.get("completed", False)
            ms = me.get("score", {})
            os_ = opp.get("score", {})
            mv = ms.get("value") if isinstance(ms, dict) else ms
            ov = os_.get("value") if isinstance(os_, dict) else os_
            wl = ""
            if completed and mv is not None and ov is not None:
                wl = "W" if mv > ov else ("L" if mv < ov else "T")
            rows.append({
                "week": e.get("week", {}).get("number"),
                "week_label": e.get("week", {}).get("text", ""),
                "date": e.get("date"),
                "opp": opp.get("team", {}).get("location") or opp.get("team", {}).get("displayName"),
                "opp_id": opp.get("team", {}).get("id"),
                "opp_logo": logo_url(opp.get("team", {}).get("id")),
                "opp_rank": (opp.get("curatedRank") or {}).get("current"),
                "home_away": me.get("homeAway"),
                "completed": completed,
                "result": wl,
                "pts_for": int(mv) if mv is not None else None,
                "pts_against": int(ov) if ov is not None else None,
                "status": st_type.get("shortDetail", ""),
            })
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()


@_cache(ttl=1800, show_spinner=False)
def get_team_stats(team_id, season: int = SEASON) -> dict:
    """Season team stats grouped by category -> {label: (value, rank)}."""
    try:
        d = _get(f"{SITE}/teams/{team_id}/statistics", params={"season": season})
        cats = d.get("results", {}).get("stats", {}).get("categories", [])
        out = {}
        for c in cats:
            block = {}
            for s in c.get("stats", []):
                block[s.get("displayName") or s.get("name")] = {
                    "value": s.get("displayValue"),
                    "rank": s.get("rank"),
                    "per_game": s.get("perGameDisplayValue"),
                }
            out[c.get("name")] = block
        return out
    except Exception:
        return {}


@_cache(ttl=1800, show_spinner=False)
def get_team_roster(team_id) -> pd.DataFrame:
    """Roster: name, position, class, height/weight, jersey, hometown."""
    try:
        d = _get(f"{SITE}/teams/{team_id}/roster")
        rows = []
        for grp in d.get("athletes", []):
            unit = grp.get("position", "")
            for a in grp.get("items", []):
                rows.append({
                    "unit": unit,
                    "jersey": a.get("jersey", ""),
                    "name": a.get("displayName"),
                    "pos": (a.get("position") or {}).get("abbreviation", ""),
                    "class": (a.get("experience") or {}).get("abbreviation", ""),
                    "height": a.get("displayHeight", ""),
                    "weight": a.get("displayWeight", ""),
                    "hometown": (a.get("birthPlace") or {}).get("displayText", ""),
                })
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()


# ─────────────────────────────────────────────────────────────────────────────
# Derived: strength of schedule (uses standings so no extra per-opponent calls)
# ─────────────────────────────────────────────────────────────────────────────
def strength_of_schedule(sched: pd.DataFrame, standings: pd.DataFrame) -> dict:
    """Avg opponent win% for games played and for the remaining slate.

    Returns {'played': x, 'remaining': y, 'full': z} on a 0-100 scale, plus the
    toughest upcoming opponents. FCS/unlisted opponents count as a weak 0.25.
    """
    out = {"played": None, "remaining": None, "full": None, "hardest_ahead": []}
    if sched is None or sched.empty:
        return out
    wp = {}
    if standings is not None and not standings.empty:
        for _, r in standings.iterrows():
            try:
                wp[str(r["team_id"])] = float(r["win_pct"]) if r["win_pct"] is not None else None
            except Exception:
                pass

    def opp_wp(oid):
        v = wp.get(str(oid))
        return v if v is not None else 0.25  # non-FBS / unknown / unplayed -> weak

    played = sched[sched["completed"]]
    remaining = sched[~sched["completed"]]
    all_wp = [opp_wp(o) for o in sched["opp_id"] if o is not None]
    pl_wp = [opp_wp(o) for o in played["opp_id"] if o is not None]
    rm = [(opp_wp(o), nm, rk) for o, nm, rk in
          zip(remaining["opp_id"], remaining["opp"], remaining["opp_rank"]) if o is not None]

    if all_wp:
        out["full"] = round(100 * sum(all_wp) / len(all_wp), 1)
    if pl_wp:
        out["played"] = round(100 * sum(pl_wp) / len(pl_wp), 1)
    if rm:
        out["remaining"] = round(100 * sum(x[0] for x in rm) / len(rm), 1)
        out["hardest_ahead"] = [(nm, round(w * 100), rk)
                                for w, nm, rk in sorted(rm, reverse=True)[:5]]
    return out
