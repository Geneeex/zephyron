# Verification evidence

This directory records the checks performed while preparing the initial public supporting-material snapshot on 23 September 2026. These are software, document-integrity and asset-portability checks; they are not physical rover experiments.

| Evidence | Scope |
|---|---|
| [Publication verification](publication_checks.json) | Fresh 45-check, 16-table and nine-figure-pair reproduction on the publication machine |
| [Import provenance](import_provenance.json) | Original ZIP identity and archived source manifest |
| [Repository readiness](repository_readiness.json) | Citation schema, local links, required files, manuscript identity and public-file inventory |
| [Root execution](../research/reports/verification_root.json) | 45 passing software checks and exact regeneration of 16 CSV files |
| [Different working directory](../research/reports/verification_other_cwd.json) | The same verification command invoked by its absolute path from outside the repository |
| [Figure regeneration](../research/reports/verification_figures.json) | Nine analytical PNG/SVG pairs generated from reproduced CSVs |
| [Rendering environment](../research/reports/render_environment.json) | Recorded dependencies and comparison of regenerated PNG pixels |
| [Blender portability](../research/blender/model_verification.json) | Fresh native-file reopen, packed assets, scene inventory and relative paths |
| [Manuscript integrity](../manuscript/artifact_verification.json) | Word and LaTeX source hashes, author order and content counts |

The preparation reports are a historical snapshot. To obtain fresh evidence after editing, run `python scripts/verify_repository.py --figures`. The [live GitHub Actions page](https://github.com/Geneeex/zephyron/actions/workflows/verify.yml) records hosted verification separately.

The root [file manifest](../SUPPORTING_FILES_MANIFEST.json) records every distributed file except itself. Check the current published snapshot with:

```sh
python scripts/check_file_manifest.py
```

This command verifies file sizes and SHA-256 checksums. It does not reject extra files, and expected differences after intentional edits are not evidence of scientific errors. The original handoff manifest is preserved as [source_archive_manifest.json](source_archive_manifest.json). The root manifest records the current reviewed publication files. For intentional updates, stage the changed files and run `python scripts/check_file_manifest.py --write`, then run the checker and commit the updated manifest. The `.gitattributes` rules preserve original line endings so checksums and historical research provenance remain meaningful.
