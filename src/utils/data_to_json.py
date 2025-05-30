import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import argparse


def generate_service_summary(input_file: str, output_file: str = "data/processed/service_summary.json"):
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        print(f"❌ Failed to read file: {e}")
        return

    # Required columns check
    required_cols = {"ID", "Created", "Predicted_Service_Tag"}
    missing = required_cols - set(df.columns)
    if missing:
        print(f"❌ Missing required columns: {missing}")
        return

    # Convert Created column to datetime
    df["Created"] = pd.to_datetime(df["Created"], errors='coerce')

    summary = {
        "generated_at": datetime.now().isoformat(),
        "source_file": input_file,
        "services": {}
    }

    for service, group in df.groupby("Predicted_Service_Tag"):
        total_tickets = len(group)
        inc_count = group["ID"].str.startswith("INC").sum()
        ritm_count = group["ID"].str.startswith("RITM").sum()
        summary["services"][service] = {
            "total_tickets": total_tickets,
            "INC_count": int(inc_count),
            "RITM_count": int(ritm_count),
            "first_ticket": group["Created"].min().isoformat() if not group["Created"].isnull().all() else None,
            "last_ticket": group["Created"].max().isoformat() if not group["Created"].isnull().all() else None
        }

    # Save JSON
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"✅ Service summary saved to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate JSON summary from prediction file")
    parser.add_argument("--input", required=True, help="Path to predictions CSV file")
    parser.add_argument("--output", default="data/processed/service_summary.json", help="Output JSON file path")
    args = parser.parse_args()

    generate_service_summary(args.input, args.output)
