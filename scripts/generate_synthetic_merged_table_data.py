#!/usr/bin/env python3

import argparse
import json
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic merged-cell table data")
    parser.add_argument("--output-dir", default="synthetic_merged_tables")
    parser.add_argument("--count", type=int, default=25)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def html_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def make_sample(index: int, rng: random.Random) -> dict:
    product = rng.choice(["MCU", "PMIC", "Sensor", "Driver", "ADC"])
    parameter = rng.choice(["VIN", "VOUT", "IQUIESCENT", "TEMP", "FREQ"])
    temp_band = rng.choice(["-40C to 85C", "-40C to 125C", "0C to 70C"])
    package = rng.choice(["QFN", "BGA", "TSSOP", "SOIC"])

    top_headers = [
        {"text": "Parameter", "rowspan": 2, "colspan": 1},
        {"text": f"Conditions ({temp_band})", "rowspan": 1, "colspan": 2},
        {"text": "Limits", "rowspan": 1, "colspan": 2},
    ]
    second_headers = ["Mode", "Package", "Min", "Max"]

    mode_a = rng.choice(["Sleep", "Standby", "Run"])
    mode_b = rng.choice(["Boost", "Buck", "Bypass"])

    parameter_rowspan = 2 if rng.random() > 0.45 else 1

    first_row = [
        [
            {"text": parameter, "rowspan": parameter_rowspan, "colspan": 1},
            {"text": mode_a, "rowspan": 1, "colspan": 1},
            {"text": package, "rowspan": 1, "colspan": 1},
            {"text": f"{rng.uniform(0.8, 5.0):.2f}", "rowspan": 1, "colspan": 1},
            {"text": f"{rng.uniform(5.1, 24.0):.2f}", "rowspan": 1, "colspan": 1},
        ]
    ]

    second_row = []
    if parameter_rowspan == 1:
        second_row.append({"text": f"{parameter} ALT", "rowspan": 1, "colspan": 1})
    second_row.extend(
        [
            {"text": mode_b, "rowspan": 1, "colspan": 1},
            {"text": package, "rowspan": 1, "colspan": 1},
            {"text": f"{rng.uniform(0.8, 5.0):.2f}", "rowspan": 1, "colspan": 1},
            {"text": f"{rng.uniform(5.1, 24.0):.2f}", "rowspan": 1, "colspan": 1},
        ]
    )

    notes_left_colspan = rng.choice([2, 3])
    notes_right_colspan = 5 - notes_left_colspan

    body_rows = first_row + [
        second_row,
        [
            {"text": f"{product} Notes", "rowspan": 1, "colspan": notes_left_colspan},
            {"text": "See footnote A", "rowspan": 1, "colspan": notes_right_colspan},
        ],
    ]

    return {
        "id": f"synthetic_{index:05d}",
        "doc_id": f"synthetic_doc_{index:05d}",
        "top_headers": top_headers,
        "second_headers": second_headers,
        "body_rows": body_rows,
        "notes": "Synthetic merged-cell table with randomized widths, heights, and spans.",
    }


def expand_rows(top_headers: list[dict], second_headers: list[str], body_rows: list[list[dict]]) -> list[list[dict | None]]:
    grid: list[list[dict | None]] = []
    width = 5

    def place_row(cells: list[dict], target_width: int) -> None:
        row = [None] * target_width
        col = 0
        for cell in cells:
            while col < target_width and row[col] is not None:
                col += 1
            for offset in range(cell["colspan"]):
                row[col + offset] = cell if offset == 0 else {"_covered": True}
            col += cell["colspan"]
        grid.append(row)

    place_row(top_headers, width)
    second_row = []
    for cell in top_headers:
        if cell["rowspan"] == 2:
            second_row.append({"_covered": True})
        else:
            for label in second_headers[: cell["colspan"]]:
                second_row.append({"text": label, "rowspan": 1, "colspan": 1})
            second_headers = second_headers[cell["colspan"] :]
    while len(second_row) < width:
        second_row.append({"_covered": True})
    grid.append(second_row)

    # Body-row placement starts after the full header block, so header rowspans
    # should not spill into the body grid state here.
    active_rowspans = [0] * width

    for cells in body_rows:
        row = [None] * width
        for col in range(width):
            if active_rowspans[col] > 0:
                row[col] = {"_covered": True}
                active_rowspans[col] -= 1

        col = 0
        for cell in cells:
            while col < width and row[col] is not None:
                col += 1
            for offset in range(cell["colspan"]):
                row[col + offset] = cell if offset == 0 else {"_covered": True}
                if cell["rowspan"] > 1:
                    active_rowspans[col + offset] = cell["rowspan"] - 1
            col += cell["colspan"]
        grid.append(row)

    return grid


def render_table(sample: dict, image_path: Path, rng: random.Random) -> None:
    grid = expand_rows(sample["top_headers"], sample["second_headers"], sample["body_rows"])
    widths = [rng.randint(120, 190), rng.randint(110, 170), rng.randint(100, 150), rng.randint(90, 130), rng.randint(90, 130)]
    heights = [rng.randint(42, 58) for _ in grid]
    pad_x = rng.randint(20, 40)
    pad_y = rng.randint(20, 36)

    total_width = sum(widths) + pad_x * 2
    total_height = sum(heights) + pad_y * 2

    image = Image.new("RGB", (total_width, total_height), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    x_positions = [pad_x]
    for width in widths[:-1]:
        x_positions.append(x_positions[-1] + width)

    y = pad_y
    visited: set[tuple[int, int]] = set()
    for row_idx, row in enumerate(grid):
        x = pad_x
        for col_idx, cell in enumerate(row):
            if (row_idx, col_idx) in visited:
                x += widths[col_idx]
                continue
            if cell is None or cell.get("_covered"):
                x += widths[col_idx]
                continue

            colspan = cell.get("colspan", 1)
            rowspan = cell.get("rowspan", 1)
            box_width = sum(widths[col_idx : col_idx + colspan])
            box_height = sum(heights[row_idx : row_idx + rowspan])
            fill = "#eef4ff" if row_idx < 2 else "#ffffff"
            draw.rectangle([x, y, x + box_width, y + box_height], outline="black", width=2, fill=fill)

            text = cell["text"]
            draw.text((x + 8, y + 8), text, fill="black", font=font)

            for row_offset in range(rowspan):
                for col_offset in range(colspan):
                    visited.add((row_idx + row_offset, col_idx + col_offset))

            x += widths[col_idx]
        y += heights[row_idx]

    image.save(image_path)


def sample_to_html(sample: dict) -> str:
    parts = ["<table>", "<thead>", "<tr>"]
    for cell in sample["top_headers"]:
        attrs = []
        if cell["rowspan"] > 1:
            attrs.append(f'rowspan="{cell["rowspan"]}"')
        if cell["colspan"] > 1:
            attrs.append(f'colspan="{cell["colspan"]}"')
        attr_text = (" " + " ".join(attrs)) if attrs else ""
        parts.append(f"<th{attr_text}>{html_escape(cell['text'])}</th>")
    parts.append("</tr>")
    parts.append("<tr>")
    for label in sample["second_headers"]:
        parts.append(f"<th>{html_escape(label)}</th>")
    parts.append("</tr>")
    parts.append("</thead>")
    parts.append("<tbody>")

    for row in sample["body_rows"]:
        parts.append("<tr>")
        for cell in row:
            attrs = []
            if cell["rowspan"] > 1:
                attrs.append(f'rowspan="{cell["rowspan"]}"')
            if cell["colspan"] > 1:
                attrs.append(f'colspan="{cell["colspan"]}"')
            attr_text = (" " + " ".join(attrs)) if attrs else ""
            parts.append(f"<td{attr_text}>{html_escape(cell['text'])}</td>")
        parts.append("</tr>")

    parts.append("</tbody>")
    parts.append("</table>")
    return "".join(parts)


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)

    output_dir = Path(args.output_dir)
    images_dir = output_dir / "images"
    jsonl_path = output_dir / "synthetic_table_html.jsonl"
    images_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for index in range(args.count):
        sample = make_sample(index, rng)
        image_path = images_dir / f"{sample['id']}.png"
        render_table(sample, image_path, rng)
        rows.append(
            {
                "id": sample["id"],
                "doc_id": sample["doc_id"],
                "image": str(image_path.resolve()),
                "html": sample_to_html(sample),
                "notes": sample["notes"],
            }
        )

    with jsonl_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Wrote {jsonl_path}")
    print(f"Generated {len(rows)} samples in {images_dir}")


if __name__ == "__main__":
    main()
