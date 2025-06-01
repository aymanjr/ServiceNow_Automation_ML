import pandas as pd
import json
from pathlib import Path
from datetime import datetime, timedelta
import argparse

def generate_service_summary(input_file: str, output_file: str = "data/processed/service_summary.json", start_date: str = None, end_date: str = None):
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        print(f"❌ Failed to read file: {e}")
        return

    required_cols = {"ID", "Created", "Predicted_Service_Tag", "Urgency"}
    missing = required_cols - set(df.columns)
    if missing:
        print(f"❌ Missing required columns: {missing}")
        return

    df["Created"] = pd.to_datetime(df["Created"], errors='coerce')
    df["Predicted_Service_Tag"] = df["Predicted_Service_Tag"].str.upper()

    # Convert input dates
    start_dt = pd.to_datetime(start_date) if start_date else None
    end_dt = pd.to_datetime(end_date) if end_date else None

    # Current period filter
    current_df = df.copy()
    if start_dt:
        current_df = current_df[current_df["Created"] >= start_dt]
    if end_dt:
        current_df = current_df[current_df["Created"] <= end_dt]

    # Previous period filter
    if start_dt and end_dt:
        delta = end_dt - start_dt
        prev_start = start_dt - delta
        prev_end = end_dt - delta
        prev_df = df[(df["Created"] >= prev_start) & (df["Created"] <= prev_end)]
    else:
        prev_df = pd.DataFrame(columns=df.columns)

    def summarize(df_slice):
        result = {}
        for service, group in df_slice.groupby("Predicted_Service_Tag"):
            total_tickets = len(group)
            inc_count = group["ID"].str.startswith("INC").sum()
            ritm_count = group["ID"].str.startswith("RITM").sum()
            urgency_pct = group["Urgency"].value_counts(normalize=True).round(4) * 100
            urgency_dist = urgency_pct.to_dict()

            result[service] = {
                "total_tickets": total_tickets,
                "INC_count": int(inc_count),
                "RITM_count": int(ritm_count),
                "urgency_distribution": urgency_dist,
                "first_ticket": group["Created"].min().isoformat() if not group["Created"].isnull().all() else None,
                "last_ticket": group["Created"].max().isoformat() if not group["Created"].isnull().all() else None
            }
        return result

    current_summary = summarize(current_df)
    previous_summary = summarize(prev_df)

    insights = {}
    for service, current_stats in current_summary.items():
        prev_stats = previous_summary.get(service, {})
        current_total = current_stats.get("total_tickets", 0)
        prev_total = prev_stats.get("total_tickets", 0)
        diff = current_total - prev_total
        change_pct = ((diff / prev_total) * 100) if prev_total > 0 else None

        if change_pct is not None:
            if change_pct > 0:
                line = f"Increase of {round(change_pct, 1)}% in {service}"
            elif change_pct < 0:
                line = f"Decrease of {round(abs(change_pct), 1)}% in {service}"
            else:
                line = f"No change in ticket volume for {service}"
        else:
            line = f"No previous data to compare for {service}"

        insights[service] = line

    overall_total = len(current_df)
    total_inc = current_df["ID"].str.startswith("INC").sum()
    total_ritm = current_df["ID"].str.startswith("RITM").sum()

    summary = {
        "generated_at": datetime.now().isoformat(),
        "source_file": input_file,
        "date_range": {
            "start": start_date,
            "end": end_date
        },
        "services": current_summary,
        "overall": {
            "total_tickets": overall_total,
            "total_INC": int(total_inc),
            "total_RITM": int(total_ritm)
        },
        "comparison": insights
    }

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
