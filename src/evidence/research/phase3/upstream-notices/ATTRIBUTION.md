# Sources and attribution

This work builds on **Joshua Levy, the squares project
(https://github.com/jlevy/squares)**, particularly the T-026 threshold certificate
at revision `7ccb679cc0827d10ee80e2cd1988c8a07d65dfdc`. Weighted covering,
threshold-counting budgets, exact event-cell sweeps and strict-core arguments
are part of that prior work.

## What comes from where

| Component | Source and changes |
|---|---|
| [global-certificate.json](global-certificate.json) | Developed from Levy's [T-026 certificate](https://github.com/jlevy/squares/blob/7ccb679cc0827d10ee80e2cd1988c8a07d65dfdc/packing/cases/n11_threshold_certificate/certificate-191-50-net1440.json). Site coordinates were rounded, sites and threshold families added, weights reoptimized, and the angle/core catalogue replaced. The final data were verified afresh. Levy's source documentation/data are CC BY 4.0; the original licence and attribution obligations are retained. |
| [exact_mixed.py](exact_mixed.py), [integer_sweep.py](integer_sweep.py) | Generalized from this project's published [s(17) Python checker](https://github.com/Kleddamag/17-squares-certified-bound/tree/v1.0.0). They use rational polygon-edge geometry and signed integer range minima for the point and threshold charges. |
| Reconstructed JavaScript checker | Adapts [Guzhou0806 / N17 project's R038 checker](https://github.com/Guzhou0806/n17-square-packing/blob/32edfd3da78bf80a309398f552b3b602b9c45d6c/certificates/R038/src/exact_parent_side_scan.js), revision `32edfd3da78bf80a309398f552b3b602b9c45d6c`, published with AI assistance. The adaptations add weighted threshold expansions, generalized coordinates and certificate validation for this s(11) result. Its clamped-extrema geometry is implemented separately from the Python polygon-edge geometry. |
| Earlier implementation lineage | [Mira's 17squares certificate attribution](https://github.com/Mira-acc/17squares/blob/ac464dd06ded72e2f6eb2c2f3d510b01391c056d/certificates/lower_bound_4p614153/ATTRIBUTION.md) records the Levy/Guzhou/Mira lineage inherited through the s(17) work. The numerical starting certificate for the present s(11) result comes directly from Levy's T-026. |

The threshold predicate charges a core for capturing at least $k$ of $m$
distinct sites, with budget $\lfloor m/k\rfloor$ across disjoint cores. This
certificate combines ordinary point charges with two-of-three, two-of-five
and three-of-five charges. It does not claim independent invention of the
underlying weighted-covering or threshold-counting methods.

## Source identity and terms

[prepare_secondary.py](prepare_secondary.py) reconstructs the JavaScript
checker from pinned upstream bytes and the edits in
[secondary-adaptation.json](secondary-adaptation.json). It verifies both hashes:

| File | SHA-256 |
|---|---|
| Original R038 checker | `63e858e28c4dee40f5763a832e1cfdf1f1fce3a1e5c632d087525bf1ee20ed14` |
| Reconstructed checker used in verification | `c1e76f97a9288b3ad7537a282fbf24437a96980ae66c5414bca0793ad5d39c0e` |

No general source-code licence grant was identified for the pinned R038
JavaScript file. Its full source and the complete derivative are therefore
not distributed here. Local reconstruction grants no additional upstream
rights. [LICENSING.md](LICENSING.md) explains the applicable terms.

The [notice index](NOTICES/README.md) links every preserved notice to its
pinned source. Levy's [full licence](NOTICES/Joshua-Levy-LICENSE.txt) distinguishes
MIT code, CC BY 4.0 documentation/data and separately governed third-party
works. No archived third-party papers are distributed.

See [AUTHORS.md](AUTHORS.md) for Kleddamag's and Codex's contributions.
Source credit does not imply endorsement or coauthorship by the upstream authors.
