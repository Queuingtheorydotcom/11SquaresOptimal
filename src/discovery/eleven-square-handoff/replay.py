#!/usr/bin/env python3
"""Inventory and run the included proof checkers; this is not a proof checker itself."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import tempfile
import zipfile


HERE = Path(__file__).resolve().parent
SOURCES = {
    "ElevenSquaresSixCaseCertificate.zip": (
        "c107a86019ee60a3dc067f7fb4c8f847f8d29becadba075d4aac169db65c209f",
        4_864_002,
    ),
    "11-squares-certified-3.8754.zip": (
        "61a3f70079bb8dd1b826b9ffc34ff0e149bfab3be111e56d592cb92b373c3934",
        22_531_299,
    ),
}
SIX_CASE = HERE / "proofs" / "ElevenSquaresSixCaseCertificate.zip"
LOWER_BOUND = HERE / "proofs" / "11-squares-certified-3.8754.zip"
PHASE3_SNAPSHOT = "work/phase3/audit/overall-union-snapshot-bc3563a0c995.json"
PHASE3_HASH = "bc3563a0c9955a561f99cbefe7278e027feff085ff6d97bc338e347f97514545"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def check_archive(path: Path) -> None:
    expected_hash, expected_size = SOURCES[path.name]
    if path.stat().st_size != expected_size:
        raise ValueError(f"wrong size for {path.name}")
    if digest(path) != expected_hash:
        raise ValueError(f"wrong SHA-256 for {path.name}")
    with zipfile.ZipFile(path) as archive:
        damaged = archive.testzip()
        if damaged is not None:
            raise ValueError(f"CRC failure in {path.name}: {damaged}")
        print(f"{path.name}: SHA-256 and CRC pass ({len(archive.infolist())} members)")


def safe_extract(path: Path, dest: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        for member in archive.infolist():
            name = PurePosixPath(member.filename)
            mode = member.external_attr >> 16
            if (name.is_absolute() or ".." in name.parts or "\\" in member.filename
                    or ":" in member.filename or stat.S_ISLNK(mode)):
                raise ValueError(f"unsafe archive member: {member.filename!r}")
        archive.extractall(dest)


def run_six_case() -> None:
    check_archive(SIX_CASE)
    with tempfile.TemporaryDirectory(prefix="eleven-square-six-") as tmp:
        root = Path(tmp)
        safe_extract(SIX_CASE, root)
        for script in (
            "endpoint/check_alpha_upper.py",
            "endpoint/audit_mask800_transfer.py",
            "satkernel/check_tenowner_transfer.py",
        ):
            print(f"Running {script}", flush=True)
            subprocess.run([sys.executable, script], cwd=root, check=True)
    print("Three included six-case audits passed; no wider case count was checked.")


def run_lower_premises() -> None:
    check_archive(LOWER_BOUND)
    with tempfile.TemporaryDirectory(prefix="eleven-square-bound-") as tmp:
        root = Path(tmp)
        safe_extract(LOWER_BOUND, root)
        package = root / "11-squares-true-19377-5000"
        subprocess.run([sys.executable, "verify.py", "--premises-only"], cwd=package, check=True)
    print("Premises-only mode finished; it did not freshly replay spatial geometry.")


def inspect_phase3(path: Path) -> None:
    if path.is_dir():
        matches = [p for p in path.rglob(Path(PHASE3_SNAPSHOT).name)
                   if str(p).endswith(PHASE3_SNAPSHOT)]
        if len(matches) != 1:
            raise ValueError(f"expected one snapshot, found {len(matches)}")
        found_hash = digest(matches[0])
        names = [str(p.relative_to(path)) for p in path.rglob("*") if p.is_file()]
    else:
        with zipfile.ZipFile(path) as archive:
            matches = [n for n in archive.namelist() if n.endswith(PHASE3_SNAPSHOT)]
            if len(matches) != 1:
                raise ValueError(f"expected one snapshot, found {len(matches)}")
            h = hashlib.sha256()
            with archive.open(matches[0]) as f:
                for block in iter(lambda: f.read(1 << 20), b""):
                    h.update(block)
            found_hash = h.hexdigest()
            names = archive.namelist()
    print(f"snapshot SHA-256: {found_hash}")
    print(f"matches saved 253-case checkpoint: {found_hash == PHASE3_HASH}")
    for name in ("PHASE3_REPLAY_MANIFEST.json", "PHASE3_GENERIC_ENTRIES.json", "SHA256SUMS.json"):
        hits = [n for n in names if n.endswith(name)]
        print(f"{name}: {len(hits)} matching member(s)")
    print("Inventory only. Run the manifest's independent replay recipes before counting exclusions.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="check hashes and ZIP CRCs of the two proof packages")
    sub.add_parser("six-case", help="run the three fast six-case audit commands")
    sub.add_parser("lower-bound-premises", help="run the catalogue's premises-only checker")
    phase3 = sub.add_parser("inspect-phase3", help="inventory a recovered Phase 3 ZIP or directory")
    phase3.add_argument("path", type=Path)
    args = parser.parse_args()
    if args.command == "check":
        for name in SOURCES:
            check_archive(HERE / "proofs" / name)
    elif args.command == "six-case":
        run_six_case()
    elif args.command == "lower-bound-premises":
        run_lower_premises()
    else:
        inspect_phase3(args.path)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, zipfile.BadZipFile, subprocess.CalledProcessError) as error:
        sys.exit(f"handoff check failed: {error}")
