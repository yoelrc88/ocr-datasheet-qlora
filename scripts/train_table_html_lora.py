#!/usr/bin/env python3

import argparse
import json
import os
import random
from pathlib import Path

import torch
from datasets import Dataset, DatasetDict
from peft import LoraConfig
from PIL import Image
from sklearn.model_selection import GroupShuffleSplit
from transformers import AutoProcessor, BitsAndBytesConfig, Qwen2_5_VLForConditionalGeneration
from trl import SFTConfig, SFTTrainer


SYSTEM_PROMPT = (
    "You are a document table transcription model. Convert the input table image into valid HTML. "
    "Preserve table structure exactly, including merged cells with rowspan and colspan. "
    "Do not summarize. Do not explain. Output HTML only."
)

USER_PROMPT = (
    "Convert this table image to HTML. Requirements: emit a single <table>...</table>; "
    "preserve row and column structure; preserve rowspan and colspan; preserve line breaks inside "
    "cells with <br/> if needed; do not add commentary."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train olmOCR table-to-HTML LoRA adapter")
    parser.add_argument("--data-jsonl", required=True, help="Path to labeled JSONL dataset")
    parser.add_argument("--output-dir", required=True, help="Directory for checkpoints and adapter")
    parser.add_argument("--model-id", default="allenai/olmOCR-2-7B-1025")
    parser.add_argument("--processor-id", default="Qwen/Qwen2.5-VL-7B-Instruct")
    parser.add_argument("--max-samples", type=int, default=0, help="0 means use all samples")
    parser.add_argument("--train-size", type=float, default=0.8)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--epochs", type=float, default=1.0)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--grad-accum", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--logging-steps", type=int, default=5)
    parser.add_argument("--eval-steps", type=int, default=10)
    parser.add_argument("--save-steps", type=int, default=25)
    parser.add_argument("--lora-r", type=int, default=8)
    parser.add_argument("--lora-alpha", type=int, default=16)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--target-modules", nargs="+", default=["q_proj", "v_proj"])
    parser.add_argument(
        "--max-length",
        type=int,
        default=0,
        help="0 disables truncation. Prefer 0 for VLM training unless you validated your sequence lengths.",
    )
    return parser.parse_args()


def set_seed(seed: int) -> None:
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def load_rows(path: Path, max_samples: int) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    if max_samples > 0:
        rows = rows[:max_samples]
    return rows


def validate_rows(rows: list[dict]) -> list[dict]:
    cleaned = []
    for index, row in enumerate(rows):
        sample_id = row.get("id", f"sample_{index:05d}")
        doc_id = row.get("doc_id", sample_id)
        image_path = row.get("image")
        html = row.get("html")

        if not image_path:
            raise ValueError(f"Missing image path for {sample_id}")
        if not html:
            raise ValueError(f"Missing html label for {sample_id}")
        if "<table" not in html.lower():
            raise ValueError(f"HTML label for {sample_id} does not contain a <table> tag")
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image does not exist for {sample_id}: {image_path}")

        with Image.open(image_path) as image:
            image.verify()

        cleaned.append(
            {
                "id": sample_id,
                "doc_id": doc_id,
                "image": image_path,
                "html": html.strip(),
                "notes": row.get("notes", ""),
            }
        )
    return cleaned


def grouped_split(rows: list[dict], train_size: float, seed: int) -> tuple[list[dict], list[dict], list[dict]]:
    indices = list(range(len(rows)))
    groups = [row["doc_id"] for row in rows]

    first_split = GroupShuffleSplit(n_splits=1, train_size=train_size, random_state=seed)
    train_idx, temp_idx = next(first_split.split(indices, groups=groups))

    train_rows = [rows[i] for i in train_idx]
    temp_rows = [rows[i] for i in temp_idx]

    if len(temp_rows) < 2:
        return train_rows, temp_rows, []

    temp_ids = list(range(len(temp_rows)))
    temp_groups = [row["doc_id"] for row in temp_rows]
    second_split = GroupShuffleSplit(n_splits=1, train_size=0.5, random_state=seed + 1)
    val_subidx, test_subidx = next(second_split.split(temp_ids, groups=temp_groups))

    val_rows = [temp_rows[i] for i in val_subidx]
    test_rows = [temp_rows[i] for i in test_subidx]
    return train_rows, val_rows, test_rows


def to_conversation(sample: dict) -> dict:
    return {
        "messages": [
            {
                "role": "system",
                "content": [{"type": "text", "text": SYSTEM_PROMPT}],
            },
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": sample["image"]},
                    {"type": "text", "text": USER_PROMPT},
                ],
            },
            {
                "role": "assistant",
                "content": [{"type": "text", "text": sample["html"]}],
            },
        ],
        "images": [sample["image"]],
        "id": sample["id"],
        "doc_id": sample["doc_id"],
        "label_html": sample["html"],
        "notes": sample["notes"],
    }


def build_dataset(rows: list[dict], train_size: float, seed: int) -> DatasetDict:
    train_rows, val_rows, test_rows = grouped_split(rows, train_size=train_size, seed=seed)
    return DatasetDict(
        {
            "train": Dataset.from_list([to_conversation(row) for row in train_rows]),
            "validation": Dataset.from_list([to_conversation(row) for row in val_rows]),
            "test": Dataset.from_list([to_conversation(row) for row in test_rows]),
        }
    )


def main() -> None:
    args = parse_args()

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for this training script")

    set_seed(args.seed)

    rows = load_rows(Path(args.data_jsonl), args.max_samples)
    rows = validate_rows(rows)
    dataset = build_dataset(rows, train_size=args.train_size, seed=args.seed)

    print(f"Loaded {len(rows)} total samples")
    print(
        f"Train={len(dataset['train'])} Validation={len(dataset['validation'])} Test={len(dataset['test'])}"
    )

    supports_bf16 = torch.cuda.get_device_capability(0)[0] >= 8
    dtype = torch.bfloat16 if supports_bf16 else torch.float16

    processor = AutoProcessor.from_pretrained(args.processor_id)
    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=dtype,
    )
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        args.model_id,
        torch_dtype=dtype,
        device_map="auto",
        quantization_config=quant_config,
    )

    peft_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        bias="none",
        target_modules=args.target_modules,
        task_type="CAUSAL_LM",
    )

    training_args = SFTConfig(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=args.grad_accum,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        learning_rate=args.learning_rate,
        logging_steps=args.logging_steps,
        eval_steps=args.eval_steps,
        save_steps=args.save_steps,
        eval_strategy="steps",
        save_strategy="steps",
        bf16=supports_bf16,
        fp16=not supports_bf16,
        warmup_ratio=0.05,
        max_grad_norm=0.3,
        lr_scheduler_type="cosine",
        optim="paged_adamw_8bit",
        remove_unused_columns=False,
        report_to="none",
        max_length=None if args.max_length == 0 else args.max_length,
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        peft_config=peft_config,
        processing_class=processor,
    )

    train_result = trainer.train()
    print(train_result)
    trainer.save_model(args.output_dir)
    processor.save_pretrained(args.output_dir)


if __name__ == "__main__":
    main()
