#!/usr/bin/env python3
"""Replay the included unmodified v9 checker against one or all case receipts.

The receipts retain their original bytes and historical absolute file paths.
The only shim below resolves those paths to this extracted bundle; it does not
change the checker, its geometric routines, or the proof data.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
CERT = ROOT / "certificates"
CHECKER = ROOT / "research/phase3/work/phase3/hull/audit_capture_v9.py"
EXPECTED_CHECKER = "95ae3362ee4992c332960e4af53697dd3d1b31e381682051b49fd47700ad9d0c"
EXPECTED_COVER = "df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mask_indices", type=int, nargs="*")
    args = ap.parse_args()
    result = json.loads((ROOT / "result.json").read_text())
    chosen = set(args.mask_indices or [r["mask_index"] for r in result["results"] if r["mask_exclusion_proved"]])
    assert chosen <= set(result["assigned_mask_indices"])
    assert sha(CHECKER) == EXPECTED_CHECKER
    cover = ROOT / "research/phase3/current/research/optimality/global_capture/center-cover-symmetric-exact.json"
    assert sha(cover) == EXPECTED_COVER
    for line in (ROOT / "SHA256SUMS").read_text().splitlines():
        expected, relative = line.split("  ", 1)
        assert sha(ROOT / relative) == expected, relative
    assert __debug__, "Run without -O and -OO"
    import gmpy2
    assert gmpy2.version() == "2.3.1", gmpy2.version()
    os.environ["ELEVEN_RATIONAL_BACKEND"] = "gmp"
    os.environ["ELEVEN_PACKING_ROOT"] = str(ROOT / "research/phase3/current")
    sys.path.insert(0, str(CHECKER.parent))
    sys.path.insert(0, str(ROOT / "research/phase3/work/phase2/hull"))
    spec = importlib.util.spec_from_file_location("audit_capture_v9", CHECKER)
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    original_locate = checker.locate

    def bundled_locate(recorded, relative):
        p = Path(recorded)
        parts = p.parts
        if p.is_absolute() and "research" in parts:
            candidate = ROOT / Path(*parts[parts.index("research"):])
            if candidate.is_file():
                return candidate.resolve()
        candidate = CERT / p.name
        if candidate.is_file():
            return candidate.resolve()
        return original_locate(recorded, relative)

    checker.locate = bundled_locate
    for entry in result["results"]:
        i = entry["mask_index"]
        if i not in chosen:
            continue
        assert entry["mask_exclusion_proved"] and entry["constraints"] == []
        source = ROOT / entry["source"]
        historical = ROOT / entry["independent_audit"]
        assert sha(source) == entry["source_sha256"]
        assert sha(historical) == entry["independent_audit_sha256"]
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / f"mask{i}-replayed.json"
            # Direct call to the unchanged checker's public classes and
            # final acceptance predicates; this avoids a CLI path monkeypatch.
            import copy
            data = json.loads(source.read_text())
            seed = bundled_locate(data["source"]["path"], source)
            replay = checker.Replay(seed, None, generic_mode=True)
            replay.replay(source)
            assert sha(seed) == replay.source_hash
            for record in replay.records:
                assert sha(record["path"]) == record["sha256"]
            terminal = replay.records[-1]
            accepted = bool(terminal["branch_exclusion_proved"] and not terminal["constraints"])
            canonical = json.loads(cover.read_text())["canonical_eleven_cell_subsets"]
            transferred = [j for j, J in enumerate(canonical)
                           if set(replay.mask) <= set(J) or set(replay.mask) <= {15 - k for k in J}] if accepted else []
            previous = json.loads(historical.read_text())
            assert accepted and i in transferred
            assert previous["status"] == "PASS_INDEPENDENT_GENERIC_HULL_AUDIT"
            assert previous["mask_exclusion_proved"] and previous["branch_exclusion_proved"]
            assert previous["constraints"] == [] and previous["mask_index"] == i
            assert previous["mask"] == entry["occupied_cells"] == replay.mask
            assert previous["parent_Uplus"] == result["parent_Uplus"] == str(replay.U)
            assert previous["source_sha256"] == sha(source)
            assert previous["root_sha256"] == sha(seed)
            assert previous["final_state_sha256"] == checker.digest(data["final_state"])
            assert previous["transferred_canonical_mask_indices"] == transferred
            assert [record["sha256"] for record in previous["nodes"]] == [record["sha256"] for record in replay.records]
        print(f"PASS mask {i}: independent v9 geometry replay; source SHA-256 {sha(source)}", flush=True)


if __name__ == "__main__":
    main()
