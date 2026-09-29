#!/usr/bin/env python3
"""Check eleven-square result packets 03–04 and their frozen evidence.

This is a manifest/integration check. The exact geometric proof still requires
running each packet's independent replay program with assertions enabled.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

U = "387708359002281417731/100000000000000000000"
CHECKER = "95ae3362ee4992c332960e4af53697dd3d1b31e381682051b49fd47700ad9d0c"
COVER = "df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def file_at(root, value):
    assert isinstance(value, str) and value and not Path(value).is_absolute(), value
    path = (root / value).resolve()
    assert path.is_relative_to(root.resolve()) and path.is_file(), value
    return path


def check_sums(root):
    sums = root / "SHA256SUMS"
    assert sums.is_file(), sums
    seen = set()
    for line in sums.read_text().splitlines():
        m = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        assert m, (sums, line)
        expected, name = m.groups()
        assert name not in seen, name
        seen.add(name)
        assert sha(file_at(root, name)) == expected, name
    assert seen, sums


def check_packet(root, job):
    assert root.is_dir(), root
    check_sums(root)
    result = json.loads((root / "result.json").read_text())
    assert result["job_id"] == job["job_id"]
    assert result["parent_Uplus"] == U
    assert result["assigned_mask_indices"] == job["mask_indices"]
    assert result["global_optimality_proved"] is False
    rows = result["results"]
    assert len(rows) == len(job["mask_indices"])
    assert sorted(row["mask_index"] for row in rows) == job["mask_indices"]
    evidence_hashes = {sha(p) for p in (root / "certificates").rglob("*") if p.is_file()}
    proved = []
    unresolved = []
    for row in rows:
        index = row["mask_index"]
        assert row["occupied_cells"] == job["masks"][str(index)]
        assert row["constraints"] == [] or not row["mask_exclusion_proved"]
        if not row["mask_exclusion_proved"]:
            assert row["status"] == "unresolved" and row["unresolved_obligations"], index
            unresolved.append(index)
            continue
        assert row["status"] == "proved" and row["constraints"] == []
        source = file_at(root, row["source"])
        audit = file_at(root, row["independent_audit"])
        assert sha(source) == row["source_sha256"]
        assert sha(audit) == row["independent_audit_sha256"]
        assert row["checker_sha256"] == CHECKER
        producer = json.loads(source.read_text())
        receipt = json.loads(audit.read_text())
        assert producer["mask_index"] == index and producer["mask"] == row["occupied_cells"]
        assert producer["contradiction"] and producer["constraints"] == []
        assert receipt["status"] == "PASS_INDEPENDENT_GENERIC_HULL_AUDIT"
        assert receipt["mask_index"] == index and receipt["mask"] == row["occupied_cells"]
        assert receipt["parent_Uplus"] == U and receipt["cover_sha256"] == COVER
        assert receipt["source_sha256"] == sha(source)
        assert receipt["dependencies"]["audit_capture_v9.py"] == CHECKER
        assert receipt["constraints"] == []
        assert receipt["branch_exclusion_proved"] is True
        assert receipt["mask_exclusion_proved"] is True
        assert receipt["global_optimality_proved"] is False
        assert index in receipt["transferred_canonical_mask_indices"]
        assert receipt["root_sha256"] in evidence_hashes, (index, "missing wall seed")
        assert all(node["sha256"] in evidence_hashes for node in receipt["nodes"]), (index, "missing ancestor")
        proved.append(index)
    assert result["status"] == ("complete" if not unresolved else "partial")
    return proved, unresolved


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("result_parent", type=Path)
    ap.add_argument("--assignments", type=Path, default=Path("CASE_ASSIGNMENTS.json"))
    args = ap.parse_args()
    assignments = json.loads(args.assignments.read_text())["jobs"][2:4]
    total_proved, total_unresolved = [], []
    for job in assignments:
        root = args.result_parent / (job["job_id"] + "-result")
        proved, unresolved = check_packet(root, job)
        print(f"{job['job_id']}: {len(proved)} independently audited, {len(unresolved)} unresolved")
        total_proved.extend(proved)
        total_unresolved.extend(unresolved)
    assert len(total_proved) + len(total_unresolved) == 30
    assert len(set(total_proved + total_unresolved)) == 30
    print(f"TOTAL: {len(total_proved)}/30 exclusions; unresolved: {total_unresolved}")


if __name__ == "__main__":
    main()
