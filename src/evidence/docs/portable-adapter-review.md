# Portable candidate adapter: static review

No remaining source-binding or mathematical-behavior defect was found in
`replay_portable.py` at SHA-256
`fb8866d02e42aaf674e2ce966c8ab3fe0eb70e0d4f3957f7afd14cd117436d4b`
(17,073 bytes). This was source inspection only. No launcher, proof checker,
geometry replay, or mutation test was executed, and no large proof file was
hashed. Frozen evidence was not edited.

The adapter retains immutable proof bytes while mapping the exact historical
workspace prefix into the package. It canonicalizes proof paths, restricts
output opens to the results directory, removes permissive geometry fallbacks,
pins proof imports to packaged source, and disables packaged bytecode. The
revised prefix mapping handles serialized POSIX paths before Windows drive
conversion. Existing exact checker arithmetic remains intact; optional geometry
replays use the existing Fraction backend and compare source-bound mathematical
fields against the historical GMP receipts.

The added feature-bridge stage invokes the existing endpoint checker unchanged
and redirects its fixed receipt path into replay results.

Review findings addressed during preparation were two missing dependency paths
(the recovered center-cover checker and local analytic proof note), installed
namespace-package overrides, preloaded geometry modules, and the serialized-path
platform issue.

The I/O trace covers Python open audit events after setup; it is not an operating
system sandbox and does not cover native-library I/O or interpreter startup.
The consumer's optimized child interpreters reject execution before proof-input
reads and do not inherit the hook. Actual relocation, platform compatibility,
final package contents, and replay results remain for the parent's validation.
This review establishes no global packing theorem.
