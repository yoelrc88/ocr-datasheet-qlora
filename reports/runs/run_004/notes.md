# Latest

- run name: run_004
- date: 2026-04-12
- status: failed during first training batch
- where it ran: Google Colab on H100
- primary goal for this run: full no-Drive smoke test through the first train step

## Arrangement

- dataset: mock dataset generated in Colab
- target format: HTML
- input type: mocked table images
- model base: allenai/olmOCR-2-7B-1025
- fine-tuning method: QLoRA smoke test
- image sizing: default mock images
- epochs: 1
- batch size: 1
- grad accumulation: 8
- LoRA target modules: `q_proj`, `v_proj`

## What Changed In This Run

- repo bootstrap succeeded through archive download
- mock asset generation succeeded
- model load succeeded on GPU
- failure moved into the TRL/Qwen collator during the first batch

## Result Summary

- did training complete: no
- any OOM or instability: no OOM observed
- main log takeaway: `IndexError: index 1 is out of bounds for dimension 0 with size 1` inside `processing_qwen2_5_vl.py` while mapping image tokens
- qualitative output takeaway: sample formatting likely passed duplicate image references into the processor

## Comparison To Past Runs

- better than: `run_001`, `run_002`, and `run_003` because setup, download, mock data generation, and model load all worked
- worse than: none
- unchanged from: still a smoke-test path, not a quality evaluation run

## Next Action

- remove the extra top-level `images` field from training samples and rely on the image embedded inside `messages`
- rerun the same smoke test before changing any training hyperparameters
