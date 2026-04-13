# Latest

- run name: run_007
- date: 2026-04-13
- status: failed on first training step
- where it ran: Google Colab on RTX PRO 6000 Blackwell / G4
- primary goal for this run: get past the first optimizer step with FP16 forced

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

- live logging showed full bootstrap and model-load progress
- FP16 was forced in the smoke-test script
- the run still failed with a BF16 unscale error on a BF16-capable GPU

## Result Summary

- did training complete: no
- any OOM or instability: no OOM observed
- main log takeaway: `NotImplementedError: "_amp_foreach_non_finite_check_and_unscale_cuda" not implemented for 'BFloat16'`
- qualitative output takeaway: the precision mode is inconsistent for this GPU; on BF16-capable GPUs we should use BF16 mode end-to-end instead of forcing FP16

## Comparison To Past Runs

- better than: previous runs in observability only; we now know the exact precision mismatch
- worse than: none
- unchanged from: still blocked at the first train step

## Next Action

- use BF16 mode on capability `>= 8`
- keep FP16 only for older GPUs like T4
