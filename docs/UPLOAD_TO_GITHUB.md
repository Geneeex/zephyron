# Maintaining the Zephyron repository

The public repository is **[SABIKGIT/zephyron](https://github.com/SABIKGIT/zephyron)**. It accompanies **[arXiv:2609.25709](https://arxiv.org/abs/2609.25709)**.

## Prepare an update

```sh
git clone https://github.com/SABIKGIT/zephyron.git
cd zephyron
git switch -c research-update
```

Make the intended changes and follow [CONTRIBUTING.md](../CONTRIBUTING.md). Preserve the distinctions between design assumptions, analytical predictions, software fixtures and physical measurements.

Run the relevant checks from the repository root:

```sh
python -m pip install -r requirements.txt
python scripts/verify_repository.py --figures
```

This validates 45 software fixtures, checks all 16 analytical tables and regenerates nine figure pairs. Windows with Python 3.12 is the recorded environment; see [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## Review and update the distribution manifest

The `.gitattributes` rules preserve exact file bytes, including original line endings. The CSV and summary checks and historical provenance use those bytes. Do not normalize research files as an incidental formatting change.

After reviewing intentional changes, stage the files and regenerate the manifest from the reviewed Git file list:

```sh
git add .
python scripts/check_file_manifest.py --write
python scripts/check_file_manifest.py
git add SUPPORTING_FILES_MANIFEST.json
git diff --cached --stat
git commit -m "Update Zephyron research materials"
git push -u origin research-update
```

`--write` records files known to Git, excluding the manifest itself. Stage new files first. Generated `build/` outputs and environments stay excluded by `.gitignore`. Do not refresh checksums to hide unexplained changes.

Open a pull request to `main` and inspect [GitHub Actions](https://github.com/SABIKGIT/zephyron/actions/workflows/verify.yml). The workflow checks distribution integrity, software, tables and figure generation, then uploads verification outputs as a downloadable artifact.

## Archive and attribution

The original handoff checksums remain in [source_archive_manifest.json](../verification/source_archive_manifest.json); [import_provenance.json](../verification/import_provenance.json) identifies that ZIP. The root manifest describes the current published distribution.

Original code uses MIT and original content uses CC BY 4.0 within the scope of [LICENSING.md](LICENSING.md). Preserve all paper authors and source-specific third-party notices. The original delivery ZIP is a transport package and is not committed into the repository.

Use [RELEASE_NOTES.md](RELEASE_NOTES.md) as a starting point for future releases. No version tag or release is implied by this initial repository publication.
