#!/usr/bin/env python3

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "notebooks" / "olmocr_table_html_colab.ipynb"


def md_cell(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": text.splitlines(keepends=True),
    }


def code_cell(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": text.splitlines(keepends=True),
    }


def build_notebook() -> dict:
    cells = [
        md_cell(
            "# olmOCR Table HTML Fine-Tuning on Colab\n\n"
            "This notebook is set up for a GitHub-based feedback loop:\n\n"
            "1. Run a smoke test in Colab\n"
            "2. Save only lightweight run reports into the repo under `reports/runs/`\n"
            "3. Commit and push those report files to GitHub\n"
            "4. I can review the run directly from GitHub\n\n"
            "Heavy artifacts like checkpoints should stay outside git.\n\n"
            "Google Drive is optional. For cheap smoke tests, the notebook can clone the repo from GitHub and generate mock data directly inside Colab.\n\n"
            "At the beginning of each run, keep a note about:\n\n"
            "- where you are running it\n"
            "- what the latest run is\n"
            "- what arrangement you are testing\n"
            "- what happened in past runs"
        ),
        md_cell("## 1. Install dependencies\n\nThis cell installs only the missing packages we need for the smoke test. It avoids blanket upgrades because those can force a runtime restart and can pull in incompatible versions."),
        code_cell(
            "import importlib.util\n"
            "import subprocess\n"
            "import sys\n\n"
            "required = {\n"
            "    'trl': 'trl==1.1.0',\n"
            "    'bitsandbytes': 'bitsandbytes==0.49.2',\n"
            "    'qwen_vl_utils': 'qwen-vl-utils==0.0.14',\n"
            "}\n"
            "missing = [spec for module, spec in required.items() if importlib.util.find_spec(module) is None]\n"
            "if missing:\n"
            "    print('Installing missing packages:', missing)\n"
            "    subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing])\n"
            "else:\n"
            "    print('Required packages already present; skipping pip install.')"
        ),
        md_cell("## 2. Validate runtime\n\nFail early if this Colab session is not actually using CUDA-backed PyTorch."),
        code_cell(
            "import torch\n\n"
            "print('torch version:', torch.__version__)\n"
            "print('cuda available:', torch.cuda.is_available())\n"
            "print('torch cuda:', torch.version.cuda)\n\n"
            "if '+cpu' in torch.__version__ or not torch.cuda.is_available():\n"
            "    raise RuntimeError(\n"
            "        'This runtime is not GPU-ready for QLoRA. Restart the runtime once after installs, '\n"
            "        'make sure GPU is enabled, and rerun from the top.'\n"
            "    )"
        ),
        md_cell("## 3. Configure workflow mode\n\nUse `USE_DRIVE = False` for the cheapest smoke test path. That mode clones the repo from GitHub and can generate mock data directly in Colab."),
        code_cell(
            "USE_DRIVE = False\n"
            "USE_MOCK_DATA = True\n"
            "REPO_URL = 'https://github.com/yoelrc88/ocr-datasheet-qlora.git'\n"
            "GITHUB_TOKEN = ''  # optional for private repos\n"
            "DRIVE_PROJECT_DIR = '/content/drive/MyDrive/finetune-test'\n"
            "GITHUB_PROJECT_DIR = '/content/ocr-datasheet-qlora'\n"
            "RUN_NAME = 'run_001'\n"
            "LOCAL_WORKDIR = '/content/finetune-test'\n"
            "ARTIFACT_DIR = f'/content/artifacts/{RUN_NAME}'\n"
            "MAX_SAMPLES = 0\n"
            "EPOCHS = 1\n"
            "BATCH_SIZE = 1\n"
            "GRAD_ACCUM = 8\n"
            "LEARNING_RATE = 1e-4"
        ),
        md_cell("## 4. Optional: mount Google Drive\n\nRun this only if `USE_DRIVE = True`. Skip it for GitHub-only smoke tests."),
        code_cell(
            "if USE_DRIVE:\n"
            "    from google.colab import drive\n"
            "    drive.mount('/content/drive')\n"
            "else:\n"
            "    print('Skipping Drive mount; using GitHub/local mode.')"
        ),
        md_cell("## 5. Prepare the repo and dataset source\n\nIf the repo is private, set `GITHUB_TOKEN` above or use Drive mode. The error message here will include clone stderr so the failure is visible in the notebook."),
        code_cell(
            "import os\n"
            "import platform\n"
            "import subprocess\n"
            "from pathlib import Path\n\n"
            "if USE_DRIVE:\n"
            "    PROJECT_DIR = DRIVE_PROJECT_DIR\n"
            "else:\n"
            "    PROJECT_DIR = GITHUB_PROJECT_DIR\n\n"
            "if not USE_DRIVE:\n"
            "    clone_url = REPO_URL\n"
            "    if GITHUB_TOKEN and REPO_URL.startswith('https://'):\n"
            "        clone_url = REPO_URL.replace('https://', f'https://{GITHUB_TOKEN}@', 1)\n"
            "    subprocess.run(['rm', '-rf', GITHUB_PROJECT_DIR], check=False)\n"
            "    clone = subprocess.run(['git', 'clone', clone_url, GITHUB_PROJECT_DIR], capture_output=True, text=True)\n"
            "    if clone.returncode != 0:\n"
            "        raise RuntimeError(\n"
            "            'Git clone failed. If the repo is private, set GITHUB_TOKEN or switch to USE_DRIVE=True. '\n"
            "            f'STDERR: {clone.stderr.strip()}'\n"
            "        )\n"
            "    print(f'Cloned repo into {GITHUB_PROJECT_DIR}')\n\n"
            "if USE_MOCK_DATA:\n"
            "    subprocess.run(['python', f'{PROJECT_DIR}/scripts/generate_mock_smoke_test_data.py'], check=True)\n"
            "    DATA_JSONL = f'{PROJECT_DIR}/mock_smoke_test/mock_table_html.jsonl'\n"
            "else:\n"
            "    DATA_JSONL = f'{PROJECT_DIR}/examples/table_html_dataset.example.jsonl'\n\n"
            "REPORTS_DIR = f'{PROJECT_DIR}/reports/runs'\n"
            "REPORT_DIR = f'{REPORTS_DIR}/{RUN_NAME}'\n"
            "Path(REPORT_DIR).mkdir(parents=True, exist_ok=True)\n"
            "Path(ARTIFACT_DIR).mkdir(parents=True, exist_ok=True)\n\n"
            "gpu_info = subprocess.run(['nvidia-smi'], capture_output=True, text=True)\n"
            "runtime_info = [\n"
            "    f'platform={platform.platform()}',\n"
            "    f'python={platform.python_version()}',\n"
            "    f'use_drive={USE_DRIVE}',\n"
            "    f'use_mock_data={USE_MOCK_DATA}',\n"
            "    f'project_dir={PROJECT_DIR}',\n"
            "    f'data_jsonl={DATA_JSONL}',\n"
            "    f'run_name={RUN_NAME}',\n"
            "    f'report_dir={REPORT_DIR}',\n"
            "    f'artifact_dir={ARTIFACT_DIR}',\n"
            "    '',\n"
            "    'nvidia-smi:',\n"
            "    gpu_info.stdout if gpu_info.stdout else gpu_info.stderr,\n"
            "]\n"
            "Path(f'{REPORT_DIR}/runtime_info.txt').write_text('\\n'.join(runtime_info), encoding='utf-8')\n"
            "print(Path(f'{REPORT_DIR}/runtime_info.txt').read_text(encoding='utf-8'))"
        ),
        md_cell("## 6. Copy repo to local runtime for faster work\n\nThis keeps training and temp files off Drive while still writing the report folder back into the repo or cloned checkout."),
        code_cell(
            "!rm -rf \"$LOCAL_WORKDIR\"\n"
            "!cp -R \"$PROJECT_DIR\" \"$LOCAL_WORKDIR\"\n"
            "LOCAL_DATA_JSONL = DATA_JSONL.replace(PROJECT_DIR, LOCAL_WORKDIR)\n"
            "LOCAL_PROJECT_DIR = LOCAL_WORKDIR\n"
            "print('LOCAL_PROJECT_DIR =', LOCAL_PROJECT_DIR)\n"
            "print('LOCAL_DATA_JSONL =', LOCAL_DATA_JSONL)"
        ),
        md_cell("## 7. Run the smoke-test training job and capture the log"),
        code_cell(
            "train_cmd = [\n"
            "    'python',\n"
            "    f'{LOCAL_PROJECT_DIR}/scripts/train_table_html_lora.py',\n"
            "    '--data-jsonl', LOCAL_DATA_JSONL,\n"
            "    '--output-dir', ARTIFACT_DIR,\n"
            "    '--max-samples', str(MAX_SAMPLES),\n"
            "    '--epochs', str(EPOCHS),\n"
            "    '--batch-size', str(BATCH_SIZE),\n"
            "    '--grad-accum', str(GRAD_ACCUM),\n"
            "    '--learning-rate', str(LEARNING_RATE),\n"
            "]\n\n"
            "print('Running:', ' '.join(train_cmd))\n"
            "result = subprocess.run(train_cmd, capture_output=True, text=True)\n"
            "Path(f'{REPORT_DIR}/train.log').write_text(result.stdout + '\\n\\n[stderr]\\n' + result.stderr, encoding='utf-8')\n"
            "Path(f'{REPORT_DIR}/command.txt').write_text(' '.join(train_cmd), encoding='utf-8')\n"
            "print(result.stdout[-4000:])\n"
            "if result.returncode != 0:\n"
            "    print(result.stderr[-4000:])\n"
            "    raise RuntimeError(f'Training failed with return code {result.returncode}')"
        ),
        md_cell("## 8. Copy lightweight outputs into the repo report folder"),
        code_cell(
            "lightweight_files = [\n"
            "    'run_config.json',\n"
            "    'dataset_split_summary.json',\n"
            "]\n\n"
            "copied = []\n"
            "for name in lightweight_files:\n"
            "    src = Path(ARTIFACT_DIR) / name\n"
            "    if src.exists():\n"
            "        dst = Path(REPORT_DIR) / name\n"
            "        dst.write_text(src.read_text(encoding='utf-8'), encoding='utf-8')\n"
            "        copied.append(name)\n\n"
            "artifact_manifest = sorted(p.name for p in Path(ARTIFACT_DIR).glob('*'))\n"
            "Path(f'{REPORT_DIR}/artifact_manifest.txt').write_text('\\n'.join(artifact_manifest), encoding='utf-8')\n"
            "notes_template = '''# Latest\n\n"
            "- run name: {run_name}\n"
            "- date:\n"
            "- status: running\n"
            "- where it ran: Colab\n"
            "- primary goal for this run:\n\n"
            "## Arrangement\n\n"
            "- dataset:\n"
            "- target format: HTML\n"
            "- input type: cropped tables or full pages\n"
            "- model base: allenai/olmOCR-2-7B-1025\n"
            "- fine-tuning method: QLoRA\n"
            "- image sizing:\n"
            "- epochs: {epochs}\n"
            "- batch size: {batch_size}\n"
            "- grad accumulation: {grad_accum}\n"
            "- LoRA target modules:\n\n"
            "## What Changed In This Run\n\n"
            "- \n\n"
            "## Result Summary\n\n"
            "- did training complete:\n"
            "- any OOM or instability:\n"
            "- main log takeaway:\n"
            "- qualitative output takeaway:\n\n"
            "## Comparison To Past Runs\n\n"
            "- better than:\n"
            "- worse than:\n"
            "- unchanged from:\n\n"
            "## Next Action\n\n"
            "- \n"
            "'''.format(run_name=RUN_NAME, epochs=EPOCHS, batch_size=BATCH_SIZE, grad_accum=GRAD_ACCUM)\n"
            "Path(f'{REPORT_DIR}/notes.md').write_text(notes_template, encoding='utf-8')\n"
            "print('Copied:', copied)\n"
            "print('Report dir:', REPORT_DIR)\n"
            "print('Artifact manifest:')\n"
            "print(Path(f'{REPORT_DIR}/artifact_manifest.txt').read_text(encoding='utf-8'))"
        ),
        md_cell("## 9. Review the report files that should be committed"),
        code_cell("!ls -la \"$REPORT_DIR\""),
        md_cell(
            "## 10. GitHub handoff\n\n"
            "After the run:\n\n"
            "1. Update `notes.md` in the run folder with the latest status and a short comparison to past runs\n"
            "2. If you changed the experiment strategy, update `reports/EXPERIMENT_MATRIX.md`\n"
            "3. Commit only the new folder under `reports/runs/` and any small tracking-doc updates\n"
            "4. Push it to GitHub\n"
            "5. Send me the repo link or tell me the run folder name\n\n"
            "That gives me a stable place to review the run without SSH or notebook access."
        ),
        code_cell(
            "print('Suggested git commands:')\n"
            "print(f'git add reports/runs/{RUN_NAME}')\n"
            "print('git commit -m \"add results for ' + RUN_NAME + '\"')\n"
            "print('git push')"
        ),
    ]

    return {
        "cells": cells,
        "metadata": {
            "colab": {"provenance": []},
            "kernelspec": {"display_name": "Python 3", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 0,
    }


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(build_notebook(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
