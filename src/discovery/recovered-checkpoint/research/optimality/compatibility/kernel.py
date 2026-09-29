"""Exact necessary compatibility of polygon/half-angle placement domains.

The return value False excludes a whole pair domain. True is inconclusive.
This module does not assert that a compatible discrete assignment is a packing.
All decisive arithmetic is rational; square-root upper bounds use integer isqrt.
"""
from fractions import Fraction as F
from dataclasses import dataclass
from math import isqrt


def check_interval(interval):
    a, b = interval
    if not isinstance(a, F) or not isinstance(b, F) or not 0 <= a <= b <= 1:
        raise ValueError('Half-angle interval must be rational and inside [0,1]')


def cs(t):
    return (1-t*t)/(1+t*t), 2*t/(1+t*t)


def extent_lower(interval):
    check_interval(interval)
    # cos(theta)+sin(theta) has one interior maximum on [0,pi/2].
    return min(sum(cs(t))/2 for t in interval)


def clip(poly, a, b, d):
    """Closed polygon intersected with a*x+b*y <= d, exact degeneracies retained."""
    if not poly:
        return ()
    result = []
    for p, q in zip(poly, poly[1:] + poly[:1]):
        fp, fq = a*p[0]+b*p[1]-d, a*q[0]+b*q[1]-d
        if fp <= 0:
            result.append(p)
        if (fp < 0 < fq) or (fq < 0 < fp):
            t = fp/(fp-fq)
            result.append((p[0]+t*(q[0]-p[0]), p[1]+t*(q[1]-p[1])))
    # Duplicate consecutive vertices can occur at degenerate clipping boundaries.
    return tuple(dict.fromkeys(result))


def wall_clip(poly, interval, side):
    e = extent_lower(interval)
    for a, b, d in [(F(-1), F(0), -e), (F(0), F(-1), -e),
                    (F(1), F(0), side-e), (F(0), F(1), side-e)]:
        poly = clip(poly, a, b, d)
    return poly


def bbox(poly):
    return tuple((min(p[k] for p in poly), max(p[k] for p in poly)) for k in (0, 1))


def sqrt_upper(q, denominator=10**12):
    if q < 0:
        raise ValueError('Negative square-root input')
    k = isqrt((q.numerator*denominator**2)//q.denominator)
    if F(k, denominator)**2 < q:
        k += 1
    return F(k, denominator)


def arc_projection_upper(a, b, interval):
    """Upper bound of a*cos(theta)+b*sin(theta), tan(theta/2) in interval."""
    check_interval(interval)
    lo, hi = interval
    values = [a*cs(t)[0]+b*cs(t)[1] for t in interval]
    dl, dh = b-2*a*lo-b*lo*lo, b-2*a*hi-b*hi*hi
    # A sinusoid on an arc of length <= pi/2 has at most one critical point.
    # A strict interior maximum can occur only for derivative + at lo, - at hi.
    if dl > 0 and dh < 0:
        values.append(sqrt_upper(a*a+b*b))
    return max(values)


def threshold_lower(first, second):
    """Lower bound of 1+cos(theta_j-theta_i)+abs(sin(theta_j-theta_i))."""
    check_interval(first)
    check_interval(second)
    lo = (second[0]-first[1])/(1+second[0]*first[1])
    hi = (second[1]-first[0])/(1+second[1]*first[0])
    absolute = (F(0) if lo <= 0 <= hi else min(abs(lo), abs(hi)), max(abs(lo), abs(hi)))
    # For |r|<=1, h(r)=cos(delta)+sin(abs(delta)) has one interior maximum.
    return 1+min((1-r*r+2*r)/(1+r*r) for r in absolute)


@dataclass(frozen=True)
class Domain:
    cell: int
    poly: tuple
    angle: tuple
    tile: tuple = ()

    def __post_init__(self):
        check_interval(self.angle)
        if type(self.cell) is not int or not isinstance(self.poly, tuple):
            raise ValueError('Integer cell and tuple polygon required')
        if any(not isinstance(p, tuple) or len(p) != 2 or
               any(not isinstance(x, F) for x in p) for p in self.poly):
            raise ValueError('Every polygon coordinate must be an exact Fraction')
        signs = set()
        for p, q in zip(self.poly, self.poly[1:] + self.poly[:1]):
            for r in self.poly:
                cross = (q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
                if cross:
                    signs.add(1 if cross > 0 else -1)
        if len(signs) > 1:
            raise ValueError('Polygon must be cyclic convex, with either orientation')


def possible_pair(first, second, receipt=False):
    """False is a rigorous exclusion of every pose pair in the two domains."""
    if not first.poly or not second.poly:
        return (False, {'kind': 'empty-domain'}) if receipt else False
    delta = tuple((q[0]-p[0], q[1]-p[1]) for p in first.poly for q in second.poly)
    max_distance_sq = max(x*x+y*y for x, y in delta)
    if max_distance_sq < 1:
        result = {'kind': 'inscribed-disks', 'max_distance_sq': str(max_distance_sq)}
        return (False, result) if receipt else False
    if max_distance_sq >= 2 and not receipt:
        # Two circumradius-sqrt(1/2) disks can be disjoint at this vertex pair.
        # An inconclusive answer is always sound, even if relaxed wall clipping
        # has admitted this pair without a feasible realizing orientation.
        return True
    threshold = threshold_lower(first.angle, second.angle)
    bounds = []
    for interval in (first.angle, second.angle):
        for perpendicular in (False, True):
            bound = F(0)
            for x, y in delta:
                a, b = (y, -x) if perpendicular else (x, y)
                bound = max(bound, arc_projection_upper(a, b, interval),
                            arc_projection_upper(-a, -b, interval))
            bounds.append(2*bound)
            if 2*bound >= threshold and not receipt:
                return True
    possible = any(b >= threshold for b in bounds)
    result = {'kind': 'sat-interval', 'threshold_lower': str(threshold),
              'four_projection_upper_bounds': [str(v) for v in bounds]}
    return (possible, result) if receipt else possible


def physical_cells(packet):
    side = F(packet['side_upper'])
    cells = [tuple((F(1, 2)+(side-1)*F(x), F(1, 2)+(side-1)*F(y))
                   for x, y in cell['vertices']) for cell in packet['cells']]
    return side, cells


def subdivide_domains(cells, side, spatial=2, angular=8):
    if type(spatial) is not int or type(angular) is not int or spatial < 1 or angular < 1:
        raise ValueError('Positive integer subdivisions required')
    domains = []
    for cell, poly in enumerate(cells):
        (xl, xh), (yl, yh) = bbox(poly)
        for ix in range(spatial):
            for iy in range(spatial):
                tile = poly
                for a, b, d in [(F(-1), F(0), -(xl+(xh-xl)*ix/spatial)),
                                (F(1), F(0), xl+(xh-xl)*(ix+1)/spatial),
                                (F(0), F(-1), -(yl+(yh-yl)*iy/spatial)),
                                (F(0), F(1), yl+(yh-yl)*(iy+1)/spatial)]:
                    tile = clip(tile, a, b, d)
                for k in range(angular):
                    angle = (F(k, angular), F(k+1, angular))
                    wall = wall_clip(tile, angle, side)
                    if wall:
                        domains.append(Domain(cell, wall, angle, (ix, iy, k)))
    return domains
