#!/usr/bin/env python3
"""
Generate Artifact_Registry_v0.6.json with SHA256 hashes
of all specification-relevant artifacts per GOV-001 §4.

Includes:
- PSL snapshot
- Spec documents (Protocols/*.md and specs/dkp-ptl-reg/v0.6/)
- Source files (engine/src/*.py)
- Test vector files

Run from repo root: python scripts/generate_artifact_registry.py
"""
import hashlib
import json
import subprocess
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def get_git_commit() -> str:
    """Get current git commit hash, or 'unknown' if not in a git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(__file__).resolve().parent.parent,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def main():
    root = Path(__file__).resolve().parent.parent

    registry = OrderedDict()
    registry["protocol_version"] = "0.6.0"
    registry["constants_version"] = "0.6.0"
    registry["generated_by"] = "scripts/generate_artifact_registry.py"
    registry["generation_timestamp_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    registry["git_commit"] = get_git_commit()

    # PSL snapshot
    psl_path = root / "engine" / "src" / "psl_snapshot" / "PSL-2026-01-01.dat"
    registry["psl_snapshot"] = OrderedDict()
    registry["psl_snapshot"]["filename"] = "PSL-2026-01-01.dat"
    registry["psl_snapshot"]["sha256"] = sha256_file(str(psl_path))

    # Spec documents (GOV-001 §4)
    spec_dir = root / "Protocols"
    spec_files = sorted([
        f for f in spec_dir.glob("*.md")
        if not f.name.endswith(":Zone.Identifier")
    ])
    registry["spec_documents"] = OrderedDict()
    for sf in spec_files:
        rel = str(sf.relative_to(root))
        registry["spec_documents"][rel] = sha256_file(str(sf))

    # Canonical spec bundle (normalized location)
    canonical_spec_dir = root / "specs" / "dkp-ptl-reg" / "v0.6"
    if canonical_spec_dir.exists():
        canonical_files = sorted([
            f for f in canonical_spec_dir.glob("*.md")
        ])
        registry["canonical_specs"] = OrderedDict()
        for sf in canonical_files:
            rel = str(sf.relative_to(root))
            registry["canonical_specs"][rel] = sha256_file(str(sf))

    # Source files
    src_dir = root / "engine" / "src"
    source_files = sorted([
        f for f in src_dir.glob("*.py")
    ])
    registry["source_files"] = OrderedDict()
    for sf in source_files:
        rel = str(sf.relative_to(root))
        registry["source_files"][rel] = sha256_file(str(sf))

    # Test vector files
    tv_dir = root / "engine" / "tests" / "test_vectors"
    tv_files = sorted(tv_dir.glob("*.json"))
    registry["test_vectors"] = OrderedDict()
    for tv in tv_files:
        rel = str(tv.relative_to(root))
        registry["test_vectors"][rel] = sha256_file(str(tv))

    # Write registry
    out_path = root / "artifact_registry" / "Artifact_Registry_v0.6.json"
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Artifact registry written to: {out_path}")
    print(f"PSL SHA256: {registry['psl_snapshot']['sha256']}")
    print(f"Spec documents: {len(registry['spec_documents'])} files")


if __name__ == "__main__":
    main()
