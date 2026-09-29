"""Cross-check the four completed case-exclusion packets against their handoff."""
from pathlib import Path
from hashlib import sha256
import json

ROOT = Path(__file__).resolve().parent
ASSIGNMENTS = json.loads((ROOT / "handoff/CASE_ASSIGNMENTS.json").read_text())
JOBS = {x["job_id"]: x for x in ASSIGNMENTS["jobs"]}
U = "387708359002281417731/100000000000000000000"
CHECKER = "95ae3362ee4992c332960e4af53697dd3d1b31e381682051b49fd47700ad9d0c"


def digest(p):
    return sha256(p.read_bytes()).hexdigest()


summary = {}
seen = set()
for packet in range(9, 13):
    job = f"cases-{packet:02}"
    folder = ROOT / f"cases-{packet:02}-result"
    if packet == 9 and not folder.exists():
        folder = ROOT / "research_agent09" / folder.name
    ledger = json.loads((folder / "result.json").read_text())
    expected = JOBS[job]
    assert ledger["job_id"] == job
    assert ledger["status"] == "complete"
    assert ledger["parent_Uplus"] == U
    assert ledger["global_optimality_proved"] is False
    indices = expected["mask_indices"]
    assert ledger["assigned_mask_indices"] == indices
    rows = ledger["results"]
    assert [x["mask_index"] for x in rows] == indices
    expected_cells = {int(i): cells for i, cells in expected["masks"].items()}
    for row in rows:
        index = row["mask_index"]
        assert index not in seen
        seen.add(index)
        assert row["occupied_cells"] == expected_cells[index]
        assert row["status"] == "proved" and row["mask_exclusion_proved"] is True
        assert row["constraints"] == [] and row["unresolved_obligations"] == []
        assert row["checker_sha256"] == CHECKER
        source = folder / row["source"]
        receipt = folder / row["independent_audit"]
        assert source.is_file() and receipt.is_file()
        assert digest(source) == row["source_sha256"]
        assert digest(receipt) == row["independent_audit_sha256"]
        d = json.loads(source.read_text())
        a = json.loads(receipt.read_text())
        assert d["mask_index"] == index and d["mask"] == row["occupied_cells"]
        assert d["contradiction"] and d["constraints"] == []
        assert a["status"] == "PASS_INDEPENDENT_GENERIC_HULL_AUDIT"
        assert a["mask_exclusion_proved"] is True and a["constraints"] == []
        assert a["source_sha256"] == digest(source) and a["mask_index"] == index
        assert a["parent_Uplus"] == U
    summary[job] = {"assigned": len(indices), "audited_exclusions": len(rows), "indices": indices}

assert len(seen) == 56
assert seen.isdisjoint(ASSIGNMENTS["candidate_masks"])
output = {
    "scope": "Packets 09–12 only; no global optimality claim",
    "status": "PASS_CROSS_PACKET_LEDGER_AND_RECEIPT_BINDING",
    "parent_Uplus": U,
    "exact_exclusions": len(seen),
    "packets": summary,
    "global_optimality_proved": False,
}
path = ROOT / "four-packet-crosscheck.json"
path.write_text(json.dumps(output, indent=2) + "\n")
print(json.dumps({"status": output["status"], "exact_exclusions": len(seen)}))
