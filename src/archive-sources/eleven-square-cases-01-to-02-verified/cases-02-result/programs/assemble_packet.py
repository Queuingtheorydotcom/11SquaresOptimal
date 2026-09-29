"""Package exact case 02 proof receipts with all source inputs and replay code."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "cases-02-result"
FRONT = ROOT / "research/frontier"
IDS = [1269, 1270, 1271, 1281, 1303, 1310, 1311, 1312, 1315, 1333,
       1335, 1341, 1342, 1343, 1347]
J = {
    1269: [0,1,3,4,5,6,10,11,12,13,14],
    1270: [0,1,3,4,5,6,10,11,12,13,15],
    1271: [0,1,3,4,5,6,10,11,12,14,15],
    1281: [0,1,3,4,5,7,8,9,10,14,15],
    1303: [0,1,3,4,5,7,9,10,11,12,13],
    1310: [0,1,3,4,5,7,9,10,12,13,15],
    1311: [0,1,3,4,5,7,9,10,12,14,15],
    1312: [0,1,3,4,5,7,9,11,12,13,14],
    1315: [0,1,3,4,5,7,10,11,12,13,14],
    1333: [0,1,3,4,5,9,10,11,12,13,15],
    1335: [0,1,3,4,6,7,8,9,10,11,13],
    1341: [0,1,3,4,6,7,8,9,10,13,14],
    1342: [0,1,3,4,6,7,8,9,10,13,15],
    1343: [0,1,3,4,6,7,8,9,10,14,15],
    1347: [0,1,3,4,6,7,8,9,11,13,14],
}
U = "387708359002281417731/100000000000000000000"
CHECKER = "95ae3362ee4992c332960e4af53697dd3d1b31e381682051b49fd47700ad9d0c"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_artifact(src, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def main():
    manifest = json.loads((ROOT / "handoff/CASE_TOOLS_MANIFEST.json").read_text())
    for item in manifest["files"]:
        p = ROOT / item["path"]
        assert p.is_file() and p.stat().st_size == item["bytes"] and sha(p) == item["sha256"], p
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    def ignore(directory, names):
        # All receipt JSON and logs are copied explicitly into certificates.
        if Path(directory) == FRONT:
            return [n for n in names if n.startswith("mask")]
        return [n for n in names if n == "__pycache__" or n.endswith(".pyc")]
    shutil.copytree(ROOT / "research", OUT / "research", ignore=ignore)
    for name in ["run_packet_lane.py", "assemble_packet.py"]:
        copy_artifact(ROOT / name, OUT / "programs" / name)
    copy_artifact(ROOT / "replay_template.py", OUT / "replay.py")
    for name in ["02-case-exclusions.md", "CASE_TOOLS_README.md", "CASE_TOOLS_MANIFEST.json"]:
        copy_artifact(ROOT / "handoff" / name, OUT / "inputs" / name)
    (OUT / "certificates").mkdir()
    cases = []
    table = []
    for i in IDS:
        files = sorted(FRONT.glob(f"mask{i}-*"))
        for p in files:
            if p.is_file() and (p.suffix in (".json", ".log")):
                copy_artifact(p, OUT / "certificates" / p.name)
        produced = [OUT / "certificates" / f"mask{i}-self-v1.json",
                    OUT / "certificates" / f"mask{i}-refined-1.json",
                    OUT / "certificates" / f"mask{i}-refined-2.json"]
        produced = [p for p in produced if p.is_file()]
        source = produced[-1] if produced else None
        audit = OUT / "certificates" / f"mask{i}-independent.json"
        proved = False
        missing = []
        contradiction = "none"
        if source:
            d = json.loads(source.read_text())
            assert d["mask_index"] == i and d["mask"] == J[i]
            assert d["U"] == U and d["constraints"] == []
            if d.get("contradiction"):
                contradiction = f"{d['contradiction']['kind']} (owner {d['contradiction'].get('owner', d['contradiction'].get('owners'))}, step {d['contradiction']['step']})"
            if audit.exists():
                a = json.loads(audit.read_text())
                proved = bool(a["status"] == "PASS_INDEPENDENT_GENERIC_HULL_AUDIT"
                              and a["mask_exclusion_proved"] and a["branch_exclusion_proved"]
                              and a["constraints"] == [] and a["mask_index"] == i
                              and a["mask"] == J[i] and a["parent_Uplus"] == U
                              and a["source_sha256"] == sha(source)
                              and i in a["transferred_canonical_mask_indices"]
                              and d.get("terminal") and d.get("contradiction"))
            if not proved:
                missing.append("No passing v9 independent audit of a complete unconditional contradiction; exact residual pose domains remain to be excluded.")
        else:
            missing.append("No complete producer source exists; exact search and independent audit remain.")
        cases.append(dict(mask_index=i, occupied_cells=J[i], status="proved" if proved else "unresolved",
                          mask_exclusion_proved=proved, constraints=[],
                          proof_kind="unconditional_v9" if proved else "other",
                          source=f"certificates/{source.name}" if source else None,
                          source_sha256=sha(source) if source else None,
                          independent_audit=f"certificates/{audit.name}" if audit.exists() else None,
                          independent_audit_sha256=sha(audit) if audit.exists() else None,
                          checker_sha256=CHECKER, unresolved_obligations=missing))
        table.append(f"| {i} | {J[i]} | {'proved' if proved else 'unresolved'} | {contradiction} | {source.name if source else 'none'} |")
    complete = all(c["mask_exclusion_proved"] for c in cases)
    result = dict(job_id="cases-02", status="complete" if complete else "partial",
                  parent_Uplus=U, assigned_mask_indices=IDS, results=cases,
                  global_optimality_proved=False)
    (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    method = '''# cases-02: exact exclusions for specified eleven-cell masks

## Statement and scope

For the fifteen cases listed below, let eleven closed unit squares with arbitrary
independent orientations have centers in the specified closed rational Voronoi
cells, inside the closed container of side
`U = 387708359002281417731/100000000000000000000`. Interiors of squares
are disjoint and all wall and square contacts are allowed. The exact rational
sites and cell inequalities are in `inputs/02-case-exclusions.md`; no center,
angle, or contact-pattern restrictions have been added. Each `proved` entry
excludes **that assigned mask** only. This packet does not prove global
optimality or address the four construction patterns.

## Proof method and independent acceptance

Set `L=191/50` and `B=L/U`, and map a unit-container center `c` to the field
center `B(c+(U/2,U/2))`. The included frozen v9 checker reconstructs the
rational Voronoi cells from the exact cover (SHA-256
`df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e`)
and verifies their diameter is smaller than one square side. Each occupied
cell therefore has a distinct square label.

A fresh wall seed partitions every owner's full rational half-angle interval
`[0,1]` into 64 adjacent **closed** intervals and bounds all legal centers
using exact rational wall inequalities. The checker verifies each seed owned
point lies strictly inside every legal square pose in its cell (using an
exact disk witness or rational projection certificate), and convexity extends
ownership to its hull. This is the unconditional induction base.

For a subsequent angle interval the checker verifies that each supplied core
polygon lies inside every oriented square in the interval by four strictly
positive rational quadratic inequalities. A legal center cannot lie in the
Minkowski forbidden region generated by a previously proved owned hull and
the negative core of another square. Validated partner pose covers give
additional collision regions. An exact rational polygon-union check covers
the complete input domain by forbidden regions and retained residuals,
including their boundaries. Exact support inequalities and independently
checked convex-combination witnesses promote only points lying inside every
remaining possible pose, preserving the owned-hull invariant. If one complete
angle-row cover has no residual poses, no legal packing exists; intersecting
strictly owned hulls likewise preclude disjoint interiors.

The producer's `mask_exclusion_proved` is deliberately false. Only the frozen,
source-distinct `audit_capture_v9.py` (SHA-256
`95ae3362ee4992c332960e4af53697dd3d1b31e381682051b49fd47700ad9d0c`)
replays the wall seed and all ancestor nodes, checks exact source hashes,
cover, seed ownership, every angle row and geometric inference, and accepts
an unconditional contradiction. `result.json` marks a case proved only after
its audit reports `PASS_INDEPENDENT_GENERIC_HULL_AUDIT`,
`branch_exclusion_proved=true`, `mask_exclusion_proved=true`, empty
`constraints`, correct mask, exact `U`, and matching source SHA-256. These
conditions give no inference about masks outside the assigned fifteen.

## Results

| Mask index | Occupied cells | Outcome | Terminal producer contradiction | Terminal source |
| --- | --- | --- | --- | --- |
''' + "\n".join(table) + '''

## Reproducibility and provenance

Extract the ZIP, install Python 3.12, native `gmpy2==2.3.1`, `sympy==1.14`,
and `numpy==2.5.3`, and run `OPENBLAS_NUM_THREADS=1 python replay.py` from
the extracted directory. Pass mask indices as arguments to replay individual
cases. The replay program verifies `SHA256SUMS`, then invokes the unmodified
v9 independent checker on every selected case. A path-only shim maps
historical absolute input paths in byte-for-byte original receipts to their
included files; it does not alter the checker or geometry. Each result must
match the included independent audit's stable mask/source/root/node hashes,
constraints, and exact outcome. Do not use Python `-O` or `-OO`.

The bundled `case-tools.zip` omitted the native GMP helper sources
`fast_arrangement.py`, `fast_convex_v2.py`, `fast_grid.py`, and
`fast_core_v2.py`. The six Python files in `research/phase3/work/phase3/capture/gmp/`
were copied byte-for-byte from the original continuation extraction; the
four active helper source bytes were checked against the original 349 MB
continuation archive. All source files, exact cover and wall groups, producer
traces, ancestor seeds, logs, audit outputs, and hashes are included. The
independent audit is conditional on the correctness of its supplied exact
algorithms and native rational arithmetic implementation; the command
replays those algorithms and supplies the checkable witness data.
'''
    (OUT / "proof.md").write_text(method)
    lines = []
    for path in sorted(OUT.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS":
            lines.append(f"{sha(path)}  {path.relative_to(OUT)}")
    (OUT / "SHA256SUMS").write_text("\n".join(lines) + "\n")
    zip_path = ROOT / "cases-02-result.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path in sorted(OUT.rglob("*")):
            if path.is_file():
                z.write(path, f"cases-02-result/{path.relative_to(OUT)}")
    print(json.dumps(dict(status=result["status"],proved=sum(x["mask_exclusion_proved"] for x in cases),
                          total=len(cases),bytes=zip_path.stat().st_size,zip=str(zip_path)), indent=2))


if __name__ == "__main__":
    main()
