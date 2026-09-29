# Optional fresh replay: tree 1383 and D4 overlays 2175/2176

This is an implementation plan from checker source and saved receipt/inventory metadata. No geometry checker was executed during preparation, and no producer file was rehashed. It supplements the already completed strict prior-inventory integration; it does not claim a new replay result.

## Recommended execution order and frozen interfaces

Use the parent's confined package loader and I/O adapter, one worker at a time. Preserve the original source and receipt bytes. Set the rational backend before importing `rational`; preload the actual native gmpy2 runtime if GMP is selected, so the frozen module's added historical dependency directory cannot choose a foreign binary. Fresh receipts must bind the current runtime, without substituting the historical binary hash used by inventory-only reuse.

1. Execute frozen `research/global-math/audit_overlay_geometry.py` as a module, with its fixed output redirected.
2. Execute frozen `research/global-math/audit_all_overlay_support.py` as a module, with its two fixed outputs redirected and reads of the geometry output redirected to step 1.
3. Replay tree 1383 with frozen `audit_tree_batch_v4.main()` and no certified cache.
4. For each overlay case, replay its terminal with frozen `audit_capture_v9.main()`, then call the original frozen `audit_overlay_exclusion.validate(terminal, fresh_geometry_receipt)` while the three fresh D4 premise read redirects remain active.

The first two scripts execute their work at module load and have no `main()` or output CLI. Use distinct module names and `spec.loader.exec_module(module)` exactly once per intended execution. The source finder must bind the frozen source hashes before execution.

Required pins already present in `SOURCE_INVENTORY.json` include:

| Source | Frozen SHA-256 |
|---|---|
| `audit_capture_v9.py` | `95ae3362ee4992c332960e4af53697dd3d1b31e381682051b49fd47700ad9d0c` |
| `audit_tree_batch_v4.py` | `04ceb52e087c7e2fec72a512bffb4b147e99391898d6ce1491215965bb715f8a` |
| `audit_overlay_geometry.py` | `17b9d97af0e9b7483a9add7ed732bcb929e08b38859283072a1a79d3b8d87ce9` |
| `audit_all_overlay_support.py` | `85e2e36bfe329652eb56bf666f3c6f3656ddace93eb4583c0d37286217c2098c` |
| `audit_overlay_exclusion.py` | `f3eefa77e6f02b977d6bfe38e5bc7e1e32fd6e355de7d226c803291b9a6ea5e1` |
| `overlay_field_halfplanes_v2.py` | `ee942f83af21aa2ab58b080b37cc95d5064d37b0458cfd2b93c2be8ab7ba1c74` |

## Three exact D4 output redirects

In this table all input-side paths are relative to the package root. `OUT` is a disjoint replay-results directory.

| Frozen logical path | Fresh destination |
|---|---|
| `research/global-math/overlay-geometry-independent-replay.json` | `OUT/d4/overlay-geometry-independent-replay.json` |
| `research/global-math/all-overlay-support-253/independent-replay.json` | `OUT/d4/all-overlay-support-253/independent-replay.json` |
| `research/global-math/all-overlay-support-253/supported-center-hulls.json` | `OUT/d4/all-overlay-support-253/supported-center-hulls.json` |

Create destination directories before installing a write guard if necessary. Redirect all three paths for both reads and writes, including `Path.open`, `Path.read_bytes`, `Path.read_text`, `Path.write_text`, `builtins.open`, and `io.open` through the parent's common mapper. The support script reads the fresh geometry receipt at its end and hashes its newly written support receipt when constructing the hull receipt. A write-only redirect would silently retain historical parent provenance.

Load and bind the immutable historical reference receipts before activating these read redirects, or use an explicit immutable-input reader that bypasses only the fresh-output redirect. Otherwise a comparison could accidentally read the new output as both actual and expected. The three original package files must remain unchanged.

Leave these read redirects active during necessity verification. `necessity.checked_context()` reads `HULLS`, its sibling `independent-replay.json`, and the geometry receipt; `audit_overlay_exclusion.validate()` hashes all three again. Call `necessity.checked_context.cache_clear()` before each validation (the frozen overlay checker already does so).

## Exact comparisons for fresh D4 premises

Normalize only each `sources[*].path` to its declared package-relative identity. Verify that identity rather than discarding the path field. Keep every corresponding SHA-256 unchanged and equal to the immutable input inventory. Ignore only `seconds`, after requiring the complete expected top-level key set.

For geometry require the exact key set:

```python
GEOMETRY_KEYS = {
    'status', 'sources', 'checker_sha256', 'regions',
    'degenerate_regions', 'exact_distance_bans', 'seconds', 'scope',
}
```

The normalized fresh and historical dictionaries must be equal after removing `seconds`. Require `sources` to have exactly `cover`, `overlay`, and `distance`, each with exactly `path` and `sha256`. Expected outcome: `PASS_INDEPENDENT_EXACT_OVERLAY_GEOMETRY`, 220 regions, 8 degenerate regions, and 1572 exact distance bans.

For finite support require the exact key set:

```python
SUPPORT_KEYS = {
    'status', 'scope', 'sources', 'checker_sha256', 'queries',
    'excluded_region_alternatives', 'surviving_witnesses', 'receipts',
    'positive_cover_frame_bounds', 'seconds',
}
```

Again require full normalized equality after removing `seconds`. `sources` must contain exactly `snapshot`, `cover`, `overlay`, `distance`, and `discovery`. Compare every receipt, including each exhaustive-search node count, and the entire positive-coordinate bound map. The frozen source is deterministic for these fixed ordered inputs; no receipt or counter should be dropped from comparison. Require `PASS_INDEPENDENT_FINITE_SUPPORT_REPLAY` and source hashes matching the unchanged inventory. The `cover`, `overlay`, and `distance` source records must identify the same files and hashes as the fresh geometry receipt. The snapshot hash remains `bc3563a0c9955a561f99cbefe7278e027feff085ff6d97bc338e347f97514545`.

For the supported hull result require exactly:

```python
HULL_KEYS = {
    'status', 'U', 'parent_independent_replay_sha256',
    'parent_geometry_replay_sha256', 'scope', 'hulls',
}
```

Require `parent_independent_replay_sha256 == sha256(fresh_support_receipt)` and `parent_geometry_replay_sha256 == sha256(fresh_geometry_receipt)`. Compare every other field exactly with the preserved historical hull result. The entire hull map, owner/region lists, positive vertices, centered vertices, exact U, status, and scope remain equality obligations. The parent hashes legitimately change because the new receipts contain new timing and path spellings; do not merely ignore them.

These scripts replay the overlay geometry and finite support premises, but retain the independently established 1931-case baseline and capacity-one cover as named inputs. The v9 fresh wall-seed constructor also runs the exact cover audit. No new global-optimality conclusion belongs in these receipts.

## Tree 1383: no historical cache required

Frozen CLI:

```text
audit_tree_batch_v4.py TREE --generic --output FRESH_TREE_AUDIT
```

Do not supply `--root-audit` or `--certified-cache`. The exact TREE is `research/endpoint-audit/mask1383-two-branch-tree.json`, with authoritative hash `7a9bf9e6738d9aa22fb4eccff97e815a0ff29f44411911b59171ddd5e0eae889`.

Its fresh wall seed is `research/endpoint-audit/mask1383-fresh-v5-seed.json`, SHA-256 `12f680f755f2aae2da87cec8156a77af36dc3679cbb84e3a5b325e22fad69deb`. The unconstrained root receipt is `mask1383-self-collision-r3.json`, SHA-256 `b72e9019736c5f0f3798117a43a6006200537b158ad714ca1e270589829a64d2`.

The partition is owner 13's centered y coordinate at `4/3`. Leaves are:

| Leaf | Terminal relative to `research/endpoint-audit/` | SHA-256 |
|---|---|---|
| `r.le` | `mask1383-y13-le-four-thirds-r2.json` | `60ccd3c82478cb06cae96e029cedf7f445efe1cb6f174ba3c6209a02c06f6129` |
| `r.ge` | `mask1383-y13-ge-four-thirds.json` | `07a0efb7d4befa2be3e77de75aa506940e00b1681eec85db08b7f7a5f1730d80` |

The frozen v4 checker constructs a new `Replay`, loads an empty list of certified caches, checks the partition, and recursively replays both leaf chains. Its in-memory cache only avoids redoing a shared ancestor already checked during this same execution. No historical audit receipt is imported as a geometry premise. Expected inventory is eight distinct nodes, 260 complete steps, **36600 replayed rows**, **0 cached rows**, and two closed leaves. All 20600 rows formerly imported from the r3 receipt are replayed anew.

Compare every common top-level field exactly with the historical tree receipt except the explicitly different fields below. Normalize node paths to declared identities, and remove only the old `cached_from_audit_sha256` tags for record comparison; require no such tags in the fresh nodes. Compare the complete ordered node records, including row/step/slab/promotion counts, conditions, hashes, and conclusions.

Explicit differences/requirements:

- `premise_audits == []`; `rows_replayed_this_run == 36600`; `rows_in_cached_premises == 0`.
- `seconds` varies. Current `rational_backend`, `rational_backend_version`, and `rational_binary_sha256` must match the actual selected runtime, not the historical runtime.
- Raw frozen v4 does not emit `native_portability_adapters` or `native_portability_scope`; require their absence rather than inventing old adapter provenance.
- Require `status == PASS_INDEPENDENT_PARTIAL_TREE_AUDIT`, `complete is True`, `unresolved_leaf_ids == []`, `mask_exclusion_proved is True`, `generic_mode is True`, `mask_reduced_to_local_guard is False`, `root_audit_sha256 is None`, transfer list `[1383]`, count 1, and `global_optimality_proved is False`.
- The exact dependency map remains the historical 11-file map (v4 plus the ten geometry dependencies). No dependency hash is waived.

Do **not** feed the raw fresh no-cache receipt to the frozen `strict_tree_inventory.validate` profile: that historical profile requires an explicit verified root premise and the native adapter list. Compare the new complete replay inventory against the already strictly validated historical tree evidence, and preserve it as a separate fresh-replay profile. An alternative compatible profile would replay the root prefix freshly with v9 and then use that new receipt as a v4 cache, but the recommended no-cache workflow is simpler and avoids importing any receipt.

## Overlay cases: fresh conditional geometry, then fresh necessity discharge

For each case the frozen v9 CLI auto-detects the generic producer schema:

```text
audit_capture_v9.py TERMINAL --output FRESH_GEOMETRY_AUDIT
```

There is no `--generic` flag on this CLI. Do not pass `--root-audit`; both seeds are `generic_wall_seed_v1`. `Replay.replay()` recursively follows and verifies every parent, beginning from the seed; no certified-cache argument exists. These two terminals each have no parent and require one node replay.

| Case | Terminal | Seed hash | Rows | Complete steps | Conditions | Seed checks |
|---|---|---|---:|---:|---:|---:|
| 2175 | `research/frontier/mask2175-overlay-v1.json` | `5652ab13cf7f9ea2c2baf955b7e94e04646d6fde45b94ad8b8b2970f7dec1e3c` | 832 | 13 | 72 | 77 |
| 2176 | `research/frontier/mask2176-overlay-v1.json` | `f89e3d6b081996e887eb6ae51719c8acb93270c74b0c25060f5f8e557dff5c9d` | 1088 | 17 | 73 | 75 |

Each seed filename replaces `.json` with `-seed.json`; each bootstrap has 704 rows covering the full angle interval `[0,1]`. Source hashes are `68864a2b4937e24985c17c6408170e7d514ebe8a71e894ab0e48a17b3e96beb5` and `6cee7964d44292b13189c950ae43c10f8d66389de860c0b319a0dc509dafbaa0`, respectively.

Compare the entire fresh geometry receipt to its historical `maskNNNN-overlay-independent.json` after normalizing node paths and removing only `seconds` and the three runtime-provenance fields. Check those three runtime fields separately against the actually used runtime. Require exactly the same key set, dependency map, root/source/cover/final-state hashes, bootstrap and seed checks, complete node records, masks, scales, and every condition. The expected geometry result is conditional: `branch_exclusion_proved=True`, `inside_local_guard=False`, `mask_exclusion_proved=False`, empty transferred list, and count 0. Do not turn this receipt alone into an unconditional exclusion.

Then run the original frozen function:

```python
# All three fresh D4 premise read redirects are already active.
fresh_exclusion = overlay.validate(terminal_path, fresh_geometry_audit_path)
```

Do not call the inventory-only adapter's `portable_overlay_validate` wrapper: its historical logical-identity restoration correctly rejects a new geometry receipt under the results directory. Keep the newly generated receipt's actual path and hash.

For exclusion-result comparison, normalize only `source` and `checked_ancestry[*].path`. Require complete dictionary equality with the preserved historical result except these five explicitly rebound fields:

```python
assert fresh_exclusion['geometric_audit'] == str(fresh_geometry_audit_path.resolve())
assert fresh_exclusion['geometric_audit_sha256'] == sha256(fresh_geometry_audit_path)
assert fresh_exclusion['source_hulls_sha256'] == sha256(fresh_supported_hulls_path)
assert fresh_exclusion['support_replay_sha256'] == sha256(fresh_support_receipt_path)
assert fresh_exclusion['geometry_replay_sha256'] == sha256(fresh_overlay_geometry_path)
```

All other keys, source and checker hashes, baseline binding, exact domain, plane counts 72/73, full ancestry inventory, status, and conclusions must remain equal. This reruns every necessary-plane check on the freshly supported original region vertices while binding the new geometric audit. It yields the unconditional case exclusions under the named 1931 baseline.

## Inputs and loader requirements

All source/dependency/seed/producer/tree/support inputs identified above are already in the 304-file inventory and present at their source locations according to metadata-only presence checks. No extra local-guard packet, Phase2 root audit, producer engine execution, historical Linux GMP library, or saved cache receipt is needed by these fresh profiles.

The loader must include frozen `audit_tree_batch_v4` and `audit_capture_v9`, plus the v9 executable dependency modules: `rational`, `arrangement_audit_v2`, `arrangement_audit`, `audit_residual_kernel`, `audit_wall_kernel`, `audit_kernel_survivor`, `validate_collision_kernel_v3`, `own_hull_constraints`, and `audit_center_cover`. It must also bind the two fresh D4 scripts, `audit_overlay_exclusion`, and `overlay_field_halfplanes_v2`. The native cached wrappers and their cached-v2/v3 dependencies are unnecessary for the recommended no-cache replay.

Override the frozen v9 `locate` helper with an exact declared-target resolver: the original helper includes basename and historical-work fallbacks. Package path mapping alone does not express the stricter no-fallback policy. Generated results are allowed only at their explicitly assigned output paths. Use each source file's real package `__file__` so its dependency hashes retain the frozen source identity.

The optional runner should report each stage separately, retain all newly generated receipts, bind their actual hashes, and only mark the fresh 76-case extension workflow complete when all ordinary generic/cached profiles handled by the parent and these three special cases pass. It must retain `global_optimality_proved=False` for this prior-extension component.
