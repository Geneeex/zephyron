# Contributing

Changes should keep the link between a scientific statement, its assumptions and its supporting evidence explicit.

For an analytical change, edit a copy of the baseline or scenario registry, describe the reason, run `python scripts/verify_repository.py`, and regenerate affected tables and figures. A failing comparison against the committed baseline is expected when assumptions change; explain the change and review the new values before updating reference data. Do not weaken comparisons just to obtain a passing result.

For code changes, add or adjust a check that addresses a real failure mode. Include the input, expected behavior and result in the pull request. The numerical verifier is independent of hardware and cannot certify collision avoidance, payload capacity or sensor accuracy.

For physical tests, supply the apparatus, calibration records, component identifiers, units, timestamps, environmental conditions and independent trial definition alongside raw observations. Label acquired measurements separately from calculation outputs and simulated data. Preserve failed runs and exclusions with reasons.

For perception studies, document dataset provenance, consent where applicable, dependency groups, fixed train/validation/calibration/test partitions, model version, hyperparameters and held-out evaluation. Do not describe the existing fixture tests as model accuracy results.

For manuscript or artwork changes, retain figure numbers, source credits, license statements and the author order. Update both editable manuscript formats when the scientific content changes. Larger Canva exports must come from the native Canva master; upscaling a preview does not supply new detail.

Respect the scope of [LICENSE](LICENSE), [the documentation license](docs/LICENSING.md) and [third-party notices](THIRD_PARTY_NOTICES.md). Do not add access tokens, expiring download links, downloaded whole papers, local environment folders or private personal records.
