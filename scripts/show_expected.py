#!/usr/bin/env python3
import json, glob, os
d = "/home/anahronic/market-lens/engine/tests/test_vectors"
for f in sorted(glob.glob(os.path.join(d, "*_expected.json"))):
    print(f"=== {os.path.basename(f)} ===")
    with open(f) as fh:
        print(fh.read())
