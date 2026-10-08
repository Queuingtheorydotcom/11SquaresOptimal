# Eleven squares: owners, support chains, and angle penalties

[Read the manuscript source](eleven-squares-synthesis.tex) and
[download the self-contained verification supplement](eleven-squares-publication.zip).
The manuscript is a standalone LaTeX document with its figures and bibliography
included. Compile it with a standard LaTeX installation.

The argument combines a marker-based global reduction with a support-chain
inequality that allows the tilted squares to rotate independently. Quantitative
nonoverlap penalties control angle disagreement, replacing the late fine capture
and branched local-isolation endpoint. The paper also gives shorter certificates
for three ownership exclusions and states the boundary-preservation obligations.

## Verification

Extract the supplement, enter its top-level directory, and run:

```sh
python3 verify.py --check-inputs
python3 verify.py --quick --jobs 2
python3 verify.py --full --jobs 2
```

The checkers were tested with CPython 3.12.4 and use its standard library.
The supplement includes the required source and certificate inputs; verification
does not require the repository's large Git LFS dataset, a solver, Lean, or a
network connection. Full replay can take substantial time.

The underlying component computations and the selected 119-node dependency
closure were replayed during preparation. The portable full command has not yet
been executed end to end. Quick checks verify the small supplement under its
stated inputs; they do not establish the complete global argument by themselves.
The proof combines displayed mathematical lemmas with exact-rational Python
checks and is not a new Lean formalization or an independently refereed result.

The publication supplement contains mathematical inputs and verification code.
Optional completed-run logs and local execution records are omitted. Required
reference certificates remain inputs whose premises the verifier must check.
Inherited source notes describe their own historical stages; the manuscript and
the supplement's entry-point documentation state the scope of this proof.

## Sources

The global marker framework, strip supports, compulsory-hull propagation, and
selected pose-cover certificates come from the shared eleven-square proof cited
in the manuscript. The original proof in this repository informed the certificate
organization and residual estimates. Common-cone compression already appears in
the related `11SquaresFormalized` development. The principal new endpoint is the
independent-angle mixed-support comparison. The attaining packing is Trump's
pre-existing construction. Full references and attribution appear in the paper.

The repository's earlier [PROOF.md](../PROOF.md) and verification route remain
available separately. They use a different global case reduction.
