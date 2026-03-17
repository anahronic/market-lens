#!/usr/bin/env python3
"""Dump all *_expected.json vectors to a single text file."""
import json
import sys
from pathlib import Path

_scripts_dir = str(Path(__file__).resolve().parent)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)
from path_safety import safe_resolve

REPO_ROOT = Path(__file__).resolve().parent.parent
VECTORS_DIR = safe_resolve(REPO_ROOT, "engine/tests/test_vectors")
OUTPUT_FILE = safe_resolve(REPO_ROOT, "_output_dump.txt")

lines: list[str] = []
for f in sorted(VECTORS_DIR.glob("*_expected.json")):
    safe_resolve(VECTORS_DIR, f.name)          # validate each match
    lines.append(f"=== {f.name} ===")
    lines.append(f.read_text())

OUTPUT_FILE.write_text("\n".join(lines))
print("Done writing to", OUTPUT_FILE)
