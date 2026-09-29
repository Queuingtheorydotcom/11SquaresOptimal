"""Recompute claimed pair exclusions and independently replay finite mask exclusions.

Uses the reviewed rational geometry kernel, but does not call the producer's
arc-consistency or clique-search implementation. Only explicit EXCLUDED masks
become proved exclusions. There is no global or local-capture success status.
"""
import argparse
import hashlib
import json
import sys
import time
from fractions import Fraction as F
from pathlib import Path
from kernel import physical_cells, subdivide_domains, possible_pair, bbox


def independent_exhaustion(mask, domains, forbidden, node_cap):
    bycell = {c: [i for i,d in enumerate(domains) if d.cell == c] for c in mask}
    # Deliberately use a stack, a largest-degree order, and direct forbidden pairs.
    order = sorted(mask, key=lambda c: (-sum(domains[a].cell == c or domains[b].cell == c
                                            for a,b in forbidden), c))
    stack = [({}, 0)]
    nodes = 0
    while stack:
        chosen, depth = stack.pop()
        nodes += 1
        if nodes > node_cap:
            return 'NODE_LIMIT', nodes
        if depth == len(order):
            return 'ABSTRACT_ASSIGNMENT', nodes
        c = order[depth]
        for v in bycell[c]:
            if all((min(v,w), max(v,w)) not in forbidden for w in chosen.values()):
                nextchosen = dict(chosen); nextchosen[c] = v
                # Check future variables each still have some possible state.
                if all(any(all((min(u,w), max(u,w)) not in forbidden
                               for w in nextchosen.values()) for u in bycell[k])
                       for k in order[depth+1:]):
                    stack.append((nextchosen, depth+1))
    return 'EXCLUDED', nodes


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cover', type=Path, required=True)
    p.add_argument('--graph', type=Path, required=True)
    p.add_argument('--search', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--seconds', type=int, default=180)
    p.add_argument('--nodes', type=int, default=10000000)
    a = p.parse_args()
    start = time.monotonic()
    cb, gb, sb = a.cover.read_bytes(), a.graph.read_bytes(), a.search.read_bytes()
    cover, graph, search = map(json.loads, (cb, gb, sb))
    if graph['cover_sha256'] != hashlib.sha256(cb).hexdigest() or search['graph_sha256'] != hashlib.sha256(gb).hexdigest():
        raise ValueError('Input digest mismatch')
    sys.path.insert(0, str(Path(__file__).parents[1]/'global_capture'))
    from verify_center_cover import verify
    checked = verify([tuple(F(v) for v in c['center']) for c in cover['cells']],
                     F(cover['unit_square_cover_radius_bound']))
    if checked['cells'] != cover['cells'] or checked['side_upper'] != cover['side_upper']:
        raise ValueError('Cover regeneration differs')
    side, cells = physical_cells(cover)
    domains = subdivide_domains(cells, side, graph['spatial_subdivisions'], graph['angular_subdivisions'])
    if len(domains) != graph['domain_count']:
        raise ValueError('Inconsistent domain graph')
    boxes = [bbox(d.poly) for d in domains]
    forbidden = set()
    for pair in graph['forbidden_pairs']:
        i, j = pair
        if type(i) is not int or type(j) is not int or not 0 <= i < j < len(domains):
            raise ValueError('Invalid pair index')
        if (i,j) in forbidden or domains[i].cell == domains[j].cell:
            raise ValueError('Duplicate or same-cell pair')
        bound = sum(max(abs(boxes[i][k][0]-boxes[j][k][1]),
                        abs(boxes[i][k][1]-boxes[j][k][0]))**2 for k in (0,1))
        if bound >= 1 and possible_pair(domains[i], domains[j]):
            raise ValueError(f'Unproved forbidden pair {pair}')
        forbidden.add((i,j))
        if time.monotonic()-start > a.seconds:
            raise TimeoutError('Pair replay time limit; no receipt emitted')
    rows = []
    for row in search['rows']:
        if row['result']['status'] != 'EXCLUDED':
            continue
        mask = row['mask']
        if len(mask) != 11 or len(set(mask)) != 11 or any(type(c) is not int or not 0 <= c < 16 for c in mask):
            raise ValueError('Invalid eleven-cell mask')
        result, nodes = independent_exhaustion(mask, domains, forbidden, a.nodes)
        if result != 'EXCLUDED':
            raise ValueError(f'Exclusion not reproduced: {mask}, {result}')
        rows.append({'mask': mask, 'nodes': nodes})
        if time.monotonic()-start > a.seconds:
            raise TimeoutError('Mask replay time limit; no receipt emitted')
    out = {'status': 'PASS_EXACT_SELECTED_MASK_EXCLUSIONS',
           'global_optimality_proved': False, 'new_lower_bound_proved': False,
           'scope': 'Only the explicitly listed eleven-cell occupancy masks are excluded.',
           'side_upper': str(side), 'forbidden_pairs_recomputed': len(forbidden),
           'excluded_masks': rows, 'excluded_count': len(rows), 'seconds': time.monotonic()-start,
           'cover_sha256': hashlib.sha256(cb).hexdigest(), 'graph_sha256': hashlib.sha256(gb).hexdigest(),
           'search_sha256': hashlib.sha256(sb).hexdigest(),
           'kernel_sha256': hashlib.sha256(Path(__file__).with_name('kernel.py').read_bytes()).hexdigest(),
           'replay_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    a.output.write_text(json.dumps(out, indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k != 'excluded_masks'}))


if __name__ == '__main__':
    main()
