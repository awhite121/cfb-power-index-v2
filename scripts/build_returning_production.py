#!/usr/bin/env python3
"""
Build a real per-team returning-production table for 2026 from data we actually have.

CFBD's official returning-production endpoint came back empty in this environment, so we
derive an equivalent signal directly:

  returning production share = (2025 production value of players who are STILL on the team)
                               / (the team's total 2025 production value)

"Players still on the team" = everyone who produced in 2025, MINUS:
  * players in the 2026 transfer portal whose origin is that team (they left), and
  * known NFL/graduation departures (the QB list we already curated).

We compute offense and defense shares separately (they get blended in the model), using
interpretable production weights instead of black-box PPA. Output columns match what
model_v2.build_returning_production_score() reads.
"""
from __future__ import annotations
import os
import unicodedata
import numpy as np
import pandas as pd

RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PROC = os.path.join(os.path.dirname(__file__), "..", "data", "processed")


def norm_name(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode("ascii")
    return " ".join(s.lower().replace(".", "").replace("'", "").replace("-", " ").split())


# QBs confirmed gone to the NFL (already curated for the QB module) — extend as needed.
KNOWN_DEPARTED = {
    "ty simpson", "fernando mendoza", "carson beck", "drew allar",
    "garrett nussmeier", "cade klubnik", "taylen green",
}

# The portal feed tells us who TRANSFERRED out, but not who GRADUATED / exhausted
# eligibility (we have no per-player class data). Pure portal-retention therefore
# overstates returning production, especially for low-portal programs (e.g. academies).
# We apply a modest, uniform graduation allowance so the output sits in a realistic
# band (real CFBD returning production is typically ~40-85%). This shifts the level
# without distorting portal-driven ordering. Tune if you later get class data.
GRAD_ALLOWANCE = 0.15  # ~15% of production assumed lost to graduation on top of portal


def pivot_stats(ps: pd.DataFrame, category: str) -> pd.DataFrame:
    sub = ps[ps["category"].astype(str).str.lower() == category].copy()
    sub["stat"] = pd.to_numeric(sub["stat"], errors="coerce")
    w = sub.pivot_table(index=["player", "team"], columns="statType", values="stat", aggfunc="first").reset_index()
    w.columns.name = None
    return w


def main() -> None:
    ps = pd.read_csv(os.path.join(RAW, "2025_player_stats.csv"))
    portal = pd.read_csv(os.path.join(RAW, "2026_transfer_portal_cfbd.csv"))

    # FBS team universe = teams in the built index (falls back to player-stats teams).
    try:
        idx = pd.read_csv(os.path.join(PROC, "cfb_power_index_v2.csv"))
        teams = sorted(idx["team"].dropna().astype(str).unique())
    except Exception:
        teams = sorted(ps["team"].dropna().astype(str).unique())

    # ---- production value per player (offense and defense separately) ----
    passing = pivot_stats(ps, "passing")
    rushing = pivot_stats(ps, "rushing")
    receiving = pivot_stats(ps, "receiving")
    defense = pivot_stats(ps, "defensive")
    ints = pivot_stats(ps, "interceptions")

    def col(df, c):
        return pd.to_numeric(df.get(c, pd.Series(0, index=df.index)), errors="coerce").fillna(0)

    passing["val"] = col(passing, "YDS") * 0.04 + col(passing, "TD") * 4 - col(passing, "INT") * 1
    rushing["val"] = col(rushing, "YDS") * 0.10 + col(rushing, "TD") * 6
    receiving["val"] = col(receiving, "YDS") * 0.10 + col(receiving, "TD") * 6
    off = pd.concat([passing[["player", "team", "val"]],
                     rushing[["player", "team", "val"]],
                     receiving[["player", "team", "val"]]], ignore_index=True)
    off = off.groupby(["player", "team"], as_index=False)["val"].sum().rename(columns={"val": "off_val"})

    defense["val"] = (col(defense, "TOT") * 1.0 + col(defense, "SACKS") * 3.0
                      + col(defense, "TFL") * 1.5 + col(defense, "PD") * 1.5)
    dv = defense[["player", "team", "val"]].copy()
    if not ints.empty:
        ints["val"] = col(ints, "INT") * 4.0
        dv = pd.concat([dv, ints[["player", "team", "val"]]], ignore_index=True)
    dv = dv.groupby(["player", "team"], as_index=False)["val"].sum().rename(columns={"val": "def_val"})

    prod = off.merge(dv, on=["player", "team"], how="outer").fillna({"off_val": 0, "def_val": 0})
    prod["key"] = prod["player"].map(norm_name)

    # ---- who left each team (portal-out + known NFL/grad) ----
    portal = portal.copy()
    portal["full"] = (portal["firstName"].astype(str) + " " + portal["lastName"].astype(str)).map(norm_name)
    left_by_team: dict[str, set] = {}
    for _, r in portal.iterrows():
        origin = str(r.get("origin", "")).strip()
        if origin:
            left_by_team.setdefault(origin, set()).add(r["full"])

    rows = []
    for team in teams:
        tp = prod[prod["team"] == team]
        off_total = tp["off_val"].clip(lower=0).sum()
        def_total = tp["def_val"].clip(lower=0).sum()
        gone = left_by_team.get(team, set()) | KNOWN_DEPARTED
        ret = tp[~tp["key"].isin(gone)]
        off_ret = ret["off_val"].clip(lower=0).sum()
        def_ret = ret["def_val"].clip(lower=0).sum()
        g = (1.0 - GRAD_ALLOWANCE)
        off_share = (off_ret / off_total * 100 * g) if off_total > 0 else np.nan
        def_share = (def_ret / def_total * 100 * g) if def_total > 0 else np.nan
        total_share = np.nanmean([off_share, def_share])
        rows.append({
            "team": team,
            "returning_production_total": round(total_share, 1) if pd.notna(total_share) else np.nan,
            "offense_returning_production": round(off_share, 1) if pd.notna(off_share) else np.nan,
            "defense_returning_production": round(def_share, 1) if pd.notna(def_share) else np.nan,
            "players_left": len(gone & set(tp["key"])),
        })

    out = pd.DataFrame(rows)
    dest = os.path.join(RAW, "2026_returning_production.csv")
    out.to_csv(dest, index=False)
    n_real = out["returning_production_total"].notna().sum()
    print(f"Wrote {dest}: {len(out)} teams, {n_real} with computed returning production.")
    print(out.sort_values("returning_production_total", ascending=False).head(10).to_string(index=False))
    print("...")
    print("Texas:", out[out["team"] == "Texas"].to_string(index=False))


if __name__ == "__main__":
    main()
