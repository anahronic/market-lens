#!/usr/bin/env python3
"""
Generate version inventory for DKP-PTL-REG release.

Scans all version strings across the repository and produces
a consolidated inventory for audit purposes.

Usage:
    python scripts/generate_version_inventory.py [--output FILE]
"""
import argparse
import json
import re
import subprocess
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path


def get_git_info(root: Path) -> dict:
    """Get git repository info."""
    info = {}
    try:
        # Get commit hash
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True, cwd=root
        )
        info["commit"] = result.stdout.strip()
        
        # Get branch
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True, cwd=root
        )
        info["branch"] = result.stdout.strip()
        
        # Get tags pointing to HEAD
        result = subprocess.run(
            ["git", "tag", "--points-at", "HEAD"],
            capture_output=True, text=True, check=True, cwd=root
        )
        info["tags"] = [t for t in result.stdout.strip().split("\n") if t]
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        info["commit"] = "unknown"
        info["branch"] = "unknown"
        info["tags"] = []
    
    return info


def extract_versions_from_file(filepath: Path, patterns: list[tuple[str, str]]) -> dict:
    """Extract version strings from a file using regex patterns."""
    versions = {}
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        
        for pattern_name, pattern in patterns:
            match = re.search(pattern, content)
            if match:
                versions[pattern_name] = match.group(1)
    except Exception:
        pass
    
    return versions


def main():
    parser = argparse.ArgumentParser(description="Generate version inventory")
    parser.add_argument("--output", "-o", default=None, help="Output file")
    args = parser.parse_args()
    
    root = Path(__file__).resolve().parent.parent
    
    inventory = OrderedDict()
    inventory["generated_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    inventory["git"] = get_git_info(root)
    
    # Version sources
    sources = OrderedDict()
    
    # constants.py
    constants_path = root / "engine" / "src" / "constants.py"
    if constants_path.exists():
        sources["engine/src/constants.py"] = extract_versions_from_file(
            constants_path,
            [
                ("PROTOCOL_VERSION", r'PROTOCOL_VERSION\s*=\s*["\']([^"\']+)["\']'),
                ("CONSTANTS_VERSION", r'CONSTANTS_VERSION\s*=\s*["\']([^"\']+)["\']'),
            ]
        )
    
    # version_info.py
    version_info_path = root / "service" / "version_info.py"
    if version_info_path.exists():
        sources["service/version_info.py"] = extract_versions_from_file(
            version_info_path,
            [
                ("ENGINE_VERSION", r'ENGINE_VERSION\s*=\s*["\']([^"\']+)["\']'),
                ("PSL_VERSION", r'PSL_VERSION\s*=\s*["\']([^"\']+)["\']'),
            ]
        )
    
    # Artifact registry
    registry_path = root / "artifact_registry" / "Artifact_Registry_v0.6.json"
    if registry_path.exists():
        with open(registry_path, "r", encoding="utf-8") as f:
            registry = json.load(f)
        sources["artifact_registry/Artifact_Registry_v0.6.json"] = {
            "protocol_version": registry.get("protocol_version"),
            "constants_version": registry.get("constants_version"),
        }
    
    # Spec documents
    spec_dir = root / "Protocols"
    for spec_file in spec_dir.glob("DKP-PTL-REG-001.md"):
        versions = extract_versions_from_file(
            spec_file,
            [("document_version", r'Version\s+(\d+\.\d+)')]
        )
        if versions:
            sources[str(spec_file.relative_to(root))] = versions
    
    inventory["sources"] = sources
    
    # Consolidate unique versions
    all_versions = set()
    for source_versions in sources.values():
        for v in source_versions.values():
            if v:
                all_versions.add(v)
    
    inventory["unique_versions_found"] = sorted(all_versions)
    
    # Consistency check
    base_versions = {v.replace("v", "").split("-")[0] for v in all_versions}
    inventory["version_consistency"] = {
        "is_consistent": len(base_versions) <= 1,
        "base_versions": sorted(base_versions),
    }
    
    # Output
    output_path = Path(args.output) if args.output else root / "release_audit" / "version_inventory.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(inventory, f, indent=2, ensure_ascii=False)
        f.write("\n")
    
    print(f"Version inventory written to: {output_path}")
    print(f"Unique versions found: {inventory['unique_versions_found']}")
    print(f"Consistency: {'PASS' if inventory['version_consistency']['is_consistent'] else 'WARN'}")


if __name__ == "__main__":
    main()
