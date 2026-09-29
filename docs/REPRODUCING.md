# Reproducing the computation

Use Python 3.12 or later, with assertions enabled. Install the exact dependency
versions in `requirements.txt` in a virtual environment:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -B VERIFY.py
```

The last command decodes the included certificate inputs, then runs the full
23-stage driver. It stops at the first error. It checks geometry and algebra;
it does not accept a theorem merely because an old file contains `PASS`.
A full replay can take hours. Intermediate output is generated under `work/`
and excluded from Git. There are no pre-existing execution logs in the repository.

On Windows, use `.venv\Scripts\python.exe` in place of `.venv/bin/python`.
Historical launchers were developed on POSIX systems; a native Windows full
replay has not been validated. Linux or macOS is the intended starting point.

To use a disk with more space:

```sh
.venv/bin/python -B VERIFY.py --workspace /path/to/empty-workspace
```

Input transport archives are reconstructed with deterministic, uncompressed
ZIP entries. The repository itself stores each distinct payload compressed
once. Consequently the decoded workspace is much larger than the download.
The launcher checks available space for a new workspace; replay outputs need
additional space. Never point it at your only copy of research data.

Two deliberately narrower operations are available:

```sh
python3 -B VERIFY.py --check-package
python3 -B VERIFY.py --prepare-only
```

The first checks the public distribution, including privacy and content hashes.
The second prepares the files. **Neither is a proof verification.** After
preparation, individual checkers and `RUN_ALL.py` live under `work/evidence/`.

## What is reproducible?

Verification checks a finite collection of supplied exact certificates.
Recreating the discovery search is a different task: the historical research
programs are included, but no claim is made that one command regenerates every
certificate or reproduces every heuristic search decision.

The source release predates this publication cleanup and records a completed
23-stage calculation. This public derivative changes addresses, transport
archives and the corresponding hashes. A fresh full geometric replay of this
public derivative is a separate validation obligation. See `PUBLICATION.md`
for the checks actually performed while preparing it.

Correctness still requires the mathematical implications in `PROOF.md` and
sound implementations of the checker rules. A successful process exit is not
an independent formal proof of those rules.
