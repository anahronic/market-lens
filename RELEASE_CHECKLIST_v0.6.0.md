# Release Checklist — DKP-PTL-REG v0.6.0

> This checklist MUST be completed before tagging and publishing v0.6.0.

---

## 1. Test Vectors (byte-for-byte)

```bash
python -m engine.tests.test_runner
```

Expected: 6 passed, 0 failed.

---

## 2. Pytest Suite

```bash
pytest engine/tests/ -v
```

Expected: all tests pass on Python 3.10, 3.11, 3.12.

---

## 3. Determinism Check

```bash
python scripts/det_check.py
```

Expected: `DETERMINISM OVERALL: PASS`

---

## 4. PSL Snapshot Hash

```bash
sha256sum engine/src/psl_snapshot/PSL-2026-01-01.dat
```

Expected: `edee63489085821c1744bbc9225bb1ff9edd34f8451f1379273e124ebf5083cf`

Verify against `artifact_registry/Artifact_Registry_v0.6.json` → `psl_snapshot.sha256`.

---

## 5. Artifact Registry Idempotency

```bash
cp artifact_registry/Artifact_Registry_v0.6.json /tmp/reg_before.json
python scripts/generate_artifact_registry.py
diff /tmp/reg_before.json artifact_registry/Artifact_Registry_v0.6.json
```

Expected: no diff (idempotent).

---

## 6. Verify No Stray Cache Files

```bash
find . -name __pycache__ -o -name "*.pyc" -o -name .pytest_cache | head -5
```

Expected: no output (all excluded by .gitignore).

---

## 7. Verify Working Tree Clean

```bash
git status --porcelain
```

Expected: empty output (all changes committed).

---

## 8. Tag and Publish

```bash
git tag -a v0.6.0 -m "DKP-PTL-REG v0.6.0 — Frozen Release"
git push origin main --tags
```

Or via GitHub CLI:

```bash
gh release create v0.6.0 --title "v0.6.0 — Frozen Release" \
  --notes "Canonical reference implementation of DKP-PTL-REG v0.6 (frozen). All specifications, constants, test vectors, and artifact registry are immutable."
```

---

## 9. Post-Publish Rule

> ⚠️ **After v0.6.0 is published:**
>
> - NO modification of any file under `engine/src/`, `Protocols/`, or `engine/tests/test_vectors/` is permitted.
> - NO modification of `artifact_registry/Artifact_Registry_v0.6.json` is permitted.
> - Any fix, even cosmetic, requires:
>   1. Version bump to v0.7+
>   2. Full regeneration of test vectors
>   3. Full regeneration of artifact registry
>   4. New tag (v0.7.0)
