# Latest

- run name: run_008
- date: 2026-04-13
- status: failed on first training step
- where it ran: Google Colab on RTX PRO 6000 Blackwell / G4
- primary goal for this run: use BF16 automatically on a modern GPU and get past the first optimizer step

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

- precision mode switched back to BF16 automatically based on GPU capability
- model loading and trainer initialization succeeded again

## Result Summary

- did training complete: no
- any OOM or instability: no OOM observed
- main log takeaway: the first train step still failed with `NotImplementedError: "_amp_foreach_non_finite_check_and_unscale_cuda" not implemented for 'BFloat16'`
- qualitative output takeaway: the Trainer mixed-precision path is the issue, so the safest smoke-test fix is to disable Trainer AMP entirely

## Comparison To Past Runs

- better than: earlier bootstrap and formatting runs only
- worse than: none
- unchanged from: still blocked at the first optimizer step

## Next Action

- keep quantized model compute in `fp16`
- set `bf16=False` and `fp16=False` in `SFTConfig` to bypass Trainer AMP for the smoke test
