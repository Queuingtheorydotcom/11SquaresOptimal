"""Bounded selected-mask longitudinal contraction; exclusions require replay."""
import argparse
import hashlib
import json
import time
from pathlib import Path
from kernel import physical_cells
from search_graph import load_graph
from chain import prove_orders, contract


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cover', type=Path, required=True)
    p.add_argument('--graph', type=Path, required=True)
    p.add_argument('--indices', default='0')
    p.add_argument('--seconds', type=int, default=60)
    p.add_argument('--rounds', type=int, default=24)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    cb,gb = a.cover.read_bytes(),a.graph.read_bytes()
    cover,graph = json.loads(cb),json.loads(gb)
    if graph['cover_sha256'] != hashlib.sha256(cb).hexdigest():
        raise ValueError('Cover context differs')
    domains,bycell,adjacency = load_graph(graph,cover)
    side,cells = physical_cells(cover)
    orders = prove_orders(cells)
    start = time.monotonic(); rows = []
    masks = cover['canonical_eleven_cell_subsets']
    for index in map(int,a.indices.split(',')):
        if not 0 <= index < len(masks):
            raise ValueError('Invalid mask index')
        result = contract(masks[index],domains,bycell,adjacency,orders,a.rounds,start+a.seconds,True)
        rows.append({'index':index,'mask':masks[index],'result':result})
        if time.monotonic()-start >= a.seconds:
            break
    out = {'status':'LONGITUDINAL_DISCOVERY_REPLAY_PENDING','global_optimality_proved':False,
           'side_upper':str(side),'graph_sha256':hashlib.sha256(gb).hexdigest(),
           'cover_sha256':hashlib.sha256(cb).hexdigest(),'ordered_cell_pairs':len(orders),
           'chain_sha256':hashlib.sha256(Path(__file__).with_name('chain.py').read_bytes()).hexdigest(),
           'seconds':time.monotonic()-start,'rows':rows}
    a.output.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({**out,'rows':[{'index':r['index'],'mask':r['mask'],'result':{k:v for k,v in r['result'].items() if k!='trace'}} for r in rows]}))


if __name__ == '__main__':
    main()
