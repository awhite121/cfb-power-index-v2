from __future__ import annotations

import pandas as pd

from config import RAW_DIR
from cfbd_client import cfbd_to_csv

CURRENT_SEASON = 2026
PRIOR_SEASON = 2025
RECRUITING_YEARS = [2022, 2023, 2024, 2025, 2026]
# Pull the transfer portal for every one of these seasons so the dashboard can
# compare classes year-over-year. Each lands as {year}_transfer_portal_cfbd.csv.
PORTAL_YEARS = [2023, 2024, 2025, 2026]


def safe_pull(name: str, endpoint: str, params: dict, filename: str):
    print(f"\nPulling {name}...")
    try:
        return cfbd_to_csv(endpoint, params, RAW_DIR / filename)
    except Exception as exc:
        print(f"SKIPPED {name}: {exc}")
        return None


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    safe_pull(
        "2026 schedule",
        "/games",
        {"year": CURRENT_SEASON, "seasonType": "regular"},
        "2026_schedule.csv",
    )

    safe_pull(
        "2026 calendar",
        "/calendar",
        {"year": CURRENT_SEASON},
        "2026_calendar.csv",
    )

    safe_pull(
        "2025 records",
        "/records",
        {"year": PRIOR_SEASON},
        "2025_records.csv",
    )

    safe_pull(
        "2025 team game stats",
        "/games/teams",
        {"year": PRIOR_SEASON, "seasonType": "regular"},
        "2025_team_game_stats.csv",
    )

    safe_pull(
        "2025 advanced season team stats",
        "/stats/season/advanced",
        {"year": PRIOR_SEASON},
        "2025_team_advanced_season_stats.csv",
    )

    safe_pull(
        "2025 player season stats",
        "/stats/player/season",
        {"year": PRIOR_SEASON, "seasonType": "regular"},
        "2025_player_stats.csv",
    )

    safe_pull(
        "2025 player game stats",
        "/games/players",
        {"year": PRIOR_SEASON, "seasonType": "regular"},
        "2025_player_game_stats.csv",
    )

    safe_pull(
        "2026 rosters",
        "/roster",
        {"year": CURRENT_SEASON},
        "2026_rosters.csv",
    )

    safe_pull(
        "2026 head coaches from CFBD",
        "/coaches",
        {"year": CURRENT_SEASON},
        "2026_head_coaches_cfbd.csv",
    )

    safe_pull(
        "2026 returning production from CFBD",
        "/player/returning",
        {"year": CURRENT_SEASON},
        "2026_returning_production_cfbd.csv",
    )

    for year in PORTAL_YEARS:
        safe_pull(
            f"{year} transfer portal from CFBD",
            "/player/portal",
            {"year": year},
            f"{year}_transfer_portal_cfbd.csv",
        )

    recruiting_frames = []
    for year in RECRUITING_YEARS:
        df = safe_pull(
            f"{year} recruiting teams",
            "/recruiting/teams",
            {"year": year},
            f"{year}_recruiting_teams.csv",
        )
        if isinstance(df, pd.DataFrame) and not df.empty:
            df["year"] = year
            recruiting_frames.append(df)

    if recruiting_frames:
        out = pd.concat(recruiting_frames, ignore_index=True)
        out.to_csv(RAW_DIR / "2022_2026_recruiting.csv", index=False)
        print(f"Saved consolidated recruiting -> {RAW_DIR / '2022_2026_recruiting.csv'}")

    # Weather may be paid-tier or may not exist until closer to game dates.
    safe_pull(
        "2026 weather, optional",
        "/games/weather",
        {"year": CURRENT_SEASON, "seasonType": "regular"},
        "2026_weather.csv",
    )


if __name__ == "__main__":
    main()
