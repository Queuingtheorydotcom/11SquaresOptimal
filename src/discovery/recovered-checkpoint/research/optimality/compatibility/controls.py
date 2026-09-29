"""Small independently formulated geometry controls for the interval kernel."""
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path
from random import Random
from kernel import Domain, arc_projection_upper, cs, extent_lower, possible_pair, wall_clip


def point(x, y, t):
    return Domain(0, ((F(x), F(y)),), (F(t), F(t)))


def independent_point_sat(a, b):
    ca, sa = cs(a.angle[0]); cb, sb = cs(b.angle[0])
    dx, dy = (b.poly[0][k]-a.poly[0][k] for k in (0, 1))
    h = 1+ca*cb+sa*sb+abs(ca*sb-sa*cb)
    return max(abs(2*(dx*ca+dy*sa)), abs(2*(-dx*sa+dy*ca)),
               abs(2*(dx*cb+dy*sb)), abs(2*(-dx*sb+dy*cb))) >= h


def main():
    checks = 0
    for dx, dy, expected in [(1, 0, True), (F(999, 1000), 0, False),
                              (1, 1, True), (F(99, 100), F(99, 100), False)]:
        assert possible_pair(point(0, 0, 0), point(dx, dy, 0)) == expected
        checks += 1
    rng = Random(1024)
    for _ in range(600):
        a = point(0, 0, F(rng.randrange(21), 20))
        b = point(F(rng.randrange(-25, 26), 20), F(rng.randrange(-25, 26), 20),
                  F(rng.randrange(21), 20))
        assert possible_pair(a, b) == independent_point_sat(a, b)
        checks += 1
    for _ in range(100):
        lo, hi = sorted([F(rng.randrange(21), 20), F(rng.randrange(21), 20)])
        a, b = F(rng.randrange(-9, 10)), F(rng.randrange(-9, 10))
        upper = arc_projection_upper(a, b, (lo, hi))
        for k in range(51):
            t = lo+(hi-lo)*F(k, 50)
            c, s = cs(t)
            assert a*c+b*s <= upper
        checks += 1
    p = tuple((F(x), F(y)) for x, y in [(0, 0), (4, 0), (4, 4), (0, 4)])
    w = wall_clip(p, (F(1, 2), F(1, 2)), F(4))
    assert set(w) == {(F(x), F(y)) for x, y in [(F(7, 10), F(7, 10)), (F(33, 10), F(7, 10)),
                                             (F(33, 10), F(33, 10)), (F(7, 10), F(33, 10))]}
    checks += 1
    # Exact contact remains possible, even with rotations and large denominators.
    for t in (F(0), F(1, 7), F(2, 5), F(1)):
        c, s = cs(t)
        assert possible_pair(point(0, 0, t), point(c, s, t))
        assert not possible_pair(point(0, 0, t), point(c*(1-F(1, 10**15)), s*(1-F(1, 10**15)), t))
        checks += 2
    for interval in ((F(-1), F(0)), (F(1), F(0)), (0., 1.)):
        try:
            extent_lower(interval)
        except ValueError:
            checks += 1
        else:
            raise AssertionError('Invalid interval accepted')
    for poly in (((0.0, 0.0),), tuple((F(x), F(y)) for x, y in [(0, 0), (1, 1), (1, 0), (0, 1)])):
        try:
            Domain(0, poly, (F(0), F(1)))
        except ValueError:
            checks += 1
        else:
            raise AssertionError('Invalid polygon accepted')
    out = {'status': 'PASS_SMALL_CONTROLS', 'checks': checks,
           'kernel_sha256': hashlib.sha256(Path(__file__).with_name('kernel.py').read_bytes()).hexdigest(),
           'global_optimality_proved': False}
    Path(__file__).with_name('controls.json').write_text(json.dumps(out, indent=2)+'\n')
    print(json.dumps(out))


if __name__ == '__main__':
    main()
