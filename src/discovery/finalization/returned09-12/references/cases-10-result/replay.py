"""Re-run the frozen independent v9 checker on every packet-10 certificate.

Usage: python replay.py [mask ...]
Requirements: Python 3.12, gmpy2 2.3.1. SymPy 1.14 is needed only to
regenerate producer traces; this checker is separately implemented.
"""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent
RESULT = json.loads((ROOT / "result.json").read_text())
REQUESTED = set(map(int, sys.argv[1:])) if len(sys.argv) > 1 else None


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for line in (ROOT / "SHA256SUMS").read_text().splitlines():
    expected, relative = line.split("  ", 1)
    assert sha(ROOT / relative) == expected, relative

with tempfile.TemporaryDirectory(prefix="eleven-squares-packet10-") as td:
    workspace = Path(td)
    with zipfile.ZipFile(ROOT / "case-tools.zip") as z:
        z.extractall(workspace)
    for file in json.loads((ROOT / "CASE_TOOLS_MANIFEST.json").read_text())["files"]:
        target = workspace / file["path"]
        assert target.stat().st_size == file["bytes"] and sha(target) == file["sha256"]
    for source in (ROOT / "producer_adapters").rglob("*.py"):
        target = workspace / source.relative_to(ROOT / "producer_adapters")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    frontier = workspace / "research/frontier"
    for source in (ROOT / "certificates").glob("*.json"):
        shutil.copy2(source, frontier / source.name)
    env = os.environ.copy()
    env.update(ELEVEN_RATIONAL_BACKEND="gmp", PYTHONDONTWRITEBYTECODE="1",
               OPENBLAS_NUM_THREADS="1")
    for entry in RESULT["results"]:
        index = entry["mask_index"]
        if REQUESTED is not None and index not in REQUESTED:
            continue
        if not entry["mask_exclusion_proved"]:
            print(f"{index}: unresolved; no exclusion claim")
            continue
        source = frontier / Path(entry["source"]).name
        assert sha(source) == entry["source_sha256"]
        target = frontier / f"mask{index}-replayed-audit.json"
        with (frontier / f"mask{index}-replayed.log").open("w") as log:
            subprocess.run([sys.executable, str(frontier / "audit_case.py"),
                            str(source), "--output", str(target)], cwd=workspace,
                           env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
        d = json.loads(target.read_text())
        assert d["mask_index"] == index and d["mask"] == entry["occupied_cells"]
        assert d["source_sha256"] == entry["source_sha256"]
        assert d["status"] == "PASS_INDEPENDENT_GENERIC_HULL_AUDIT"
        assert d["constraints"] == [] and d["mask_exclusion_proved"]
        print(f"{index}: PASS_INDEPENDENT_GENERIC_HULL_AUDIT")
