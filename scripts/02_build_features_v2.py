import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from model_v2 import PROCESSED_DIR, build_all_feature_scores


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df = build_all_feature_scores()
    output = PROCESSED_DIR / "team_features_v2.csv"
    df.to_csv(output, index=False)
    print(f"Saved {len(df):,} rows -> {output}")


if __name__ == "__main__":
    main()
