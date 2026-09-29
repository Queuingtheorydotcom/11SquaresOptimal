"""Additional finite geometry controls; these are not the full certificate replay."""
from fractions import Fraction
from hashlib import sha256
import json
from math import gcd
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent / 'eleven-square-handoff/lower-bound/11-squares-true-19377-5000'
sys.path.insert(0, str(PACKAGE / 'catalogue/checker'))
from majority_mixed import validate, geometry
from majority_precompute import prepare_majority, row_strips
from majority_geometry import median_strips
from integer_sweep import accumulate


def normalized(strips):
    answer = set()
    for a, b, lo, hi in strips:
        g = gcd(abs(a), abs(b))
        assert lo % g == hi % g == 0
        a, b, lo, hi = a // g, b // g, lo // g, hi // g
        if a < 0 or (a == 0 and b < 0):
            a, b, lo, hi = -a, -b, -hi, -lo
        answer.add((a, b, lo, hi))
    return answer


def main():
    started = time.monotonic()
    raw = (PACKAGE / 'catalogue/candidate.json').read_bytes()
    candidate = json.loads(raw)
    data, jobs, margin = validate(candidate)
    prepared = prepare_majority(data)
    rows = []
    cases = [(0, False), (3067, False), (6134, False),
             (9201, False), (len(jobs) - 1, False), (6134, True)]
    comparisons = 0
    for index, conditional in cases:
        start = time.monotonic()
        arrays, meta = geometry(*data, *jobs[index], meta=True,
                               domain_conditional=conditional, prepared=prepared,
                               verify_staircase_corners=True)
        factor = meta['scale'] // (2 * data[4])
        for feature, (group, k, weight) in zip(prepared, data[-1]):
            points = [meta['uv'][i] for i in group]
            direct = median_strips(points, meta['half'])
            cached = row_strips(feature, points, meta['half'], meta['C'],
                                meta['S'], meta['R'], factor)
            assert normalized(direct) == normalized(cached)
            comparisons += 1
        optimized = tuple(map(int, accumulate(*arrays)))
        direct = tuple(map(int, accumulate(*arrays, direct=True)))
        assert optimized == direct
        entry = dict(leaf_index=index, conditional=conditional,
                     proxy_minimum_units=optimized[0], cells=optimized[1],
                     rectangles=len(meta['rect']),
                     absolute_rectangle_units=meta['absolute_rectangle_units'],
                     seconds=time.monotonic() - start)
        rows.append(entry)
        print(json.dumps(entry), flush=True)
    result = dict(status='PASS_SELECTED_ACTUAL_GEOMETRY_CONTROLS',
                  scope='Finite controls only; full verifier must replay all jobs separately.',
                  candidate_sha256=sha256(raw).hexdigest(),
                  raw_vs_cached_majority_strip_comparisons=comparisons,
                  exact_staircase_corner_and_domain_checks=True,
                  direct_vs_segment_tree_sweeps=len(rows),
                  rows=rows, seconds=time.monotonic() - started)
    (HERE / 'selected-geometry-controls.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=2))


if __name__ == '__main__':
    main()
