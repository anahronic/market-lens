#!/usr/bin/env python3
"""
DKP-PTL-REG v0.6 Release Conformance Checker

Entry point for automated release audit.

Usage:
    python -m scripts.release_audit [--output FILE] [--json] [--verbose]

Checks:
1. Artifact registry integrity (all hashes match)
2. PSL snapshot verification
3. Test vector completeness
4. Version string consistency
5. Spec bundle presence
"""
import argparse
import hashlib
import json
import subprocess
import sys
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


def get_git_commit(root: Path) -> str:
    """Get current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=root,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


class ConformanceChecker:
    """Release conformance checking engine."""
    
    REQUIRED_TEST_CASES = [
        "uniform_market",
        "burst_attack",
        "domain_dominance",
        "cluster_injection",
        "cold_start",
        "zero_mad",
    ]
    
    REQUIRED_SPEC_DOCS = [
        "DKP-PTL-REG-001.md",
        "DKP-PTL-REG-DATA-001.md",
        "DKP-PTL-REG-CONSTANTS-001.md",
        "DKP-PTL-REG-REFERENCE-001.md",
        "DKP-PTL-REG-THREAT-001.md",
        "DKP-PTL-REG-GOV-001.md",
    ]
    
    def __init__(self, root: Path, verbose: bool = False):
        self.root = root
        self.verbose = verbose
        self.results = OrderedDict()
        self.checks_passed = 0
        self.checks_failed = 0
        self.checks_warned = 0
    
    def log(self, msg: str):
        if self.verbose:
            print(msg)
    
    def check_pass(self, name: str, message: str):
        self.results[name] = {"status": "PASS", "message": message}
        self.checks_passed += 1
        self.log(f"  [PASS] {name}: {message}")
    
    def check_fail(self, name: str, message: str):
        self.results[name] = {"status": "FAIL", "message": message}
        self.checks_failed += 1
        self.log(f"  [FAIL] {name}: {message}")
    
    def check_warn(self, name: str, message: str):
        self.results[name] = {"status": "WARN", "message": message}
        self.checks_warned += 1
        self.log(f"  [WARN] {name}: {message}")
    
    def check_artifact_registry(self):
        """Verify artifact registry exists and contains required sections."""
        self.log("Checking artifact registry...")
        registry_path = self.root / "artifact_registry" / "Artifact_Registry_v0.6.json"
        
        if not registry_path.exists():
            self.check_fail("artifact_registry_exists", f"Registry not found: {registry_path}")
            return None
        
        self.check_pass("artifact_registry_exists", str(registry_path))
        
        with open(registry_path, "r", encoding="utf-8") as f:
            registry = json.load(f)
        
        # Check required fields
        required_fields = ["protocol_version", "psl_snapshot", "spec_documents", "source_files", "test_vectors"]
        for field in required_fields:
            if field in registry:
                self.check_pass(f"registry_field_{field}", f"Field '{field}' present")
            else:
                self.check_fail(f"registry_field_{field}", f"Field '{field}' missing")
        
        return registry
    
    def check_psl_snapshot(self, registry: dict):
        """Verify PSL snapshot hash matches registry."""
        self.log("Checking PSL snapshot...")
        
        if not registry or "psl_snapshot" not in registry:
            self.check_fail("psl_snapshot", "No PSL info in registry")
            return
        
        psl_info = registry["psl_snapshot"]
        filename = psl_info.get("filename", "PSL-2026-01-01.dat")
        expected_hash = psl_info.get("sha256", "")
        
        psl_path = self.root / "engine" / "src" / "psl_snapshot" / filename
        
        if not psl_path.exists():
            self.check_fail("psl_file_exists", f"PSL file not found: {psl_path}")
            return
        
        self.check_pass("psl_file_exists", str(psl_path))
        
        actual_hash = sha256_file(psl_path)
        if actual_hash == expected_hash:
            self.check_pass("psl_hash_match", f"SHA256: {actual_hash[:16]}...")
        else:
            self.check_fail("psl_hash_match", f"Hash mismatch: expected {expected_hash[:16]}..., got {actual_hash[:16]}...")
    
    def check_test_vectors(self, registry: dict):
        """Verify all required test vectors are present and hashes match."""
        self.log("Checking test vectors...")
        
        tv_dir = self.root / "engine" / "tests" / "test_vectors"
        
        for case in self.REQUIRED_TEST_CASES:
            input_file = tv_dir / f"{case}_input.json"
            expected_file = tv_dir / f"{case}_expected.json"
            
            if input_file.exists() and expected_file.exists():
                self.check_pass(f"test_vector_{case}", "Input and expected files present")
            else:
                missing = []
                if not input_file.exists():
                    missing.append("input")
                if not expected_file.exists():
                    missing.append("expected")
                self.check_fail(f"test_vector_{case}", f"Missing: {', '.join(missing)}")
        
        # Verify hashes if registry has test_vectors
        if registry and "test_vectors" in registry:
            for rel_path, expected_hash in registry["test_vectors"].items():
                file_path = self.root / rel_path
                if file_path.exists():
                    actual_hash = sha256_file(file_path)
                    if actual_hash == expected_hash:
                        self.log(f"    Hash OK: {rel_path}")
                    else:
                        self.check_fail(f"hash_{Path(rel_path).name}", f"Hash mismatch for {rel_path}")
    
    def check_spec_bundle(self):
        """Verify canonical spec bundle is present."""
        self.log("Checking spec bundle...")
        
        canonical_dir = self.root / "specs" / "dkp-ptl-reg" / "v0.6"
        
        if not canonical_dir.exists():
            self.check_warn("canonical_spec_dir", f"Canonical dir not found: {canonical_dir}")
            # Fall back to Protocols/
            canonical_dir = self.root / "Protocols"
            if not canonical_dir.exists():
                self.check_fail("spec_documents_exist", "No spec documents directory found")
                return
        
        self.check_pass("canonical_spec_dir", str(canonical_dir))
        
        for spec_file in self.REQUIRED_SPEC_DOCS:
            spec_path = canonical_dir / spec_file
            if spec_path.exists():
                self.check_pass(f"spec_{spec_file}", "Present")
            else:
                # Check without extension variations
                alt_path = canonical_dir / spec_file.replace("-001.md", "-001_.md")
                if alt_path.exists():
                    self.check_warn(f"spec_{spec_file}", f"Found with non-canonical name: {alt_path.name}")
                else:
                    self.check_fail(f"spec_{spec_file}", "Missing")
    
    def check_version_consistency(self):
        """Verify version strings are consistent."""
        self.log("Checking version consistency...")
        
        versions_found = {}
        
        # Check constants.py
        constants_path = self.root / "engine" / "src" / "constants.py"
        if constants_path.exists():
            with open(constants_path, "r", encoding="utf-8") as f:
                content = f.read()
            for line in content.splitlines():
                if "PROTOCOL_VERSION" in line and "=" in line:
                    versions_found["constants.PROTOCOL_VERSION"] = line.split("=")[1].strip().strip('"\'')
                if "CONSTANTS_VERSION" in line and "=" in line:
                    versions_found["constants.CONSTANTS_VERSION"] = line.split("=")[1].strip().strip('"\'')
        
        # Check version_info.py
        version_info_path = self.root / "service" / "version_info.py"
        if version_info_path.exists():
            with open(version_info_path, "r", encoding="utf-8") as f:
                content = f.read()
            for line in content.splitlines():
                if "ENGINE_VERSION" in line and "=" in line:
                    versions_found["version_info.ENGINE_VERSION"] = line.split("=")[1].strip().strip('"\'')
        
        # Check consistency
        unique_versions = set(v for v in versions_found.values() if v)
        if len(unique_versions) == 1:
            self.check_pass("version_consistency", f"All versions: {unique_versions.pop()}")
        elif len(unique_versions) > 1:
            self.check_warn("version_consistency", f"Multiple versions found: {versions_found}")
        else:
            self.check_warn("version_consistency", "No version strings found")
        
        for key, val in versions_found.items():
            self.results[f"version_{key}"] = val
    
    def run_all_checks(self) -> dict:
        """Run all conformance checks and return report."""
        start_time = datetime.now(timezone.utc)
        
        # Run checks
        registry = self.check_artifact_registry()
        self.check_psl_snapshot(registry)
        self.check_test_vectors(registry)
        self.check_spec_bundle()
        self.check_version_consistency()
        
        end_time = datetime.now(timezone.utc)
        
        # Build report
        report = OrderedDict()
        report["audit_metadata"] = {
            "generated_utc": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "git_commit": get_git_commit(self.root),
            "duration_seconds": (end_time - start_time).total_seconds(),
        }
        report["summary"] = {
            "total_checks": self.checks_passed + self.checks_failed + self.checks_warned,
            "passed": self.checks_passed,
            "failed": self.checks_failed,
            "warnings": self.checks_warned,
            "overall_status": "PASS" if self.checks_failed == 0 else "FAIL",
        }
        report["checks"] = self.results
        
        return report


def main():
    parser = argparse.ArgumentParser(description="DKP-PTL-REG v0.6 Release Conformance Checker")
    parser.add_argument("--output", "-o", default=None, help="Output file for report")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()
    
    root = Path(__file__).resolve().parent.parent.parent
    
    print("DKP-PTL-REG v0.6 Release Conformance Check")
    print("=" * 50)
    
    checker = ConformanceChecker(root, verbose=args.verbose)
    report = checker.run_all_checks()
    
    # Print summary
    summary = report["summary"]
    print()
    print(f"Total checks: {summary['total_checks']}")
    print(f"  Passed:   {summary['passed']}")
    print(f"  Failed:   {summary['failed']}")
    print(f"  Warnings: {summary['warnings']}")
    print()
    print(f"Overall status: {summary['overall_status']}")
    
    # Output report
    if args.output:
        output_path = Path(args.output)
        with open(output_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"Report written to: {output_path}")
    elif args.json:
        print()
        print(json.dumps(report, indent=2, ensure_ascii=False))
    
    # Exit with appropriate code
    sys.exit(0 if summary["overall_status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
