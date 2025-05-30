import argparse
import json
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
import matplotlib.pyplot as plt

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

def add_summary_table_slide(prs, data):
    slide_layout = prs.slide_layouts[5]
    slide = prs.slides.add_slide(slide_layout)
    slide.shapes.title.text = "Weekly Service Summary"

    rows = len(data) + 2
    cols = 4

    left = Inches(0.5)
    top = Inches(1.5)
    width = Inches(8.5)
    height = Inches(0.8 + 0.3 * rows)

    table = slide.shapes.add_table(rows, cols, left, top, width, height).table
    col_titles = ["Services", "Incidents", "Requests", "Total Tickets"]
    for i, title in enumerate(col_titles):
        table.cell(0, i).text = title

    total_inc = total_ritm = total_all = 0

    services_order = ["SIP", "Flow", "AUTO", "AD", "IW", "CF", "MVM", "HV", "IFS"]
    for row_idx, service in enumerate(services_order, start=1):
        display_name = map_service_name(service)
        stats = data.get(service) or data.get(service.upper()) or {}
        inc = stats.get("INC_count", 0)
        ritm = stats.get("RITM_count", 0)
        total = stats.get("total_tickets", inc + ritm)

        total_inc += inc
        total_ritm += ritm
        total_all += total

        table.cell(row_idx, 0).text = display_name
        table.cell(row_idx, 1).text = str(inc)
        table.cell(row_idx, 2).text = str(ritm)
        table.cell(row_idx, 3).text = str(total)

    # Totals row
    table.cell(rows - 1, 0).text = "Total"
    table.cell(rows - 1, 1).text = str(total_inc)
    table.cell(rows - 1, 2).text = str(total_ritm)
    table.cell(rows - 1, 3).text = str(total_all)

def generate_ppt(json_path: str, output_dir: str):
    with open(json_path, 'r') as f:
        summary = json.load(f)

    data = summary.get("services", {})
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    ppt = Presentation()

    # Add summary table as first slide
    add_summary_table_slide(ppt, data)

    ppt_path = output_path / "Service_Report.pptx"
    ppt.save(ppt_path)
    print(f"✅ Presentation saved to {ppt_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate service report PowerPoint")
    parser.add_argument("--input", required=True, help="Path to JSON summary file")
    parser.add_argument("--output", required=True, help="Directory to save PPT")
    args = parser.parse_args()

    generate_ppt(args.input, args.output)
