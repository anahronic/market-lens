#!/usr/bin/env python3
"""
Compare two runtime fingerprints for DKP-PTL-REG deployment audit.

Compares local vs server fingerprints to identify discrepancies.
Always writes a deterministic JSON report to release_audit/runtime_diff.json.

Usage:
    python scripts/compare_fingerprints.py LOCAL_FINGERPRINT SERVER_FINGERPRINT
    python scripts/compare_fingerprints.py release_audit/local_fingerprint.json release_audit/server_fingerprint.json
"""
import argparse
import json
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path


def load_fingerprint(path: Path) -> dict:
    """Load fingerprint JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compare_dicts(name: str, local: dict, server: dict, indent: int = 0) -> list[str]:
    """Compare two dicts and return list of discrepancies."""
    discrepancies = []
    prefix = "  " * indent
    
    all_keys = set(local.keys()) | set(server.keys())
    
    for key in sorted(all_keys):
        local_val = local.get(key)
        server_val = server.get(key)
        
        if local_val is None:
            discrepancies.append(f"{prefix}{name}.{key}: MISSING in local, server has: {server_val}")
        elif server_val is None:
            discrepancies.append(f"{prefix}{name}.{key}: MISSING in server, local has: {local_val}")
        elif isinstance(local_val, dict) and isinstance(server_val, dict):
            discrepancies.extend(compare_dicts(f"{name}.{key}", local_val, server_val, indent))
        elif local_val != server_val:
            discrepancies.append(f"{prefix}{name}.{key}: MISMATCH")
            discrepancies.append(f"{prefix}  local:  {local_val}")
            discrepancies.append(f"{prefix}  server: {server_val}")
    
    return discrepancies


def main():
    parser = argparse.ArgumentParser(description="Compare runtime fingerprints")
    parser.add_argument("local", help="Path to local fingerprint JSON")
    parser.add_argument("server", help="Path to server fingerprint JSON")
    parser.add_argument("--strict", action="store_true", help="Fail on any discrepancy")
    parser.add_argument("--output", "-o", default=None, help="Output path for JSON report (default: release_audit/runtime_diff.json)")
    args = parser.parse_args()
    
    local_path = Path(args.local)
    server_path = Path(args.server)
    
    # Determine output path
    root = Path(__file__).resolve().parent.parent
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = root / "release_audit" / "runtime_diff.json"
    
    # Build report structure
    report = OrderedDict()
    report["comparison_timestamp_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report["local_fingerprint_path"] = str(local_path.resolve())
    report["server_fingerprint_path"] = str(server_path.resolve())
    report["compared_sections"] = ["git", "artifact_hashes", "embedded_versions", "api_version", "system"]
    report["informational_differences"] = []
    report["critical_mismatches"] = []
    report["final_status"] = "UNKNOWN"
    
    # Check files exist
    if not local_path.exists():
        report["final_status"] = "ERROR"
        report["error"] = f"Local fingerprint not found: {local_path}"
        _write_report(output_path, report)
        print(f"ERROR: Local fingerprint not found: {local_path}")
        sys.exit(2)
    
    if not server_path.exists():
        report["final_status"] = "ERROR"
        report["error"] = f"Server fingerprint not found: {server_path}"
        _write_report(output_path, report)
        print(f"ERROR: Server fingerprint not found: {server_path}")
        sys.exit(2)
    
    local_fp = load_fingerprint(local_path)
    server_fp = load_fingerprint(server_path)
    
    print("=" * 60)
    print("DKP-PTL-REG Fingerprint Comparison")
    print("=" * 60)
    print(f"Local:  {local_path}")
    print(f"Server: {server_path}")
    print()
    
    # Critical comparisons
    critical_mismatches = []
    informational = []
    
    # 1. Git commit
    local_commit = local_fp.get("git", {}).get("commit", "unknown")
    server_commit = server_fp.get("git", {}).get("commit", "unknown")
    if local_commit != server_commit:
        critical_mismatches.append({
            "section": "git.commit",
            "local": local_commit,
            "server": server_commit,
            "description": f"Git commit mismatch: local={local_commit[:12]}..., server={server_commit[:12]}..."
        })
    
    # 2. Artifact hashes
    local_hashes = local_fp.get("artifact_hashes", {})
    server_hashes = server_fp.get("artifact_hashes", {})
    hash_mismatches = compare_dicts("artifact_hashes", local_hashes, server_hashes)
    for mismatch in hash_mismatches:
        critical_mismatches.append({
            "section": "artifact_hashes",
            "description": mismatch
        })
    
    # 3. Embedded versions
    local_versions = local_fp.get("embedded_versions", {})
    server_versions = server_fp.get("embedded_versions", {})
    version_mismatches = compare_dicts("embedded_versions", local_versions, server_versions)
    for mismatch in version_mismatches:
        critical_mismatches.append({
            "section": "embedded_versions",
            "description": mismatch
        })
    
    # 4. API version (if present)
    local_api = local_fp.get("api_version", {})
    server_api = server_fp.get("api_version", {})
    if local_api and server_api:
        api_mismatches = compare_dicts("api_version", local_api, server_api)
        for mismatch in api_mismatches:
            critical_mismatches.append({
                "section": "api_version",
                "description": mismatch
            })
    
    # Informational differences (not critical)
    local_sys = local_fp.get("system", {})
    server_sys = server_fp.get("system", {})
    if local_sys.get("hostname") != server_sys.get("hostname"):
        informational.append({
            "section": "system.hostname",
            "local": local_sys.get("hostname"),
            "server": server_sys.get("hostname"),
            "description": f"Hostname: local={local_sys.get('hostname')}, server={server_sys.get('hostname')}"
        })
    if local_sys.get("platform") != server_sys.get("platform"):
        informational.append({
            "section": "system.platform",
            "local": local_sys.get("platform"),
            "server": server_sys.get("platform"),
            "description": "Platform differs (expected for local vs server)"
        })
    
    # Populate report
    report["informational_differences"] = informational
    report["critical_mismatches"] = critical_mismatches
    
    # Determine final status
    if critical_mismatches:
        report["final_status"] = "MISMATCH"
    else:
        report["final_status"] = "MATCH"
    
    # Write report
    _write_report(output_path, report)
    
    # Console output
    if critical_mismatches:
        print("CRITICAL MISMATCHES:")
        for m in critical_mismatches:
            print(f"  {m.get('description', m)}")
        print()
    
    if informational:
        print("INFORMATIONAL (expected differences):")
        for i in informational:
            print(f"  {i.get('description', i)}")
        print()
    
    print(f"Report written to: {output_path}")
    print()
    
    if not critical_mismatches:
        print("STATUS: MATCH - Local and server fingerprints are consistent")
        sys.exit(0)
    else:
        print(f"STATUS: MISMATCH - Found {len(critical_mismatches)} critical discrepancies")
        sys.exit(1 if args.strict else 0)


def _write_report(path: Path, report: dict):
    """Write JSON report to file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        f.write("\n")


if __name__ == "__main__":
    main()
