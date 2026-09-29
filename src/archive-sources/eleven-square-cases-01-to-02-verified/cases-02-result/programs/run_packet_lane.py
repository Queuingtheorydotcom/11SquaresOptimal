"""Run assigned case producers and independent audits, one case at a time.

This launcher is orchestration only; its JSON summaries are never proof evidence.
The original source ancestry and audit outputs are retained in research/frontier.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
FRONT = ROOT / "research/frontier"
ENV = dict(os.environ, OPENBLAS_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1")


def call(args, log):
    with log.open("w") as out:
        p = subprocess.run([sys.executable, *map(str, args)], cwd=ROOT,
                           env=ENV, stdout=out, stderr=subprocess.STDOUT)
    if p.returncode:
        print(f"FAILED {args} exit={p.returncode} log={log}", flush=True)
    return p.returncode == 0


def contradiction(path):
    try:
        record = json.loads(path.read_text())
    except (OSError, ValueError):
        return False
    return bool(record.get("terminal") and record.get("contradiction")
                and not record.get("constraints"))


def process(index):
    root = FRONT / f"mask{index}-self-v1.json"
    if not root.exists():
        if not call(["research/frontier/run_case.py", index, "--seconds", 120],
                    FRONT / f"mask{index}-producer.log"):
            return
    source = root
    for round_number in range(1, 3):
        if contradiction(source):
            break
        new = FRONT / f"mask{index}-refined-{round_number}.json"
        if not new.exists():
            if not call(["research/frontier/refine_case.py", source,
                         "--output", new, "--seconds", 180],
                        FRONT / f"mask{index}-refine-{round_number}.log"):
                return
        source = new
    if not contradiction(source):
        print(f"OPEN {index} {source}", flush=True)
        return
    audit = FRONT / f"mask{index}-independent.json"
    if not audit.exists():
        if not call(["research/frontier/audit_case.py", source,
                     "--output", audit], FRONT / f"mask{index}-audit.log"):
            return
    a = json.loads(audit.read_text())
    if a.get("mask_exclusion_proved") and a.get("constraints") == []:
        print(f"PROVED {index} {source.name}", flush=True)
    else:
        print(f"AUDIT NOT EXCLUSION {index} {audit}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("indices", type=int, nargs="+")
    for index in parser.parse_args().indices:
        process(index)
