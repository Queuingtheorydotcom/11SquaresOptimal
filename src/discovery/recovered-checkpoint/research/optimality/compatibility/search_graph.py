"""Search a frozen necessary compatibility graph; results require geometric replay."""
import argparse
import hashlib
import json
import time
from pathlib import Path
from collections import defaultdict
from probe import arc_consistency, clique_search
from kernel import physical_cells, subdivide_domains


def load_graph(graph, cover):
    # Every untested pair remains compatible. A partial exclusion list is sound.
    side, cells = physical_cells(cover)
    domains = subdivide_domains(cells, side, graph['spatial_subdivisions'], graph['angular_subdivisions'])
    if len(domains) != graph['domain_count']:
        raise ValueError('Domain count mismatch')
    bycell = defaultdict(list)
    for k, d in enumerate(domains):
        bycell[d.cell].append(k)
    adjacency = [set(j for j in range(len(domains)) if domains[j].cell != d.cell) for d in domains]
    seen = set()
    for a, b in graph['forbidden_pairs']:
        if not (type(a) is int and type(b) is int and 0 <= a < b < len(domains)):
            raise ValueError('Invalid forbidden pair')
        if domains[a].cell == domains[b].cell or (a,b) in seen:
            raise ValueError('Duplicate or same-cell forbidden pair')
        seen.add((a,b)); adjacency[a].remove(b); adjacency[b].remove(a)
    return domains, bycell, adjacency


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--graph', type=Path, required=True)
    p.add_argument('--cover', type=Path, required=True)
    p.add_argument('--seconds', type=int, default=60)
    p.add_argument('--nodes', type=int, default=100000)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.seconds <= 0 or a.nodes <= 0:
        p.error('Positive search limits required')
    graphbytes, coverbytes = a.graph.read_bytes(), a.cover.read_bytes()
    graph, cover = json.loads(graphbytes), json.loads(coverbytes)
    if graph['cover_sha256'] != hashlib.sha256(coverbytes).hexdigest():
        raise ValueError('Cover digest mismatch')
    domains, bycell, adjacency = load_graph(graph, cover)
    bitadj = [sum(1 << v for v in neighbors) for neighbors in adjacency]
    start = time.monotonic()
    rows = []
    for index, mask in enumerate(cover.get('canonical_eleven_cell_subsets', cover['all_eleven_cell_subsets'])):
        if time.monotonic()-start > a.seconds:
            break
        empty, active, deletions = arc_consistency(mask, bycell, adjacency)
        result = {'status': 'EXCLUDED', 'nodes': 0, 'assignment': None} if empty else clique_search(mask, active, adjacency, a.nodes, bitadj)
        rows.append({'index': index, 'mask': mask, 'result': result,
                     'arc_deletions': sum(len(d['removed']) for d in deletions)})
    out = {'status': 'FINITE_RELAXATION_SEARCH_GEOMETRY_REPLAY_PENDING',
           'global_optimality_proved': False,
           'graph_sha256': hashlib.sha256(graphbytes).hexdigest(),
           'cover_sha256': hashlib.sha256(coverbytes).hexdigest(),
           'seconds': time.monotonic()-start, 'rows': rows,
           'counts': {s: sum(r['result']['status'] == s for r in rows)
                      for s in ('EXCLUDED', 'ABSTRACT_ASSIGNMENT', 'NODE_LIMIT')}}
    a.output.write_text(json.dumps(out, indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k != 'rows'}))


if __name__ == '__main__':
    main()
