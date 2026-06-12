"""Resolve each FBS team's projected 2026 starting QB using REAL data:
  1. 2025 primary passer (most attempts) as the baseline.
  2. 2026 transfer portal: if that passer is leaving (origin==team), promote the
     highest-rated incoming QB transfer; a transfer's 2025 stats follow them.
  3. A small, editable KNOWN_DEPARTED list for NFL/graduation cases the portal
     can't see (seeded with the only early-declare QB: Ty Simpson).
Outputs data/raw/2026_qb_starters.csv — fully editable to override any team.
"""
from pathlib import Path
import pandas as pd, numpy as np

RAW = Path("data/raw")
idx = pd.read_csv("data/processed/cfb_power_index_v2.csv")
stats = pd.read_csv(RAW / "2025_player_stats.csv")
portal = pd.read_csv(RAW / "2026_transfer_portal_cfbd.csv")
portal["player"] = (portal["firstName"].fillna("").astype(str) + " " +
                    portal["lastName"].fillna("").astype(str)).str.strip()
portal["rating"] = pd.to_numeric(portal["rating"], errors="coerce")

# 2025 passing wide table (player-level, keeps their old team)
pa = stats[stats["category"].astype(str).str.lower() == "passing"].copy()
pa["stat"] = pd.to_numeric(pa["stat"], errors="coerce")
pw = pa.pivot_table(index=["player", "team"], columns="statType", values="stat", aggfunc="first").reset_index()
pw.columns.name = None
for c in ["ATT", "YDS", "TD", "INT", "PCT", "YPA"]:
    if c not in pw.columns:
        pw[c] = np.nan

# 2025 starters who left for the NFL (drafted in the 2026 draft) and so are NOT
# in the transfer portal. Web-confirmed from 2026 NFL Draft coverage. Editable.
# (Confirmed RETURNING to college, do NOT add: John Mateer, Dante Moore,
#  LaNorris Sellers, Arch Manning, Dylan Raiola[transferred].)
KNOWN_DEPARTED = {
    "Ty Simpson",          # Alabama -> NFL (1st rd)
    "Fernando Mendoza",    # Indiana -> NFL (No. 1 overall)
    "Carson Beck",         # Miami -> NFL (3rd rd)
    "Drew Allar",          # Penn State -> NFL
    "Garrett Nussmeier",   # LSU -> NFL
    "Cade Klubnik",        # Clemson -> NFL
    "Taylen Green",        # Arkansas -> NFL
}

qbs_portal = portal[portal["position"].astype(str).str.upper().eq("QB")].copy()
out_by_team = qbs_portal.dropna(subset=["origin"]).groupby("origin")["player"].apply(set).to_dict()
inc = qbs_portal.dropna(subset=["destination"]).copy()

def best_2025_line(name, team=None):
    cand = pw[pw["player"] == name]
    if team is not None and (cand["team"] == team).any():
        cand = cand[cand["team"] == team]
    return cand.sort_values("ATT", ascending=False).head(1)

teams = sorted(idx["team"].unique())
rows = []
for t in teams:
    # returning 2025 passers for this team, most attempts first
    team_passers = pw[pw["team"] == t].sort_values("ATT", ascending=False)
    departed = out_by_team.get(t, set()) | KNOWN_DEPARTED
    returning = team_passers[~team_passers["player"].isin(departed)]
    incoming = inc[inc["destination"] == t].sort_values("rating", ascending=False)

    qb = status = prev = source = note = None
    # Keep a meaningful returning starter (>=100 att) if available
    starter_2025 = team_passers.head(1)["player"].iloc[0] if not team_passers.empty else None
    ret_top = returning.head(1)
    if not ret_top.empty and ret_top["ATT"].iloc[0] >= 100:
        qb = ret_top["player"].iloc[0]; prev = t
        status = "Returning starter" if qb == starter_2025 else "Returning (stepped up)"
        source = "2025 stats"
        if not incoming.empty and incoming["rating"].iloc[0] >= 0.90:
            note = f"competition from transfer {incoming['player'].iloc[0]}"
    elif not incoming.empty:
        r = incoming.iloc[0]
        qb = r["player"]; prev = r["origin"]; status = "Transfer (incoming)"
        source = f"portal: {r['origin']} -> {t}"
    elif not returning.empty:
        qb = returning.head(1)["player"].iloc[0]; prev = t
        status = "Returning (limited 2025)"; source = "2025 stats"
    else:
        qb = ""; status = "Open / unknown"; source = "no data"

    # Score the chosen QB off their 2025 line (follows transfers)
    line = best_2025_line(qb, prev) if qb else pd.DataFrame()
    yds = td = inte = pct = ypa = att = np.nan
    if not line.empty:
        yds, td, inte, pct, ypa, att = (line[["YDS","TD","INT","PCT","YPA","ATT"]].iloc[0])
    rows.append({"team": t, "qb": qb, "status": status, "prev_team_2025": prev,
                 "att_2025": att, "yds_2025": yds, "td_2025": td, "int_2025": inte,
                 "pct_2025": pct, "ypa_2025": ypa, "source": source, "note": note})

out = pd.DataFrame(rows)
out.to_csv(RAW / "2026_qb_starters.csv", index=False)
print("Wrote", RAW / "2026_qb_starters.csv", "rows:", len(out))
print("\nStatus breakdown:")
print(out["status"].value_counts().to_string())
print("\nSpot checks:")
for t in ["Texas","Oregon","Nebraska","Alabama","Ohio State","LSU","Notre Dame","Miami","Penn State","Cincinnati"]:
    r = out[out["team"]==t]
    if not r.empty:
        x=r.iloc[0]; print(f"  {t:14s} -> {str(x['qb']):20s} | {x['status']:24s} | {x['source']}")
