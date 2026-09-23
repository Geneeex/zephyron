# Reproducing the analytical supplement

The repository supplies deterministic analytical scenarios and software fixtures. It contains no acquired rover test logs, trained detector weights, fitted sensor regressor, field accuracy measurements, or experimental endurance observations. Reproducing a table verifies the implementation of the stated model, not the performance of the physical prototype.

## Quick start

Use Python 3.12. The default verification uses only the Python standard library and works offline:

```sh
python scripts/verify_repository.py
```

Expected successful output: **45 software checks; 16/16 CSVs byte-identical**. The machine-readable report is written to `build/reports/verification_report.json`. The checks comprise 12 engineering regressions and 33 ML evaluation/data-handling fixtures. All committed calculation tables remain unchanged. The runner generates its comparison tables in a temporary directory and removes that directory afterward.

The runner resolves its inputs relative to its own file, so it also works when invoked from another directory:

```sh
python /path/to/zephyron-research/scripts/verify_repository.py
```

On Windows, quote a path that contains spaces. No `PYTHONPATH` setting, private dependency directory, local drive mapping, or environment secret is required.

## Regenerate the nine analytical figure pairs

Install the optional plotting dependencies into an ordinary virtual environment:

```sh
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/verify_repository.py --figures
```

This additionally creates `build/reproduced/analysis/` and `build/reproduced/figures/`, with nine PNG/SVG figure pairs and their captions. It does not overwrite committed figures. The pinned rendering dependencies are NumPy 2.5.3 and Matplotlib 3.11.2; these require Python 3.12 or newer. Figure metadata such as timestamps, font resolution and SVG identifiers can vary by environment, so the verifier checks successful production of all expected outputs rather than claiming identical image bytes. The 16 numerical CSVs are compared byte for byte.

The committed baseline was verified on CPython 3.12.14, Windows AMD64. The code is path-portable. Floating-point transcendental functions can differ in their last bits between operating-system math libraries, so byte-level CSV parity is only established for the recorded environment. A discrepancy on another platform is reported as a failure for investigation; it is not silently rounded away. The workflow uses Windows and Python 3.12 for the same reason.

## Run or vary individual calculations

```sh
python research/build_engineering_analysis.py --output build/custom-analysis
python research/build_engineering_figures.py --data build/custom-analysis --output build/custom-figures
```

The analysis generator also accepts `--baseline PATH` and `--scenarios PATH`. Make copies of `research/new_design_baseline.json` and `research/engineering_scenarios.json`, edit those copies, and pass the paths explicitly. Derived geometry must remain consistent: tire-footprint length equals wheelbase plus wheel diameter, tire-footprint width equals track plus tread, and gross model mass equals dry target plus chassis payload allocation. The generator rejects inconsistent combinations.

Each regeneration writes an analytical summary and provenance with the input snapshots, input hashes, generator hashes and dataset hashes. When code changes, the generator hash is expected to change. The committed `analysis_provenance.json` records the original analytical generation; the public verifier separately records the current public source hashes. Use the data dictionary and calculation notes to interpret outputs before changing inputs.

## Public-source adaptations

The mathematical functions, baseline choices, grids, CSV values and ML fixtures were retained. The copied plotter was changed to use installed packages, accept explicit input/output directories, emit relative figure filenames, and place its default cache and outputs under `build/`. The engineering test temporary directory uses the system temporary location. The standalone ML test report now goes under `build/reports/`. Private workspace helpers and private QA logs are excluded.

No detector inference is performed by these commands. `research/ml_methods_revision.md` describes proposed training and evaluation methods; the two runnable manuscript listings are checked against their exact fenced source text. The supplied box matcher is a threshold diagnostic for ordinary boxes, not an implementation of COCO AP.

## Related files

- [Calculations and assumptions](CALCULATIONS.md)
- [CSV data dictionary](DATA_DICTIONARY.md)
- [Test scope and recorded execution](TESTING.md)
- [ML primitive documentation](../research/ml/README.md)

The editable manuscript, native 3D scenes and Canva diagram provenance accompany this supplement, but they are not rebuilt by the numerical verifier. Follow their own source documentation for visual editing. No PDFs are required or produced by the numerical verification commands.
