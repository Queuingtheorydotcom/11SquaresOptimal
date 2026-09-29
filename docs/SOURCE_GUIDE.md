# Reading the source

`src/evidence/` mirrors the paths used inside the decoded proof workspace.
`src/discovery/` contains the additional available research programs. Duplicate
versions are intentional: a later research version must not silently replace
the version bound to a certificate. The content index identifies each version.

Start with:

- `src/evidence/code/verify_recorded_proof.py`: final theorem composition,
  exact exclusion sets, premise bindings and scope checks.
- `src/evidence/RUN_ALL.py`: full replay stage order.
- `src/evidence/research/phase3/work/phase3/hull/audit_capture_v9.py`:
  independent rational polygon/orientation certificate replay.
- `src/evidence/research/finalization/baseline-portable/verify_baseline.py`:
  baseline replay and smaller-antecedent transfer bookkeeping.
- `src/evidence/code/replay_prior_geometry.py`: 76 extension cases.
- `src/evidence/code/verify_returned.py`: 173 additional cases.
- `src/evidence/research/finalization/global-composition/audit_d4_bridge.py`:
  exact closed overlay and finite symmetry argument.
- `src/evidence/research/global-math/audit_focused_local_box.py`:
  quantitative local isolation using exact dual inequalities.
- `src/evidence/research/candidate-capture/audit_complete_capture438.py`:
  candidate branch coverage, coordinate frames and final capture composition.

Discovery programs are organized under the original research areas:
`phase3/`, `frontier/`, `endpoint-audit/`, `candidate-capture/`, `local-radius/`
and `global-math/`. These include intermediate and unsuccessful approaches;
being present in the research archive does not make a script part of the proof.
Several expect particular certificate states or command-line arguments.

For the final replay, use the entry point at the repository root. Source files
are browsable copies, checked against the content index. To experiment with
modified mathematical checkers, first prepare a separate workspace, modify that
workspace and consciously update the relevant dependency pins. Such a modified
run is a different proof computation and should be reviewed as such.
