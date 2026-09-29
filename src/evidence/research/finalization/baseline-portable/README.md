# Portable verification of the existing 1,931-case baseline

This directory verifies the **previously completed** baseline: 59 independently checked field certificates and 34 independently checked generic certificates. Their exact union excludes 1,931 of 2,184 canonical cell assignments. The other 253 assignments, and the final optimality theorem, require the separate continuation and candidate arguments in the complete package.

The original JSON files, checkers, and receipts are immutable. The adapter changes addresses in memory; it never rewrites hash-bound inputs. The complete historical receipt is `research/PHASE3_FRESH_REPLAY_RESULT.json`, SHA-256 `04fa1ebb37f5dace29946224fe8c7c5d8a1bedb4fa860c65b359f4200415de57`.

## Verify the completed baseline

From any directory, set `PACKAGE` to the relocated `eleven-square-verification` directory. Use an ordinary Python 3.12 interpreter with assertions enabled. This mode needs only the standard library; it does not import or pretend to execute the historical GMP binary.

```sh
PACKAGE="/absolute/path/to/eleven-square-verification"
python3 "$PACKAGE/research/finalization/baseline-portable/verify_baseline.py" --package-root "$PACKAGE" reuse
```

The result is `results/baseline-portable/HISTORICAL_BASELINE_RESULT.json`. Acceptance requires:

- `status == "PASS_HISTORICAL_BASELINE_BINDINGS_AND_EXACT_UNION"`;
- `fresh_geometry_replayed == false`;
- `field_certificates == 59`, `generic_certificates == 34`, `excluded == 1931`, `remaining == 253`;
- the exact excluded/remaining lists, 498 declared file hashes, adapter/inventory/consumer hashes, and historical receipt hash recorded in that result.

The adapter hashes all 398 archived dependencies and all 100 external historical artifacts. It recomputes charge-field transfers, canonical assignments, and the complete union from the pinned 59+34 receipts, and compares every field of the reconstructed historical aggregate with the immutable historical aggregate. It validates original sources as well as receipt status strings. It does **not** repeat the original geometric computations in `reuse` mode.

Historical generic audits used native gmpy2 2.3.1 with binary SHA-256 `4fdf5fbaea9d3c4f756f9f656d0d7656fc4a66c82a8e921f326e570702dc463d`. This identity is preserved as historical provenance; the old binary need not execute or exist on the new machine. The source inventory and adapter establish historical receipt integrity, not a cryptographic attestation that a particular machine executed a program. Independent mathematical verification can rerun the geometry below.

## Optional fresh independent geometric replay

Use a Python 3.12 environment with native `gmpy2==2.3.1`, NumPy, and SymPy. The original replay used NumPy 2.5.3 and SymPy 1.14.0. Use a clean virtual environment; keep it outside the proof package to separate runtime libraries from proof inputs. Do not put the archived Linux dependency directory on `PYTHONPATH`. Python optimization (`-O` or `-OO`) is rejected.

```sh
python3.12 -m venv /absolute/path/to/eleven-verifier-venv
/absolute/path/to/eleven-verifier-venv/bin/python -m pip install gmpy2==2.3.1 numpy==2.5.3 sympy==1.14.0
PYTHON="/absolute/path/to/eleven-verifier-venv/bin/python"
"$PYTHON" "$PACKAGE/research/finalization/baseline-portable/verify_baseline.py" --package-root "$PACKAGE" field --index 0
"$PYTHON" "$PACKAGE/research/finalization/baseline-portable/verify_baseline.py" --package-root "$PACKAGE" generic --index 0
```

Field indices are 0–58; generic indices are 0–33. Each command runs one original immutable checker in a clean process, with every geometric premise checked afresh. It does not use a cached ownership receipt or a cached root audit. The optional full run is serial and may take many hours:

```sh
"$PYTHON" "$PACKAGE/research/finalization/baseline-portable/verify_baseline.py" --package-root "$PACKAGE" all
```

`all` first validates the historical baseline, then runs all 93 independent checks in separate processes and builds the fresh summary. It does not automatically trust or skip existing stage files. For a manual restart, rerun only the unfinished or failed indices, then request the summary:

```sh
"$PYTHON" "$PACKAGE/research/finalization/baseline-portable/verify_baseline.py" --package-root "$PACKAGE" summary
```

A completed fresh run writes `results/baseline-portable/FRESH_BASELINE_RESULT.json` with status `PASS_PORTABLE_FRESH_1931_CASE_BASELINE` and `fresh_geometry_replayed: true`. Summary validation requires all 93 distinct stage receipts, corresponding traces, exact source/receipt bindings, one recorded native GMP binary identity, semantic agreement, and the same exact 1,931-case union. A partial run cannot produce this status. Files produced by a previous adapter revision cannot be silently combined with a new revision.

## Exact comparison and relocation rules

Fresh receipt comparison is recursive equality of the entire JSON value, with only these explicit exceptions:

1. Field `control_receipts[*].path` and generic `nodes[*].path` are converted to declared package-relative identities. Their hashes remain equal to the immutable inventory.
2. Generic elapsed `seconds` may differ.
3. Generic `rational_binary_sha256` may differ only because the fresh receipt records the actually loaded native binary; its digest and version are separately checked and recorded. All stages in a full fresh summary use the same native identity.

Every mathematical field remains compared: source/root/checker hashes, exact coefficients, ownership results, row results, constraints, final state, exclusion statuses, transferred cases, and full-domain claims. Float tolerance and approximate comparison are never used. A deterministic receipt difference causes failure; it is not silently accepted as a portability exception.

Old macOS references map only to the same relative location within the declared package. Archived Linux references resolve only by a complete `work/...` or `current/...` member suffix, into the selected certificate's declared input set. Unknown or ambiguous paths fail closed. There is no external-file or basename fallback. Internal symlink aliases and paths that escape the package are rejected. Package sources are loaded from pinned `.py` files; package bytecode caches are disabled, and loaded proof-module origins are checked. Writes are restricted to `results/baseline-portable/`.

The process-level path and Python I/O guards prevent accidental fallback to the original workspace. They are not an operating-system security sandbox for malicious native libraries. Python, its standard library, NumPy/SymPy for field replay, and the native GMP implementation are explicit execution dependencies. The archived proof data are treated as data, not executable instructions.

## Files and provenance

- `SOURCE_INVENTORY.json`: all 498 immutable input identities and per-certificate groups. SHA-256 `eb86c86ca071bc3a6286cec3c7d90bef62800a96154dc1ccf6be74ac45eb80fb`.
- `baseline_reconstruct.py`: exact union consumer adapted from frozen `research/aggregate_phase3_fresh.py` (`e6af5b32d54bb0cd675568b85425a63961e277c7d6b802877022baf3d24df691`). The only changes are explicit package/read/hash/provenance arguments, optional fresh-receipt substitution, and returning the result instead of rewriting the historical aggregate. SHA-256 `ec47984510e847bbbb87dc924d8865fb5ff4510f0ce7c8558f55531b502a1b0c`.
- `verify_baseline.py`: launcher, input binding, path/import isolation, exact semantic comparison, and separately labeled historical/fresh result modes. It records its own digest before running and checks it again before acceptance.
- `inputs/original/eleven-square-continuation-2026-09-27.zip`: original distribution, SHA-256 `8739c76e681f900923b900c9df0ef75cf421d39cabb54650c4b9ad19b6a76d85`. `reuse` verifies the extracted proof files individually; it does not need to scan or extract this ZIP again.

These portable commands have been prepared without launching another baseline geometric replay. See the package's generated results for which commands were actually run. The historical 59+34 geometric replays are already completed and source-bound; the optional portable fresh replay is a separate verification claim.
