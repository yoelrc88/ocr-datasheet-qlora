# Run Reports

This directory is for lightweight run outputs that are safe and useful to commit back to GitHub.

Do commit:

- `run_config.json`
- `dataset_split_summary.json`
- `runtime_info.txt`
- `train.log`
- `artifact_manifest.txt`
- `notes.md`
- small prediction samples if they are lightweight and non-sensitive

Do not commit:

- full model checkpoints
- adapter weights unless you explicitly want them in git
- large image datasets
- private or licensed source documents

Recommended layout:

```text
reports/
  README.md
  RUN_NOTES_TEMPLATE.md
  EXPERIMENT_MATRIX.md
  runs/
    run_001/
      runtime_info.txt
      run_config.json
      dataset_split_summary.json
      train.log
      artifact_manifest.txt
      notes.md
```

Suggested workflow:

1. Run `notebooks/olmocr_table_html_colab.ipynb` in Colab.
2. Let it write a new folder under `reports/runs/`.
3. Review the generated files.
4. Commit and push only the report folder back to GitHub.
5. I can then review the run directly from the GitHub repo.

Important:

- if you only save the executed notebook from Colab, only the `.ipynb` is guaranteed to appear on GitHub
- generated files under `reports/runs/` are not automatically synced to GitHub just because the notebook created them
- the notebook now prints the key run-report files into notebook output so that notebook-only saves are still reviewable

Use these helper files:

- `reports/RUN_NOTES_TEMPLATE.md`: what changed in this run, where it ran, latest outcome, and comparison to prior runs
- `reports/EXPERIMENT_MATRIX.md`: the set of variants to try in parallel or sequence
