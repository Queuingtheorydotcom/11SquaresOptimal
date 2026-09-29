"""Continue refined propagation without a further full angle bisection.

This is a producer only. The frozen independent v9 checker must replay all
ancestry before any contradiction becomes an accepted case exclusion.
"""
from pathlib import Path
import argparse
import sys
import gmpy2

if not __debug__:
    raise SystemExit('Assertions must remain enabled.')

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'endpoint-audit'))
import capture_engine_self_resume_v1 as E
F = E.F

def outer(vertices, world, grid=10**12):
    if not vertices:
        return [], []
    normals = set(tuple(map(F, n)) for n in E.DIRECTIONS)
    for n, _ in E.geo.rows(E.geo.hull(vertices)):
        scale = max(map(abs, n))
        if scale:
            n = tuple(F(round(v / scale * 10**6), 10**6) for v in n)
            if any(n):
                normals.add(n)
    result, bounds = world, []
    for n in sorted(normals):
        m = max(n[0]*x + n[1]*y for x, y in vertices)
        b = F(-((-m.numerator * grid)//m.denominator), grid)
        assert all(n[0]*x + n[1]*y <= b for x, y in vertices)
        bounds.append(dict(normal=n, upper=b))
        result = E.geo.clip_linear(result, n, b)
    return result, bounds

E.outer = outer
original_inner = E.inner_grid.inner_grid
def inner_grid(points, denominator=10**8, directions=16):
    return original_inner(points, denominator=denominator, directions=32)
E.inner_grid.inner_grid = inner_grid
original_save = E.save
def save(path, data):
    if 'dependencies' in data:
        data['dependencies'][str(Path(__file__).resolve())] = E.sha(__file__)
    return original_save(path, data)
E.save = save

def main():
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--seconds', type=float, default=180)
    p.add_argument('--partners', type=int, default=5)
    p.add_argument('--passes', type=int, default=30)
    p.add_argument('--priority', default='5,2,4,10,1,9,6',
                   help='Comma-separated occupied cell labels updated first')
    a = p.parse_args()
    if a.output.exists():
        raise FileExistsError(a.output)
    state, parent = E.load_state(a.source.resolve())
    assert not state['constraints'], 'This launcher handles unconditional cases only.'
    assert state['mask_index'] not in (438, 999, 1462, 1659, 1383, 1839)
    priority = [i for i in (int(x) for x in a.priority.split(',') if x) if i in state['mask']]
    E.run_node(state, a.output.resolve(), a.seconds, a.passes, priority, True,
               a.output.stem, parent, a.partners)

if __name__ == '__main__':
    main()
