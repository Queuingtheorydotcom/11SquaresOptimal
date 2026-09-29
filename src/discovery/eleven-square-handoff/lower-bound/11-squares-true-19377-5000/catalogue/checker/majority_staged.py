"""Staged exact true-majority row verification for checkpointed full replay.

1. Fast integer inner staircases.
2. Local exact true-polygon patches over deficient equal-charge boxes.
3. Only if a patch node limit is reached, construct conditional staircases for
   features meeting those boxes and repeat the scan/patch proof.

The certified logical charge is unchanged between stages. A true deficient
pose stops the row immediately; an exhausted resource limit is an explicit
FAIL/incomplete receipt. No incomplete row can be accepted as a proof.
"""
from fractions import Fraction as F
import time
from integer_sweep import accumulate,need
from majority_mixed import validate,geometry
from majority_precompute import prepare_majority
from majority_low_cells import extract_low_cells
from majority_patches import PatchVerifier

SUBDIVISIONS=4
FIRST_PATCH_NODE_LIMIT=5000
FINAL_PATCH_NODE_LIMIT=100000
_prepared_input=None
_prepared_value=None


def prepared_for(data):
    global _prepared_input,_prepared_value
    if _prepared_input is not data:
        _prepared_value=prepare_majority(data);_prepared_input=data
    return _prepared_value


def conditional_candidates(data,meta,boxes):
    """Only features whose axis bounds meet a low box can improve its charge."""
    candidates=set();half=meta['half']
    for i,(group,k,w) in enumerate(data[-1]):
        middle=len(group)//2
        um=sorted(meta['uv'][j][0] for j in group)[middle]
        vm=sorted(meta['uv'][j][1] for j in group)[middle]
        left,right,bottom,top=um-half,um+half,vm-half,vm+half
        if any(left<x1 and x0<right and bottom<y1 and y0<top for x0,x1,y0,y1,z in boxes):
            candidates.add(i)
    return candidates


def patch_boxes(data,meta,boxes,required_units,prepared,node_limit):
    verifier=PatchVerifier(data,meta,required_units,max_nodes=node_limit,prepared=prepared)
    for index,(x0,x1,y0,y1,z) in enumerate(sorted(boxes,key=lambda box:box[-1])):
        answer=verifier.verify_cell((x0,x1,y0,y1),z)
        if not answer['status'].startswith('PASS'):
            if 'point' in answer:
                u,v=answer['point'];C,S,R,scale=(meta[k] for k in ('C','S','R','scale'))
                x=F(191,100)+(C*u-S*v)/(R*R*scale)
                y=F(191,100)+(S*u+C*v)/(R*R*scale)
                answer['world_center']=[str(x),str(y)]
                answer['scope']='Core-row witness; full-parent containment and charge require a separate check'
                answer['point']=list(map(str,answer['point']))
            return dict(status=answer['status'],box_index=index,answer=answer,statistics=verifier.stats)
    return dict(status='PASS',statistics=verifier.stats)


def verify_row(data,job,required_units):
    need(type(required_units) is int and required_units>=0,'Invalid required charge')
    start=time.monotonic();prepared=prepared_for(data);history=[];conditional=None
    for phase in range(2):
        phase_start=time.monotonic()
        arrays,meta=geometry(*data,*job,meta=True,subdivisions=SUBDIVISIONS,
                             domain_conditional=phase>0,prepared=prepared,
                             conditional_features=conditional)
        minimum,cells,winner=accumulate(*arrays)
        minimum,cells=int(minimum),int(cells);slabs=int(sum(x>=0 for x in arrays[-2]))
        stage='integer_staircase' if phase==0 else 'selective_conditional_staircase'
        entry=dict(stage=stage,proxy_minimum_units=minimum,rectangles=len(meta['rect']),
                   majority_features=len(data[-1]),conditional_features=len(conditional or ()),
                   geometry_sweep_seconds=time.monotonic()-phase_start)
        history.append(entry)
        if minimum>=required_units:
            return dict(status='PASS',minimum_units=minimum,cells=cells,slabs=slabs,
                        stage=stage,history=history,seconds=time.monotonic()-start,
                        minimum_interpretation='Certified lower bound on true logical charge')
        if not data[-1]:
            return dict(status='FAIL',minimum_units=minimum,cells=cells,slabs=slabs,
                        reason='Rectangle bound insufficient and no majority features available for patches',
                        stage=stage,history=history,seconds=time.monotonic()-start)
        low=extract_low_cells(arrays,meta,required_units);boxes=low.merged_boxes()
        entry['low_cells']=low.stats;entry['low_boxes']=len(boxes)
        patched=patch_boxes(data,meta,boxes,required_units,prepared,
                            FIRST_PATCH_NODE_LIMIT if phase==0 else FINAL_PATCH_NODE_LIMIT)
        entry['patches']=patched
        if patched['status']=='PASS':
            return dict(status='PASS',minimum_units=required_units,cells=cells,slabs=slabs,
                        stage=stage+'_true_polygon_patches',history=history,
                        seconds=time.monotonic()-start,
                        minimum_interpretation='Certified lower bound; not an assertion of the exact minimum')
        if patched['status']=='COUNTEREXAMPLE':
            return dict(status='FAIL',minimum_units=minimum,cells=cells,slabs=slabs,
                        reason='Exactly checked true-charge-deficient core pose',stage=stage,
                        history=history,seconds=time.monotonic()-start)
        need(patched['status']=='INCOMPLETE_NODE_LIMIT','Unknown patch result')
        if phase==0:conditional=conditional_candidates(data,meta,boxes)
    return dict(status='FAIL',minimum_units=minimum,cells=cells,slabs=slabs,
                reason='INCOMPLETE: exact patch node limit exhausted; no true deficit asserted',
                stage=stage,history=history,seconds=time.monotonic()-start)
