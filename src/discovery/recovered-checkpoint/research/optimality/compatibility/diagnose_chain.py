"""Bounded ablation of the concrete cell-1 longitudinal loss in mask2045."""
import json,time,hashlib
from pathlib import Path
from kernel import physical_cells
from search_graph import load_graph
from chain import contract,prove_orders


def main():
    root = Path(__file__).parent
    cb = (root.parent/'global_capture/center-cover-symmetric-exact.json').read_bytes()
    gb = (root/'symmetric-pilot-3x4.json').read_bytes()
    cover,graph = json.loads(cb),json.loads(gb)
    domains,bycell,adjacency = load_graph(graph,cover)
    _,cells = physical_cells(cover);orders=prove_orders(cells)
    subsets = [[1,5],[1,5,9],[1,5,13],[1,5,9,13],[1,4,5,6],
               [1,2,5],[1,3,5],[1,2,3,5],[1,2,3,4,5,6]]
    rows=[]
    for mask in subsets:
        start=time.monotonic()
        result=contract(mask,domains,bycell,adjacency,orders,32,start+10,True)
        eliminated=[e for e in result['trace'] if e['kind'].startswith('no_')]
        rows.append({'mask':mask,'seconds':time.monotonic()-start,'status':result['status'],
                     'updates':result['updates'],'deleted_states':[e['state'] for e in eliminated],
                     'state54_eliminated':any(e['state']==54 for e in eliminated),
                     'result':result})
    reduced=[1,2,3,4,5,6,8,9,11,13,14]
    reductions=[]
    for c in reduced[:]:
        if c in (1,5):
            continue
        trial=[k for k in reduced if k!=c]
        start=time.monotonic();result=contract(trial,domains,bycell,adjacency,orders,32,start+10,True)
        lost=any(e['state']==54 and e['kind'].startswith('no_') for e in result['trace'])
        reductions.append({'removed_cell':c,'state54_eliminated':lost,'seconds':time.monotonic()-start})
        if lost:
            reduced=trial
    start=time.monotonic();result=contract(reduced,domains,bycell,adjacency,orders,32,start+10,True)
    rows.append({'mask':reduced,'seconds':time.monotonic()-start,'status':result['status'],
                 'updates':result['updates'],'deleted_states':[e['state'] for e in result['trace'] if e['kind'].startswith('no_')],
                 'state54_eliminated':any(e['state']==54 and e['kind'].startswith('no_') for e in result['trace']),
                 'result':result})
    out={'status':'BOUNDED_CHAIN_ABLATION','global_optimality_proved':False,
         'graph_sha256':hashlib.sha256(gb).hexdigest(),'cover_sha256':hashlib.sha256(cb).hexdigest(),'rows':rows,
         'greedy_reductions':reductions,'reduced_obstruction_occupancy':reduced}
    (root/'chain-neighbor-ablation.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps([{k:v for k,v in r.items() if k!='result'} for r in rows]))


if __name__=='__main__':main()
