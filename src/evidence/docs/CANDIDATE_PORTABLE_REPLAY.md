# Portable candidate replay

Copy the immutable files listed in `candidate-file-list.txt` to the final
package, preserving their relative paths. Copy `replay_portable.py` as
`code/replay_candidate.py`. The file list contains a shared missing historical
D4 producer packet discussed in `REVIEW.md`; GlobalMath's new D4 checker is a
separate resolution of that issue. The candidate stages themselves do not
read that producer packet.

Two additional frozen sources were added during launcher review:
`research/recovered-checkpoint/research/optimality/audit/audit_center_cover.py`
and `research/recovered-checkpoint/research/classical/TRUMP-LOCAL-RADIUS.md`.
The final count is 84 files before any new final receipts or new D4 code.

The launcher is deliberately separate from the frozen mathematical checkers.
It maps the recorded original workspace prefix into the supplied package root,
preserves input JSON/source bytes, routes outputs into
`results/candidate-replay/`, and refuses proof reads outside the package.
Ordinary Python/NumPy/SciPy/SymPy runtime reads are allowed from explicit
library directories. The I/O trace lists packaged files read through Python
open events and historical path remappings. No program source in a certificate
is rewritten. Proof namespace and geometry modules are pinned to their exact
packaged source paths, preventing installed packages or stale bytecode from
silently replacing them.

This guard is not an operating-system sandbox: it does not observe native
C-library I/O, interpreter startup before installation of the hook, or general
subprocess activity. The consumer test's two optimized-Python child controls
are an explicit exception; their unchanged source refuses execution before
opening proof inputs. A independent relocation test remains required.

The launcher was first reviewed without executing proof code. It has now
passed all nine main stages from the relocated final package on the supplied
macOS/Python 3.12 runtime, including 40 verifier refusal controls. Every stage
used the same adapter hash and package-only Python I/O guard; no runtime or
path failure occurred. See `results/candidate-replay/summary.json` and
`SUMMARY.md` for all result and trace hashes. Other operating systems and the
optional complete Fraction geometry replays have not been executed here.

## Commands from the final directory

Use Python 3.12 or a compatible newer interpreter with NumPy, SciPy, and
SymPy installed. The frozen local modules import those libraries even though
the acceptance paths use exact arithmetic. The previous successful runtime
used NumPy 2.5.3, SciPy 1.18.1, SymPy 1.14.0, and Python 3.12. Keep assertions
enabled. The launcher refuses `-O` and `-OO`.

Run these stages sequentially:

```sh
python code/replay_candidate.py construction
python code/replay_candidate.py cover
python code/replay_candidate.py local-algebra
python code/replay_candidate.py local-baseline
python code/replay_candidate.py local-weighted
python code/replay_candidate.py focused
python code/replay_candidate.py feature-bridge
python code/replay_candidate.py composition
python code/replay_candidate.py consumer-tests
```

Each stage has its own result and `-io.json` trace. The launcher limits common
numerical libraries to one thread; it does not itself impose a CPU percentage
quota. Apply operating-system throttling if required.

`construction` invokes the frozen exact packing/verification functions, checks
all eleven shapes and all 55 pairs, checks the side polynomial and exact
`T<U`, and records exact opposite-wall contacts. `cover` invokes the frozen
center-cover replay. The three local stages invoke the original algebra,
baseline and weighted-coordinate checkers with output-path routing only.
`focused` replays the directional rectangle arithmetic and pose inclusion;
`feature-bridge` independently reconstructs the raw nonlinear feature choices
and their complete reduction to the 128 derivative matrices.
`composition` checks the full four-leaf implication using the completed,
hash-bound independent geometry premises. `consumer-tests` runs the existing
independent malformed-receipt tests without editing their inputs.

When running from another location, pass the exact package root:

```sh
python /path/to/package/code/replay_candidate.py composition --package-root /path/to/package
```

The old workspace must not be necessary. The final acceptance test should run
from a second directory where it is unavailable or denied. A manifest scan
should confirm no symbolic links escape the package. The launcher also
resolves paths before its read/write containment checks and ignores packaged
Python bytecode in favor of source.

## Replaying every geometric implication on another platform

The unchanged composition reads the archived Darwin GMP binary solely to
verify the binary hash recorded in the historical geometry receipts. It does
not import that binary. Include it as provenance data even on other operating
systems; a Linux or Windows machine is not expected to load a Darwin library.

The optional geometry stages select the already supported pure-Python
`Fraction` backend and replay complete source ancestry without cached prior
branch receipts. They can be much slower than the original GMP runs:

```sh
python code/replay_candidate.py root-geometry
python code/replay_candidate.py far15-geometry
python code/replay_candidate.py far13-geometry
python code/replay_candidate.py far2-geometry
python code/replay_candidate.py near-geometry
```

The branch stages require the fresh `root-geometry.json` created by the first
command. They do not substitute or forge a GMP runtime identity. They retain
the new `fraction` backend in their fresh receipts and compare their exact
source hashes, masks, scales, assumptions, final pose-state digests and
contradiction/capture conclusions against the historical receipts. The
root-stage comparison includes the complete per-round cell inventory and
exact replay counts. Backend fields, timing, root-audit hashes, and cache
inventory can legitimately differ.

These comparisons confirm the same mathematical conclusions from unchanged
source bytes under a new rational backend. Historical receipts remain
immutable; the fresh replay results and their explicit comparison traces are
additional evidence. The ordinary composition command continues to bind the
historical accepted receipts rather than pretending that their runtime fields
have changed.

## Relocation acceptance requirements

The final independent validation should confirm:

1. Every stage read only package proof files plus listed ordinary runtime
   libraries, and wrote only within `results/candidate-replay/`.
2. The packaged mathematical checker hashes match the original receipt pins.
3. The current composition result pins current checker
   `0ca02cfb0fa5304251f80fff0356dd63e33a87ffb74b8ada5c5a17cfa8afa040`.
4. A forged external proof reference or symlink cannot bypass the package-only
   resolver. The historical workspace must not be consulted even when it
   happens to exist.
5. All proof receipts retain their limited scope: candidate capture is only
   mask 438 at actual side `S<=T`; the complete global theorem additionally
   requires the independently verified noncandidate union and D4 bridge.

No command in this note claims global optimality by itself.
