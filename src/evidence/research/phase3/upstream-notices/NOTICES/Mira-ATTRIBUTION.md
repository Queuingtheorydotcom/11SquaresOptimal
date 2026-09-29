# Attribution, source identity, and scope

## Guzhou0806 / N17 project

R012 at commit `931a0dfd64302e277057006e99388fe5c00b7f53` supplies the concrete
n=17 parent-angle catalogue, rounded and reverified fixed measure, public exact
Python sweep, and retained failed-core witnesses audited here.

Source: https://github.com/Guzhou0806/n17-square-packing/tree/931a0dfd64302e277057006e99388fe5c00b7f53/certificates/R012

Credit for that completed certificate belongs to Guzhou0806 / N17 project, with
the AI assistance disclosed there. Their stated mathematical and programming
experience is not a reason to discount a valid exact argument. Their attribution
carefully distinguishes their application from antecedent ideas.

Five numerical/code/notice files are retained in `upstream/`. Their Git blob
hashes were matched to the pinned source while preparing this package; the
pinned commit and per-file lineage are recorded here. This is not represented
as a downloaded copy of the complete upstream repository or its original
manifest/CLI.

## Mira / 17squares

The spatial support originates in Mira's 4.613 certificate. Exact rounding to
1e-5 coordinates, upward rounding to 1e-6 weights, and coincident-point merging
reproduce R012's canonical atom table. The prior source endpoint is
`4.61302863588611076617...`, with squared value recorded in R012's catalogue.

This continuation adds adaptive interval refinement, maximal safe rational cores,
parent-aware weight exchange, and mixtures of unchanged and wall-adjusted support.
The new C++ implementation adapts Mira's earlier exact integer sweep, replacing
its core-containment center domain with certified parent envelopes. Its direct
prefix backend shares that geometry with its segment-tree backend.

The research and verification work were performed with ChatGPT assistance. The
result depends on executable exact certificates, not the assistant's authority.

## Joshua Levy / squares

Weighted covering, exact event-cell verification, strict-core transport, and the
parent-center restriction have prior work in Levy's squares project. Guzhou
explicitly cites the following parent-center note, which is an analytic antecedent
rather than an imported n=17 numerical certificate:

https://github.com/jlevy/squares/blob/fb14f5174fdf675b296b442c98b7127fccc8a84d/packing/cases/n11_five_dot_cover/unit-parent-centre-contract.md

The byte-identical R012 Python `sweep.py` retains that source lineage. Its MIT
notice, Copyright (c) 2026 Joshua Levy, is preserved in `upstream/LICENSE-MIT.txt`.
This notice is not presented as a blanket license for all third-party material.

The discussion of threshold atoms refers to Levy's actual n=11 construction:
https://github.com/jlevy/squares/blob/main/packing/cases/n11_threshold_certificate/t-025-verifiable-claim-191-50.md

The threshold-budget rule is attributed to that work. This continuation proves
that parent-aware transport also supports that rule, but does not claim to have
computed an n=17 threshold-atom result.

## Claim discipline

This audit is source and exact-computation review, not peer review or proof-assistant
formalization. A second accumulator is not a second geometric proof. The retained
original Python geometry and the newly written C++ geometry are compared honestly
in the audit logs, including whether a Python run is complete or only a subset.

No exhaustive world-priority assertion, global-optimality proof, new packing, or
ongoing automatic record-monitoring service is claimed. Historical and unsuccessful trials are not promoted from numerical solver objectives to exact obstruction theorems.

## Repository integration (2026-09-19)

This copy is the theorem-critical subset integrated into `Mira-Cult/17squares`
as `certificates/lower_bound_4p614153/`. Large discovery logs and redundant
replay JSONL files from the research bundle are intentionally omitted: they are
not trusted proof inputs and can be regenerated. The exact certificate bytes are
stored as `certificate.json`; the verifier checks the SHA-256 of the exact JSON
bytes before use.

For the broader historical and contemporary contributor map, including Stanislav
Fort, Sam Burns, Gustavo Massaccesi, anabologyco-maker, Trevor Green, Friedman,
Stromquist, Nagamochi, MacIver, Bidwell and Hämäläinen, see the repository root
`CONTRIBUTORS.md`. Those sources are distinguished there from direct dependencies
of this certificate.
