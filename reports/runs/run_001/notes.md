# Latest

- run name: run_001
- date: 2026-04-12
- status: failed before training started
- where it ran: Google Colab on T4
- primary goal for this run: initial notebook smoke test

## Arrangement

- dataset: unresolved because the configured Drive project path was missing
- target format: HTML
- input type: intended smoke test
- model base: allenai/olmOCR-2-7B-1025
- fine-tuning method: intended QLoRA
- image sizing: not reached
- epochs: 1
- batch size: 1
- grad accumulation: 8
- LoRA target modules: not reached

## What Changed In This Run

- first Colab execution of the original notebook
- notebook output was committed directly instead of writing a structured run report

## Result Summary

- did training complete: no
- any OOM or instability: no OOM observed, failure happened earlier
- main log takeaway: `PROJECT_DIR` did not exist, copy to `/content/finetune-test` failed, and the training script path was therefore missing
- qualitative output takeaway: this run is only useful as a setup failure reference

## Comparison To Past Runs

- better than: none
- worse than: none
- unchanged from: none

## Next Action

- use the cleaned notebook workflow that writes reports under `reports/runs/`
- verify `PROJECT_DIR` and `DATA_JSONL` exist before starting training
