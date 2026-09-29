# Prior-union portable adapter: independent source review

Status: source review only. No proof consumer was executed, no large proof file was hashed, and no geometric or inventory validation result is asserted by this note.

Reviewed `research/finalization/prior-union/replay_portable.py` together with its frozen `integrate_prior_union.py`, generic/tree inventory validators, overlay exclusion checker, and necessary-halfplane helper. The follow-up review inspected the two requested adapter fixes directly.

## Follow-up fixes

1. After adding the launcher and inventory manifest to the declared-file map, the adapter now rejects any result directory containing a declared input. Both paths are already resolved. This closes the identified `--output-relative research` issue: the results read exemption and write permission can no longer cover declared proof inputs, their pinned Python sources, the launcher, or the manifest.
2. Before applying the package declared-file rule, the read guard now permits only `p == native_binary`. That path was resolved from the independently loaded gmpy2 module and separately hashed before the guard was installed. This lets the unchanged generic validator inspect that current runtime binary when a venv lives inside the package. It does not exempt the binary's directory or other undeclared package files, and the write branch still executes first.

These two source changes address the concrete issues reported in the initial review. No additional POSIX blocker was identified in the reviewed execution path.

## Interaction checked by reading source

- On macOS/Linux, the historical workspace root resolves to the package root, so the frozen integrator's original-workspace refusal and every source/target equality remain meaningful under the explicit mapping.
- The five executable proof modules are selected by the custom source finder and checked against the declared hashes. Generic Validator is replaced before the tree validator imports that symbol.
- Original receipts and proof files are read without byte rewriting. The historical GMP version/hash are the receipt obligations; the current native binary is recorded separately. This is inventory/composition reuse, not a new geometric replay.
- Overlay normalization changes exactly its `source`, `geometric_audit`, and each `checked_ancestry[*].path` output field back to the corresponding historical logical identity. The frozen full-dictionary comparison retains the other fields.
- Path.open, builtins.open, and io.open use the same relocation mapping. The audit guard rejects undeclared package reads and reads outside the package/runtime exceptions; missing package proof files have no historical fallback.

## Remaining execution obligations

The root worker's separate integration result establishes execution status; this source-review note does not replace that result or its I/O trace.

The follow-up `synthetic_helper_controls.py` run passed all 22 controls against adapter SHA-256 `e2292e844827d811d61f8cefb0158442febae097cbcdc92e414dd59f018dde14`; see `SYNTHETIC_HELPER_CONTROLS.json`. The script AST-extracts the exact helper functions and output-overlap guard, uses tiny synthetic files, and enables the actual Python audit mechanism. It does not import or run the adapter module/main or any proof consumer.

The controls cover result/input overlap and a resolved results symlink, all three open interfaces, missing packaged input despite an existing historical original, root identity and missing-file stat mapping, undeclared/outside reads, packaged bytecode, exact native versus neighboring package runtime files, forbidden proof/native writes, permitted result writes, forbidden directory creation, and preservation of synthetic proof bytes.

The source finder and exact set of overlay output fields changed by normalization remain source-reviewed rather than exercised by this synthetic helper suite. No mathematical or proof-data validation is part of that suite.

Windows remains outside this source review's compatibility conclusion: the historical POSIX workspace string is rejected by the current `Path(...).is_absolute()` check on Windows. The immediate macOS/Linux run is unaffected.

This note does not claim that all 76 receipts have passed in the relocated package, that the final global proof is complete, or that the Python audit hook is an operating-system sandbox.
