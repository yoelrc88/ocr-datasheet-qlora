# Experiment Matrix

Use this file to decide what to try next and to keep multiple runs comparable.

## First Wave

| Run | Goal | Main Change | Hold Constant | Expected Signal |
| --- | --- | --- | --- | --- |
| `run_001` | smoke test | baseline QLoRA HTML setup | dataset, crop policy | confirms training works at all |
| `run_002` | structure fidelity | increase hard merged-cell examples | training config | better `rowspan` / `colspan` behavior |
| `run_003` | adapter strength | expand LoRA modules beyond `q_proj`, `v_proj` | same dataset | stronger structural learning |
| `run_004` | memory/speed tradeoff | reduce image size or max sample count | same task | more stable or faster training |

## Good Early Branches

1. Data branch
   - more merged-header failures
   - more row/column span examples
   - more multi-line cell examples
2. Adapter branch
   - `q_proj`, `v_proj`
   - `q_proj`, `k_proj`, `v_proj`, `o_proj`
3. Input branch
   - cropped tables only
   - slightly larger crops with caption/header context
4. Output branch
   - strict HTML
   - strict JSON if downstream needs it

## Rules For Faster Iteration

- change one main variable per run when possible
- keep a smoke-test run small
- write down exactly what changed before pushing results
- compare on unseen documents only
- do not commit checkpoints into git unless there is a clear reason
