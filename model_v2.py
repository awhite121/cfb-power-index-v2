"""CFB Power Index V2 scoring model.

This file is intentionally built to run even when some raw/manual CSVs are still
missing. Missing inputs default to neutral 50/100 component scores so the app can
launch immediately, then scores improve as you fill/pull more data.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

# Weights are tuned for a FORWARD-LOOKING "2026 season outlook" rather than a
# backward-looking recap of 2025. Last year's team quality is now a program-baseline
# input (still the second-largest piece) instead of the dominant factor, and the
# roster-construction signals that actually drive a new season — who's coming back,
# the QB, the transfer haul, and recruiting talent — carry the most weight together.
POWER_WEIGHTS = {
    "prior_year_team_quality_score": 0.22,
    "returning_production_score": 0.26,
    "qb_score": 0.14,
    "transfer_impact_score": 0.14,
    "recruiting_talent_score": 0.12,
    "coaching_continuity_score": 0.05,
    "schedule_strength_score": 0.04,
    "context_score": 0.03,
}

# Pure team strength = how good the roster is, independent of who they play.
# Schedule strength is path difficulty, NOT team quality, so it is excluded here
# and the remaining weights are renormalized. The game predictor uses THIS, so a
# hard schedule never makes a team better at beating an opponent.
_STRENGTH_RAW = {k: v for k, v in POWER_WEIGHTS.items() if k != "schedule_strength_score"}
_STRENGTH_TOTAL = sum(_STRENGTH_RAW.values())
TEAM_STRENGTH_WEIGHTS = {k: v / _STRENGTH_TOTAL for k, v in _STRENGTH_RAW.items()}

POSITION_TRANSFER_MULTIPLIER = {
    "QB": 1.40,
    "OT": 1.20,
    "T": 1.20,
    "EDGE": 1.20,
    "CB": 1.20,
    "WR": 1.10,
    "DL": 1.10,
    "DT": 1.10,
    "DE": 1.10,
    "LB": 1.10,
    "TE": 1.00,
    "S": 1.00,
    "SAF": 1.00,
    "RB": 0.90,
}

QB_STATUS_BASE = {
    "returning_elite_starter": 95,
    "returning_solid_starter": 84,
    "returning_starter": 78,
    "returning_poor_starter": 66,
    "returning_backup": 58,
    "experienced_transfer": 70,
    "p4_transfer": 68,
    "g5_transfer": 58,
    "freshman_5_star": 66,
    "freshman": 45,
    "unknown": 50,
}


def read_csv_if_exists(path: Path) -> pd.DataFrame:
    # Some CFBD endpoints return an empty body (e.g. 0 rows) which lands on disk as a
    # 1-byte file with no header. size>0 isn't enough — guard the parse itself.
    if path.exists() and path.stat().st_size > 0:
        try:
            return pd.read_csv(path)
        except (pd.errors.EmptyDataError, pd.errors.ParserError):
            return pd.DataFrame()
    return pd.DataFrame()


def first_existing_col(df: pd.DataFrame, candidates: Iterable[str]) -> str | None:
    lower_map = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in lower_map:
            return lower_map[c.lower()]
    return None


def team_col(df: pd.DataFrame) -> str | None:
    return first_existing_col(df, ["team", "school", "Team", "School"])


def to_num(value, default: float | None = np.nan) -> pd.Series:
    if isinstance(value, pd.Series):
        return pd.to_numeric(value, errors="coerce")
    return pd.Series(default)


def percent_series(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    if not s.dropna().empty and s.dropna().max() <= 1:
        s = s * 100
    return s


def normalize_series(s: pd.Series, higher_is_better: bool = True, default: float = 50.0) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    out = pd.Series(default, index=s.index, dtype=float)
    valid = s.dropna()
    if valid.empty or valid.max() == valid.min():
        return out
    out = 100 * (s - valid.min()) / (valid.max() - valid.min())
    if not higher_is_better:
        out = 100 - out
    return out.fillna(default).clip(0, 100)


def weighted_average(parts: list[tuple[pd.Series, float]], default: float = 50.0) -> pd.Series:
    if not parts:
        return pd.Series(dtype=float)
    idx = parts[0][0].index
    numerator = pd.Series(0.0, index=idx)
    denominator = pd.Series(0.0, index=idx)
    for series, weight in parts:
        s = pd.to_numeric(series, errors="coerce")
        present = s.notna()
        numerator[present] += s[present] * weight
        denominator[present] += weight
    return (numerator / denominator.replace(0, np.nan)).fillna(default).clip(0, 100)


def build_prior_year_team_quality() -> pd.DataFrame:
    """Build prior-year score from existing Excel and/or CFBD advanced stats."""
    advanced = read_csv_if_exists(RAW_DIR / "2025_team_advanced_season_stats.csv")
    if not advanced.empty:
        tcol = team_col(advanced)
        if tcol:
            df = advanced.copy()
            # Direction-aware composite of the headline efficiency metrics. Averaging
            # every column blindly is wrong: defensive PPA/success/explosiveness are
            # "lower is better", and volume columns (plays, drives) aren't quality at
            # all. Offense higher = better; defense lower = better.
            quality_cols = {
                "offense.ppa": True,
                "offense.successRate": True,
                "offense.explosiveness": True,
                "defense.ppa": False,
                "defense.successRate": False,
                "defense.explosiveness": False,
            }
            parts = [
                (normalize_series(df[col], higher_is_better=hib), 1.0)
                for col, hib in quality_cols.items()
                if col in df.columns
            ]
            if parts:
                score = weighted_average(parts, default=50)
                return pd.DataFrame({"team": df[tcol].astype(str), "prior_year_team_quality_score": score}).groupby("team", as_index=False).mean(numeric_only=True)

    xlsx = ROOT / "cfb_combined_data.xlsx"
    if not xlsx.exists():
        return pd.DataFrame(columns=["team", "prior_year_team_quality_score"])

    df = pd.read_excel(xlsx)
    tcol = team_col(df) or df.columns[0]
    # Direction-aware V1 features. Lower rank/allowed/turnovers/penalties are better.
    candidates = {
        "Off_Rank": False,
        "Off_PPG": True,
        "Off_Total_Yds": True,
        "Off_Yds_Per_Play": True,
        "Off_Turnovers": False,
        "Def_Rank": False,
        "Def_PPG_Allowed": False,
        "Def_TotalYds_Allowed": False,
        "Def_YdsPerPlay_Allowed": False,
        "Def_Takeaways": True,
        "Off_3rdDown_Pct": True,
        "Def_3rdDown_Pct": False,
        "Off_redzone_score_pct": True,
        "Off_redzone_TD_pct": True,
        "Def_RZ_Score_%": False,
        "Deff_RZ_TD_%": False,
    }
    parts = []
    for col, high_good in candidates.items():
        if col in df.columns:
            parts.append((normalize_series(df[col], higher_is_better=high_good), 1.0))
    score = weighted_average(parts, default=50) if parts else df.select_dtypes(include=[np.number]).apply(normalize_series).mean(axis=1)
    out = pd.DataFrame({"team": df[tcol].astype(str), "prior_year_team_quality_score": score})
    return out.groupby("team", as_index=False).mean(numeric_only=True)


def build_returning_production_score() -> pd.DataFrame:
    df = read_csv_if_exists(RAW_DIR / "2026_returning_production.csv")
    if df.empty:
        cfbd = read_csv_if_exists(RAW_DIR / "2026_returning_production_cfbd.csv")
        df = cfbd
    if df.empty or "team" not in df.columns:
        return pd.DataFrame(columns=["team", "returning_production_score"])

    total_col = first_existing_col(df, ["returning_production_total", "total", "overall", "percentPPA"])
    off_col = first_existing_col(df, ["offense_returning_production", "offense", "offense_returning", "offensePPA"])
    def_col = first_existing_col(df, ["defense_returning_production", "defense", "defense_returning", "defensePPA"])

    total = percent_series(df[total_col]) if total_col else pd.Series(np.nan, index=df.index)
    off = percent_series(df[off_col]) if off_col else pd.Series(np.nan, index=df.index)
    defense = percent_series(df[def_col]) if def_col else pd.Series(np.nan, index=df.index)

    score = weighted_average([(total, 0.50), (off, 0.28), (defense, 0.22)], default=50)
    out = pd.DataFrame({
        "team": df["team"].astype(str),
        "returning_production_score": score,
        "offense_returning_production": off,
        "defense_returning_production": defense,
    })
    return out.groupby("team", as_index=False).mean(numeric_only=True)


def build_position_returning_scores() -> pd.DataFrame:
    """Optional position-level returning score from 2025 player stats + 2026 roster."""
    stats = read_csv_if_exists(RAW_DIR / "2025_player_stats.csv")
    roster = read_csv_if_exists(RAW_DIR / "2026_rosters.csv")
    if stats.empty or roster.empty:
        return pd.DataFrame(columns=["team", "position_returning_score"])
    if "team" not in stats.columns or "team" not in roster.columns or "player" not in stats.columns or "player" not in roster.columns:
        return pd.DataFrame(columns=["team", "position_returning_score"])

    stats = stats.copy()
    roster = roster.copy()
    stats["player_key"] = stats["player"].astype(str).str.lower().str.replace(r"\s+", " ", regex=True).str.strip()
    roster["player_key"] = roster["player"].astype(str).str.lower().str.replace(r"\s+", " ", regex=True).str.strip()
    keep = stats.merge(roster[["team", "player_key"]].drop_duplicates(), on=["team", "player_key"], how="inner")
    if keep.empty:
        return pd.DataFrame(columns=["team", "position_returning_score"])

    pos = keep.get("position", pd.Series("", index=keep.index)).astype(str).str.upper()
    keep["position_group"] = np.select(
        [pos.eq("QB"), pos.isin(["G", "OG", "C", "OT", "OL", "T"]), pos.isin(["WR", "TE"]), pos.eq("RB"), pos.isin(["DL", "DE", "DT", "EDGE"]), pos.isin(["LB", "CB", "S", "SAF", "DB"])],
        ["QB", "OL", "WR_TE", "RB", "DEF_FRONT", "DEF_BACK"],
        default="OTHER",
    )
    production_cols = [
        "passing_yards", "passing_tds", "rushing_yards", "rushing_tds", "receiving_yards", "receiving_tds",
        "tackles", "tfl", "sacks", "passes_defended", "interceptions_def", "forced_fumbles", "snaps", "games_started",
    ]
    available = [c for c in production_cols if c in keep.columns]
    if not available:
        return pd.DataFrame(columns=["team", "position_returning_score"])
    keep["production"] = keep[available].apply(pd.to_numeric, errors="coerce").fillna(0).sum(axis=1)
    group_scores = keep.groupby(["team", "position_group"], as_index=False).agg(returning_prod=("production", "sum"))
    group_scores["group_score"] = group_scores.groupby("position_group")["returning_prod"].transform(normalize_series)
    weights = {"QB": 0.25, "OL": 0.20, "WR_TE": 0.15, "RB": 0.07, "DEF_FRONT": 0.18, "DEF_BACK": 0.15, "OTHER": 0.03}
    group_scores["weight"] = group_scores["position_group"].map(weights).fillna(0.03)
    out = group_scores.assign(weighted=lambda x: x["group_score"] * x["weight"]).groupby("team", as_index=False).agg(
        weighted_score=("weighted", "sum"),
        weight_sum=("weight", "sum"),
    )
    out["position_returning_score"] = (out["weighted_score"] / out["weight_sum"].replace(0, np.nan)).fillna(50).clip(0, 100)
    return out[["team", "position_returning_score"]]


def build_qb_from_2025_stats() -> pd.DataFrame:
    """Derive a QB-room quality prior from real 2025 passing stats.

    Used when neither the manual 2026_qb_rooms.csv nor CFBD returning-production is
    available (e.g. preseason, before 2026 rosters/returning-production publish). We
    take each team's primary 2025 passer (most attempts) and score passing quality.
    This is a PRIOR on the QB room, not a guarantee the same QB returns — incoming
    QBs are separately credited by the transfer component. Labeled accordingly.
    """
    stats = read_csv_if_exists(RAW_DIR / "2025_player_stats.csv")
    if stats.empty or not {"category", "statType", "stat", "team", "player"}.issubset(stats.columns):
        return pd.DataFrame(columns=["team", "qb_score", "qb_status", "projected_qb"])
    passing = stats[stats["category"].astype(str).str.lower() == "passing"].copy()
    if passing.empty:
        return pd.DataFrame(columns=["team", "qb_score", "qb_status", "projected_qb"])
    passing["stat"] = pd.to_numeric(passing["stat"], errors="coerce")
    wide = passing.pivot_table(
        index=["playerId", "player", "team"], columns="statType", values="stat", aggfunc="first"
    ).reset_index()
    for c in ["ATT", "YDS", "TD", "INT", "PCT", "YPA"]:
        if c not in wide.columns:
            wide[c] = np.nan
    # Require a real workload so we don't crown a backup who threw a few passes.
    wide = wide[pd.to_numeric(wide["ATT"], errors="coerce").fillna(0) >= 50]
    if wide.empty:
        return pd.DataFrame(columns=["team", "qb_score", "qb_status", "projected_qb"])
    primary = wide.sort_values("ATT", ascending=False).groupby("team", as_index=False).first()
    score = (
        0.30 * normalize_series(primary["YPA"])
        + 0.25 * normalize_series(primary["TD"])
        + 0.20 * normalize_series(primary["PCT"])
        + 0.15 * normalize_series(primary["INT"], higher_is_better=False)
        + 0.10 * normalize_series(primary["ATT"])
    ).clip(0, 100)
    out = pd.DataFrame({
        "team": primary["team"].astype(str),
        "qb_score": score,
        "qb_status": "2025 starter (returning TBD)",
        "projected_qb": primary["player"].astype(str),
    })
    return out.groupby("team", as_index=False).agg(
        qb_score=("qb_score", "max"),
        qb_status=("qb_status", "first"),
        projected_qb=("projected_qb", "first"),
    )


def build_qb_from_starters_file() -> pd.DataFrame:
    """Authoritative 2026 QB signal from the curated, portal- and draft-aware
    2026_qb_starters.csv (built by scripts/build_2026_qbs.py). Each projected
    starter is scored off their 2025 passing line, which follows transfers to
    their new school. QBs with no 2025 college passing line (true freshmen /
    FCS / JUCO) get a modest unproven prior. Fully editable by hand."""
    qb = read_csv_if_exists(RAW_DIR / "2026_qb_starters.csv")
    if qb.empty or not {"team", "qb"}.issubset(qb.columns):
        return pd.DataFrame(columns=["team", "qb_score", "qb_status", "projected_qb"])
    for c in ["att_2025", "yds_2025", "td_2025", "int_2025", "pct_2025", "ypa_2025"]:
        if c not in qb.columns:
            qb[c] = np.nan
        qb[c] = pd.to_numeric(qb[c], errors="coerce")
    score = pd.Series(np.nan, index=qb.index)
    has = qb["att_2025"].fillna(0) >= 50
    if has.any():
        sub = qb[has]
        s = (
            0.30 * normalize_series(sub["ypa_2025"])
            + 0.25 * normalize_series(sub["td_2025"])
            + 0.20 * normalize_series(sub["pct_2025"])
            + 0.15 * normalize_series(sub["int_2025"], higher_is_better=False)
            + 0.10 * normalize_series(sub["att_2025"])
        ).clip(0, 100)
        score.loc[sub.index] = s
    # Unproven QBs (no qualifying 2025 line) get a slightly-below-neutral prior.
    score = score.fillna(45.0).clip(0, 100)
    out = pd.DataFrame({
        "team": qb["team"].astype(str),
        "qb_score": score,
        "qb_status": qb.get("status", pd.Series("", index=qb.index)).astype(str),
        "projected_qb": qb["qb"].astype(str),
    })
    out = out[out["projected_qb"].astype(str).str.strip().ne("")]
    return out.groupby("team", as_index=False).agg(
        qb_score=("qb_score", "max"),
        qb_status=("qb_status", "first"),
        projected_qb=("projected_qb", "first"),
    )


def build_qb_score() -> pd.DataFrame:
    # Highest priority: the curated, portal/draft-aware 2026 starter list.
    from_starters = build_qb_from_starters_file()
    if not from_starters.empty:
        return from_starters

    qb = read_csv_if_exists(RAW_DIR / "2026_qb_rooms.csv")
    if not qb.empty and "team" in qb.columns:
        out = qb[["team"]].copy()
        status = qb.get("qb_status", pd.Series("unknown", index=qb.index)).astype(str).str.lower().str.strip()
        status_base = status.map(QB_STATUS_BASE).fillna(50)
        parts = [
            (status_base, 0.35),
            (normalize_series(qb.get("prior_passing_efficiency", pd.Series(index=qb.index))), 0.25),
            (normalize_series(qb.get("prior_attempts", pd.Series(index=qb.index))), 0.15),
            (normalize_series(qb.get("prior_rushing_yards", pd.Series(index=qb.index))), 0.10),
            (normalize_series(qb.get("turnover_avoidance", pd.Series(index=qb.index))), 0.10),
            (normalize_series(qb.get("recruiting_transfer_grade", pd.Series(index=qb.index))), 0.05),
        ]
        out["qb_score"] = weighted_average(parts, default=50)
        out["qb_status"] = qb.get("qb_status", "unknown")
        out["projected_qb"] = qb.get("projected_qb", "")
        return out

    # No manual QB rooms file: prefer a real signal derived from 2025 passing stats.
    from_stats = build_qb_from_2025_stats()
    if not from_stats.empty:
        return from_stats

    rp = build_returning_production_score()
    if rp.empty:
        return pd.DataFrame(columns=["team", "qb_score", "qb_status"])
    out = rp[["team"]].copy()
    off = rp.get("offense_returning_production", rp["returning_production_score"])
    out["qb_score"] = (pd.to_numeric(off, errors="coerce").fillna(50) * 0.60 + 20).clip(25, 90)
    out["qb_status"] = "needs 2026_qb_rooms.csv"
    return out


def build_transfer_score() -> pd.DataFrame:
    df = read_csv_if_exists(RAW_DIR / "2026_transfers.csv")
    if df.empty:
        df = read_csv_if_exists(RAW_DIR / "2026_transfer_portal_cfbd.csv")
    if df.empty:
        return pd.DataFrame(columns=["team", "transfer_impact_score"])
    df = df.copy()
    # Transfer IMPACT credits the team gaining the player. CFBD's portal feed has
    # no "team" column — the receiving school is "destination" (origin = where they
    # left). Manual templates may already supply "team". Drop rows with no landing
    # spot (still in the portal / withdrawn) so they don't pollute team scores.
    if "team" not in df.columns:
        dest_col = first_existing_col(df, ["destination", "team", "new_team"])
        if not dest_col:
            return pd.DataFrame(columns=["team", "transfer_impact_score"])
        df["team"] = df[dest_col]
    df = df[df["team"].notna() & (df["team"].astype(str).str.strip().str.lower() != "none")]
    if df.empty:
        return pd.DataFrame(columns=["team", "transfer_impact_score"])
    rating = normalize_series(df.get("rating", df.get("transfer_rating", pd.Series(index=df.index))))
    stars = normalize_series(df.get("stars", pd.Series(index=df.index)))
    projected = pd.to_numeric(df.get("projected_starter", pd.Series(0, index=df.index)), errors="coerce").fillna(0).clip(0, 1) * 100
    rank_score = normalize_series(df.get("national_rank", pd.Series(index=df.index)), higher_is_better=False)
    prior_prod_cols = [c for c in ["prior_passing_yards", "prior_rushing_yards", "prior_receiving_yards", "prior_tackles", "prior_tfl", "prior_sacks", "prior_int", "prior_starts", "prior_snaps"] if c in df.columns]
    prior_prod = normalize_series(df[prior_prod_cols].apply(pd.to_numeric, errors="coerce").fillna(0).sum(axis=1)) if prior_prod_cols else pd.Series(50, index=df.index)
    base = 0.35 * rating + 0.15 * stars + 0.20 * projected + 0.15 * rank_score + 0.15 * prior_prod
    pos = df.get("position", pd.Series("", index=df.index)).astype(str).str.upper()
    mult = pos.map(POSITION_TRANSFER_MULTIPLIER).fillna(1.0)
    df["projected_starter"] = projected / 100
    df["player_transfer_score"] = (base * mult).clip(0, 100)
    out = df.groupby("team", as_index=False).agg(
        transfer_impact_score=("player_transfer_score", "mean"),
        transfer_count=("player_transfer_score", "size"),
        projected_transfer_starters=("projected_starter", "sum"),
    )
    out["transfer_impact_score"] = (out["transfer_impact_score"].fillna(50) + np.log1p(out["transfer_count"]) * 3).clip(0, 100)
    return out


def build_recruiting_score() -> pd.DataFrame:
    frames = []
    consolidated = read_csv_if_exists(RAW_DIR / "2022_2026_recruiting.csv")
    if not consolidated.empty:
        frames.append(consolidated)
    for y in [2022, 2023, 2024, 2025, 2026]:
        temp = read_csv_if_exists(RAW_DIR / f"{y}_recruiting_teams.csv")
        if not temp.empty:
            temp["year"] = y
            frames.append(temp)
    if not frames:
        return pd.DataFrame(columns=["team", "recruiting_talent_score"])
    df = pd.concat(frames, ignore_index=True)
    tcol = team_col(df)
    if not tcol:
        return pd.DataFrame(columns=["team", "recruiting_talent_score"])
    rank_col = first_existing_col(df, ["rank", "ranking", "team_rank"])
    points_col = first_existing_col(df, ["points", "rating", "avg_rating", "score"])
    out = pd.DataFrame({"team": df[tcol].astype(str)})
    out["rank_score"] = normalize_series(df[rank_col], higher_is_better=False) if rank_col else 50
    out["points_score"] = normalize_series(df[points_col]) if points_col else out["rank_score"]
    out["class_score"] = 0.55 * out["rank_score"] + 0.45 * out["points_score"]
    return out.groupby("team", as_index=False).agg(recruiting_talent_score=("class_score", "mean"))


def build_coaching_score() -> pd.DataFrame:
    df = read_csv_if_exists(RAW_DIR / "2026_coaches.csv")
    if df.empty or "team" not in df.columns:
        return pd.DataFrame(columns=["team", "coaching_continuity_score"])
    flags = {
        "head_coach_retained": 40,
        "oc_retained": 20,
        "dc_retained": 20,
        "qb_coach_retained": 5,
        "ol_coach_retained": 5,
        "dl_coach_retained": 5,
    }
    out = df[["team"]].copy()
    zero = pd.Series(0, index=df.index)
    score = pd.Series(5.0, index=df.index)
    for col, weight in flags.items():
        score += pd.to_numeric(df.get(col, zero), errors="coerce").fillna(0).clip(0, 1) * weight
    scheme_penalty = (
        pd.to_numeric(df.get("offensive_scheme_change", zero), errors="coerce").fillna(0).clip(0, 1)
        + pd.to_numeric(df.get("defensive_scheme_change", zero), errors="coerce").fillna(0).clip(0, 1)
    ) * 5
    new_qb_new_oc_penalty = (
        pd.to_numeric(df.get("new_oc", zero), errors="coerce").fillna(0).clip(0, 1)
        * pd.to_numeric(df.get("new_projected_qb", zero), errors="coerce").fillna(0).clip(0, 1)
    ) * 8
    out["coaching_continuity_score"] = (score - scheme_penalty - new_qb_new_oc_penalty).clip(0, 100)
    return out


def build_schedule_score(prior_scores: pd.DataFrame) -> pd.DataFrame:
    sched = read_csv_if_exists(RAW_DIR / "2026_schedule.csv")
    if sched.empty or prior_scores.empty:
        if not prior_scores.empty:
            out = prior_scores[["team"]].copy()
            out["schedule_strength_score"] = 50
            return out
        return pd.DataFrame(columns=["team", "schedule_strength_score"])
    ratings = prior_scores.rename(columns={"prior_year_team_quality_score": "opponent_rating"})
    # CFBD /games returns camelCase homeTeam/awayTeam; manual templates may use
    # snake_case home_team/away_team. Support both.
    home_col = first_existing_col(sched, ["home_team", "homeTeam", "home"])
    away_col = first_existing_col(sched, ["away_team", "awayTeam", "away"])
    games = []
    if home_col and away_col:
        home = sched[[home_col, away_col]].rename(columns={home_col: "team", away_col: "opponent"})
        home["road_game"] = 0
        away = sched[[away_col, home_col]].rename(columns={away_col: "team", home_col: "opponent"})
        away["road_game"] = 1
        games = [home, away]
    if not games:
        return pd.DataFrame(columns=["team", "schedule_strength_score"])
    games = pd.concat(games, ignore_index=True)
    games = games.merge(ratings[["team", "opponent_rating"]].rename(columns={"team": "opponent"}), on="opponent", how="left")
    out = games.groupby("team", as_index=False).agg(
        avg_opponent_rating=("opponent_rating", "mean"),
        road_games=("road_game", "sum"),
        total_games=("road_game", "size"),
    )
    out["road_game_rate"] = out["road_games"] / out["total_games"].replace(0, np.nan)
    out["schedule_strength_score"] = (0.80 * normalize_series(out["avg_opponent_rating"]) + 0.20 * normalize_series(out["road_game_rate"])).fillna(50).clip(0, 100)
    return out[["team", "schedule_strength_score", "avg_opponent_rating", "road_games"]]


def build_context_score(prior_scores: pd.DataFrame) -> pd.DataFrame:
    # Weather is game-level; preseason team context stays neutral until game predictor is added.
    if prior_scores.empty:
        return pd.DataFrame(columns=["team", "context_score"])
    out = prior_scores[["team"]].copy()
    out["context_score"] = 50
    return out


def build_all_feature_scores() -> pd.DataFrame:
    prior = build_prior_year_team_quality()
    rp = build_returning_production_score()
    pos_rp = build_position_returning_scores()
    if not rp.empty and not pos_rp.empty:
        rp = rp.merge(pos_rp, on="team", how="outer")
        rp["returning_production_score"] = weighted_average([
            (rp.get("returning_production_score", pd.Series(index=rp.index)), 0.70),
            (rp.get("position_returning_score", pd.Series(index=rp.index)), 0.30),
        ], default=50)
    elif rp.empty and not pos_rp.empty:
        rp = pos_rp.rename(columns={"position_returning_score": "returning_production_score"})

    features = [
        prior,
        rp,
        build_qb_score(),
        build_transfer_score(),
        build_recruiting_score(),
        build_coaching_score(),
        build_schedule_score(prior),
        build_context_score(prior),
    ]
    # Anchor the team universe to the FBS set (teams that have prior-year quality:
    # the curated Excel or CFBD advanced stats). Otherwise transfer destinations and
    # schedule opponents drag in FCS/non-FBS schools that have no prior-year quality,
    # inflating their ranking off transfer/recruiting signal alone.
    if not prior.empty and "team" in prior.columns:
        teams = sorted(set(prior["team"].astype(str)))
    else:
        teams = sorted(set().union(*[set(f["team"].astype(str)) for f in features if "team" in f.columns and not f.empty]))
    out = pd.DataFrame({"team": teams})
    for f in features:
        if not f.empty and "team" in f.columns:
            out = out.merge(f, on="team", how="left")

    for col in POWER_WEIGHTS:
        if col not in out.columns:
            out[col] = 50
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(50).clip(0, 100)
    return out


def build_power_index_v2() -> pd.DataFrame:
    df = build_all_feature_scores()
    if df.empty:
        return df
    df["power_index_v2"] = sum(df[col] * weight for col, weight in POWER_WEIGHTS.items())
    # Schedule-independent roster strength (drives the game predictor).
    df["team_strength_rating"] = sum(df[col] * weight for col, weight in TEAM_STRENGTH_WEIGHTS.items())
    df["rank_v2"] = df["power_index_v2"].rank(ascending=False, method="dense").astype(int)
    df["strength_rank"] = df["team_strength_rating"].rank(ascending=False, method="dense").astype(int)
    df = df.sort_values(["rank_v2", "team"]).reset_index(drop=True)
    lead = ["rank_v2", "team", "power_index_v2", "team_strength_rating", "strength_rank"]
    ordered = lead + [c for c in df.columns if c not in lead]
    return df[ordered]


def build_coverage_report() -> pd.DataFrame:
    """Report which components are backed by REAL data vs the neutral-50 default.

    A component is 'real' for a team when its raw value differs from exactly 50.0
    (the default). This keeps the model honest: the app can flag exactly how much
    of each ranking is data-driven instead of filler.
    """
    df = build_all_feature_scores()
    rows = []
    n_teams = len(df)
    for col in POWER_WEIGHTS:
        if col in df.columns and n_teams:
            vals = pd.to_numeric(df[col], errors="coerce")
            real = int((vals.round(6) != 50.0).sum())
        else:
            real = 0
        rows.append({
            "component": col,
            "weight": POWER_WEIGHTS[col],
            "teams_with_real_data": real,
            "teams_total": n_teams,
            "coverage_pct": round(100 * real / n_teams, 1) if n_teams else 0.0,
        })
    return pd.DataFrame(rows)


def save_outputs() -> pd.DataFrame:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df = build_power_index_v2()
    df.to_csv(PROCESSED_DIR / "cfb_power_index_v2.csv", index=False)
    df.to_csv(PROCESSED_DIR / "team_features_v2.csv", index=False)
    coverage = build_coverage_report()
    coverage.to_csv(PROCESSED_DIR / "coverage_report.csv", index=False)
    return df


if __name__ == "__main__":
    final = save_outputs()
    if final.empty:
        print("No teams found. Add cfb_combined_data.xlsx or raw CSV files.")
    else:
        print(final[["rank_v2", "team", "power_index_v2"]].head(25).to_string(index=False))
        print(f"\nSaved outputs to {PROCESSED_DIR}")
