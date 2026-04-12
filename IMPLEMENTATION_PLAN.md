# olmOCR Datasheet Table Fine-Tuning Plan

## Goal

Fine-tune `allenai/olmOCR-2-7B-1025` for a narrow OCR task: datasheet tables with hard structure failures such as merged headers, `rowspan` / `colspan`, multi-line cells, footnotes, rotated tables, and vendor-specific layouts.

This plan assumes a first-pass training target on a `12 GB` GPU such as an `RTX A2000`, so the scope is intentionally small and adapter-based.

## Constraints

- Use `allenai/olmOCR-2-7B-1025` `BF16` as the fine-tuning base.
- Do not fine-tune a `Q8` inference artifact.
- Keep the existing `olmOCR` rendering and prompting pipeline intact for baseline compatibility.
- Start with `SFT`, not `RL` / `GRPO`.
- Default to `QLoRA 4-bit NF4`.
- Treat the first run as a narrow adaptation, not a general OCR improvement effort.

## First Deliverable

Produce a smoke-tested adapter that improves table structure extraction on a small unseen eval set of datasheet tables.

Success means at least one of the following improves over baseline:

- exact table structure match
- `rowspan` / `colspan` correctness
- row and column count consistency
- numeric fidelity for units, signs, and decimals
- output validity for `HTML` or `JSON`

## Recommended Task Shape

Start with one failure class only:

- merged-cell datasheet tables

Preferred first output format:

- `HTML` if the main problem is preserving structure exactly
- `JSON` if downstream tooling already expects normalized tables

Avoid markdown as the first target format because it cannot represent many merged-cell layouts cleanly.

## Dataset Plan

### First pass

- `100-300` hard examples
- prefer cropped table regions over full pages
- keep examples grouped by source document
- hold out unseen documents for validation and test

### Expansion pass

- `300-500` high-value examples if the smoke test shows improvement

### Required sample schema

Each row should include:

- `id`
- `doc_id`
- `image`
- `html` or `json`
- `notes`

### Labeling rules

- keep labels strict and consistent
- do not mix multiple target formats in one run
- reject examples with ambiguous gold structure
- preserve merged-cell structure in the label exactly

## Baseline Before Training

Run stock `olmOCR-2-7B-1025` using the normal `olmOCR` toolkit path before training anything.

Measure failures by bucket:

- merged headers
- row and column span errors
- multi-line cell flattening
- row split or row merge errors
- decimal, sign, and unit mistakes
- reading order mistakes
- invalid `HTML` / `JSON`

Do not compare on pages seen during training.

## Training Plan

### First-pass configuration

- base model: `allenai/olmOCR-2-7B-1025`
- method: `QLoRA`
- quantization: `4-bit NF4`
- batch size: `1`
- gradient accumulation: enabled
- gradient checkpointing: enabled
- image size: roughly `768-1024px` longest side for training
- output format: one strict format only

### LoRA scope

Start narrow:

- target modules: `q_proj`, `v_proj`
- freeze most of vision on the first pass

Expand only if the adapter is clearly too weak.

### Runtime strategy

- run a `1 epoch` smoke test first
- confirm VRAM stability before longer runs
- prefer short validation intervals
- save predictions for manual review, not just loss curves

## Evaluation Plan

Track results by error type, not average impressions.

Core metrics:

- exact structure match when possible
- predicted vs gold row count
- predicted vs gold cell count
- `rowspan` count match
- `colspan` count match
- valid `HTML` / `JSON`
- numeric fidelity checks on held-out samples

Manual review buckets:

- invented rows or cells
- dropped rows or headers
- span collapse
- footnote leakage into cells
- header and footer contamination
- ordering mistakes

## Known Risks

- Fine-tuning alone will not fix poor rendering or bad table localization.
- Full-page training is heavier and may hide whether crop-level learning works.
- Long target outputs slow training and increase memory pressure.
- A small dataset can help a narrow vendor or table family but will not create a general OCR upgrade.
- Random page-level splits can leak document structure across train and eval.

## Colab Handoff

Use this path when you want quick GPU access without provisioning a VM.

### What to prepare

- a notebook runtime with `L4` or `A100` if available
- dataset path in Drive or notebook storage
- a small eval set of `20-30` hard unseen samples
- a train set of `100-300` labeled samples

### Working model

Because direct browser control is not the practical path here, the operating pattern should be:

1. You create or open the notebook.
2. You paste in the cells or scripts I provide.
3. You run them and send back logs, errors, and sample outputs.
4. I adjust the config and debug from those results.

### Colab details to capture

- GPU type
- available VRAM
- dataset location
- whether inputs are table crops or full pages
- target output format
- training logs and any out-of-memory errors

### If you want shell-style remote access from Colab

Possible but secondary:

- `tmate`
- `ngrok`
- `cloudflared`

This is more brittle than using a normal VM and should only be used if needed.

Note: Google Colab's FAQ explicitly says remote control workflows such as `SSH shells` are disallowed on free managed runtimes and may be terminated at any time. Treat Colab SSH as best-effort only.

## SSH Handoff

Use this path when you want stable repeated iteration on a remote GPU box.

### Recommended setup

- provision a fresh Linux GPU machine
- create a non-admin user for this work
- place the repo and dataset in a dedicated directory
- prefer Ubuntu with CUDA already working

### Information needed for SSH testing

- host or IP
- port
- username
- auth method: password or SSH key
- GPU model and VRAM
- working directory
- dataset directory
- internet access rules on the box

### Why SSH is cleaner than Colab

- stable shell access
- easier dependency management
- simpler repeated experiments
- easier logging and checkpoint recovery

## Immediate Next Steps

1. Create the first dataset manifest with the required schema.
2. Build a baseline eval set from unseen datasheets.
3. Run stock `olmOCR` on that eval set and record failure buckets.
4. Start a `QLoRA` smoke test on cropped tables only.
5. Compare tuned outputs against the baseline before expanding scope.
6. Use `notebooks/olmocr_table_html_colab.ipynb` for a first Colab smoke test.

## Questions To Resolve Later

- final target format: `HTML` or `JSON`
- table crops or full pages for the first milestone
- exact metric that matters most in production
- whether training stays local on `A2000` or moves to `Colab` / remote GPU
- whether the main bottleneck is the model or upstream table detection and cropping
