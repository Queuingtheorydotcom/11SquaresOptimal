#!/usr/bin/env python3
"""Portable, source-distinct exact replay of packet 11's fourteen certificates.

Requires Python 3.12 and native gmpy2 2.3.1. Run with assertions enabled:
    python replay.py
or replay selected indices:
    python replay.py 2071 2084
"""

from pathlib import Path
from hashlib import sha256
from tempfile import TemporaryDirectory
from zipfile import ZipFile
from shutil import copy2
import json
import os
import subprocess
import sys

HERE = Path(__file__).resolve().parent
CHECKER_HASH = "95ae3362ee4992c332960e4af53697dd3d1b31e381682051b49fd47700ad9d0c"
COVER_HASH = "df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e"


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def verify_inventory():
    lines = (HERE / "SHA256SUMS").read_text().splitlines()
    seen = set()
    for line in lines:
        hexdigest, relative = line.split("  ", 1)
        path = HERE / relative
        assert relative not in seen and path.is_file() and digest(path) == hexdigest, relative
        seen.add(relative)
    actual = {p.relative_to(HERE).as_posix() for p in HERE.rglob("*") if p.is_file() and p.name != "SHA256SUMS"}
    assert actual == seen, f"Inventory mismatch: missing {actual-seen}, extraneous {seen-actual}"


def extract_profile(profile, destination, assigned):
    with ZipFile(HERE / "programs/case-tools.zip") as archive:
        archive.extractall(destination)
    for name in ("fast_convex_v2.py", "fast_grid.py"):
        copy2(HERE / "programs" / profile / name,
              destination / "research/phase3/work/phase2/hull" / name)
    if profile == "low":
        copy2(HERE / "programs/low/fast_core_v2.py",
              destination / "research/phase3/work/phase3/core/fast_core_v2.py")
    checker = destination / "research/phase3/work/phase3/hull/audit_capture_v9.py"
    cover = destination / "research/phase3/current/research/optimality/global_capture/center-cover-symmetric-exact.json"
    assert digest(checker) == CHECKER_HASH and digest(cover) == COVER_HASH
    frontier = destination / "research/frontier"
    for name in ("center-cover-symmetric-exact.json", "wall_ownership_groups.json"):
        copy2(HERE / "certificates" / profile / name, frontier / name)
    assert digest(frontier / cover.name) == COVER_HASH
    for index in assigned:
        for suffix in ("self-v1-seed.json", "self-v1.json", "independent.json"):
            name = f"mask{index}-{suffix}"
            copy2(HERE / "certificates" / profile / name, frontier / name)
    return frontier


def relocate_original_program_path(old_path, destination):
    parts = Path(old_path).parts
    assert "research" in parts, old_path
    return destination / Path(*parts[parts.index("research"):])


def replay_case(index, row, destination, frontier, env):
    source = frontier / f"mask{index}-self-v1.json"
    seed = frontier / f"mask{index}-self-v1-seed.json"
    old_audit = frontier / f"mask{index}-independent.json"
    assert digest(source) == row["source_sha256"]
    assert digest(seed) == row["seed_sha256"]
    assert digest(old_audit) == row["independent_audit_sha256"]
    producer = json.loads(source.read_text())
    root = json.loads(seed.read_text())
    recorded = json.loads(old_audit.read_text())
    assert producer["source"]["sha256"] == digest(seed) == recorded["root_sha256"]
    assert recorded["source_sha256"] == digest(source)
    assert producer["mask_index"] == index and producer["mask"] == row["occupied_cells"]
    for old_path, expected in producer["dependencies"].items():
        relocated = relocate_original_program_path(old_path, destination)
        assert relocated.is_file() and digest(relocated) == expected, old_path
    for name in ("cover_source", "wall_groups_source", "producer_source"):
        ref = root[name]
        relocated = relocate_original_program_path(ref["path"], destination)
        assert relocated.is_file() and digest(relocated) == ref["sha256"], name

    # The frozen v9 locate() routine finds the original byte-identical seed
    # beside this trace when its old absolute path is unavailable. For the
    # cover_source path inside the seed, it finds the extra verified copy here.
    output = frontier / f"mask{index}-fresh-v9-audit.json"
    command = [sys.executable, str(frontier / "audit_case.py"), str(source),
               "--output", str(output)]
    completed = subprocess.run(command, cwd=destination, env=env,
                               capture_output=True, text=True, timeout=900)
    if completed.returncode:
        raise RuntimeError(f"Case {index} failed v9 replay:\n{completed.stdout[-4000:]}\n{completed.stderr[-4000:]}")
    fresh = json.loads(output.read_text())
    for key in ("status", "mask_index", "mask", "parent_Uplus", "source_sha256",
                "root_sha256", "constraints", "branch_exclusion_proved", "mask_exclusion_proved"):
        assert fresh[key] == recorded[key], (index, key, fresh[key], recorded[key])
    assert fresh["status"] == "PASS_INDEPENDENT_GENERIC_HULL_AUDIT"
    assert fresh["constraints"] == [] and fresh["mask_exclusion_proved"] is True
    print(f"{index}: PASS, unconditional exclusion", flush=True)


def main():
    assert __debug__, "Run without Python -O/-OO"
    import gmpy2
    assert gmpy2.version() == "2.3.1"
    verify_inventory()
    ledger = json.loads((HERE / "result.json").read_text())
    rows = {r["mask_index"]: r for r in ledger["results"]}
    indices = list(map(int, sys.argv[1:])) if len(sys.argv) > 1 else ledger["assigned_mask_indices"]
    assert indices and len(set(indices)) == len(indices) and all(i in rows for i in indices)
    env = {**os.environ, "OPENBLAS_NUM_THREADS": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    with TemporaryDirectory(prefix="eleven-packet11-") as temporary:
        for profile in ("low", "high"):
            selected = [i for i in indices if ("low" if i <= 2075 else "high") == profile]
            if not selected:
                continue
            destination = Path(temporary) / profile
            frontier = extract_profile(profile, destination, selected)
            for index in selected:
                replay_case(index, rows[index], destination, frontier, env)
    print(f"Verified {len(indices)} of {len(rows)} packet-11 exclusions")


if __name__ == "__main__":
    main()
