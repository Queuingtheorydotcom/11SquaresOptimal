"""Replay the separate all-line-intersections audit on the symmetric cover."""
from pathlib import Path
from itertools import combinations
from fractions import Fraction as F
import hashlib
import json
import runpy

if not __debug__:
    raise SystemExit('Assertions must remain enabled.')
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
source = ROOT/'phase3/current/research/optimality/global_capture/center-cover-symmetric-exact.json'
checker = ROOT/'recovered-checkpoint/research/optimality/audit/audit_center_cover.py'
module = runpy.run_path(str(checker))
result = module['audit'](source)
data = json.loads(source.read_text())
turn = lambda J: tuple(sorted(15-i for i in J))
canonical = sorted({min(J, turn(J)) for J in combinations(range(16), 11)})
assert list(map(list, canonical)) == data['canonical_eleven_cell_subsets']
assert len(canonical) == 2184
for i in range(16):
    reflected = {(1-F(x), 1-F(y)) for x,y in data['cells'][i]['vertices']}
    assert reflected == {tuple(map(F, p)) for p in data['cells'][15-i]['vertices']}
result.update(half_turn_cells_checked=16, canonical_masks=2184,
              checker_sha256=hashlib.sha256(checker.read_bytes()).hexdigest(),
              wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
output = HERE/'fresh-center-cover-verification.json'
output.write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
