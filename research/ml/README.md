# Reproducible ML-method support code

This directory implements data-handling and evaluation primitives for a proposed detector pipeline. It contains no detector weights, training set, acquired timestamps or measured sensor data. The detector architectures and sensor regressor in the manuscript are proposed experiments.

Run from this directory with Python 3.10 or newer:

    python listing1_freshness.py
    python listing2_matching.py
    python test_validation_primitives.py

No packages beyond the Python standard library are required. Tests write `build/reports/ml_code_checks.json` relative to the repository root.

`validation_primitives.py` supplies finite positive-area xyxy IoU, class-aware one-to-one matching, explicit undefined metric denominators, bounded frame-age admission and stable group hashing. Boxes use continuous coordinates with width x2 - x1, without inclusive-pixel +1 arithmetic. The matcher is a single-image threshold diagnostic for ordinary boxes; use the pinned official COCO evaluator for publication AP, crowd/ignore semantics and area ranges. Sequence/session and displayed-image identity are caller inputs to the admission gate; the function does not synchronize clocks or control rover motion.

`group_partition` hashes a previously defined dependency group. It does not detect duplicate images or infer related sites. Selected split proportions are 55/15/15/15 for train/validation/calibration/test. Hashing is order- and append-invariant but can create empty or imbalanced partitions. Report them and acquire sufficient independent groups; do not retry seeds to improve a test result. `split_manifest` rejects repeated frame identifiers.

The fixture assertions verify arithmetic and failure handling only. They do not establish learned accuracy, runtime suitability, collision avoidance or calibrated sensor performance.
