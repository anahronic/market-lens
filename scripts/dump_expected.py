#!/usr/bin/env python3
import json, glob, os
d = "/home/anahronic/market-lens/engine/tests/test_vectors"
out = "/home/anahronic/market-lens/_output_dump.txt"
lines = []
for f in sorted(glob.glob(os.path.join(d, "*_expected.json"))):
    lines.append(f"=== {os.path.basename(f)} ===")
    with open(f) as fh:
        lines.append(fh.read())
with open(out, "w") as o:
    o.write("\n".join(lines))
print("Done writing to", out)
