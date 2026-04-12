#!/usr/bin/env python3

import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "mock_smoke_test"
IMAGES_DIR = OUT_DIR / "images"
DATA_PATH = OUT_DIR / "mock_table_html.jsonl"


SAMPLES = [
    {
        "id": "mock_001",
        "doc_id": "mock_doc_a",
        "filename": "mock_001.png",
        "html": "<table><tbody><tr><th>Parameter</th><th>Min</th><th>Max</th></tr><tr><td>VIN</td><td>3.5 V</td><td>18 V</td></tr></tbody></table>",
        "lines": ["Parameter | Min | Max", "VIN       | 3.5 | 18"],
        "notes": "Simple mocked table",
    },
    {
        "id": "mock_002",
        "doc_id": "mock_doc_b",
        "filename": "mock_002.png",
        "html": "<table><thead><tr><th rowspan=\"2\">Mode</th><th colspan=\"2\">Current</th></tr><tr><th>Min</th><th>Max</th></tr></thead><tbody><tr><td>Sleep</td><td>10 uA</td><td>20 uA</td></tr></tbody></table>",
        "lines": ["Mode  | Current", "      | Min | Max", "Sleep | 10  | 20"],
        "notes": "Mock merged header case",
    },
]


def create_image(path: Path, lines: list[str]) -> None:
    img = Image.new("RGB", (640, 220), color="white")
    draw = ImageDraw.Draw(img)
    y = 30
    for line in lines:
        draw.text((30, y), line, fill="black")
        y += 40
    img.save(path)


def main() -> None:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for sample in SAMPLES:
        image_path = IMAGES_DIR / sample["filename"]
        create_image(image_path, sample["lines"])
        rows.append(
            {
                "id": sample["id"],
                "doc_id": sample["doc_id"],
                "image": str(image_path),
                "html": sample["html"],
                "notes": sample["notes"],
            }
        )

    with DATA_PATH.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Wrote {DATA_PATH}")
    print(f"Images in {IMAGES_DIR}")


if __name__ == "__main__":
    main()
