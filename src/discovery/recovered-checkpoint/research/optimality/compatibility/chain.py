"""Rational longitudinal gap propagation coupling multiple neighbor supports."""
from fractions import Fraction as F
from functools import lru_cache
from itertools import combinations
from math import isqrt
import time
from kernel import bbox, clip, cs, threshold_lower


def hull(points):
    points = sorted(set(points))
    if len(points) < 3:
        return tuple(points)
    def cross(p, q, r):
        return (q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
    lower, upper = [], []
    for p in points:
        while len(lower) > 1 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(points):
        while len(upper) > 1 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return tuple(lower[:-1]+upper[:-1])


def prove_orders(cells):
    result = []
    for axis in (0, 1):
        lines = [list(range(4*k, 4*k+4)) for k in range(4)] if axis == 0 else [list(range(k,16,4)) for k in range(4)]
        for line in lines:
            for i, j in combinations(line, 2):
                delta = hull([(q[0]-p[0], q[1]-p[1]) for p in cells[i] for q in cells[j]])
                reverse = clip(delta, F(axis == 0), F(axis == 1), F(0))
                maximum = max((x*x+y*y for x,y in reverse), default=F(0))
                if reverse and maximum >= 1:
                    continue
                result.append({'left': i, 'right': j, 'axis': axis,
                               'reversed_difference_max_distance_squared': str(maximum),
                               'reversed_difference_polygon': [[str(x),str(y)] for x,y in reverse]})
    return result


@lru_cache(maxsize=None)
def angular_gap_data(a, b):
    h = threshold_lower(a, b)/2
    coefficients = []
    for interval in (a,b):
        cmax, smax = cs(interval[0])[0], cs(interval[1])[1]
        coefficients += [(cmax,smax), (smax,cmax)]
    return h, tuple(coefficients)


def gap_lower(a, b, transverse):
    """Necessary positive ordered-coordinate gap, rational lower approximation."""
    if transverse < 0:
        raise ValueError('Negative transverse bound')
    h, coefficients = angular_gap_data(a,b)
    candidates = []
    for along, across in coefficients:
        numerator = h-across*transverse
        if numerator <= 0:
            candidates.append(F(0))
        elif along > 0:
            candidates.append(numerator/along)
    if not candidates:
        raise ValueError('No possible projection axes')
    sat = min(candidates)
    d = 10**9
    q = max(F(0), 1-transverse*transverse)
    disk = F(isqrt(q.numerator*d*d//q.denominator), d)
    return max(sat,disk)


def contract(mask, domains, bycell, adjacency, orders, max_rounds=24, deadline=None, collect_trace=False):
    active = {c:set(bycell[c]) for c in mask}
    limits = {}
    for c in mask:
        for a in active[c]:
            (xl,xh),(yl,yh) = bbox(domains[a].poly)
            limits[a] = [xl,xh,yl,yh]
    selected = [r for r in orders if r['left'] in active and r['right'] in active]
    updates = 0
    trace = []
    for round_index in range(max_rounds):
        changed = False
        for order in selected:
            if deadline is not None and time.monotonic() >= deadline:
                return {'status': 'TIME_LIMIT_UNRESOLVED', 'rounds': round_index, 'updates': updates,
                        'survivors': {str(k):len(v) for k,v in active.items()}, 'trace': trace}
            left, right, axis = order['left'],order['right'],order['axis']
            along, trans = 2*axis, 2*(1-axis)
            lower_right = {}; upper_left = {}
            for a in active[left]:
                aa = limits[a]
                for b in adjacency[a] & active[right]:
                    bb = limits[b]
                    transverse = max(abs(aa[trans]-bb[trans+1]),abs(aa[trans+1]-bb[trans]))
                    gap = gap_lower(domains[a].angle,domains[b].angle,transverse)
                    if aa[along]+gap > bb[along+1]:
                        continue
                    lower_right[b] = min(lower_right.get(b, aa[along]+gap), aa[along]+gap)
                    upper_left[a] = max(upper_left.get(a, bb[along+1]-gap), bb[along+1]-gap)
            for a in list(active[left]):
                if a not in upper_left:
                    if collect_trace:
                        trace.append({'round':round_index,'kind':'no_successor','state':a,'cell':left,'against':right,'axis':axis,
                                      'bounds':[str(v) for v in limits[a]],'remaining_neighbor_states':sorted(active[right])})
                    active[left].remove(a); changed = True; updates += 1
                elif upper_left[a] < limits[a][along+1]:
                    if collect_trace:
                        trace.append({'round':round_index,'kind':'upper_bound','state':a,'cell':left,'against':right,'axis':axis,
                                      'old':str(limits[a][along+1]),'new':str(upper_left[a])})
                    limits[a][along+1] = upper_left[a]; changed = True; updates += 1
            for b in list(active[right]):
                if b not in lower_right:
                    if collect_trace:
                        trace.append({'round':round_index,'kind':'no_predecessor','state':b,'cell':right,'against':left,'axis':axis,
                                      'bounds':[str(v) for v in limits[b]],'remaining_neighbor_states':sorted(active[left])})
                    active[right].remove(b); changed = True; updates += 1
                elif lower_right[b] > limits[b][along]:
                    if collect_trace:
                        trace.append({'round':round_index,'kind':'lower_bound','state':b,'cell':right,'against':left,'axis':axis,
                                      'old':str(limits[b][along]),'new':str(lower_right[b])})
                    limits[b][along] = lower_right[b]; changed = True; updates += 1
            for c in (left,right):
                for a in list(active[c]):
                    if limits[a][0] > limits[a][1] or limits[a][2] > limits[a][3]:
                        active[c].remove(a); changed = True; updates += 1
                if not active[c]:
                    return {'status': 'EXCLUDED', 'rounds': round_index+1, 'updates': updates,
                            'empty_cell': c, 'survivors': {str(k):len(v) for k,v in active.items()}, 'trace': trace}
        if not changed:
            return {'status': 'FIXED_POINT_UNRESOLVED', 'rounds': round_index+1, 'updates': updates,
                    'survivors': {str(k):len(v) for k,v in active.items()}, 'trace': trace}
    return {'status': 'ROUND_LIMIT_UNRESOLVED', 'rounds': max_rounds, 'updates': updates,
            'survivors': {str(k):len(v) for k,v in active.items()}, 'trace': trace}
