"""Check the SHA-256 snapshot, or explicitly refresh it from Git-tracked files."""
from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys

MANIFEST_NAME = "SUPPORTING_FILES_MANIFEST.json"


def checked_path(root: Path, value: str) -> tuple[str, Path]:
    if not isinstance(value, str) or not value:
        raise ValueError(f"Unsafe manifest path: {value!r}")
    relative = PurePosixPath(value)
    if relative.is_absolute() or ".." in relative.parts or ":" in value or "\\" in value:
        raise ValueError(f"Unsafe manifest path: {value}")
    path = root.joinpath(*relative.parts)
    if not path.resolve().is_relative_to(root) or not path.is_file():
        raise ValueError(f"Missing file or path outside repository: {relative}")
    current = path
    while current != root:
        if current.is_symlink() or current.is_junction():
            raise ValueError(f"Symlink or junction is not a regular snapshot file: {relative}")
        current = current.parent
    return relative.as_posix(), path


def write_manifest(root: Path) -> int:
    try:
        top = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            capture_output=True, check=True)
        if Path(top.stdout.decode("utf-8").strip()).resolve() != root:
            raise ValueError("The repository folder must be a Git repository root.")
        tracked = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError) as error:
        raise ValueError("Writing the manifest requires Git and an initialized repository.") from error
    entries = []
    seen = set()
    for value in sorted(tracked.stdout.decode("utf-8").split("\0")):
        if not value or value == MANIFEST_NAME:
            continue
        relative, path = checked_path(root, value)
        if relative in seen:
            raise ValueError(f"Duplicate Git entry; resolve index conflicts first: {relative}")
        seen.add(relative)
        content = path.read_bytes()
        entries.append({"path": relative, "bytes": len(content),
                        "sha256": hashlib.sha256(content).hexdigest()})
    if not entries:
        raise ValueError("No tracked files to include; stage the reviewed snapshot with Git first.")
    manifest = {
        "snapshot_date": date.today().isoformat(),
        "scope": "Reviewed Git-tracked publication snapshot, including staged additions; "
                 "excludes this manifest and untracked files, including ignored build outputs. "
                 "Hashes and sizes describe exact file bytes without text normalization.",
        "algorithm": "SHA-256",
        "file_count": len(entries),
        "files": entries,
    }
    target = root / MANIFEST_NAME
    if target.is_symlink() or target.is_junction():
        raise ValueError("Refusing to overwrite a symlink or junction manifest.")
    target.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"WROTE: {len(entries)} tracked files to {MANIFEST_NAME}.")
    return 0


def check_manifest(root: Path) -> int:
    manifest = json.loads((root / MANIFEST_NAME).read_text(encoding="utf-8"))
    failures = []
    entries = manifest["files"]
    seen = set()
    for entry in entries:
        try:
            relative, path = checked_path(root, entry["path"])
        except ValueError as error:
            failures.append(str(error))
            continue
        if relative in seen:
            failures.append(f"Duplicate manifest entry: {relative}")
            continue
        seen.add(relative)
        if path.stat().st_size != entry["bytes"]:
            failures.append(f"Size differs: {relative}")
        with path.open("rb") as handle:
            actual_hash = hashlib.file_digest(handle, "sha256").hexdigest()
        if actual_hash != entry["sha256"]:
            failures.append(f"SHA-256 differs: {relative}")
    if failures:
        print("FAIL: original snapshot differs")
        print("\n".join(failures))
        return 1
    print(f"PASS: {len(entries)} distributed files match their size and SHA-256 checksums.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true",
                        help="replace the manifest using reviewed Git-tracked/staged files")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        return write_manifest(root) if args.write else check_manifest(root)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"FAIL: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
