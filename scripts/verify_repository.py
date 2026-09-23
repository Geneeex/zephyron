#!/usr/bin/env python3
"""Verify software fixtures and regenerate analytical tables without hardware."""
from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import importlib.metadata
import importlib.util
import io
import json
import platform
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
EXPECTED = {
    "energy_duty_sweep.csv", "energy_mission_duty_limits.csv",
    "pv_irradiance_temperature.csv", "solar_recharge_lower_bound.csv",
    "grade_load.csv", "wheel_diameter_speed.csv", "odometry_mismatch_paths.csv",
    "gm_counting_time.csv", "gm_background_scenario.csv", "tds_fullscale_spec.csv",
    "tds_partial_uncertainty.csv", "vision_latency_scenarios.csv",
    "zero_miss_confidence.csv", "arm_torque_budget.csv",
    "arm_unconstrained_workspace.csv", "baseline_parameters.csv",
}
sys.path[:0] = [str(RESEARCH), str(RESEARCH / "ml")]
from build_engineering_analysis import generate  # noqa: E402


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def safe_text(value):
    """Keep generated reports free of private filesystem locations."""
    value = str(value)
    replacements = [(str(ROOT), "<repository>"),
                    (str(Path(tempfile.gettempdir())), "<temporary-directory>"),
                    (sys.prefix, "<python-environment>")]
    for source, replacement in replacements:
        value = value.replace(source, replacement)
        value = value.replace(source.replace("\\", "/"), replacement)
    return value


class RecordedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.records.append({"test": test.id(), "status": "PASS"})

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.records.append({"test": test.id(), "status": "FAIL",
                             "details": safe_text(self._exc_info_to_string(err, test))})

    def addError(self, test, err):
        super().addError(test, err)
        self.records.append({"test": test.id(), "status": "ERROR",
                             "details": safe_text(self._exc_info_to_string(err, test))})


def run_suite(name, source, expected_count):
    spec = importlib.util.spec_from_file_location(name, source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
        result = unittest.TextTestRunner(stream=stream, verbosity=2,
                                        resultclass=RecordedResult).run(suite)
    passed = result.wasSuccessful() and result.testsRun == expected_count
    return {"status": "PASS" if passed else "FAIL", "test_count": result.testsRun,
            "expected_test_count": expected_count, "failures": len(result.failures),
            "errors": len(result.errors), "tests": result.records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--figures", action="store_true",
                        help="also regenerate nine PNG/SVG figure pairs under build/reproduced")
    args = parser.parse_args()
    report = {
        "scope": "Analytical scenario and software regression checks only; no physical tests, detector training, model accuracy benchmarks, acquired sensor observations, or safety certification.",
        "environment": {"python": platform.python_version(),
                        "implementation": platform.python_implementation(),
                        "operating_system": platform.system(),
                        "machine": platform.machine()},
        "suites": {}, "datasets": [],
    }
    report["suites"]["engineering"] = run_suite(
        "engineering_checks", RESEARCH / "test_engineering_reproduction.py", 12)
    report["suites"]["ml_primitives"] = run_suite(
        "ml_primitive_checks", RESEARCH / "ml/test_validation_primitives.py", 33)
    with tempfile.TemporaryDirectory(prefix="zephyron-reproduction-") as temporary:
        regenerated = Path(temporary) / "analysis"
        baseline = json.loads((RESEARCH / "new_design_baseline.json").read_text(encoding="utf-8-sig"))
        scenarios = json.loads((RESEARCH / "engineering_scenarios.json").read_text(encoding="utf-8-sig"))
        generate(baseline, scenarios, regenerated)
        committed_names = {p.name for p in (RESEARCH / "analysis").glob("*.csv")}
        regenerated_names = {p.name for p in regenerated.glob("*.csv")}
        report["dataset_inventory_matches"] = committed_names == regenerated_names == EXPECTED
        for name in sorted(EXPECTED):
            original = RESEARCH / "analysis" / name
            actual = regenerated / name
            exists = original.exists() and actual.exists()
            item = {"path": "research/analysis/" + name,
                    "status": "PASS" if exists and original.read_bytes() == actual.read_bytes() else "FAIL"}
            if exists:
                with actual.open(encoding="utf-8", newline="") as handle:
                    rows = list(csv.reader(handle))
                item.update({"rows": len(rows) - 1, "columns": len(rows[0]),
                             "committed_sha256": digest(original),
                             "regenerated_sha256": digest(actual)})
            report["datasets"].append(item)
        summary = "analytical_summary.json"
        report["summary_identical"] = ((RESEARCH / "analysis" / summary).read_bytes()
                                        == (regenerated / summary).read_bytes())
        original_provenance = json.loads((RESEARCH / "analysis/analysis_provenance.json").read_text(encoding="utf-8"))
        new_provenance = json.loads((regenerated / "analysis_provenance.json").read_text(encoding="utf-8"))
        report["input_snapshots_identical"] = all(
            original_provenance[key] == new_provenance[key]
            for key in ("baseline_snapshot", "scenario_registry_snapshot", "derived_parameters", "input_snapshot_hashes"))
        report["figure_regeneration"] = {"status": "NOT_REQUESTED"}
        if args.figures:
            target = ROOT / "build/reproduced"
            shutil.copytree(regenerated, target / "analysis", dirs_exist_ok=True)
            result = subprocess.run(
                [sys.executable, str(RESEARCH / "build_engineering_figures.py"),
                 "--data", str(target / "analysis"), "--output", str(target / "figures")],
                capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT)
            expected_stems = {p.stem for p in (RESEARCH / "figures").glob("ENG_*.png")}
            outputs = [target / "figures" / (stem + suffix)
                       for stem in sorted(expected_stems) for suffix in (".png", ".svg")]
            passed = result.returncode == 0 and len(expected_stems) == 9 and all(
                p.exists() and p.stat().st_size > 0 for p in outputs)
            report["figure_regeneration"] = {
                "status": "PASS" if passed else "FAIL", "expected_pairs": 9,
                "outputs": [{"path": p.relative_to(ROOT).as_posix(), "sha256": digest(p)}
                            for p in outputs if p.exists()],
                "console": safe_text(result.stdout + result.stderr),
                "comparison": "All nine figure pairs generated from reproduced data; visual files are not required to be byte-identical across rendering environments.",
            }
            for package in ("numpy", "matplotlib"):
                try:
                    report["environment"][package] = importlib.metadata.version(package)
                except importlib.metadata.PackageNotFoundError:
                    report["environment"][package] = "not installed"
    tracked_inputs = [RESEARCH / name for name in (
        "engineering_models.py", "build_engineering_analysis.py", "build_engineering_figures.py",
        "test_engineering_reproduction.py", "new_design_baseline.json", "engineering_scenarios.json",
        "engineering_caption_text.json", "ml_methods_revision.md")]
    tracked_inputs += list((RESEARCH / "ml").glob("*.py")) + [Path(__file__)]
    report["source_sha256"] = {p.relative_to(ROOT).as_posix(): digest(p)
                               for p in sorted(tracked_inputs)}
    report["test_count"] = sum(suite["test_count"] for suite in report["suites"].values())
    passed = (all(suite["status"] == "PASS" for suite in report["suites"].values())
              and report["dataset_inventory_matches"] and report["summary_identical"]
              and report["input_snapshots_identical"]
              and all(item["status"] == "PASS" for item in report["datasets"])
              and report["figure_regeneration"]["status"] in ("PASS", "NOT_REQUESTED"))
    report["status"] = "PASS" if passed else "FAIL"
    output = ROOT / "build/reports/verification_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{report['status']}: {report['test_count']} software checks; "
          f"{sum(item['status'] == 'PASS' for item in report['datasets'])}/16 CSVs byte-identical.")
    print("Report: build/reports/verification_report.json")
    if args.figures:
        print("Figure regeneration: " + report["figure_regeneration"]["status"])
    if not passed:
        print("Read the report for failures. These checks do not establish physical rover performance.")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
