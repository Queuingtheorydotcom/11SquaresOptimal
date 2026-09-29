"""Show the checked longitudinal cut removes an abstract pair-clique state."""
import json,hashlib
from pathlib import Path
from search_graph import load_graph
from probe import clique_search


def main():
    root=Path(__file__).parent
    cover=json.loads((root.parent/'global_capture/center-cover-symmetric-exact.json').read_text())
    gb=(root/'symmetric-pilot-3x4.json').read_bytes();graph=json.loads(gb)
    domains,bycell,adjacency=load_graph(graph,cover)
    ablation=json.loads((root/'chain-neighbor-ablation.json').read_text())
    mask=ablation['reduced_obstruction_occupancy']
    active={c:set(bycell[c]) for c in mask};active[1]={54}
    result=clique_search(mask,active,adjacency,100000)
    if result['status']!='ABSTRACT_ASSIGNMENT':
        raise ValueError('No abstract pair-clique witness found')
    chosen=[state for cell,state in result['assignment']]
    if any(b not in adjacency[a] for a in chosen for b in chosen if a!=b):
        raise ValueError('Invalid pair-clique assignment')
    out={'status':'PASS_ABSTRACT_PAIR_CLIQUE_REMOVED_BY_JOINT_CHAIN',
         'global_optimality_proved':False,'physical_packing_claimed':False,
         'conditional_occupied_cells':mask,'pinned_state':54,'pinned_cell':1,
         'pinned_tile':domains[54].tile,'pinned_half_angle':[str(x) for x in domains[54].angle],
         'abstract_assignment':result['assignment'],'search_nodes':result['nodes'],
         'graph_sha256':hashlib.sha256(gb).hexdigest(),
         'chain_replay_reference':'chain-neighbor-ablation-replay.json'}
    (root/'joint-consistency-gap.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out))


if __name__=='__main__':main()
