#!/usr/bin/env python3
"""
Collect runtime fingerprint for DKP-PTL-REG deployment.

Gathers version info, artifact hashes, and system state to enable
comparison between local and server deployments.

Usage:
    python scripts/collect_runtime_fingerprint.py [--output FILE] [--api-url URL]
"""
import argparse
import hashlib
import json
import platform
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


def get_git_info(root: Path) -> dict:
    """Get git repository info."""
    info = {}
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True, cwd=root
        )
        info["commit"] = result.stdout.strip()
        
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True, cwd=root
        )
        info["branch"] = result.stdout.strip()
        
        # Check if working directory is clean
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, check=True, cwd=root
        )
        info["is_clean"] = len(result.stdout.strip()) == 0
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        info["commit"] = "unknown"
        info["branch"] = "unknown"
        info["is_clean"] = None
    
    return info


def get_python_info() -> dict:
    """Get Python runtime info."""
    return {
        "version": platform.python_version(),
        "implementation": platform.python_implementation(),
        "executable": sys.executable,
    }


def get_system_info() -> dict:
    """Get system info."""
    return {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "hostname": platform.node(),
    }


def collect_artifact_hashes(root: Path) -> dict:
    """Collect hashes of key artifacts."""
    hashes = OrderedDict()
    
    # PSL snapshot
    psl_path = root / "engine" / "src" / "psl_snapshot" / "PSL-2026-01-01.dat"
    if psl_path.exists():
        hashes["psl_snapshot"] = sha256_file(psl_path)
    
    # Constants
    constants_path = root / "engine" / "src" / "constants.py"
    if constants_path.exists():
        hashes["constants.py"] = sha256_file(constants_path)
    
    # Core engine modules
    for module in ["data_pipeline.py", "reference_boundary.py", "threat_status.py", "json_canonical.py"]:
        module_path = root / "engine" / "src" / module
        if module_path.exists():
            hashes[module] = sha256_file(module_path)
    
    return hashes


def get_api_version(api_url: str) -> dict | None:
    """Query API version endpoint."""
    try:
        import urllib.request
        import ssl
        
        # Allow self-signed certs for local testing
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        version_url = f"{api_url.rstrip('/')}/version"
        with urllib.request.urlopen(version_url, timeout=10, context=ctx) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Collect runtime fingerprint")
    parser.add_argument("--output", "-o", default=None, help="Output file")
    parser.add_argument("--api-url", default=None, help="API URL to query version (e.g., http://localhost:8000)")
    args = parser.parse_args()
    
    root = Path(__file__).resolve().parent.parent
    
    fingerprint = OrderedDict()
    fingerprint["collected_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    fingerprint["collector"] = "scripts/collect_runtime_fingerprint.py"
    
    # Git info
    fingerprint["git"] = get_git_info(root)
    
    # System info
    fingerprint["system"] = get_system_info()
    fingerprint["python"] = get_python_info()
    
    # Artifact hashes
    fingerprint["artifact_hashes"] = collect_artifact_hashes(root)
    
    # Embedded version strings
    try:
        sys.path.insert(0, str(root / "engine" / "src"))
        from constants import PROTOCOL_VERSION, CONSTANTS_VERSION
        fingerprint["embedded_versions"] = {
            "PROTOCOL_VERSION": PROTOCOL_VERSION,
            "CONSTANTS_VERSION": CONSTANTS_VERSION,
        }
    except ImportError:
        fingerprint["embedded_versions"] = {"error": "Could not import constants"}
    
    # API version (optional)
    if args.api_url:
        fingerprint["api_version"] = get_api_version(args.api_url)
    
    # Output
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = root / "release_audit" / "local_fingerprint.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(fingerprint, f, indent=2, ensure_ascii=False)
        f.write("\n")
    
    print(f"Fingerprint collected: {output_path}")
    print(f"Git commit: {fingerprint['git'].get('commit', 'unknown')[:12]}...")
    print(f"PSL hash: {fingerprint['artifact_hashes'].get('psl_snapshot', 'missing')[:16]}...")


if __name__ == "__main__":
    main()
