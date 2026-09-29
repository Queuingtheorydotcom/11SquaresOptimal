#!/usr/bin/env python3
"""Assemble the exact packet-08 case receipts without changing their bytes.

Usage (after producer and independent checker runs have finished):
    python cases-08b-working/package_08.py --output cases-08-result

The archived receipts contain absolute paths.  The frozen v9 checker checks the
hash at each path and, when that original location is absent, resolves the
basename beside the copied receipt.  Each case's ancestry is therefore kept
together, unchanged, in certificates/maskNNNN/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parents[1]
WORKS = (HERE / "work08", HERE / "work08b", HERE / "work1840alt")
INDICES = (1731, 1769, 1774, 1775, 1783, 1805, 1810,
           1821, 1822, 1823, 1824, 1831, 1840, 1842)
U = "387708359002281417731/100000000000000000000"
CHECKER_REL = Path("research/phase3/work/phase3/hull/audit_capture_v9.py")
COVER_REL = Path("research/phase3/current/research/optimality/global_capture/center-cover-symmetric-exact.json")
CHECKER_HASH = "95ae3362ee4992c332960e4af53697dd3d1b31e381682051b49fd47700ad9d0c"
COVER_HASH = "df7938d9ba27095a38fabe45f8b26b259a2cc896c2ae4aac6bae874f417adc4e"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def find_bound(path: str, expected: str, relative: Path) -> Path:
    """Resolve a receipt reference and require its recorded exact byte hash."""
    candidates = [Path(path), relative.parent / Path(path).name]
    candidates += [root / "research/frontier" / Path(path).name for root in WORKS]
    for candidate in candidates:
        if candidate.is_file() and sha(candidate) == expected:
            return candidate.resolve()
    raise ValueError(f"Missing or altered source {path!r}, SHA-256 {expected}")


def add_file(src: Path, directory: Path) -> Path:
    dst = directory / src.name
    if dst.exists():
        if sha(dst) != sha(src):
            raise ValueError(f"Two different files would share {dst}")
    else:
        shutil.copy2(src, dst)
    return dst


def bind_program(path: str, expected: str, directory: Path) -> None:
    """Require a producer input/program and place the same bytes in research/."""
    original = Path(path)
    assert original.is_file() and sha(original) == expected, path
    parts = original.parts
    assert "research" in parts, path
    relative = Path(*parts[parts.index("research"):])
    target = directory.parents[1] / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copy2(original, target)
    assert sha(target) == expected, (target, path)


def ancestry(src: Path, directory: Path, mask_index: int,
             covered: set[str] | None = None) -> list[Path]:
    """Copy a producer plus every hash-bound parent and its fresh wall seed."""
    covered = set() if covered is None else covered
    digest = sha(src)
    if digest in covered:
        return []
    covered.add(digest)
    node = read(src)
    assert node["mask_index"] == mask_index
    assert node["schema"] in ("generic_wall_seed_v1",
                              "exact_generic_owned_hull_v1",
                              "exact_branch_owned_hull_v1")
    files = [add_file(src, directory)]
    if node["schema"] == "generic_wall_seed_v1":
        assert node["U"] == U
        for key in ("producer_source", "wall_groups_source"):
            ref = node[key]
            bind_program(ref["path"], ref["sha256"], directory)
        cover = node["cover_source"]
        assert cover["sha256"] == COVER_HASH
        src_cover = find_bound(cover["path"], cover["sha256"], src)
        files.append(add_file(src_cover, directory))
    else:
        assert node["U"] == U and node["source"]["sha256"]
        assert node["mask_exclusion_proved"] is False
        assert node["global_optimality_proved"] is False
        for path, expected in node["dependencies"].items():
            bind_program(path, expected, directory)
        parent = node.get("parent")
        if parent:
            p = find_bound(parent["path"], parent["sha256"], src)
            files += ancestry(p, directory, mask_index, covered)
        source = node["source"]
        s = find_bound(source["path"], source["sha256"], src)
        files += ancestry(s, directory, mask_index, covered)
    return files


def valid_audit(a: dict, source: Path, mask: list[int], index: int) -> bool:
    if a.get("status") != "PASS_INDEPENDENT_GENERIC_HULL_AUDIT":
        return False
    if a.get("mask_index") != index or a.get("mask") != mask:
        return False
    if a.get("source_sha256") != sha(source) or a.get("parent_Uplus") != U:
        return False
    if a.get("cover_sha256") != COVER_HASH or a.get("constraints") != []:
        return False
    if a.get("dependencies", {}).get("audit_capture_v9.py") != CHECKER_HASH:
        return False
    if index not in a.get("transferred_canonical_mask_indices", []) and a.get("mask_exclusion_proved"):
        return False
    nodes = a.get("nodes", [])
    if not nodes or nodes[-1].get("sha256") != sha(source):
        return False
    if a.get("mask_exclusion_proved") and not a.get("branch_exclusion_proved"):
        return False
    return True


def candidates(index: int) -> tuple[list[tuple[Path, dict]], list[tuple[Path, dict]]]:
    producers, audits = [], []
    for root in WORKS:
        for path in sorted((root / "research/frontier").glob(f"mask{index}-*.json")):
            try:
                d = read(path)
            except (ValueError, OSError):  # A running producer can have a .writing file.
                continue
            if d.get("mask_index") != index:
                continue
            if d.get("schema") in ("exact_generic_owned_hull_v1", "exact_branch_owned_hull_v1"):
                if d.get("terminal"):
                    producers.append((path, d))
            elif d.get("status", "").startswith("PASS_INDEPENDENT_"):
                audits.append((path, d))
    return producers, audits


def collect_case(index: int, mask: list[int], output: Path) -> dict:
    producers, audits = candidates(index)
    audited_pairs = []
    for audit_path, audit in audits:
        for source_path, source in producers:
            if not valid_audit(audit, source_path, mask, index):
                continue
            proved = bool(audit.get("mask_exclusion_proved"))
            if proved and (source.get("contradiction") is None or source["constraints"]):
                raise ValueError(f"An audit claims {index} closed without unconditional contradiction")
            audited_pairs.append((audit_path, audit, source_path, source))
    def lineage_cost(path: Path, node: dict) -> tuple[int, int, int]:
        """Prefer the smallest complete independent proof ancestry."""
        parent = node.get("parent")
        if not parent:
            return (1, len(node.get("steps", [])), path.stat().st_size)
        p = find_bound(parent["path"], parent["sha256"], path)
        p_nodes, p_steps, p_bytes = lineage_cost(p, read(p))
        return (1 + p_nodes, p_steps + len(node.get("steps", [])),
                p_bytes + path.stat().st_size)

    proven = min((pair for pair in audited_pairs if pair[1]["mask_exclusion_proved"]),
                 key=lambda pair: lineage_cost(pair[2], pair[3]), default=None)
    if proven:
        audit_path, audit, source_path, source = proven
    else:
        audit_path = audit = None
        source_path = source = None
        if producers:
            # Prefer a terminal contradiction awaiting an audit, then the
            # deepest refinement ancestry, not merely the largest local
            # step count in a fresh seed producer.
            def depth(path: Path, node: dict) -> int:
                parent = node.get("parent")
                if not parent:
                    return 0
                p = find_bound(parent["path"], parent["sha256"], path)
                return 1 + depth(p, read(p))

            source_path, source = max(producers, key=lambda pair: (
                bool(pair[1].get("contradiction")),
                depth(*pair),
                sum(bool(s["complete"]) for s in pair[1].get("steps", [])),
                len(pair[1].get("steps", []))))
            same_source = [pair for pair in audited_pairs if pair[2] == source_path]
            if same_source:
                audit_path, audit, _, _ = same_source[0]
    cert_dir = output / "certificates" / f"mask{index}"
    cert_dir.mkdir(parents=True, exist_ok=True)
    result = dict(mask_index=index, occupied_cells=mask, status="unresolved",
                  mask_exclusion_proved=False, constraints=[], proof_kind="unresolved",
                  source=None, source_sha256=None, independent_audit=None,
                  independent_audit_sha256=None, checker_sha256=CHECKER_HASH,
                  unresolved_obligations=[])
    if source_path:
        ancestry(source_path, cert_dir, index)
        result["source"] = str((cert_dir / source_path.name).relative_to(output))
        result["source_sha256"] = sha(source_path)
        result["constraints"] = source["constraints"]
    if audit_path:
        # The independent audit is an output of the frozen v9 checker.  Its
        # source and parent receipts have already been copied byte for byte.
        add_file(audit_path, cert_dir)
        result["independent_audit"] = str((cert_dir / audit_path.name).relative_to(output))
        result["independent_audit_sha256"] = sha(audit_path)
        for rec in audit.get("nodes", []):
            p = find_bound(rec["path"], rec["sha256"], audit_path)
            ancestry(p, cert_dir, index)
    if audit and audit["mask_exclusion_proved"]:
        result.update(status="proved", mask_exclusion_proved=True,
                      proof_kind="unconditional_v9")
    elif source and source.get("contradiction"):
        result["unresolved_obligations"].append(
            "Run the frozen independent v9 audit on this contradictory receipt and its complete ancestry.")
    elif source:
        result["unresolved_obligations"].append(
            "Close every retained center and angle domain with an exact contradiction or an exhaustive branch tree, then independently replay the complete source ancestry.")
    else:
        result["unresolved_obligations"].append(
            "No terminal producer receipt and independent v9 exclusion audit were available.")
    return result


def make_proof(results: list[dict]) -> str:
    lines = [
        "# Packet 08: exact eleven-square case exclusions",
        "",
        f"The endpoint is $U={U}$. A square center with label $i$ lies in the closed",
        "Voronoi cell $C_i$ specified in `08-case-exclusions.md`; the eleven labels",
        "for each index are repeated in `result.json`. Orientations range through",
        "$t=\\tan(\\theta/2)\\in[0,1]$ with both endpoints included. This",
        "covers every physical square orientation modulo a quarter turn. Touching",
        "between squares and with container walls is allowed.",
        "",
        "## Exact inference rules",
        "",
        "Work in the field square of side $L=191/50$, scaled by $B=L/U$. An",
        "original centered coordinate $c$ maps exactly to $B(c+(U/2,U/2))$.",
        "The field center domain is the image of the closed polygon $C_i$.",
        "Let $K_i$ be a finite convex hull proved strictly inside every possible",
        "square $i$, and let each angular row have a closed center outer polygon",
        "$D_{i,r}$ containing all still-possible centers in that row. These are",
        "invariants, established from the seed and preserved by each completed",
        "ordered update. In particular, no contact configuration is discarded.",
        "",
        "1. **Wall seed and necessary outer domains.** The initial angle rows",
        "   $[k/m,(k+1)/m]$ cover $[0,1]$ with shared endpoints. At half tangent",
        "   $t$, the wall halfwidth is $h(t)=B(c(t)+s(t))/2$, where",
        "   $c=(1-t^2)/(1+t^2)$ and $s=2t/(1+t^2)$. The minimum of $h$ on a row",
        "   occurs at an endpoint. Thus every legal center is in the closed cell",
        "   clipped by $h_{min}\\le x,y\\le L-h_{min}$. The checker proves these",
        "   endpoint inequalities exactly, checks the rational center-cover cells",
        "   and their diameter bound, and separately certifies every seed point",
        "   strictly inside *every* legal square of its owner cell. The seed",
        "   ownership test uses the source-distinct `audit_wall_kernel.py`: exact",
        "   vertex distance where sufficient, otherwise an exhaustive rational",
        "   interval projection check. Strict margins are required, not inferred",
        "   from a floating-point screen.",
        "",
        "2. **Strict angular core.** Each row supplies a rational convex polygon",
        "   $Q_{i,r}$. For each vertex and each of the two oriented square axes,",
        "   the checker verifies the two signed coordinate inequalities strictly",
        "   over the *entire* closed row. Clearing positive $1+t^2$ gives a",
        "   quadratic; exact endpoint values and its interior vertex (when",
        "   relevant) certify positivity. Hence $x+Q_{i,r}$ lies in the interior",
        "   of square $i$ for every retained pose $(x,t)$ in that row.",
        "",
        "3. **Forbidden centers.** For another owner's previously proved hull",
        "   $K_j$, a query center $x\\in K_j-Q_{i,r}$ makes $x+Q_{i,r}$ intersect",
        "   $K_j$ in the interiors of both squares. The closed Minkowski polygon",
        "   is therefore forbidden, including its boundary. A partner collision",
        "   region can also be forbidden when it is independently checked to lie",
        "   inside $y+Q_{j,s}-Q_{i,r}$ for *every* possible partner row $s$ and",
        "   every $y\\in D_{j,s}$. The partner rows cover the entire allowed",
        "   angular interval. The checker reconstructs this universal inclusion",
        "   by a separate collision validator; an empty partner cover cannot",
        "   silently justify a nonempty collision region.",
        "",
        "4. **Exact residual cover and ownership promotion.** An independent",
        "   rational polygon arrangement proves that each old center domain is",
        "   covered by the forbidden regions and the reported residual polygons.",
        "   Point and segment domains are handled by exact one-dimensional",
        "   interval coverage. A new outer domain is accepted only after the",
        "   checker verifies every residual vertex satisfies its supporting",
        "   halfplanes. For a row core facet $n\\cdot q\\le h_Q(n)$, every point",
        "   $p$ with $n\\cdot p\\le h_Q(n)+\\min_{x\\in R}n\\cdot x$ for all",
        "   facets lies in $x+Q$ for every residual center $x\\in R$. The",
        "   checker compares these exact halfplanes with the receipt and verifies",
        "   the promoted kernel vertices. Every compressed vertex must be an",
        "   exact convex combination of previously proved owned vertices and",
        "   these kernel vertices. Convexity and strict interior preserve the",
        "   owned-hull invariant.",
        "",
        "5. **Ordered induction and contradiction.** Each complete cell update",
        "   is checked against an immutable prior snapshot and then promoted",
        "   before the next update. An incomplete step does not promote a new",
        "   hull. If all rows for one owner have empty residual domains, no pose",
        "   remains. If two proved owned hulls intersect, their common point lies",
        "   strictly inside two squares, which is impossible. Shared angular",
        "   endpoints, polygon edges, and square contacts remain covered by the",
        "   closed inequalities; the strict interior margins belong only to",
        "   the owned points and cores used to forbid overlap.",
        "",
        "The frozen `research/phase3/work/phase3/hull/audit_capture_v9.py`",
        "(SHA-256 given below) independently replays each receipt and all of its",
        "SHA-bound ancestors. Only a passing audit with `mask_exclusion_proved: true`,",
        "an empty constraint list, and a recorded contradiction establishes an",
        "unconditional exclusion. Every such claim is shown case by case below.",
        "The original receipt bytes and path/hash parent references are",
        "preserved. `replay.py` verifies package hashes and reruns the checker.",
        "",
        "## Case outcomes",
        "",
        "| Index | Cells | Outcome | Source | Audit |",
        "| ---: | --- | --- | --- | --- |",
    ]
    for r in results:
        cells = ", ".join(map(str, r["occupied_cells"]))
        lines.append(f"| {r['mask_index']} | {cells} | {r['status']} | "
                     f"{r['source'] or 'none'} | {r['independent_audit'] or 'none'} |")
    lines += ["", "A row marked `proved` is backed by an unconditional passing v9",
              "audit with `mask_exclusion_proved: true`. All other rows are open.",
              "This packet makes no claim of global optimality.", "",
              "## Unresolved obligations", ""]
    for r in results:
        if r["unresolved_obligations"]:
            lines.append(f"- **{r['mask_index']}**: " + " ".join(r["unresolved_obligations"]))
    if all(not r["unresolved_obligations"] for r in results):
        lines.append("None within this packet.")
    lines += ["", "## Dependencies and scope", "",
              "Replay requires Python 3.12, gmpy2 2.3.1, SymPy 1.14, and NumPy 2.5.3",
              "for the bundled workflow. The v9 checker hash and exact cover hash",
              f"must be `{CHECKER_HASH}` and `{COVER_HASH}`.",
              "`research/` is the original case-tools code, supplemented with the",
              "missing source modules from `eleven-square-continuation-2026-09-27.zip`.",
              "The supplementary files and their hashes are listed in",
              "`supplemental-provenance.json`. No source certificate is edited.", ""]
    return "\n".join(lines)


def write_replay(output: Path) -> None:
    """A standalone replay that verifies bundled hashes and recomputes audits."""
    script = '''#!/usr/bin/env python3
"""Verify SHA256SUMS, then independently replay packet-08 case audits."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,tempfile
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for line in (HERE/'SHA256SUMS').read_text().splitlines():
    expected,name=line.split('  ',1);actual=sha(HERE/name)
    if actual!=expected:raise SystemExit(f'Hash mismatch: {name}')
results=json.loads((HERE/'result.json').read_text())['results']
checker=HERE/'research/phase3/work/phase3/hull/audit_capture_v9.py'
assert sha(checker)=='95ae3362ee4992c332960e4af53697dd3d1b31e381682051b49fd47700ad9d0c'
for row in results:
    a=row['independent_audit'];s=row['source']
    if not a:
        print(f"{row['mask_index']}: unresolved; no independent audit")
        continue
    recorded=json.loads((HERE/a).read_text());assert sha(HERE/s)==row['source_sha256']
    with tempfile.TemporaryDirectory() as tmp:
        target=Path(tmp)/'audit.json'
        command=[sys.executable,str(HERE/'research/frontier/audit_case.py'),str(HERE/s),'--output',str(target)]
        subprocess.run(command,check=True,cwd=HERE,env={**os.environ,'OPENBLAS_NUM_THREADS':'1','PYTHONDONTWRITEBYTECODE':'1'})
        fresh=json.loads(target.read_text())
    for key in ('status','source_sha256','root_sha256','mask_index','mask',
                'parent_Uplus','cover_sha256','constraints','mask_exclusion_proved'):
        assert fresh[key]==recorded[key],(row['mask_index'],key)
    assert [n['sha256'] for n in fresh['nodes']]==[n['sha256'] for n in recorded['nodes']]
    assert fresh['mask_exclusion_proved']==row['mask_exclusion_proved']
    print(f"{row['mask_index']}: independently replayed; excluded={fresh['mask_exclusion_proved']}")
print('Packet replay completed. Global optimality is not asserted.')
'''
    (output / "replay.py").write_text(script)


def provenance(output: Path) -> None:
    # SHA256SUMS.json inside the original continuation archive binds these
    # eight archive members.  They were absent from the smaller case-tools ZIP.
    expected = {
        "work/phase3/capture/gmp/fast_arrangement.py": "bcca8c319c0887e5f34f16d40c72667e18afb9203ecdda7a7dc63f2f473b853c",
        "work/phase3/capture/gmp/fast_convex.py": "5d0763a754b3ccf60377d4cd2c8b4e3cdb429dca3e98e80036ac8e672d4c6567",
        "work/phase3/capture/gmp/fast_convex_v2.py": "c4085125aa1c106ec51f607038058ef73df4fd1972add5052ce3fb4ae3cc48e1",
        "work/phase3/capture/gmp/fast_core.py": "f37c9642bb785660e244d7126c1bb5d4f850bbc71af07adf368db95ffa6eaf9c",
        "work/phase3/capture/gmp/fast_core_v2.py": "2b9a30ab81189c47aa29b1fab445167334554f9ce1d3dab6602582a6e40508ea",
        "work/phase3/capture/gmp/fast_grid.py": "9a9242a8817dd5e02707f215e17e2d7b860d605436a0a26bfd61319fca911de7",
        "work/phase3/shared/SELF_HULL_CONTAINMENT_LEMMA.md": "ef259ce89f42a832b17832d5904d1600143a5a477a2c4389466f4b5dd0541573",
        "work/phase3/shared/UNIVERSAL_COLLISION_LEMMA.md": "5ec82e9a621756f869ec645b377b3092e411bca3449da6279a9a65c9c24bbc3b",
    }
    p = output / "research/phase3/work/phase3/capture/gmp"
    s = output / "research/phase3/work/phase3/shared"
    paths = {**{f"work/phase3/capture/gmp/{name}": p / name for name in (
        "fast_arrangement.py", "fast_convex.py", "fast_convex_v2.py",
        "fast_core.py", "fast_core_v2.py", "fast_grid.py")},
        **{f"work/phase3/shared/{name}": s / name for name in (
            "SELF_HULL_CONTAINMENT_LEMMA.md", "UNIVERSAL_COLLISION_LEMMA.md")}}
    for name, path in paths.items():
        assert path.is_file() and sha(path) == expected[name], path
    (output / "supplemental-provenance.json").write_text(json.dumps({
        "source_archive": "eleven-square-continuation-2026-09-27.zip",
        "archive_hash_manifest": "SHA256SUMS.json",
        "method": "Original archive members copied only when absent from case-tools.zip; no bundled file overwritten.",
        "files": {str(path.relative_to(output)): expected[name] for name, path in paths.items()}
    }, indent=2) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=HERE / "cases-08-result")
    args = ap.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"Refusing to replace {output}")
    code = WORKS[1] / "research"
    assert sha(code / CHECKER_REL.relative_to("research")) == CHECKER_HASH
    assert sha(code / COVER_REL.relative_to("research")) == COVER_HASH
    def ignore(directory: str, names: list[str]) -> set[str]:
        excluded = {n for n in names if n == "__pycache__" or n.endswith((".pyc", ".writing"))}
        if Path(directory).resolve() == (code / "frontier").resolve():
            excluded.update(n for n in names if n.startswith("mask") and n.endswith(".json"))
        return excluded

    shutil.copytree(code, output / "research", ignore=ignore)
    # Include the exact assignment specification so cell sites and theorem are
    # available without relying on a remembered conversation.
    shutil.copy2(HERE / "handoff/08-case-exclusions.md", output / "08-case-exclusions.md")
    for name in ("CASE_TOOLS_MANIFEST.json", "CASE_TOOLS_README.md"):
        shutil.copy2(WORKS[1] / name, output / name)
    shutil.copy2(Path(__file__), output / "package_08.py")
    canonical = read(code / COVER_REL.relative_to("research"))["canonical_eleven_cell_subsets"]
    results = [collect_case(index, canonical[index], output) for index in INDICES]
    status = "complete" if all(r["mask_exclusion_proved"] for r in results) else "partial"
    manifest = dict(job_id="cases-08", status=status, parent_Uplus=U,
                    assigned_mask_indices=list(INDICES), results=results,
                    global_optimality_proved=False)
    (output / "result.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (output / "proof.md").write_text(make_proof(results))
    write_replay(output)
    provenance(output)
    lines = [f"{sha(p)}  {p.relative_to(output)}" for p in sorted(output.rglob("*"))
             if p.is_file() and p.name != "SHA256SUMS"]
    (output / "SHA256SUMS").write_text("\n".join(lines) + "\n")
    print(f"Created {output}: {sum(r['mask_exclusion_proved'] for r in results)}/{len(results)} proved")


if __name__ == "__main__":
    main()
