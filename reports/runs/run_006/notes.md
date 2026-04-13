# Latest

- run name: run_006
- date: 2026-04-13
- status: failed on first training step
- where it ran: Google Colab on T4
- primary goal for this run: get through model load and reach the first optimizer step

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

- live logging showed processor load, model download, quantized model materialization, trainer init, and training start
- smoke test got much further than previous runs

## Result Summary

- did training complete: no
- any OOM or instability: no OOM observed
- main log takeaway: the first train step failed with `NotImplementedError: "_amp_foreach_non_finite_check_and_unscale_cuda" not implemented for 'BFloat16'`
- qualitative output takeaway: this is now a precision/AMP compatibility issue, not a dataset/bootstrap issue

## Comparison To Past Runs

- better than: all prior runs because the model reached `Starting training...`
- worse than: none
- unchanged from: still a smoke-test infrastructure/debugging path

## Next Action

- force `fp16=True` and `bf16=False` in the smoke-test script
- keep everything else constant and rerun
