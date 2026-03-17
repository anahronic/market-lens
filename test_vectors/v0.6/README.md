# DKP-PTL-REG v0.6 Official Test Vectors

This package contains the official test vectors for DKP-PTL-REG v0.6.0.

## Contents

| Test Case | Description |
|-----------|-------------|
| uniform_market | Uniform price distribution baseline |
| burst_attack | Price manipulation burst detection |
| domain_dominance | Single-domain pricing context |
| cluster_injection | Cluster-based price injection |
| cold_start | Initial state with minimal history |
| zero_mad | Zero median absolute deviation edge case |

## Usage

Each test case has two files:
- `<case>_input.json` - Input data for the engine
- `<case>_expected.json` - Expected output (deterministic)

Run the engine with an input file and compare the output against the expected file.

## Verification

See `MANIFEST.json` for SHA256 hashes of all files.

Generated: 2026-03-17T07:49:50Z
Protocol Version: 0.6.0
