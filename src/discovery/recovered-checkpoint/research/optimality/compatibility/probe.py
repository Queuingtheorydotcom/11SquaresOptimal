"""Bounded necessary-domain compatibility pilot; never a global optimality verdict."""
import argparse
import hashlib
import json
import time
import math
from collections import defaultdict, deque
from itertools import combinations
from pathlib import Path
from kernel import physical_cells, subdivide_domains, possible_pair, bbox


def heuristic_maybe_conflict(first, second):
    """Float screening only skips exact exclusions; it never excludes anything."""
    firstpoly, (a0, a1) = first
    secondpoly, (b0, b1) = second
    delta = [(q[0]-p[0], q[1]-p[1]) for p in firstpoly for q in secondpoly]
    maxdist = max(x*x+y*y for x, y in delta)
    if maxdist >= 2-1e-12:
        return False
    if maxdist < 1+1e-12:
        return True
    lo, hi = b0-a1, b1-a0
    abslo, abshi = (0 if lo <= 0 <= hi else min(abs(lo), abs(hi))), max(abs(lo), abs(hi))
    threshold = (1+min(math.cos(t)+math.sin(t) for t in (abslo, abshi)))/2
    for left, right in ((a0, a1), (b0, b1)):
        for perp in (False, True):
            for x, y in delta:
                a, b = (y, -x) if perp else (x, y)
                for aa, bb in ((a, b), (-a, -b)):
                    bound = max(aa*math.cos(t)+bb*math.sin(t) for t in (left, right))
                    if -aa*math.sin(left)+bb*math.cos(left) > 0 and -aa*math.sin(right)+bb*math.cos(right) < 0:
                        bound = max(bound, math.hypot(aa, bb))
                    if bound >= threshold-1e-10:
                        return False
    return True


def arc_consistency(mask, by_cell, adjacency):
    active = {c: set(by_cell[c]) for c in mask}
    queue = deque((i, j) for i in mask for j in mask if i != j)
    deletions = []
    while queue:
        i, j = queue.popleft()
        removed = [v for v in active[i] if not (adjacency[v] & active[j])]
        if not removed:
            continue
        deletions.append({'cell': i, 'against': j, 'removed': sorted(removed),
                          'remaining_against': sorted(active[j])})
        active[i].difference_update(removed)
        if not active[i]:
            return True, active, deletions
        queue.extend((k, i) for k in mask if k != i and k != j)
    return False, active, deletions


def clique_search(mask, active, adjacency, max_nodes, bitadj=None):
    """Complete finite CSP search if it returns EXCLUDED; compatible witness is abstract."""
    if bitadj is None:
        bitadj = [sum(1 << v for v in neighbors) for neighbors in adjacency]
    nodes = 0
    def visit(sets, assignment):
        nonlocal nodes
        nodes += 1
        if nodes > max_nodes:
            return 'NODE_LIMIT', None
        if not sets:
            return 'ABSTRACT_ASSIGNMENT', assignment
        c = min(sets, key=lambda x: sets[x].bit_count())
        choices = sets[c]
        if not choices:
            return 'EXCLUDED', None
        rest = {k:v for k,v in sets.items() if k != c}
        while choices:
            bit = choices & -choices; choices ^= bit
            v = bit.bit_length()-1
            nextsets = {k:s & bitadj[v] for k,s in rest.items()}
            if any(not s for s in nextsets.values()):
                continue
            result, witness = visit(nextsets, assignment+[(c, v)])
            if result != 'EXCLUDED':
                return result, witness
        return 'EXCLUDED', None
    status, assignment = visit({c:sum(1 << v for v in active[c]) for c in mask}, [])
    return {'status': status, 'nodes': nodes, 'assignment': assignment}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cover', type=Path, default=Path(__file__).parents[1]/'global_capture/center-cover-exact.json')
    parser.add_argument('--spatial', type=int, default=1)
    parser.add_argument('--angular', type=int, default=4)
    parser.add_argument('--mask-count', type=int, default=32)
    parser.add_argument('--seconds', type=int, default=120)
    parser.add_argument('--search-nodes', type=int, default=0)
    parser.add_argument('--resume', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.mask_count < 1 or args.mask_count > 4368 or args.seconds < 1:
        parser.error('positive bounded masks/seconds required')
    start = time.monotonic()
    kernel_sha = hashlib.sha256(Path(__file__).with_name('kernel.py').read_bytes()).hexdigest()
    cover_bytes = args.cover.read_bytes()
    cover = json.loads(cover_bytes)
    side, cells = physical_cells(cover)
    domains = subdivide_domains(cells, side, args.spatial, args.angular)
    approximate = [(tuple((float(x), float(y)) for x,y in d.poly),
                    tuple(2*math.atan(float(t)) for t in d.angle)) for d in domains]
    boxes = [bbox(d.poly) for d in domains]
    by_cell = defaultdict(list)
    for k, d in enumerate(domains):
        by_cell[d.cell].append(k)
    adjacency = [set(j for j,dj in enumerate(domains) if di.cell != dj.cell) for di in domains]
    forbidden = []
    resume_pairs = 0
    if args.resume:
        old = json.loads(args.resume.read_text())
        if (old['kernel_sha256'] != kernel_sha or old['cover_sha256'] != hashlib.sha256(cover_bytes).hexdigest()
            or old['spatial_subdivisions'] != args.spatial or old['angular_subdivisions'] != args.angular
            or old['domain_count'] != len(domains)):
            raise ValueError('Resume context differs')
        forbidden = old['forbidden_pairs'][:]
        if len(set(map(tuple, forbidden))) != len(forbidden):
            raise ValueError('Duplicate resume pair')
        for a,b in forbidden:
            if type(a) is not int or type(b) is not int or not 0 <= a < b < len(domains) or domains[a].cell == domains[b].cell:
                raise ValueError('Invalid resume pair')
            adjacency[a].remove(b); adjacency[b].remove(a)
        resume_pairs = old['pair_checks']
    pair_count = 0
    graph_complete = True
    for a, b in combinations(range(len(domains)), 2):
        if domains[a].cell == domains[b].cell:
            continue
        if pair_count < resume_pairs:
            pair_count += 1
            continue
        if time.monotonic()-start > args.seconds:
            graph_complete = False
            break
        pair_count += 1
        maybe = True
        if heuristic_maybe_conflict(approximate[a], approximate[b]):
            bound_sq = sum(max(abs(boxes[a][k][0]-boxes[b][k][1]),
                               abs(boxes[a][k][1]-boxes[b][k][0]))**2 for k in (0,1))
            maybe = bound_sq >= 1 and possible_pair(domains[a], domains[b])
        if maybe:
            pass
        else:
            forbidden.append([a, b])
            adjacency[a].remove(b); adjacency[b].remove(a)
    graph_seconds = time.monotonic()-start
    masks = cover.get('canonical_eleven_cell_subsets', list(combinations(range(16), 11)))[:args.mask_count]
    excluded = []; survivors = []
    if graph_complete:
        bitadj = [sum(1 << v for v in neighbors) for neighbors in adjacency]
        for mask in masks:
            if time.monotonic()-start > args.seconds:
                break
            empty, active, deletions = arc_consistency(mask, by_cell, adjacency)
            row = {'mask': list(mask), 'deletions': deletions,
                   'survivor_counts': {str(c): len(v) for c, v in active.items()}}
            if not empty and args.search_nodes:
                row['finite_search'] = clique_search(mask, active, adjacency, args.search_nodes, bitadj)
                empty = row['finite_search']['status'] == 'EXCLUDED'
            (excluded if empty else survivors).append(row)
    status = 'PARTIAL_BOUNDED_COMPATIBILITY' if graph_complete else 'INCOMPLETE_PAIR_GRAPH'
    out = {'status': status, 'global_optimality_proved': False,
           'side_upper': str(side), 'cover_sha256': hashlib.sha256(cover_bytes).hexdigest(),
           'kernel_sha256': kernel_sha,
           'spatial_subdivisions': args.spatial, 'angular_subdivisions': args.angular,
           'domain_count': len(domains), 'domains_per_cell': {str(c): len(v) for c, v in by_cell.items()},
           'graph_complete': graph_complete, 'pair_checks': pair_count, 'forbidden_pairs': forbidden,
           'resumed_pair_checks': resume_pairs,
           'graph_seconds': graph_seconds, 'total_seconds': time.monotonic()-start,
           'masks_checked': len(excluded)+len(survivors), 'excluded_masks': excluded,
           'surviving_masks': survivors}
    args.output.write_text(json.dumps(out, indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ('excluded_masks', 'surviving_masks', 'forbidden_pairs')}))
    print(json.dumps({'excluded': len(excluded), 'surviving': len(survivors), 'forbidden_pairs': len(forbidden)}))


if __name__ == '__main__':
    main()
