import argparse
import json
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from datetime import datetime

SERVICES = {
    "SIP": "SIP",
    "FLOW": "FLOW",
    "AUTO": "Terminal Automation",
    "AD": "Asset Digitalisation",
    "IW": "Industrial Wireless",
    "CF": "Confluence",
    "MVM": "Mavim",
    "HV": "Horizon View",
    "IFS": "IFS"
}

COLORS = sns.color_palette("Set2")

def load_data(json_path):
    with open(json_path) as f:
        return json.load(f)

def generate_volume_bar_chart(data, output_path):
    services = []
    totals = []

    for tag, label in SERVICES.items():
        stats = data.get(tag.upper())
        if stats:
            services.append(label)
            totals.append(stats.get("total_tickets", 0))

    plt.figure(figsize=(10, 6))
    sns.barplot(y=services, x=totals, palette=COLORS)
    plt.xlabel("Total Tickets")
    plt.ylabel("Service")
    plt.title("Ticket Volume by Service")
    plt.tight_layout()

    chart_path = output_path / "volume_by_service.png"
    plt.savefig(chart_path)
    plt.close()
    print(f"✅ Volume bar chart saved to {chart_path}")

def generate_urgency_heatmap(data, output_path):
    urgency_levels = ["1 - High", "2 - Medium", "3 - Low"]

    # Heatmap for INC
    df_inc = pd.DataFrame(index=[SERVICES[k] for k in SERVICES], columns=urgency_levels).fillna(0)
    # Heatmap for RITM
    df_ritm = pd.DataFrame(index=[SERVICES[k] for k in SERVICES], columns=urgency_levels).fillna(0)

    for tag, label in SERVICES.items():
        stats = data.get(tag.upper())
        if stats:
            urg_dist = stats.get("urgency_distribution", {})
            inc_count = stats.get("INC_count", 0)
            ritm_count = stats.get("RITM_count", 0)
            total = inc_count + ritm_count if (inc_count + ritm_count) else 1
            for level in urgency_levels:
                val = urg_dist.get(level, 0)
                df_inc.loc[label, level] = round((val * inc_count / total), 1)
                df_ritm.loc[label, level] = round((val * ritm_count / total), 1)

    plt.figure(figsize=(8, 6))
    sns.heatmap(df_inc.astype(float), annot=True, cmap="YlGnBu", fmt=".1f")
    plt.title("Urgency Distribution for INC (%)")
    plt.tight_layout()
    heatmap_inc_path = output_path / "urgency_heatmap_INC.png"
    plt.savefig(heatmap_inc_path)
    plt.close()
    print(f"✅ INC urgency heatmap saved to {heatmap_inc_path}")

    plt.figure(figsize=(8, 6))
    sns.heatmap(df_ritm.astype(float), annot=True, cmap="YlGnBu", fmt=".1f")
    plt.title("Urgency Distribution for RITM (%)")
    plt.tight_layout()
    heatmap_ritm_path = output_path / "urgency_heatmap_RITM.png"
    plt.savefig(heatmap_ritm_path)
    plt.close()
    print(f"✅ RITM urgency heatmap saved to {heatmap_ritm_path}")

def generate_monthly_progress(csv_file, output_path):
    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        print(f"❌ Failed to load predictions file: {e}")
        return

    if "Created" not in df or "ID" not in df:
        print("❌ Required columns not found in data")
        return

    df["Created"] = pd.to_datetime(df["Created"], errors='coerce')
    df = df.dropna(subset=["Created"])

    current_year = datetime.now().year
    df = df[df["Created"].dt.year == current_year]

    df["month"] = df["Created"].dt.to_period("M")
    df["type"] = df["ID"].apply(lambda x: "INC" if str(x).startswith("INC") else ("RITM" if str(x).startswith("RITM") else "OTHER"))
    filtered = df[df["type"].isin(["INC", "RITM"])]

    summary = filtered.groupby(["month", "type"]).size().unstack(fill_value=0)
    summary = summary.sort_index()

    plt.figure(figsize=(10, 5))
    for t in ["INC", "RITM"]:
        if t in summary:
            plt.plot(summary.index.astype(str), summary[t], marker='o', label=t)

    plt.xlabel("Month")
    plt.ylabel("Ticket Count")
    plt.title(f"{current_year} Monthly Ticket Progress: INC vs RITM")
    plt.legend()
    plt.tight_layout()

    line_path = output_path / "monthly_progress.png"
    plt.savefig(line_path)
    plt.close()
    print(f"✅ Monthly progress chart saved to {line_path}")

def generate_total_donut(data, output_path):
    total_inc = total_ritm = 0

    for stats in data.values():
        total_inc += stats.get("INC_count", 0)
        total_ritm += stats.get("RITM_count", 0)

    total_all = total_inc + total_ritm if (total_inc + total_ritm) else 1
    inc_pct = round((total_inc / total_all) * 100, 1)
    ritm_pct = round((total_ritm / total_all) * 100, 1)

    labels = [f"RITM - {total_ritm} ({ritm_pct}%)", f"INC - {total_inc} ({inc_pct}%)"]
    sizes = [total_ritm, total_inc]
    colors = ['#2ecc71', '#e67e22']

    fig, ax = plt.subplots(figsize=(3.5, 3.5))
    wedges, texts = ax.pie(sizes, labels=labels, startangle=90,
                           colors=colors, wedgeprops={'width': 0.4})

    plt.text(0, 0, f"{total_all}\nTotal", ha='center', va='center', fontsize=12, weight='bold')
    plt.title("Total Tickets: INC vs RITM", fontsize=10)
    
    donut_path = output_path / "donut_total.png"
    plt.savefig(donut_path, bbox_inches='tight')
    plt.close()
    print(f"✅ Donut chart saved to {donut_path}")

def generate_charts(json_path: str, output_dir: str, csv_path: str):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    data = load_data(json_path).get("services", {})

    generate_volume_bar_chart(data, output_path)
    generate_urgency_heatmap(data, output_path)
    generate_monthly_progress(csv_path, output_path)
    generate_total_donut(data, output_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate advanced service charts")
    parser.add_argument("--input", required=True, help="Path to JSON summary file")
    parser.add_argument("--output", default="data/charts", help="Directory to save charts")
    parser.add_argument("--csv", required=True, help="CSV file with predictions and Created/ID columns")
    args = parser.parse_args()

    generate_charts(args.input, args.output, args.csv)
