# Implemented restricted portable integration adapter

The preserved filename reflects the original plan. The implementation is now `replay_portable.py`, installed as `code/replay_prior.py` in the final package. It composes the completed, hash-bound prior proof receipts without rerunning geometry. The execution is a separate step; source review and syntax parsing do not count as a successful replay.

## Immutable inputs and address translation

`SOURCE_INVENTORY.json` is pinned at `bec43e9ea5d9f3e3dbfdad6a07bf58190ba8edaac815732266a3201b1386b800`. Its 304 entries give original logical addresses, package-relative targets, expected whole-file hashes, byte sizes and roles. The original integration runner is unchanged at `89f602362f6d129e2a539af1d971cb8ca6361a0cc4cb03c802616c6db67fa0bc`; it hashes every declared input before invoking the strict receipt validators. The manifest and each imported proof source are checked before parsing or loading. Large inputs are then streamed and hash checked by the unchanged consumer.

The adapter maps historical paths to declared package targets and maps historical directory roots consistently for the original runner's comparisons. It never checks for an old proof file as an alternative source. Missing package inputs fail even if the original files still exist. Duplicate identities, unlisted file reads, escaping paths, packaged bytecode, and result directories containing proof inputs are rejected. The source-frozen runner still refuses relocation when invoked directly without the adapter.

The implementation installs process-local wrappers for Path.resolve/stat/lstat/open, builtins.open and io.open because frozen consumers use all of these entrypoints. This supersedes the earlier proposal to change separate consumer copies. A Python audit hook independently rejects proof reads outside the exact package allowlist and filesystem writes outside the selected results directory. Normal interpreter libraries and the independently recorded native binary are separate runtime dependencies; the guard is not an operating-system sandbox. POSIX package relocation is supported; Windows historical address syntax is not implemented.

## Frozen proof consumers

An explicit source finder loads only the designated, whole-hash-checked sources for strict_generic_inventory, strict_tree_inventory, audit_overlay_exclusion, overlay_field_halfplanes_v2 and prior_integration_frozen. No historical directory import fallback is retained. Generic source `7df54d904bb5d0cc609a4765eeafc3fb57922bcb3a4b210082df9fda36266530`, tree source `b6a298ccfa1a27911b3e88c832f890a983e0c6e7c374455808e42eb730626059`, dependency-pin manifest `8a46589d35e3bbd1efce02b2a196db5ddb636a85259bf7f30d6b31daa65b01f8` and all mathematical checks remain unchanged.

The original generic validator's native runtime fields are specialized solely for historical receipt comparison: the pinned receipts must name GMP 2.3.1 with historical binary SHA-256 `4fdf5fbaea9d3c4f756f9f656d0d7656fc4a66c82a8e921f326e570702dc463d`. The current loaded GMP 2.3.1 binary is hashed and reported separately. This does not claim those receipts were produced by the current binary and does not alter a proof result or receipt byte.

For overlay output, only `source`, `geometric_audit` and `checked_ancestry[*].path` are converted from the physical package path back to the corresponding immutable historical logical identity. The unmodified integration runner then compares the entire produced result with the pinned saved receipt. No mathematical, rational, mask, hash, ancestry, partition, cached-premise or status field is normalized away.

## Baseline and coverage obligations

The runner requires the completed fresh baseline receipt `04fa1ebb37f5dace29946224fe8c7c5d8a1bedb4fa860c65b359f4200415de57`, bound to the immutable 1931-case snapshot `bc3563a0c9955a561f99cbefe7278e027feff085ff6d97bc338e347f97514545`. It records that earlier replay as complete and present-run geometry as false. The full 59+34 baseline source package remains separately packaged and verified.

Exactly 76 frozen extension receipts must each exclude their assigned singleton, with no duplicated extension and no baseline overlap. The union must equal the fixed 2007-case candidate set and differ from the old 1997 strict set by exactly `[927, 998, 1111, 1112, 1114, 1115, 1124, 1125, 1128, 1143]`. The 177-case complement must retain `[438, 999, 1462, 1659]`. This composition is not the final global theorem.

## Historical provenance and controls

The historical common wrapper could load the phase2 convex-combination helper while listing phase3 sibling dependencies. Both source profiles and the wrapper are included in the inventory; the relevant helper and parse function bodies were identical exact-rational code in static review. New geometry replay is separately managed by root with explicit phase3 import provenance.

Independent source review identified and fixed the results-directory overlap loophole, and distinguished exactly the current native runtime binary from arbitrary files inside a package-local virtual environment. Source review found no further POSIX integration blocker. Actual acceptance, relocated execution and negative controls are separate result obligations and are not asserted complete here. The earlier 16/19 tree mutation controls ran against an older source revision and remain explicitly incomplete.

The output trace records all proof-module origins, adapter hash, package input reads, output hashes and both runtime identities. Historical receipts remain byte-for-byte unchanged. No external proof fallback, current geometric replay or global optimality claim is made by this adapter.
