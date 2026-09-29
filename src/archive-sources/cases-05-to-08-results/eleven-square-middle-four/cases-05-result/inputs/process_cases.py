"""Run packet 05 exact producer, refinement, and independent checker sequentially."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
FRONTIER = ROOT / "research/frontier"
# Initial breadth pass after the first five masks were handled separately.
MASKS = [1530, 1538, 1539, 1554, 1567, 1574, 1582, 1594, 1595, 1597]
ENV = dict(os.environ, OPENBLAS_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1")
LOG = ROOT / "process.log"


def line(*args):
    message = " ".join(map(str, args))
    print(message, flush=True)
    with LOG.open("a") as f:
        f.write(message + "\n")


def run(label, args):
    started = time.monotonic()
    line("START", label, " ".join(map(str, args)))
    with (ROOT / f"{label}.log").open("w") as out:
        p = subprocess.run([sys.executable, *map(str, args)], cwd=ROOT,
                           env=ENV, stdout=out, stderr=subprocess.STDOUT)
    line("END", label, "rc", p.returncode, "wall_seconds", round(time.monotonic()-started, 3))
    if p.returncode:
        line("ERROR", label, (ROOT / f"{label}.log").read_text()[-3000:])
    return p.returncode == 0


def summary(path):
    d = json.loads(path.read_text())
    return d.get("closed"), bool(d.get("contradiction")), len(d.get("steps", []))


for mask in MASKS:
    source = FRONTIER / f"mask{mask}-self-v1.json"
    if not source.exists():
        if not run(f"mask{mask}-producer", [FRONTIER / "run_case.py", mask,
                                               "--seconds", 120, "--bins", 32]):
            continue
    try:
        closed, contradicted, steps = summary(source)
    except Exception as exc:
        line("ERROR", mask, "source malformed", repr(exc))
        continue
    line("SOURCE", mask, "closed", closed, "contradiction", contradicted, "steps", steps)
    if not contradicted:
        line("OPEN", mask, "retained exact domains in", source.name,
             "for a separate selective refinement pass")
        continue
    if source.exists():
        audit = FRONTIER / f"mask{mask}-independent.json"
        if not audit.exists():
            run(f"mask{mask}-audit", [FRONTIER / "audit_case.py", source, "--output", audit])
        if audit.exists():
            d = json.loads(audit.read_text())
            line("AUDIT", mask, d.get("status"), "exclusion", d.get("mask_exclusion_proved"),
                 "seconds", d.get("seconds"), "source", source.name)

line("ALL DONE")
