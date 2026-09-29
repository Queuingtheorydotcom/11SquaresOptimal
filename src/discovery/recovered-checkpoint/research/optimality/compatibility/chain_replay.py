"""Exact checker of explicit longitudinal bound/deletion traces.

Recomputes relevant forbidden pairs and checks each inference, without calling
the producer's contraction loop. A nonempty result is only a domain refinement.
"""
import argparse
import hashlib
import json
import sys
import time
from fractions import Fraction as F
from pathlib import Path
from kernel import physical_cells, subdivide_domains, bbox, possible_pair
from chain import prove_orders, gap_lower


def verify_trace(row, domains, forbidden, orders):
    mask = row['mask']
    if not 1 <= len(mask) <= 16 or len(set(mask)) != len(mask) or any(type(c) is not int or not 0 <= c < 16 for c in mask):
        raise ValueError('Invalid occupancy mask')
    active = {c:set(i for i,d in enumerate(domains) if d.cell == c) for c in mask}
    limits = {i:[v for pair in bbox(domains[i].poly) for v in pair] for values in active.values() for i in values}
    ordered = {(r['left'],r['right'],r['axis']) for r in orders}
    deleted = []
    for event in row['result']['trace']:
        state,cell,neighbor,axis = event['state'],event['cell'],event['against'],event['axis']
        if state not in active[cell] or neighbor not in active or axis not in (0,1):
            raise ValueError('Invalid active-state event')
        kind = event['kind']
        predecessor = kind in ('lower_bound','no_predecessor')
        left,right = (neighbor,cell) if predecessor else (cell,neighbor)
        if (left,right,axis) not in ordered:
            raise ValueError('Unproved ordered cell pair')
        along,trans = 2*axis,2*(1-axis)
        candidates = []
        for other in active[neighbor]:
            if (min(state,other),max(state,other)) in forbidden:
                continue
            a,b = (other,state) if predecessor else (state,other)
            aa,bb = limits[a],limits[b]
            transverse = max(abs(aa[trans]-bb[trans+1]),abs(aa[trans+1]-bb[trans]))
            gap = gap_lower(domains[a].angle,domains[b].angle,transverse)
            if aa[along]+gap <= bb[along+1]:
                candidates.append(aa[along]+gap if predecessor else bb[along+1]-gap)
        if kind in ('no_predecessor','no_successor'):
            if candidates:
                raise ValueError('Deleted state still has longitudinal support')
            if [F(v) for v in event['bounds']] != limits[state]:
                raise ValueError('Deletion bound snapshot differs')
            active[cell].remove(state); deleted.append({'state':state,'cell':cell,'against':neighbor,'axis':axis})
        elif kind in ('lower_bound','upper_bound'):
            index = along if predecessor else along+1
            old,new = F(event['old']),F(event['new'])
            if old != limits[state][index] or not candidates:
                raise ValueError('Invalid bound event context')
            necessary = min(candidates) if predecessor else max(candidates)
            if predecessor:
                if not old < new <= necessary:
                    raise ValueError('Lower bound is not justified')
            elif not necessary <= new < old:
                raise ValueError('Upper bound is not justified')
            limits[state][index] = new
        else:
            raise ValueError('Unknown inference kind')
    counts = {str(c):len(v) for c,v in active.items()}
    if counts != row['result']['survivors']:
        raise ValueError('Final survivor count differs')
    excluded = any(not values for values in active.values())
    if (row['result']['status'] == 'EXCLUDED') != excluded:
        raise ValueError('Exclusion verdict differs')
    return {'index':row.get('index'),'mask':mask,'excluded':excluded,'verified_inferences':len(row['result']['trace']),
            'deleted_states':deleted,'survivors':counts}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cover',type=Path,required=True)
    p.add_argument('--graph',type=Path,required=True)
    p.add_argument('--trace',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a = p.parse_args();start = time.monotonic()
    cb,gb,tb = a.cover.read_bytes(),a.graph.read_bytes(),a.trace.read_bytes()
    cover,graph,trace = map(json.loads,(cb,gb,tb))
    if trace['cover_sha256'] != hashlib.sha256(cb).hexdigest() or trace['graph_sha256'] != hashlib.sha256(gb).hexdigest():
        raise ValueError('Input digests differ')
    sys.path.insert(0,str(Path(__file__).parents[1]/'global_capture'))
    from verify_center_cover import verify
    checked = verify([tuple(F(v) for v in c['center']) for c in cover['cells']],F(cover['unit_square_cover_radius_bound']))
    if checked['cells'] != cover['cells'] or checked['side_upper'] != cover['side_upper']:
        raise ValueError('Cover regeneration differs')
    side,cells = physical_cells(cover)
    domains = subdivide_domains(cells,side,graph['spatial_subdivisions'],graph['angular_subdivisions'])
    orders = prove_orders(cells);boxes = [bbox(d.poly) for d in domains]
    relevant = {tuple(sorted((i,j))) for r in trace['rows'] for i in r['mask'] for j in r['mask'] if i != j}
    forbidden = set()
    for i,j in graph['forbidden_pairs']:
        if (domains[i].cell,domains[j].cell) not in relevant:
            continue
        if not 0 <= i < j < len(domains) or (i,j) in forbidden:
            raise ValueError('Invalid forbidden pair')
        bound = sum(max(abs(boxes[i][k][0]-boxes[j][k][1]),abs(boxes[i][k][1]-boxes[j][k][0]))**2 for k in (0,1))
        if bound >= 1 and possible_pair(domains[i],domains[j]):
            raise ValueError('Forbidden pair not proved')
        forbidden.add((i,j))
    rows = [verify_trace(row,domains,forbidden,orders) for row in trace['rows']]
    out = {'status':'PASS_EXACT_CHAIN_REFINEMENTS','global_optimality_proved':False,'new_lower_bound_proved':False,
           'side_upper':str(side),'seconds':time.monotonic()-start,'recomputed_forbidden_pairs':len(forbidden),
           'rows':rows,'trace_sha256':hashlib.sha256(tb).hexdigest(),
           'chain_sha256':hashlib.sha256(Path(__file__).with_name('chain.py').read_bytes()).hexdigest(),
           'replay_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    a.output.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='rows'}))
    print(json.dumps({'verified_inferences':sum(r['verified_inferences'] for r in rows),
                      'deleted_states':sum(len(r['deleted_states']) for r in rows),
                      'excluded_masks':sum(r['excluded'] for r in rows)}))


if __name__ == '__main__':
    main()
