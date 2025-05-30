import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import argparse

def generate_service_summary(input_file: str, output_file: str = "data/processed/service_summary.json", start_date: str = None, end_date: str = None):
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        print(f"❌ Failed to read file: {e}")
        return

    # Required columns check
    required_cols = {"ID", "Created", "Predicted_Service_Tag", "Urgency"}
    missing = required_cols - set(df.columns)
    if missing:
        print(f"❌ Missing required columns: {missing}")
        return

    # Convert Created column to datetime
    df["Created"] = pd.to_datetime(df["Created"], errors='coerce')

    # Filter by date range if provided
    if start_date:
        start_dt = pd.to_datetime(start_date)
        df = df[df["Created"] >= start_dt]
    if end_date:
        end_dt = pd.to_datetime(end_date)
        df = df[df["Created"] <= end_dt]

    # Normalize service tag casing
    df["Predicted_Service_Tag"] = df["Predicted_Service_Tag"].str.upper()

    summary = {
        "generated_at": datetime.now().isoformat(),
        "source_file": input_file,
        "date_range": {
            "start": start_date,
            "end": end_date
        },
        "services": {},
        "overall": {}
    }

    total_inc = 0
    total_ritm = 0
    total_all = len(df)

    for service, group in df.groupby("Predicted_Service_Tag"):
        total_tickets = len(group)
        inc_count = group["ID"].str.startswith("INC").sum()
        ritm_count = group["ID"].str.startswith("RITM").sum()

        total_inc += inc_count
        total_ritm += ritm_count

        urgency_pct = group["Urgency"].value_counts(normalize=True).round(4) * 100
        urgency_dist = urgency_pct.to_dict()

        summary["services"][service] = {
            "total_tickets": total_tickets,
            "INC_count": int(inc_count),
            "RITM_count": int(ritm_count),
            "urgency_distribution": urgency_dist,
            "first_ticket": group["Created"].min().isoformat() if not group["Created"].isnull().all() else None,
            "last_ticket": group["Created"].max().isoformat() if not group["Created"].isnull().all() else None
        }

    summary["overall"] = {
        "total_tickets": total_all,
        "total_INC": int(total_inc),
        "total_RITM": int(total_ritm)
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
    parser.add_argument("--start-date", help="Start date in YYYY-MM-DD format", required=False)
    parser.add_argument("--end-date", help="End date in YYYY-MM-DD format", required=False)
    args = parser.parse_args()

    generate_service_summary(args.input, args.output, args.start_date, args.end_date)
