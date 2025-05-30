import argparse
import json
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
import matplotlib.pyplot as plt


def generate_bar_chart(data: dict, output_path: Path) -> Path:
    services = []
    totals = []

    for service, entry in data.items():
        if isinstance(entry, dict) and "total_tickets" in entry:
            services.append(service)
            totals.append(entry["total_tickets"])

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(services, totals, color='skyblue')
    ax.set_xlabel('Total Tickets')
    ax.set_ylabel('Service')
    ax.set_title('Total Tickets per Service')
    ax.invert_yaxis()  # Highest at top

    for bar in bars:
        width = bar.get_width()
        ax.text(width + 5, bar.get_y() + bar.get_height() / 2, str(int(width)), va='center')

    plt.tight_layout()
    chart_path = output_path / "tickets_per_service.png"
    plt.savefig(chart_path)
    plt.close()
    return chart_path


def add_slide_with_image(prs, image_path: Path, title: str):
    slide_layout = prs.slide_layouts[5]  # Title Only
    slide = prs.slides.add_slide(slide_layout)
    title_shape = slide.shapes.title
    title_shape.text = title
    left = Inches(1)
    top = Inches(1.5)
    height = Inches(5)
    slide.shapes.add_picture(str(image_path), left, top, height=height)


def add_progress_slide(prs, service: str, inc: int, ritm: int):
    total = inc + ritm if inc + ritm > 0 else 1
    inc_ratio = inc / total
    ritm_ratio = ritm / total

    slide_layout = prs.slide_layouts[5]
    slide = prs.slides.add_slide(slide_layout)
    title_shape = slide.shapes.title
    title_shape.text = f"Service: {service}"

    left = Inches(1)
    top = Inches(2)
    width = Inches(6)
    height = Inches(1)

    # INC progress bar (blue)
    inc_box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width * inc_ratio, height)
    inc_box.fill.solid()
    inc_box.fill.fore_color.rgb = RGBColor(0, 102, 204)
    inc_box.line.fill.background()

    # RITM progress bar (green)
    ritm_box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left + width * inc_ratio, top, width * ritm_ratio, height)
    ritm_box.fill.solid()
    ritm_box.fill.fore_color.rgb = RGBColor(0, 204, 102)
    ritm_box.line.fill.background()

    # Labels
    slide.shapes.add_textbox(left, top - Inches(0.4), width, Inches(0.3)).text = f"INC: {inc}, RITM: {ritm}"


def generate_ppt(json_path: str, output_dir: str):
    with open(json_path, 'r') as f:
        summary = json.load(f)

    data = summary.get("services", {})
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    ppt = Presentation()

    # Bar chart slide
    chart_img = generate_bar_chart(data, output_path)
    add_slide_with_image(ppt, chart_img, "Total Tickets per Service")

    # Progress slides
    for service, stats in data.items():
        inc = stats.get("INC_count", 0)
        ritm = stats.get("RITM_count", 0)
        add_progress_slide(ppt, service, inc, ritm)

    ppt_path = output_path / "Service_Report.pptx"
    ppt.save(ppt_path)
    print(f"✅ Presentation saved to {ppt_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate service report PowerPoint")
    parser.add_argument("--input", required=True, help="Path to JSON summary file")
    parser.add_argument("--output", required=True, help="Directory to save PPT")
    args = parser.parse_args()


    generate_ppt(args.input, args.output)
