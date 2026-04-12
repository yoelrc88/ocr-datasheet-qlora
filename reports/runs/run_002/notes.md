# Latest

- run name: run_002
- date: 2026-04-12
- status: failed before repo setup completed
- where it ran: Google Colab on T4
- primary goal for this run: no-Drive smoke test using GitHub clone

## Arrangement

- dataset: planned mock dataset generated inside Colab
- target format: HTML
- input type: synthetic smoke test only
- model base: allenai/olmOCR-2-7B-1025
- fine-tuning method: intended QLoRA smoke test
- image sizing: not reached
- epochs: 1
- batch size: 1
- grad accumulation: 8
- LoRA target modules: not reached

## What Changed In This Run

- switched from Drive mode to GitHub clone mode
- install cell upgraded several packages in-place
- runtime showed `torch 2.10.0+cpu` during dependency output

## Result Summary

- did training complete: no
- any OOM or instability: no OOM, failure happened before training
- main log takeaway: package installation forced a runtime restart condition and repo clone failed with git exit code `128`
- qualitative output takeaway: the notebook needs an early CUDA check and better clone/auth guidance

## Comparison To Past Runs

- better than: `run_001` because the failure is more specific and helped identify the next notebook fixes
- worse than: none
- unchanged from: still a setup-only failure, not a model-training result

## Next Action

- avoid blanket package upgrades in Colab
- fail early if PyTorch is CPU-only
- support private-repo clone guidance via `GITHUB_TOKEN` or `USE_DRIVE=True`
