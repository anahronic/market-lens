"""Centralized path-safety helper for market-lens scripts.

Every path derived from arguments, environment variables, or any external
input MUST pass through ``safe_resolve`` before it is opened / read / written.
"""

from pathlib import Path
import sys


def safe_resolve(base_dir: Path, subpath: str | Path) -> Path:
    """Return *subpath* resolved under *base_dir*, or abort.

    Guarantees that the resulting path is strictly inside (or equal to)
    *base_dir* after symlink resolution.  Blocks ``../`` traversal,
    absolute paths pointing elsewhere, and symlink escapes.

    Parameters
    ----------
    base_dir : Path
        Trusted root directory.
    subpath : str | Path
        Untrusted relative component.

    Returns
    -------
    Path
        Fully resolved path that is inside *base_dir*.

    Raises
    ------
    SystemExit
        Exits with code **2** when *subpath* escapes *base_dir*.
    """
    base_dir = base_dir.resolve()
    candidate = (base_dir / subpath).resolve()

    try:
        candidate.relative_to(base_dir)
    except ValueError:
        print(f"ERROR: path escapes base_dir: {subpath}", file=sys.stderr)
        sys.exit(2)

    return candidate
