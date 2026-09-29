#!/usr/bin/env python3
"""Independent asymmetric-core controls for the universal collision validator."""
from pathlib import Path
import sys,json,hashlib
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'collision'))
import validate_collision_kernel as v
F=v.F
Qi=[(F(1),F(0)),(F(2),F(0)),(F(2),F(1)),(F(1),F(1))]
Qj=[(F(-1),F(0)),(F(0),F(0)),(F(0),F(1)),(F(-1),F(1))]
D=[(F(-5),F(-5)),(F(5),F(-5)),(F(5),F(5)),(F(-5),F(5))]
rows=[dict(core=Qj,domain=[(F(0),F(0))],reference='zero')]
f=lambda rs,P:v.validate_collision_polygon(Qi,rs,D,P)['passed']
assert f(rows,[(F(-2),F(0))])
assert not f(rows,[(F(2),F(0))])
assert f(rows,[(F(-3),F(1)),(F(-1),F(-1))])
assert not f(rows,[(F(-3)-F(1,10**50),F(0))])
shift=[dict(core=Qj,domain=[(F(2),F(0))],reference='two')]
assert f(shift,[(F(0),F(0))])
assert not f(shift,[(F(-2),F(0))])
assert f(rows+shift,[(F(-1),F(-1)),(F(-1),F(1))])
assert not f(rows+shift,[(F(-1)+F(1,10**50),F(0))])
assert not f(rows+shift,[(F(-1)-F(1,10**50),F(0))])
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
out=dict(status='PASS_INDEPENDENT_ASYMMETRIC_COLLISION_SIGN_CONTROLS',checks=9,checker_sha256=sha(__file__),collision_validator_sha256=sha(v.__file__),arrangement_dependency_sha256=sha(v.geo.__file__),scope='Exact analytic rectangle controls establish the Qj−Qi sign, translation direction, universal intersection over all partner poses, preservation of a one-dimensional kernel, and rejection of 10^-50 violations. Complete case certificates require the separate pose-cover and strict-core induction.')
(HERE/'collision-sign-controls.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
