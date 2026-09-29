#!/usr/bin/env python3
"""Replay the packet's source-distinct, exact v9 audits from this directory.

Run without -O: python replay.py [MASK_INDEX ...]
Only the archived files and a native gmpy2 2.3.1 are needed. The source
paths recorded in the immutable receipts are historical absolute paths;
the frozen checker resolves missing paths by sibling filename.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
U = "387708359002281417731/100000000000000000000"
CHECKER = ROOT / "research/phase3/work/phase3/hull/audit_capture_v9.py"
WRAPPER = ROOT / "research/frontier/audit_case.py"
EXPECTED_CHECKER = "95ae3362ee4992c332960e4af53697dd3d1b31e381682051b49fd47700ad9d0c"
EXPECTED_COVER = "df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e"
COVER = ROOT / "research/phase3/current/research/optimality/global_capture/center-cover-symmetric-exact.json"


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def require(value, message):
    if not value:
        raise AssertionError(message)


def resolve_historical(path):
    """Map source dependency paths while preserving every JSON byte."""
    p = Path(path)
    try:
        relative = Path(*p.parts[p.parts.index("research"):])
    except ValueError:
        raise AssertionError(f"No research/ path in {path}")
    resolved = ROOT / relative
    require(resolved.is_file(), f"Missing bundled dependency: {relative}")
    return resolved


def check_sums():
    for line in (ROOT / "SHA256SUMS").read_text().splitlines():
        digest, name = line.split("  ", 1)
        path = ROOT / name
        require(path.is_file() and sha(path) == digest, f"SHA256SUMS mismatch: {name}")


def replay_one(entry, canonical, tmpdir):
    index = entry["mask_index"]
    require(entry["occupied_cells"] == canonical[index], f"Wrong cells for {index}")
    if not entry.get("source"):
        require(not entry["mask_exclusion_proved"], f"Unproved {index} has no source")
        return f"{index}: unresolved (no producer source)"
    src = ROOT / entry["source"]
    require(sha(src) == entry["source_sha256"], f"Source hash for {index}")
    d = json.loads(src.read_text())
    require(d["mask_index"] == index and d["mask"] == canonical[index], f"Source M/J for {index}")
    require(d["U"] == U and d["constraints"] == [], f"Source U/constraints for {index}")
    require(d["terminal"], f"Interrupted source for {index}")
    require(d["source"]["sha256"] == sha(ROOT / "certificates" / Path(d["source"]["path"]).name),
            f"Seed hash for {index}")
    for historical, digest in d["dependencies"].items():
        require(sha(resolve_historical(historical)) == digest, f"Producer dependency: {historical}")
    parent = d.get("parent")
    while parent:
        ancestor = ROOT / "certificates" / Path(parent["path"]).name
        require(sha(ancestor) == parent["sha256"], f"Ancestor hash for {index}")
        ancestor_data = json.loads(ancestor.read_text())
        for historical, digest in ancestor_data["dependencies"].items():
            require(sha(resolve_historical(historical)) == digest, f"Ancestor dependency: {historical}")
        parent = ancestor_data.get("parent")
    archived = ROOT / entry["independent_audit"] if entry.get("independent_audit") else None
    if archived:
        require(sha(archived) == entry["independent_audit_sha256"], f"Audit hash for {index}")
    output = tmpdir / f"mask{index}-fresh-audit.json"
    env = os.environ.copy()
    env["OPENBLAS_NUM_THREADS"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    subprocess.run([sys.executable, str(WRAPPER), str(src), "--output", str(output)],
                   check=True, env=env, stdout=subprocess.DEVNULL)
    fresh = json.loads(output.read_text())
    require(fresh["status"] == "PASS_INDEPENDENT_GENERIC_HULL_AUDIT", f"v9 status for {index}")
    require(fresh["source_sha256"] == sha(src), f"v9 source hash for {index}")
    require(fresh["root_sha256"] == d["source"]["sha256"], f"v9 seed for {index}")
    require(fresh["mask_index"] == index and fresh["mask"] == canonical[index], f"v9 M/J for {index}")
    require(fresh["parent_Uplus"] == U and fresh["constraints"] == [], f"v9 U/constraints for {index}")
    require(fresh["cover_sha256"] == EXPECTED_COVER, f"v9 cover for {index}")
    if archived:
        old = json.loads(archived.read_text())
        for key in ("status", "source_sha256", "root_sha256", "mask_index", "mask",
                    "parent_Uplus", "constraints", "cover_sha256", "mask_exclusion_proved",
                    "branch_exclusion_proved", "transferred_canonical_mask_indices"):
            require(fresh[key] == old[key], f"v9 comparison {key} for {index}")
        require([n["sha256"] for n in fresh["nodes"]] == [n["sha256"] for n in old["nodes"]],
                f"v9 ancestry for {index}")
    if entry["mask_exclusion_proved"]:
        require(entry["status"] == "proved" and fresh["mask_exclusion_proved"]
                and fresh["branch_exclusion_proved"] and index in fresh["transferred_canonical_mask_indices"],
                f"Unjustified exclusion for {index}")
        require(entry["checker_sha256"] == EXPECTED_CHECKER, f"Checker hash for {index}")
        return f"{index}: independently proved"
    require(not fresh["mask_exclusion_proved"], f"Unrecorded exclusion for {index}")
    return f"{index}: unresolved (exact partial source audited)"


def main():
    require(__debug__, "Never run with Python -O or -OO")
    require(sha(CHECKER) == EXPECTED_CHECKER and sha(COVER) == EXPECTED_COVER, "Frozen inputs changed")
    check_sums()
    results = json.loads((ROOT / "result.json").read_text())
    require(results["job_id"] == "cases-01" and results["parent_Uplus"] == U, "Wrong packet/endpoint")
    require(not results["global_optimality_proved"], "Packet cannot establish global optimality")
    canonical = json.loads(COVER.read_text())["canonical_eleven_cell_subsets"]
    entries = {x["mask_index"]: x for x in results["results"]}
    require(sorted(entries) == sorted(results["assigned_mask_indices"]), "Incomplete result list")
    selected = [int(x) for x in sys.argv[1:]] or results["assigned_mask_indices"]
    require(all(i in entries for i in selected), "Index not in packet")
    with tempfile.TemporaryDirectory() as directory:
        for i in selected:
            print(replay_one(entries[i], canonical, Path(directory)), flush=True)


if __name__ == "__main__":
    main()
