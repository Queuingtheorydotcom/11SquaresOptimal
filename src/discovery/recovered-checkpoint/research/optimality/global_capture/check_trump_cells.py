#!/usr/bin/env python3
"""Exact assignment of all eight Trump images to the certified center cells."""
import sys,json,argparse
from pathlib import Path
from itertools import combinations
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'work/construction'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from verify_trump import E,u,configuration,M,I
from verify_center_cover import CENTERS,DEN,SIDE_UPPER,dot,norm2,require
from fractions import Fraction as F

def ef(q): return E(str(q))

def run(sites=None, concentric=False):
    require(M.count_roots(*I)==1 and M.eval(I[0])<0<M.eval(I[1]),'exact defining root isolation')
    squares,L,_=configuration(E(u))
    require((ef(SIDE_UPPER)-L).sign()>0,'Trump side must lie below cover endpoint')
    centers=[(sum(p[0] for p in sq)/4,sum(p[1] for p in sq)/4) for sq in squares]
    sites=sites or [tuple(F(v,DEN) for v in p) for p in CENTERS]
    radius=F(1,248)
    rows=[]
    selections=list(combinations(range(16),11))
    for swap in (False,True):
        for sx in (False,True):
            for sy in (False,True):
                image=[]
                for x,y in centers:
                    if swap:x,y=y,x
                    if sx:x=L-x
                    if sy:y=L-y
                    image.append((x,y))
                cells=[];contained=[];smallest=None
                for k,(x,y) in enumerate(image):
                    normal=((x-ef(F(1,2)))/ef(SIDE_UPPER-1),(y-ef(F(1,2)))/ef(SIDE_UPPER-1))
                    if concentric:normal=((x-L/2)/ef(SIDE_UPPER-1)+ef(F(1,2)),(y-L/2)/ef(SIDE_UPPER-1)+ef(F(1,2)))
                    dist=[sum((v-ef(q))**2 for v,q in zip(normal,p)) for p in sites]
                    i=min(range(16),key=lambda j:dist[j]);cells.append(i)
                    yes=True
                    for j in range(16):
                        if i==j:continue
                        a=tuple(2*(sites[j][d]-sites[i][d]) for d in range(2))
                        b=norm2(sites[j])-norm2(sites[i])
                        gap=ef(b)-sum(ef(a[d])*normal[d] for d in range(2))
                        require(gap.sign()>0,'Trump center on Voronoi boundary')
                        room=gap*ef(SIDE_UPPER-1)-ef(radius*sum(abs(v) for v in a))
                        if room.sign()<=0:yes=False
                    contained.append(yes)
                require(len(set(cells))==11,'two Trump squares assigned same certified cell')
                subset=tuple(sorted(cells))
                rows.append({'symmetry':{'swap':swap,'reflect_x':sx,'reflect_y':sy},'label_to_cell':cells,'selection':list(subset),'selection_index':selections.index(subset),'local_center_boxes_radius':str(radius),'nearest_site_inequalities_strict_throughout_local_center_boxes':contained})
    return {'status':'PASS_EXACT_TRUMP_16_CELL_ASSIGNMENTS','global_optimality_proved':False,'eight_D4_images':rows,'number_of_distinct_Trump_selections':len({tuple(r['selection']) for r in rows}),'all_local_center_boxes_have_unique_nearest_site':all(all(r['nearest_site_inequalities_strict_throughout_local_center_boxes']) for r in rows),'root_interval':[str(q) for q in E.root_interval],'exact_sign_refinements':E.refinements}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--symmetric',action='store_true')
    args=parser.parse_args()
    if args.symmetric:
        from verify_symmetric_cover import symmetric_sites
        out=run(symmetric_sites(),concentric=True)
        out['coordinate_convention']='Trump centers centered at alpha/2, then mapped concentrically to the fixed U_plus cover.'
        dest='trump-cell-symmetric-assignments.json'
    else:
        out=run();dest='trump-cell-assignments.json'
    out['local_box_scope']='Each radius1/248 center box satisfies its nearest-site inequalities strictly. A local center box can extend outside the global center domain. Every feasible center in the box is therefore in the stated clipped cell.'
    canonical=sorted({min(tuple(r['selection']),tuple(sorted(15-i for i in r['selection']))) for r in out['eight_D4_images']}) if args.symmetric else None
    if canonical is not None:
        out['canonical_capture_masks']=[list(v) for v in canonical]
        out['number_of_canonical_capture_masks']=len(canonical)
        out['canonical_masks_disjoint_from_all_Trump_local_neighborhoods']=2184-len(canonical)
    Path(__file__).with_name(dest).write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='eight_D4_images'},indent=2))
