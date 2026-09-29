#!/usr/bin/env python3
"""Portable independent replay of every proved packet 04 exclusion.

Requirements: Python 3.12 with assertions enabled; gmpy2 2.3.1, SymPy 1.14,
NumPy 2.5.3 (the exact v9 replay itself primarily uses gmpy2).
Use --mask M for one case. The bundled case-tools.zip is extracted to a
temporary directory and the recovered authentic fast geometry sources are
installed there. Existing producer traces are never modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPECTED_U = "387708359002281417731/100000000000000000000"
EXPECTED_CHECKER = "95ae3362ee4992c332960e4af53697dd3d1b31e381682051b49fd47700ad9d0c"
EXPECTED_COVER = "df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def check_manifest():
    for line in (HERE / "SHA256SUMS").read_text().splitlines():
        h, name = line.split("  ", 1)
        assert sha(HERE / name) == h, f"SHA256 mismatch: {name}"


def check_cert_chain(source, cert, expected_cover):
    """Verify packaged byte ancestry before running the independent checker."""
    seen = set()
    current = source
    while True:
        assert current.is_file()
        name = current.name
        assert name not in seen, "Cycle in producer ancestry"
        seen.add(name)
        d = json.loads(current.read_text())
        seed = cert / Path(d["source"]["path"]).name
        assert sha(seed) == d["source"]["sha256"]
        seed_data = json.loads(seed.read_text())
        assert seed_data["schema"] == "generic_wall_seed_v1"
        assert sha(expected_cover) == seed_data["cover_source"]["sha256"]
        assert (cert / expected_cover.name).is_file()
        assert sha(cert / expected_cover.name) == sha(expected_cover)
        if not d["parent"]:
            break
        current = cert / Path(d["parent"]["path"]).name
        assert sha(current) == d["parent"]["sha256"]
    return len(seen)


def replay_one(entry, root, tmp):
    m = entry["mask_index"]
    if not entry["mask_exclusion_proved"]:
        print(f"{m}: unresolved in result.json; no exclusion claimed")
        return
    source = HERE / entry["source"]
    frozen_audit = HERE / entry["independent_audit"]
    assert sha(source) == entry["source_sha256"]
    assert sha(frozen_audit) == entry["independent_audit_sha256"]
    cover = root / "research/phase3/current/research/optimality/global_capture/center-cover-symmetric-exact.json"
    assert sha(cover) == EXPECTED_COVER
    length = check_cert_chain(source, HERE / "certificates", cover)
    output = tmp / f"audit-{m}.json"
    wrapper = root / "research/frontier/audit_case.py"
    subprocess.run([sys.executable, str(wrapper), str(source), "--output", str(output)],
                   check=True, stdout=subprocess.DEVNULL,
                   env={**os.environ, "OPENBLAS_NUM_THREADS": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    result = json.loads(output.read_text())
    original = json.loads(frozen_audit.read_text())
    assert result["status"] == original["status"] == "PASS_INDEPENDENT_GENERIC_HULL_AUDIT"
    assert result["mask_index"] == m and result["mask"] == entry["occupied_cells"]
    assert result["parent_Uplus"] == EXPECTED_U
    assert result["constraints"] == []
    assert result["source_sha256"] == entry["source_sha256"]
    assert result["branch_exclusion_proved"] is True
    assert result["mask_exclusion_proved"] is True
    assert m in result["transferred_canonical_mask_indices"]
    assert [n["sha256"] for n in result["nodes"]] == entry["audited_node_hashes"]
    assert len(result["nodes"]) == length
    for key in ("root_sha256", "cover_sha256", "final_state_sha256"):
        assert result[key] == original[key]
    print(f"{m}: PASS, {length} source node(s), {len(result['seed_ownership_checks'])} seed points")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mask", type=int, help="Replay just one assigned mask")
    args = ap.parse_args()
    if not __debug__:
        raise SystemExit("Python -O/-OO disables required assertions")
    check_manifest()
    result = json.loads((HERE / "result.json").read_text())
    assert result["job_id"] == "cases-04" and result["parent_Uplus"] == EXPECTED_U
    jobs = json.loads((HERE / "inputs/CASE_ASSIGNMENTS.json").read_text())["jobs"]
    assignment = next(j for j in jobs if j["job_id"] == "cases-04")
    assert result["assigned_mask_indices"] == assignment["mask_indices"]
    assert [e["mask_index"] for e in result["results"]] == assignment["mask_indices"]
    for e in result["results"]:
        assert e["occupied_cells"] == assignment["masks"][str(e["mask_index"])]
    assert result["global_optimality_proved"] is False
    if result["status"] == "complete":
        assert all(e["mask_exclusion_proved"] for e in result["results"])
    entries = [e for e in result["results"] if args.mask is None or e["mask_index"] == args.mask]
    assert entries and len({e["mask_index"] for e in entries}) == len(entries)
    with tempfile.TemporaryDirectory(prefix="cases04-v9-") as dirname:
        root = Path(dirname)
        with zipfile.ZipFile(HERE / "inputs/case-tools.zip") as z:
            z.extractall(root)
        dest = root / "research/phase3/work/phase3/capture/gmp"
        dest.mkdir(parents=True)
        for src in (HERE / "inputs/gmp").glob("*.py"):
            shutil.copy2(src, dest / src.name)
        checker = root / "research/phase3/work/phase3/hull/audit_capture_v9.py"
        assert sha(checker) == EXPECTED_CHECKER
        for e in entries:
            replay_one(e, root, root)


if __name__ == "__main__":
    main()
