# Latest

- run name: run_003
- date: 2026-04-12
- status: failed during repo bootstrap
- where it ran: Google Colab on A100
- primary goal for this run: no-Drive smoke test with GPU-enabled runtime

## Arrangement

- dataset: intended mock dataset generated in Colab
- target format: HTML
- input type: smoke-test only
- model base: allenai/olmOCR-2-7B-1025
- fine-tuning method: intended QLoRA smoke test
- image sizing: not reached
- epochs: 1
- batch size: 1
- grad accumulation: 8
- LoRA target modules: not reached

## What Changed In This Run

- Colab runtime had GPU correctly enabled
- no-Drive mode still used HTTPS GitHub bootstrap
- repo access failed before mock asset generation

## Result Summary

- did training complete: no
- any OOM or instability: no
- main log takeaway: runtime was healthy, but repo access failed with `fatal: could not read Username for 'https://github.com'`
- qualitative output takeaway: the next fix should avoid `git clone` auth behavior in Colab and use archive download instead

## Comparison To Past Runs

- better than: `run_001` and `run_002` because GPU/runtime setup is now confirmed good
- worse than: none
- unchanged from: still blocked before actual asset generation and training

## Next Action

- replace `git clone` with archive download for `USE_DRIVE=False`
- keep token support for private repos
