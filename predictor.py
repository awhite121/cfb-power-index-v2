"""CFB Power Index V2 — explainable game prediction engine.

Turns two teams' component scores into a win probability, projected margin,
projected score, and a per-factor edge breakdown with a plain-English rationale.

Design choices (kept transparent so the app's Methodology page can cite them):

- Team strength is expressed on a POINTS scale. The 0-100 `power_index_v2` is
  standardized to points using an empirically reasonable spread for FBS
  (std ~= 11 points), so a rating gap reads like a neutral-field point spread.
- Win probability uses the standard normal model on the projected margin with a
  game-outcome standard deviation of ~16 points (typical for a single CFB game).
- Home-field advantage defaults to 2.4 points (0 at a neutral site).
- Weather only dampens the total and slightly compresses the favorite's edge;
  it never invents an advantage.

Nothing here fabricates data: every number traces back to component scores that
came from real inputs (or the neutral 50 default when an input is missing).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
PROCESSED = ROOT / "data" / "processed" / "cfb_power_index_v2.csv"

# Points-scale calibration.
RATING_POINTS_STD = 11.0          # how many points one std of power index is worth
GAME_OUTCOME_STD = 16.0           # std of (actual margin - projected margin) for one game
DEFAULT_HFA = 2.4                 # home-field advantage in points
BASE_TOTAL = 51.0                 # league-average projected combined score

# Component -> (label, weight used when summarizing on-field edges).
EDGE_COMPONENTS = {
    "qb_score": ("QB", 0.26),
    "prior_year_team_quality_score": ("Overall talent/quality", 0.24),
    "returning_production_score": ("Returning production", 0.16),
    "transfer_impact_score": ("Transfer portal", 0.12),
    "recruiting_talent_score": ("Recruiting talent", 0.09),
    "coaching_continuity_score": ("Coaching", 0.08),
    "schedule_strength_score": ("Schedule tested", 0.05),
}


@dataclass
class Edge:
    component: str
    label: str
    team_a_value: float
    team_b_value: float

    @property
    def diff(self) -> float:
        return self.team_a_value - self.team_b_value

    @property
    def favors(self) -> str:
        if abs(self.diff) < 1.0:
            return "even"
        return "A" if self.diff > 0 else "B"


@dataclass
class Prediction:
    team_a: str
    team_b: str
    location: str
    neutral_site: bool
    margin: float                 # positive => team_a favored, in points
    win_prob_a: float
    win_prob_b: float
    proj_score_a: float
    proj_score_b: float
    rating_a_pts: float
    rating_b_pts: float
    hfa_applied: float
    weather_note: str
    edges: list[Edge] = field(default_factory=list)
    narrative: str = ""

    @property
    def favorite(self) -> str:
        return self.team_a if self.margin >= 0 else self.team_b

    @property
    def spread_text(self) -> str:
        return f"{self.favorite} -{abs(self.margin):.1f}"


def load_ratings(path: Path = PROCESSED) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        raise FileNotFoundError(
            f"No processed ratings at {path}. Run scripts/03_build_power_index_v2.py first."
        )
    return pd.read_csv(path)


def _points_rating(df: pd.DataFrame) -> pd.Series:
    """Map power_index_v2 (or team_strength_rating if present) to a points scale."""
    if "team_strength_rating" in df.columns:
        base = pd.to_numeric(df["team_strength_rating"], errors="coerce")
    else:
        base = pd.to_numeric(df["power_index_v2"], errors="coerce")
    mean = base.mean()
    std = base.std(ddof=0) or 1.0
    return (base - mean) / std * RATING_POINTS_STD


def _weather_adjust(total: float, margin: float, weather: dict | None) -> tuple[float, float, str]:
    if not weather:
        return total, margin, "No weather adjustment."
    wind = float(weather.get("wind_speed", 0) or 0)
    precip = float(weather.get("precipitation", 0) or 0)
    indoors = bool(weather.get("game_indoors", False))
    if indoors:
        return total, margin, "Indoor venue — no weather effect."
    notes = []
    if wind >= 15:
        total -= min(8.0, (wind - 14) * 0.5)
        margin *= 0.92
        notes.append(f"high wind ({wind:.0f} mph) lowers scoring and compresses the edge")
    if precip and precip > 0:
        total -= 3.0
        margin *= 0.95
        notes.append("precipitation lowers scoring")
    if not notes:
        return total, margin, "Mild conditions — negligible weather effect."
    return max(total, 24.0), margin, "Weather: " + "; ".join(notes) + "."


def predict_game(
    team_a: str,
    team_b: str,
    df: pd.DataFrame | None = None,
    location: str = "neutral",     # "home_a", "home_b", or "neutral"
    weather: dict | None = None,
    hfa: float = DEFAULT_HFA,
) -> Prediction:
    df = load_ratings() if df is None else df
    teams = df.set_index("team")
    for t in (team_a, team_b):
        if t not in teams.index:
            raise KeyError(f"Team not found in ratings: {t}")

    pts = _points_rating(df)
    pts.index = df["team"]
    rating_a, rating_b = float(pts[team_a]), float(pts[team_b])

    neutral = location == "neutral"
    hfa_applied = 0.0 if neutral else (hfa if location == "home_a" else -hfa)
    margin = (rating_a - rating_b) + hfa_applied

    total = BASE_TOTAL
    total, margin, weather_note = _weather_adjust(total, margin, weather)

    win_prob_a = _normal_cdf(margin / GAME_OUTCOME_STD)
    proj_a = (total + margin) / 2.0
    proj_b = (total - margin) / 2.0

    edges = _build_edges(teams.loc[team_a], teams.loc[team_b])
    pred = Prediction(
        team_a=team_a,
        team_b=team_b,
        location=location,
        neutral_site=neutral,
        margin=margin,
        win_prob_a=win_prob_a,
        win_prob_b=1 - win_prob_a,
        proj_score_a=max(0.0, round(proj_a)),
        proj_score_b=max(0.0, round(proj_b)),
        rating_a_pts=rating_a,
        rating_b_pts=rating_b,
        hfa_applied=hfa_applied,
        weather_note=weather_note,
        edges=edges,
    )
    pred.narrative = _narrative(pred)
    return pred


def _build_edges(row_a: pd.Series, row_b: pd.Series) -> list[Edge]:
    edges = []
    for col, (label, _w) in EDGE_COMPONENTS.items():
        if col in row_a.index and col in row_b.index:
            a = float(pd.to_numeric(row_a[col], errors="coerce") or 50.0)
            b = float(pd.to_numeric(row_b[col], errors="coerce") or 50.0)
            edges.append(Edge(component=col, label=label, team_a_value=a, team_b_value=b))
    # Biggest swing factors first.
    return sorted(edges, key=lambda e: abs(e.diff), reverse=True)


def _narrative(p: Prediction) -> str:
    fav, dog = (p.team_a, p.team_b) if p.margin >= 0 else (p.team_b, p.team_a)
    conf = max(p.win_prob_a, p.win_prob_b)
    if conf >= 0.80:
        strength = "a clear favorite"
    elif conf >= 0.62:
        strength = "a solid favorite"
    elif conf >= 0.54:
        strength = "a slight favorite"
    else:
        strength = "essentially a coin flip"

    loc_txt = {
        "home_a": f"with {p.team_a} at home",
        "home_b": f"with {p.team_b} at home",
        "neutral": "at a neutral site",
    }[p.location]

    drivers = [e for e in p.edges if abs(e.diff) >= 4.0][:3]
    if drivers:
        parts = []
        for e in drivers:
            winner = p.team_a if e.diff > 0 else p.team_b
            parts.append(f"{e.label} (edge: {winner}, {abs(e.diff):.0f} pts of component gap)")
        driver_txt = "The biggest separators are " + "; ".join(parts) + "."
    else:
        driver_txt = "The teams are closely matched across every component."

    return (
        f"{fav} is {strength} {loc_txt} ({max(p.win_prob_a, p.win_prob_b)*100:.0f}% to win), "
        f"projected {p.spread_text}, score ~{p.proj_score_a:.0f}-{p.proj_score_b:.0f}. "
        f"{driver_txt} {p.weather_note}"
    )


def _normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


if __name__ == "__main__":
    data = load_ratings()
    sample = data["team"].head(2).tolist()
    if len(sample) == 2:
        pred = predict_game(sample[0], sample[1], df=data, location="home_a")
        print(pred.narrative)
        print()
        for e in pred.edges:
            print(f"  {e.label:<26} {e.team_a_value:6.1f} vs {e.team_b_value:6.1f}  -> favors {e.favors}")
