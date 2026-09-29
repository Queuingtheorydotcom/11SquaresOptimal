# Strict integration of the 76 prior extensions

The standalone portable adapter passed its actual guarded package run: all 304 whole-file bindings (3,145,197,526 bytes), all 76 strict extension receipts, and the exact 2007/177 partition passed in 36.42 seconds. Result and trace hashes are in `PORTABLE_INTEGRATION_STATUS.json`. This is inventory/composition validation; no new geometric replay occurred.

`integrate_prior_union.py` is a corrected, isolated replacement for the old `research/frontier/extend_union.py` consumer. It selects exactly the frozen 76 receipt identities, validates their complete inventories, and writes a new result under this directory. It never imports or writes the root consumer or canonical root ledger.

The root consumer still pins the earlier tree validator `ed615c...`. The new runner pins the final tree validator `b6a298ccfa1a27911b3e88c832f890a983e0c6e7c374455808e42eb730626059`, generic validator `7df54d904bb5d0cc609a4765eeafc3fb57922bcb3a4b210082df9fda36266530`, and the unchanged dependency-pin manifest.

The old 1997-case ledger's `fresh_baseline_geometry_replay_completed=false` describes its creation time. It is not the current baseline state. The new runner requires the immutable completed baseline receipt `04fa1ebb37f5dace29946224fe8c7c5d8a1bedb4fa860c65b359f4200415de57`, bound to the immutable 1931-case snapshot `bc3563a0c9955a561f99cbefe7278e027feff085ff6d97bc338e347f97514545`. It records completion of that earlier replay separately from replay in the present run. It does not rerun the baseline aggregator or overwrite its completed receipt.

The ten additions pending after the last strict checkpoint are:

`927, 998, 1111, 1112, 1114, 1115, 1124, 1125, 1128, 1143`.

The target is 1931 baseline exclusions plus 76 distinct additional exclusions = **2007 excluded / 177 remaining**. The script rejects duplicate extension coverage, baseline overlap, missing selected receipts, inconsistent transfers, and any difference from the fixed candidate set. It leaves `[438, 999, 1462, 1659]` unresolved and always reports `global_optimality_proved=false`.

## Inputs and packaging

`SOURCE_INVENTORY.json` lists each file's absolute source, portable target relative to the package root, expected SHA-256, byte size, roles, and affected cases. The inventory has 304 unique files, covering:

- All 76 selected exclusion receipts and their direct/cached/tree/overlay proof kinds.
- All listed producer nodes, parent references, wall seeds, and referenced seed provenance.
- Recursive cached premises, both native adapters, the complete 1383 partition tree, all reviewed checker dependencies, and the adapter's transitive cached-node/tree imports.
- Both D4 overlay exclusions, source hulls, finite-support/geometry receipts and their named source inputs, plus their checker sources.
- Completed baseline root/provenance receipts, the frozen 76-case selection, and the previous strict 1997-case snapshot.
- Source-program provenance declared in producer trailers, the historical replay wrapper, and the phase2 helper sources that it could actually import.

Small files up to 200,000 bytes were hashed while preparing the inventory. No large file was hashed. Large producer metadata was read only from an 8 KiB prefix and 32 KiB suffix; each seed used an 8 KiB suffix; the finite-support receipt used a 4 KiB header. These bounded metadata reads identify references, not proof validity. The full verifier must verify all whole-file hashes and strict source ancestry.

The completed baseline's full 59+34 geometric source package remains the separate baseline packaging obligation. This prior-extension inventory deliberately binds its immutable completed root receipt and provenance without duplicating its entire packaging task.

No proof file is copied by the prepared scripts. Preserve original file bytes and the `target` directory layout when packaging. Preserve historical receipts; do not rewrite their source paths or backend hashes in place.

## Root execution

Use the packaged `code/replay_prior.py` entrypoint and the command in `PORTABLE_EXECUTION_PLAN.json`. Run one integration process with numerical thread counts set to one. `EXECUTION_PLAN.json` preserves the original-workspace command for provenance.

The runner requires `--inventory-sha256` and refuses optimized Python. It first streams and verifies the prepared file inventory, then invokes the source-pinned strict generic/tree validators and the source-pinned D4-necessity consumer. These are inventory/induction/necessity checks, not a repeat of the already completed geometric searches or v9 replays.

Portable outputs go to `results/prior-union/` by default:

- `validated-source-inventory.json`: whole-file hash results and portable targets.
- `progress.json`: completed strict receipt records.
- `PRIOR_UNION_RESULT.json`: exact 2007-case set, 177-case complement, per-case evidence, ten-case reconciliation, checker/input bindings, and precise replay-reuse scope.

The old partially completed tree mutation suite is not claimed complete by this runner. Its result explicitly sets `negative_control_suite_completion_claimed=false`. Any separate final-revision control obligation remains separately labeled.

## Portability implementation

The source-frozen validators and integration runner retain their original bytes. Direct invocation of the original runner still refuses relocation. The separately reviewed packaged `code/replay_prior.py` adapter translates historical logical addresses to exact declared package files in a dedicated process. It handles compared directory roots as well as file opens, loads five proof modules from hash-checked explicit package paths, disables packaged bytecode, and rejects undeclared or external proof reads. Its output directory must not contain any declared input. POSIX paths are supported; Windows historical-path handling is not implemented.

The historical GMP 2.3.1 binary identity in immutable receipts remains independently checked. The current GMP 2.3.1 binary is recorded separately and may differ because this is inventory reuse, not new geometry. Only three kinds of overlay result path fields are restored to their historical logical spelling for full-receipt equality; all mathematical and hash fields retain exact equality.

`PORTABLE_ADAPTER_PLAN.md` documents the implemented adapter, its narrow path/provenance changes and its limits. `PORTABLE_PRIOR_IO_TRACE.json` records the launcher hash, every imported proof-module origin, current and historical backend identities, and package inputs read. The Python audit hook is a trace and accidental-fallback guard, not an operating-system security sandbox. Ordinary interpreter/runtime libraries are allowed separately; all proof inputs must come from the declared package inventory.

Independent synthetic I/O checks passed all 22 controls against the same adapter source hash. They cover root relocation, three open interfaces, missing package inputs despite historical originals, undeclared/external reads, bytecode rejection, exact-native runtime access and output isolation. These do not replace geometry or complete the separate historical tree mutation suite.
