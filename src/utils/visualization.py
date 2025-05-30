import argparse
import json
from pathlib import Path
import matplotlib.pyplot as plt
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor


def map_service_name(name):
    mapping = {
        "AUTO": "Terminal Automation",
        "AD": "Asset Digitalisation",
        "IW": "Industrial Wireless",
        "CF": "Confluence",
        "MVM": "Mavim",
        "HV": "Horizon View"
    }
    return mapping.get(name.upper(), name)


def add_summary_slide(prs, data, overall):
    slide_layout = prs.slide_layouts[6]  # Blank slide
    slide = prs.slides.add_slide(slide_layout)

    # Table section
    rows = 11
    cols = 4
    left = Inches(0.3)
    top = Inches(0.3)
    width = Inches(6.2)
    height = Inches(4.5)

    table = slide.shapes.add_table(rows, cols, left, top, width, height).table
    col_titles = ["Services", "Incidents", "Requests", "Total Tickets"]
    for i, title in enumerate(col_titles):
        table.cell(0, i).text = title
        table.cell(0, i).text_frame.paragraphs[0].font.bold = True

    services_order = ["SIP", "FLOW", "AUTO", "AD", "IW", "CF", "MVM", "HV", "IFS"]
    total_inc = total_ritm = total_all = 0

    for i, service in enumerate(services_order):
        stats = data.get(service.upper(), {})
        inc = stats.get("INC_count", 0)
        ritm = stats.get("RITM_count", 0)
        total = stats.get("total_tickets", inc + ritm)

        total_inc += inc
        total_ritm += ritm
        total_all += total

        table.cell(i + 1, 0).text = map_service_name(service)
        table.cell(i + 1, 1).text = str(inc)
        table.cell(i + 1, 2).text = str(ritm)
        table.cell(i + 1, 3).text = str(total)

    # Total row
    table.cell(10, 0).text = "Total"
    table.cell(10, 1).text = str(total_inc)
    table.cell(10, 2).text = str(total_ritm)
    table.cell(10, 3).text = str(total_all)
    for i in range(4):
        table.cell(10, i).text_frame.paragraphs[0].font.bold = True

    # Donut chart - INC vs RITM
    fig1, ax1 = plt.subplots(figsize=(2.5, 2.5))
    wedges, texts = ax1.pie([total_ritm, total_inc], labels=['RITM', 'INC'], startangle=90,
                             colors=['#2ecc71', '#e67e22'], wedgeprops={'width': 0.4})
    plt.text(0, 0, f"{total_all}\nTotal", ha='center', va='center', fontsize=10)
    plt.text(-1.2, 0.5, f"{total_ritm} RITM", fontsize=9)
    plt.text(0.8, 0.5, f"{total_inc} INC", fontsize=9)
    donut_path = Path("data/reports/donut_total.png")
    plt.savefig(donut_path, bbox_inches='tight')
    plt.close()
    slide.shapes.add_picture(str(donut_path), Inches(7.2), Inches(0.3), height=Inches(2.8))

    # Urgency donut chart
    urgency_counts = {}
    for s in data.values():
        for level, pct in s.get("urgency_distribution", {}).items():
            urgency_counts[level] = urgency_counts.get(level, 0) + pct

    total_services = len(data)
    if total_services:
        urgency_pct = {k: round(v / total_services, 2) for k, v in urgency_counts.items()}
        labels = [f"{k}\n{v:.1f}%" for k, v in urgency_pct.items()]
        sizes = list(urgency_pct.values())

        fig2, ax2 = plt.subplots(figsize=(2.5, 2.5))
        colors = ['#3498db', '#f1c40f', '#e74c3c', '#9b59b6']
        ax2.pie(sizes, labels=labels, startangle=90, colors=colors, wedgeprops={'width': 0.4})
        plt.title("Urgency Split", fontsize=10)
        urgency_path = Path("data/reports/urgency_donut.png")
        plt.savefig(urgency_path, bbox_inches='tight')
        plt.close()
        slide.shapes.add_picture(str(urgency_path), Inches(7.2), Inches(3.2), height=Inches(2.8))

    # Keynotes area
    left = Inches(0.3)
    top = Inches(5.1)
    width = Inches(6.2)
    height = Inches(1.2)
    textbox = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    textbox.fill.solid()
    textbox.fill.fore_color.rgb = RGBColor(255, 165, 0)  # Orange
    textbox.text = "Weekly Keynotes (to be filled manually)"
    textbox.text_frame.paragraphs[0].font.size = Pt(14)
    textbox.text_frame.paragraphs[0].font.bold = True


def generate_ppt(json_path: str, output_dir: str):
    with open(json_path, 'r') as f:
        summary = json.load(f)

    data = summary.get("services", {})
    overall = summary.get("overall", {})
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    prs = Presentation()

    # Add summary slide with expanded visuals
    add_summary_slide(prs, data, overall)

    ppt_path = output_path / "Service_Report.pptx"
    prs.save(ppt_path)
    print(f"✅ Presentation saved to {ppt_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate service report PowerPoint")
    parser.add_argument("--input", required=True, help="Path to JSON summary file")
    parser.add_argument("--output", required=True, help="Directory to save PPT")
    args = parser.parse_args()

    generate_ppt(args.input, args.output)
