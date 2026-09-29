"""Exact diagnostic of a frozen selected-row benchmark, not a bound proof."""
from copy import deepcopy
from fractions import Fraction as F
from hashlib import sha256
from math import lcm
from pathlib import Path
import json
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
from exact_mixed import expand
from majority_geometry import median_strips, require


def run():
    start = time.monotonic()
    raw = (HERE / 'true-probe.json').read_bytes()
    cert = json.loads(raw)
    benchmark = json.loads((HERE / 'benchmark.json').read_text())
    original = json.loads((ROOT / 'source/11-squares-certified-bound-main/global-certificate.json').read_text())
    proxy = deepcopy(cert)
    for atom in proxy['charge_orbits']:
        if atom.get('kind') == 'majority_hull':
            atom['kind'] = 'threshold'
    points, weights, _, _, D = expand(proxy)
    L, A = F(cert['L']), F(cert['A'])
    scale = lcm(2 * D, (A / 2).denominator)
    factor, LD = scale // (2 * D), int(L * D)
    positive_atoms = [atom for atom in cert['charge_orbits'] if atom['weight']]
    results = []
    for row in benchmark['rows']:
        idx = row['row']
        core_answer = row['history'][-1]['patches']['answer']
        center = tuple(map(F, core_answer['world_center']))
        entry = original['entries'][idx]
        poses = []
        for label, t in [('left_endpoint', F(entry[0])), ('core_angle', F(row['core_halfangle'])), ('right_endpoint', F(entry[1]))]:
            p, q = t.numerator, t.denominator
            C, S, R = q*q-p*p, 2*p*q, q*q+p*p
            radius = A * (abs(C) + abs(S)) / (2 * R)
            x, y = (max(radius, min(L-radius, z)) for z in center)
            require(radius <= x <= L-radius and radius <= y <= L-radius, 'Parent outside walls')
            uv = [(factor*(C*(2*a-LD)+S*(2*b-LD)), factor*(-S*(2*a-LD)+C*(2*b-LD))) for a,b in points]
            half = int(A*scale/2)*R
            u = scale * (C*(x-L/2) + S*(y-L/2))
            v = scale * (-S*(x-L/2) + C*(y-L/2))
            den = lcm(u.denominator, v.denominator)
            U, V = int(u*den), int(v*den)
            captured = [abs(U-a*den) <= half*den and abs(V-b*den) <= half*den for a,b in uv]
            totals = {'point': sum(w for w, hit in zip(weights, captured) if hit), 'floor': 0, 'majority_hull': 0, 'threshold': 0}
            for atom in positive_atoms:
                kind, k, w = atom.get('kind', 'threshold'), atom['threshold'], atom['weight']
                for group in atom['sets']:
                    if kind == 'majority_hull':
                        require(len(group) == 2*k-1, 'Invalid odd majority')
                        hit = all(lo*den <= a*U+b*V <= hi*den for a,b,lo,hi in median_strips([uv[i] for i in group], half))
                    else:
                        count = sum(captured[i] for i in group)
                        require(kind in ('floor', 'threshold'), 'Unsupported kind')
                        hit = count//k if kind == 'floor' else int(count >= k)
                    totals[kind] += w*hit
            charge = sum(totals.values())
            poses.append(dict(label=label, halfangle=str(t), center=[str(x), str(y)], clamped=(x,y) != center,
                              contained=True, true_charge_units=charge, components=totals,
                              deficient=charge < cert['minimum_units']))
        results.append(dict(row=idx, core_true_charge_units=core_answer['true_charge_units'], parents=poses,
                            any_deficient_parent=any(p['deficient'] for p in poses)))
        print(idx, [p['true_charge_units'] for p in poses], flush=True)
    result = dict(status='COMPLETE_FROZEN_SNAPSHOT_PARENT_DIAGNOSTIC',
                  scope='Individually legal parents for these frozen weights only; no packing or global bound proof',
                  certificate_sha256=sha256(raw).hexdigest(), threshold_units=cert['minimum_units'],
                  target_side=str(L/A), parent_side=str(A), rows=results,
                  genuine_parent_deficit_rows=[r['row'] for r in results if r['any_deficient_parent']],
                  core_only_for_these_three_parent_tests=[r['row'] for r in results if not r['any_deficient_parent']],
                  seconds=time.monotonic()-start)
    (HERE/'full-parent-checks.json').write_text(json.dumps(result, indent=2)+'\n')
    print(result['genuine_parent_deficit_rows'], 'seconds', result['seconds'])


if __name__ == '__main__':
    if not __debug__:
        raise SystemExit('Assertions must remain enabled')
    run()
