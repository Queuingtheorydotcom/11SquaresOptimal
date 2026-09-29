#!/usr/bin/env python3
"""Verify packet 06 hashes and rerun the frozen independent geometric checker."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CHECKER = ROOT / "code/research/phase3/work/phase3/hull/audit_capture_v9.py"
WRAPPER = ROOT / "code/research/frontier/audit_case.py"
PINNED = "95ae3362ee4992c332960e4af53697dd3d1b31e381682051b49fd47700ad9d0c"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_manifest() -> None:
    for line in (ROOT / "SHA256SUMS").read_text().splitlines():
        expected, name = line.split(maxsplit=1)
        path = (ROOT / name).resolve()
        assert path.is_relative_to(ROOT) and path.is_file(), name
        assert sha(path) == expected, name
    assert sha(CHECKER) == PINNED


def replay(entry: dict) -> None:
    receipt = ROOT / entry["source"]
    saved = json.loads((ROOT / entry["independent_audit"]).read_text())
    with tempfile.TemporaryDirectory(prefix="eleven-square-06-") as temporary:
        output = Path(temporary) / "audit.json"
        env = dict(os.environ, OPENBLAS_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1")
        cmd = [sys.executable, str(WRAPPER), str(receipt), "--output", str(output)]
        print(f"Replaying case {entry['mask_index']} ...", flush=True)
        with (Path(temporary) / "audit.log").open("w") as log:
            subprocess.run(cmd, cwd=ROOT / "code", env=env, stdout=log,
                           stderr=subprocess.STDOUT, check=True)
        fresh = json.loads(output.read_text())
        assert fresh["status"] == "PASS_INDEPENDENT_GENERIC_HULL_AUDIT"
        assert fresh["mask_index"] == entry["mask_index"]
        assert fresh["source_sha256"] == entry["source_sha256"] == sha(receipt)
        assert fresh["mask_exclusion_proved"] is True and fresh["constraints"] == []
        assert fresh["parent_Uplus"] == saved["parent_Uplus"]
        assert fresh["root_sha256"] == saved["root_sha256"]
        assert [(node["sha256"], node["branch_exclusion_proved"])
                for node in fresh["nodes"]] == [(node["sha256"], node["branch_exclusion_proved"])
                                                 for node in saved["nodes"]]
        print(f"PASS case {entry['mask_index']}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", type=int, help="replay one assigned case (default: all proved cases)")
    args = ap.parse_args()
    if not __debug__:
        raise SystemExit("Assertions must be enabled: do not run Python -O or -OO")
    verify_manifest()
    result = json.loads((ROOT / "result.json").read_text())
    entries = [e for e in result["results"] if e["status"] == "proved"
               and (args.case is None or e["mask_index"] == args.case)]
    if not entries:
        raise SystemExit("No proved case matches the selection")
    for entry in entries:
        replay(entry)
    print(f"PASS all {len(entries)} selected independent audits")


if __name__ == "__main__":
    main()
