# Licence scope

The [MIT licence](LICENSE) covers this project's original code, documentation
and additions, to the extent the project can grant those rights. It does not
relicense upstream material.

## Joshua Levy's source material

The s(11) certificate was developed from Joshua Levy's T-026 data. The
[pinned source licence](NOTICES/Joshua-Levy-LICENSE.txt) grants MIT terms for
code and CC BY 4.0 for documentation and data, excluding separately governed
third-party works. Those source attribution obligations continue to apply
to adapted material, including [global-certificate.json](global-certificate.json).
[ATTRIBUTION.md](ATTRIBUTION.md) identifies the source revision and the changes
made here. The repository's MIT licence must not be read as removing the
CC BY obligations attached to the source data.

## Guzhou and earlier source notices

The pinned Guzhou R038 tree supplies attribution and licence-scope notices,
but no general licence grant was identified for its JavaScript checker.
The full upstream file and complete derivative are not bundled.
[prepare_secondary.py](prepare_secondary.py) fetches the pinned source,
checks its hash, applies this project's edits and checks the reconstructed
file's hash. A local download or reconstruction grants no additional rights
in the upstream material. An existing pinned file can be supplied offline.

The [preserved notices](NOTICES/README.md) also document the historical
Guzhou/Mira/Levy lineage of the checker. Their statements describe their own
source packages. Each source retains its own terms; no notice grants rights
over another author's contribution.

Python, Node.js, NumPy, Numba and llvmlite are installed dependencies and are
not redistributed with this package. Their own licences apply.
