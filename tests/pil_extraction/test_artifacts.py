"""
Artifact hash validation tests for PIL extraction.
Per DKP-PTL-REG-PIL-INTEGRATION-001 v0.6.

Validates that all artifact hashes in registry match actual files.
Any mismatch indicates unauthorized modification.
"""

import json
import hashlib
from pathlib import Path

import pytest


# Path to artifact registry relative to repo root
ARTIFACT_REGISTRY_PATH = "artifacts/Artifact_Registry_v0.6.0.json"


def get_repo_root() -> Path:
    """Get repository root directory."""
    # Start from this test file and go up to find artifacts/
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "artifacts").is_dir():
            return parent
    raise RuntimeError("Could not find repository root")


def compute_sha256(filepath: Path) -> str:
    """Compute SHA256 hash of file contents."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


class TestArtifactRegistry:
    """Tests for artifact registry integrity."""
    
    @pytest.fixture
    def registry(self) -> dict:
        """Load artifact registry."""
        repo_root = get_repo_root()
        registry_path = repo_root / ARTIFACT_REGISTRY_PATH
        
        if not registry_path.exists():
            pytest.fail(f"Artifact registry not found: {registry_path}")
        
        with open(registry_path) as f:
            return json.load(f)
    
    def test_registry_has_required_fields(self, registry):
        """Registry must have required top-level fields."""
        assert "version" in registry, "Missing 'version' field"
        assert "pil_extraction_version" in registry, "Missing 'pil_extraction_version' field"
        assert "pil_vectors_version" in registry, "Missing 'pil_vectors_version' field"
        assert "artifacts" in registry, "Missing 'artifacts' field"
    
    def test_registry_version_is_0_6_0(self, registry):
        """Registry version must be 0.6.0."""
        assert registry["version"] == "0.6.0", f"Expected version 0.6.0, got {registry['version']}"
    
    def test_pil_extraction_version_is_0_3(self, registry):
        """PIL extraction version must be 0.3."""
        assert registry["pil_extraction_version"] == "0.3"
    
    def test_pil_vectors_version_is_0_1(self, registry):
        """PIL vectors version must be 0.1."""
        assert registry["pil_vectors_version"] == "0.1"
    
    def test_artifacts_is_sorted_by_path(self, registry):
        """Artifacts must be sorted by path for determinism."""
        artifacts = registry["artifacts"]
        paths = [a["path"] for a in artifacts]
        assert paths == sorted(paths), "Artifacts not sorted by path"
    
    def test_all_artifacts_have_required_fields(self, registry):
        """Each artifact must have name, path, sha256."""
        for artifact in registry["artifacts"]:
            assert "name" in artifact, f"Artifact missing 'name': {artifact}"
            assert "path" in artifact, f"Artifact missing 'path': {artifact}"
            assert "sha256" in artifact, f"Artifact missing 'sha256': {artifact}"


class TestArtifactHashes:
    """Tests that validate artifact file hashes."""
    
    @pytest.fixture
    def registry(self) -> dict:
        """Load artifact registry."""
        repo_root = get_repo_root()
        registry_path = repo_root / ARTIFACT_REGISTRY_PATH
        
        with open(registry_path) as f:
            return json.load(f)
    
    @pytest.fixture
    def repo_root(self) -> Path:
        """Get repository root."""
        return get_repo_root()
    
    def test_all_artifact_files_exist(self, registry, repo_root):
        """All artifact files must exist."""
        missing = []
        for artifact in registry["artifacts"]:
            filepath = repo_root / artifact["path"]
            if not filepath.exists():
                missing.append(artifact["path"])
        
        if missing:
            pytest.fail(f"Missing artifact files: {missing}")
    
    def test_all_artifact_hashes_match(self, registry, repo_root):
        """All artifact hashes must match computed values."""
        mismatches = []
        
        for artifact in registry["artifacts"]:
            filepath = repo_root / artifact["path"]
            
            if not filepath.exists():
                # Skip non-existent files (covered by other test)
                continue
            
            expected_hash = artifact["sha256"]
            actual_hash = compute_sha256(filepath)
            
            if expected_hash != actual_hash:
                mismatches.append({
                    "name": artifact["name"],
                    "path": artifact["path"],
                    "expected": expected_hash,
                    "actual": actual_hash,
                })
        
        if mismatches:
            msg = "Artifact hash mismatches detected:\n"
            for m in mismatches:
                msg += f"  {m['path']}:\n"
                msg += f"    expected: {m['expected']}\n"
                msg += f"    actual:   {m['actual']}\n"
            pytest.fail(msg)
    
    def test_no_unauthorized_modifications(self, registry, repo_root):
        """
        Explicit test that no files have been modified.
        This is the primary integrity gate.
        """
        # Just calls the hash match test - it's the same logic
        # but named explicitly for CI output clarity
        self.test_all_artifact_hashes_match(registry, repo_root)


class TestArtifactCompleteness:
    """Tests that all required artifacts are registered."""
    
    REQUIRED_ARTIFACTS = [
        "client/pil_extraction/__init__.py",
        "client/pil_extraction/constants.py",
        "client/pil_extraction/extractor.py",
        "client/pil_extraction/mappings.py",
        "client/pil_extraction/normalization.py",
        "client/pil_extraction/page_unit.py",
        "client/pil_extraction/schemas.py",
        "client/pil_extraction/source_collectors.py",
        "client/pil_extraction/title_parser.py",
        "client/pil_extraction/url_tokens.py",
        "tests/pil_extraction/test_runner_pil.py",
        "tests/pil_extraction/vectors/pil_vectors_v0_1.json",
    ]
    
    @pytest.fixture
    def registry(self) -> dict:
        """Load artifact registry."""
        repo_root = get_repo_root()
        registry_path = repo_root / ARTIFACT_REGISTRY_PATH
        
        with open(registry_path) as f:
            return json.load(f)
    
    def test_all_required_artifacts_registered(self, registry):
        """All required PIL extraction files must be in registry."""
        registered_paths = {a["path"] for a in registry["artifacts"]}
        
        missing = []
        for required in self.REQUIRED_ARTIFACTS:
            if required not in registered_paths:
                missing.append(required)
        
        if missing:
            pytest.fail(f"Required artifacts not registered: {missing}")
