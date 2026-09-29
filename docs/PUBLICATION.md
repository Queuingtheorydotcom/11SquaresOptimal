# Publication scope and validation

This is a privacy-normalized, source-and-certificate publication derived from
the completed computational release. It contains no console execution logs,
run-history directories, user conversations, virtual environments or Git author
history. Mathematical certificate/audit JSON needed by the existing consumers
is included; such an input is not a substitute for recomputing its premises.

## What changed

- The private workspace prefix was replaced consistently by the logical prefix
  `/workspace/eleven-square`; other home paths use `/home/researcher`, and private
  temporary-directory identifiers use `/tmp/session`.
- Content hashes were recomputed in dependency order. Literal hash pins,
  manifest entries, file lengths and the aggregate manifest length were rebound
  to the public bytes. Original digests remain only as opaque provenance IDs
  in `data/INDEX.json`; the public `sha256` fields identify actual public bytes.
- Returned-case ZIPs retain the members required by the replay plan. Their
  source scripts are supplied separately where they add to the source collection.
  Unneeded archive logs, caches and metadata are absent.
- The legacy continuation ZIP becomes an empty transport marker. Its required
  proof files are already present individually at the paths bound by the
  baseline inventory. No verifier reads its old redundant members.
- Historical runtime binaries that consumers reference only for provenance
  are replaced by explanatory text markers and corresponding updated hashes.
  They are never executed by the portable replay. Install the live arithmetic
  dependencies through `requirements.txt`.
- Distinct payloads are stored once, in gzip files without original filenames
  or timestamps. ZIP recipes reconstruct deterministic entries with a fixed
  timestamp. The data store contains 2,646 indexed objects representing 2,524
  decoded paths. Compressed certificate storage is approximately **2.34 GB**;
  decoding all paths takes approximately **11.3 GB**, before new replay output.
- The available research and archived source collection is exposed under
  `src/`. It includes 978 Python files, plus C++/SMT sources and supporting notes.
  Public attribution and third-party license notices are retained.

The mathematical formulas, rational certificate coordinates and checker rules
were not intentionally changed. Privacy normalization does change source and
certificate bytes; this publication therefore does **not** claim byte identity
with the private historical release.

Private execution-approval and CPU-preference references were also removed
from historical notes, plan metadata and source comments. Their dependent
content hashes and manifest sizes were updated consistently.

## Checks performed during publication preparation

The publication integrity check passed. It:

1. Decompressed and hashed every stored payload, reconstructed every ZIP recipe
   and checked lengths and digests against the public index.
2. Checked that the browsable source copies agree with the encoded sources.
3. Parsed all 978 Python source files.
4. Checked the inventory excludes execution logs and bytecode.
5. Scanned decoded payloads and public files for private home paths, workspace
   IDs, private temporary paths and common credential markers.

The final composition checker also accepted the sanitized inputs, recovering
exactly 2,180 excluded canonical cases and residual cases 438, 999, 1462 and 1659.
It checked 1,861 proof-manifest entries totaling 11,298,167,390 decoded bytes.
This diagnostic used a read-only virtual filesystem for the compressed inputs
to inspect the compressed inputs without requiring an additional decoded workspace.
Payload and reconstructed-archive hashes were recomputed, rather than replaced
with unverified claimed digests. This is an integration diagnostic, not a native
end-to-end execution of the public launcher. Its complete adapter is published
as `tools/check_composition.py`; run it with the installed proof dependencies
to repeat this narrower check without decoding the whole workspace.

**A fresh full geometric replay of the sanitized public derivative has not been
performed as part of publication preparation.** The source project records a
completed full computation; its console logs are intentionally not distributed.
Run `python3 -B VERIFY.py` with the required dependencies and enough disk space
to perform a new full replay. `--check-package` checks distribution integrity
and privacy patterns only and never claims to prove optimality.

The privacy checks target the known private identifiers and common secret
patterns; they are not a mathematical guarantee that every possible personal
reference can be detected. The repository has no commits or configured remote.
