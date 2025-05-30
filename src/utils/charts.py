import argparse
import json
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


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
    df = pd.DataFrame(index=[SERVICES[k] for k in SERVICES], columns=urgency_levels).fillna(0)

    for tag, label in SERVICES.items():
        stats = data.get(tag.upper())
        if stats:
            for level, pct in stats.get("urgency_distribution", {}).items():
                if level in urgency_levels:
                    df.loc[label, level] = pct

    plt.figure(figsize=(8, 6))
    sns.heatmap(df.astype(float), annot=True, cmap="YlOrRd", fmt=".1f")
    plt.title("Urgency Distribution per Service (%)")
    plt.tight_layout()

    heatmap_path = output_path / "urgency_heatmap.png"
    plt.savefig(heatmap_path)
    plt.close()
    print(f"✅ Urgency heatmap saved to {heatmap_path}")


def generate_charts(json_path: str, output_dir: str):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    data = load_data(json_path).get("services", {})

    generate_volume_bar_chart(data, output_path)
    generate_urgency_heatmap(data, output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate advanced service charts")
    parser.add_argument("--input", required=True, help="Path to JSON summary file")
    parser.add_argument("--output", default="data/charts", help="Directory to save charts")
    args = parser.parse_args()

    generate_charts(args.input, args.output)
