"""Tests for scripts/path_safety.safe_resolve."""
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

# Import safe_resolve directly
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
from path_safety import safe_resolve


# ---------- helpers ----------

def _run_safe_resolve_in_subprocess(base_dir: str, subpath: str) -> int:
    """Run safe_resolve in a child process and return its exit code.

    We need a subprocess because safe_resolve calls sys.exit(2) on
    violation, and we must not kill the test runner.
    """
    code = textwrap.dedent(f"""\
        import sys
        from pathlib import Path
        sys.path.insert(0, {str(SCRIPTS_DIR)!r})
        from path_safety import safe_resolve
        safe_resolve(Path({base_dir!r}), {subpath!r})
    """)
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )
    return result.returncode


# ---------- allowed paths ----------

class TestAllowedPaths:
    """Paths that must resolve successfully."""

    def test_simple_relative(self, tmp_path: Path) -> None:
        child = tmp_path / "a"
        child.mkdir()
        target = child / "b.txt"
        target.touch()

        result = safe_resolve(tmp_path, "a/b.txt")
        assert result == target.resolve()

    def test_single_file(self, tmp_path: Path) -> None:
        (tmp_path / "file.json").touch()
        result = safe_resolve(tmp_path, "file.json")
        assert result == (tmp_path / "file.json").resolve()

    def test_nested_directory(self, tmp_path: Path) -> None:
        nested = tmp_path / "x" / "y" / "z"
        nested.mkdir(parents=True)
        result = safe_resolve(tmp_path, "x/y/z")
        assert result == nested.resolve()


# ---------- blocked paths ----------

class TestBlockedPaths:
    """Paths that must trigger exit code 2."""

    def test_dotdot_traversal(self, tmp_path: Path) -> None:
        rc = _run_safe_resolve_in_subprocess(str(tmp_path), "../outside.txt")
        assert rc == 2

    def test_absolute_path(self, tmp_path: Path) -> None:
        rc = _run_safe_resolve_in_subprocess(str(tmp_path), "/etc/passwd")
        assert rc == 2

    def test_deep_traversal(self, tmp_path: Path) -> None:
        rc = _run_safe_resolve_in_subprocess(str(tmp_path), "a/../../outside.txt")
        assert rc == 2

    def test_dotdot_at_end(self, tmp_path: Path) -> None:
        rc = _run_safe_resolve_in_subprocess(str(tmp_path), "subdir/..")
        # subdir/.. resolves to base_dir itself, which is allowed (equal to base)
        # But let's verify: if it goes ABOVE, it must fail.
        # "subdir/.." == base_dir, which is fine (relative_to succeeds).
        assert rc == 0

    def test_double_dotdot_escapes(self, tmp_path: Path) -> None:
        rc = _run_safe_resolve_in_subprocess(str(tmp_path), "a/b/../../../escape")
        assert rc == 2
