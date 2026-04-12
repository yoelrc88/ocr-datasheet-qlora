#!/usr/bin/env python3

import argparse
import json
import re
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate HTML table structure predictions")
    parser.add_argument("--predictions-jsonl", required=True, help="JSONL with gold and predicted HTML")
    return parser.parse_args()


def count(pattern: str, text: str) -> int:
    return len(re.findall(pattern, text, flags=re.IGNORECASE))


def normalize_html(text: str) -> str:
    return re.sub(r">\s+<", "><", text.strip())


def evaluate_row(row: dict) -> dict:
    gold = normalize_html(row["gold_html"])
    pred = normalize_html(row["pred_html"])
    return {
        "exact_match": int(gold == pred),
        "gold_tr": count(r"<tr\b", gold),
        "pred_tr": count(r"<tr\b", pred),
        "gold_cells": count(r"<(td|th)\b", gold),
        "pred_cells": count(r"<(td|th)\b", pred),
        "gold_rowspan": count(r"rowspan=", gold),
        "pred_rowspan": count(r"rowspan=", pred),
        "gold_colspan": count(r"colspan=", gold),
        "pred_colspan": count(r"colspan=", pred),
    }


def main() -> None:
    args = parse_args()
    rows = []

    with Path(args.predictions_jsonl).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            rows.append({**row, **evaluate_row(row)})

    if not rows:
        raise RuntimeError("No prediction rows found")

    exact_match = sum(row["exact_match"] for row in rows) / len(rows)
    avg_row_delta = sum(abs(row["gold_tr"] - row["pred_tr"]) for row in rows) / len(rows)
    avg_cell_delta = sum(abs(row["gold_cells"] - row["pred_cells"]) for row in rows) / len(rows)
    avg_rowspan_delta = sum(abs(row["gold_rowspan"] - row["pred_rowspan"]) for row in rows) / len(rows)
    avg_colspan_delta = sum(abs(row["gold_colspan"] - row["pred_colspan"]) for row in rows) / len(rows)

    print(f"Rows evaluated: {len(rows)}")
    print(f"Exact match: {exact_match:.3f}")
    print(f"Average row-count delta: {avg_row_delta:.3f}")
    print(f"Average cell-count delta: {avg_cell_delta:.3f}")
    print(f"Average rowspan-count delta: {avg_rowspan_delta:.3f}")
    print(f"Average colspan-count delta: {avg_colspan_delta:.3f}")


if __name__ == "__main__":
    main()
