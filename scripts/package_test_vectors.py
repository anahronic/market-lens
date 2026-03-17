#!/usr/bin/env python3
"""
Package official test vectors for DKP-PTL-REG v0.6 release.

Creates:
- test_vectors/v0.6/ directory with normalized structure
- official_test_vectors_v0.6.zip archive
- test_vectors/v0.6/MANIFEST.json with hashes

Usage:
    python scripts/package_test_vectors.py [--output-dir DIR]
"""
import argparse
import hashlib
import json
import shutil
import zipfile
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(filepath: Path) -> str:
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


TEST_CASES = [
    "uniform_market",
    "burst_attack",
    "domain_dominance",
    "cluster_injection",
    "cold_start",
    "zero_mad",
]


def main():
    parser = argparse.ArgumentParser(description="Package official test vectors")
    parser.add_argument("--output-dir", default=None, help="Output directory for packaged vectors")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    source_dir = root / "engine" / "tests" / "test_vectors"
    
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = root / "test_vectors" / "v0.6"
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Build manifest
    manifest = OrderedDict()
    manifest["protocol_version"] = "0.6.0"
    manifest["package_type"] = "official_test_vectors"
    manifest["generated_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest["test_cases"] = []
    
    # Copy and catalog each test case
    for case_name in TEST_CASES:
        input_file = source_dir / f"{case_name}_input.json"
        expected_file = source_dir / f"{case_name}_expected.json"
        
        if not input_file.exists() or not expected_file.exists():
            print(f"WARNING: Missing files for test case '{case_name}'")
            continue
        
        # Copy files
        shutil.copy2(input_file, output_dir / input_file.name)
        shutil.copy2(expected_file, output_dir / expected_file.name)
        
        # Add to manifest
        case_entry = OrderedDict()
        case_entry["name"] = case_name
        case_entry["input_file"] = input_file.name
        case_entry["input_sha256"] = sha256_file(input_file)
        case_entry["expected_file"] = expected_file.name
        case_entry["expected_sha256"] = sha256_file(expected_file)
        manifest["test_cases"].append(case_entry)
    
    # Write manifest
    manifest_path = output_dir / "MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")
    
    # Create README
    readme_content = f"""# DKP-PTL-REG v0.6 Official Test Vectors

This package contains the official test vectors for DKP-PTL-REG v0.6.0.

## Contents

| Test Case | Description |
|-----------|-------------|
| uniform_market | Uniform price distribution baseline |
| burst_attack | Price manipulation burst detection |
| domain_dominance | Single-domain pricing context |
| cluster_injection | Cluster-based price injection |
| cold_start | Initial state with minimal history |
| zero_mad | Zero median absolute deviation edge case |

## Usage

Each test case has two files:
- `<case>_input.json` - Input data for the engine
- `<case>_expected.json` - Expected output (deterministic)

Run the engine with an input file and compare the output against the expected file.

## Verification

See `MANIFEST.json` for SHA256 hashes of all files.

Generated: {manifest["generated_utc"]}
Protocol Version: {manifest["protocol_version"]}
"""
    readme_path = output_dir / "README.md"
    with open(readme_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(readme_content)
    
    # Create ZIP archive
    zip_path = root / "official_test_vectors_v0.6.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in output_dir.iterdir():
            zf.write(file, f"v0.6/{file.name}")
    
    print(f"Test vectors packaged to: {output_dir}")
    print(f"ZIP archive created: {zip_path}")
    print(f"Test cases: {len(manifest['test_cases'])}")
    for tc in manifest["test_cases"]:
        print(f"  - {tc['name']}")


if __name__ == "__main__":
    main()
