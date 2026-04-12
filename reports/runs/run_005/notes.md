# Latest

- run name: run_005
- date: 2026-04-12
- status: failed during TRL dataset preparation
- where it ran: Google Colab on RTX PRO 6000 / G4
- primary goal for this run: verify that the smoke test reaches the first train batch with the previous VLM formatting fix

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

- archive bootstrap worked
- mock data generation worked
- previous duplicate-image issue moved forward into a new preparation-stage error

## Result Summary

- did training complete: no
- any OOM or instability: no OOM observed
- main log takeaway: `ValueError: Number of images provided (0) does not match number of image placeholders (1)` during `prepare_multimodal_messages`
- qualitative output takeaway: TRL wants the image supplied in a top-level vision column, not only inline in the message content

## Comparison To Past Runs

- better than: `run_004` because the failure is now more precise about the expected multimodal dataset contract
- worse than: none
- unchanged from: still a smoke-test formatting issue, not a model-quality issue

## Next Action

- keep the inline image placeholder in `messages`
- add a top-level `image` column for the single image sample
