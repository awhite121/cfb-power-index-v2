import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from model_v2 import save_outputs


def main():
    df = save_outputs()
    if df.empty:
        print("No output rows. Check cfb_combined_data.xlsx or raw data files.")
        return
    print(df[["rank_v2", "team", "power_index_v2"]].head(25).to_string(index=False))
    print("\nCreated:")
    print("- data/processed/team_features_v2.csv")
    print("- data/processed/cfb_power_index_v2.csv")


if __name__ == "__main__":
    main()
