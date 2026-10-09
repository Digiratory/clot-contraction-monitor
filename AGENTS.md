# AGENTS.md

## Layout

- The app is a single Poetry package at `clot-contraction-monitor-app/` (src layout, Python >= 3.8): `clot_contraction_monitor` with subpackages `app/` (Tkinter GUI, entry `app/main.py`), `processing/` (segmentation pipeline, `ProcessingSession`), `io/`, `annotators/`, `analysis/`, and `assets/` (ONNX models).
- `notebooks/` is a separate workflow: LitUNet training (PyTorch Lightning + MONAI). Those deps are NOT in `pyproject.toml` — notebooks need their own environment. Export models with `python notebooks/export_model.py --checkpoint_path <ckpt> --batch_size <40|96>`; exported ONNX files go into the app's `src/clot_contraction_monitor/assets/`.

## Commands

- Install: `poetry install` inside `clot-contraction-monitor-app/` (or `pip install -e clot-contraction-monitor-app`). No lockfile is committed.
- Run GUI: `clot-contraction-monitor-app` (Poetry script → `clot_contraction_monitor.app.main:main`).
- Headless: `... --headless --input-folder <folder of frames> [--output-csv results.csv]`. `--batch` (requires `--headless`) processes each subfolder and ignores `--output-csv`, writing `<subfolder>_results.csv` into the input folder.
- Tests: `unittest`, not pytest. From repo root: `python tests/run_tests.py` or `python -m unittest discover -s tests`. Tests import `clot_contraction_monitor` directly, and `run_tests.py` does NOT add the src dir to `sys.path` — install the package first or set `PYTHONPATH=clot-contraction-monitor-app/src`.
- Do not trust root `.env`: its `PYTHONPATH=./cell-contraction-monitor-app/src` has a typo ("cell" ≠ "clot") and points nowhere.
- Format/lint: pre-commit (black + isort with black profile + hygiene hooks): `pre-commit install`, `pre-commit run --all-files`.
- Build exe from repo root: `pyinstaller .\clot-contraction-monitor-app\clot-contraction-monitor.exe.spec` (PowerShell syntax; spec bundles onnxruntime DLLs and `assets/*.onnx`).

## Gotchas

- Conventional Commits 1.0.0 are REQUIRED (`contribution.md`): `feat|fix|refactor|docs(scope): ...`.
- Per-frame segmentation persists as gzip JSON sidecars `<frame>.annotation.json.gz` next to each image. Processing reuses valid sidecars (shown as "cached" in headless output) — delete them to force reprocessing after model/algorithm changes. Sidecars carry a version checked by `check_annotation_version`; bump it when changing the annotation format.
- ONNX models are chosen by batch size and only `40`/`96` are supported (`ValueError` otherwise); they correspond to the supported culture-plate formats.
- Windows-first codebase: OpenVINO helper libs are prepended to `sys.path` only on Windows/Python >= 3.9 (best-effort), and image I/O goes through `io.utils.read_image`/`write_image` (`np.fromfile` + `cv2.imdecode`, handles non-ASCII paths on Windows) — prefer these over `cv2.imread`/`cv2.imwrite`.
