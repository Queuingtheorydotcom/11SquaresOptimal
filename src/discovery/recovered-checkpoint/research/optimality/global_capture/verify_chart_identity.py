#!/usr/bin/env python3
"""Exact identity between the independently reconstructed and retained Trump chart.

The retained source formulas are re-expressed below, rather than importing the
external Python3.14 research environment. Its current bytes are hash-bound.
"""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'work/construction'))
from verify_trump import E,u,M,I,configuration

def need(ok,message):
    if not ok:raise ValueError(message)

def retained_formula_reconstruction(t):
    # Direct transcription of packing.py build_in, preserving its square order.
    cos_a=(1-t*t)/(1+t*t);sin_a=2*t/(1+t*t)
    side=(6*t+4)/(1+2*t-t*t)
    r1=1-(side-3)*cos_a
    u1=((1+r1)*cos_a-1)/sin_a
    v1=cos_a-sin_a
    v2=(side-1)/sin_a-r1-(3+u1)*(cos_a/sin_a)
    x0=1+2/cos_a-(side-2)*(sin_a/cos_a)
    def axis_aligned(x,y):
        return [(x,y),(x+1,y),(x+1,y+1),(x,y+1)]
    def tilted(ox,oy):
        corners=[]
        for dx,dy in ((0,0),(1,0),(1,1),(0,1)):
            px,py=ox+dx,oy+dy-r1
            corners.append((1+cos_a*px-sin_a*py,1+sin_a*px+cos_a*py))
        return corners
    squares=[axis_aligned(E(0),E(0)),axis_aligned(side-1,E(0)),axis_aligned(x0,side-1),axis_aligned(E(0),side-1),axis_aligned(E(1),side-1),axis_aligned(E(0),side-2),tilted(E(0),E(0)),tilted(u1,-E(1)),tilted(E(1),v1),tilted(u1+1,v1-1),tilted(u1+2,-v2)]
    return squares,side

def main():
    need(M.count_roots(*I)==1 and M.eval(I[0])<0<M.eval(I[1]),'defining root isolation')
    squares,side,_=configuration(E(u))
    retained,retained_side=retained_formula_reconstruction(E(u))
    need((side-retained_side).iszero(),'side identity')
    for i in range(11):
        for k in range(4):
            for d in range(2):
                need((squares[i][k][d]-retained[i][k][d]).iszero(),'labelled vertex coordinate identity')
        for d in range(2):
            old=sum(q[d] for q in retained[i])/4;new=sum(q[d] for q in squares[i])/4
            need((old-new).iszero(),'labelled center identity')
        edge=[squares[i][1][d]-squares[i][0][d] for d in range(2)]
        expected=(E(1),E(0)) if i<6 else ((1-E(u)**2)/(1+E(u)**2),2*E(u)/(1+E(u)**2))
        need(all((a-b).iszero() for a,b in zip(edge,expected)),'orientation identity')
    sources=['work/construction/verify_trump.py','research/jlevy/packing/cases/trump11/packing.py','research/jlevy/packing/cases/trump11/tangent_cones.py','research/jlevy/packing/cases/trump11/isolation_radius.py','research/classical/trump-local-weighted-coordinate-radius.json']
    out={'status':'PASS_EXACT_LABELLED_TRUMP_CHART_IDENTITY','label_permutation':list(range(11)),'container_symmetry':'identity','corner_order_permutation':[0,1,2,3],'equal_vertex_coordinates':88,'equal_center_coordinates':22,'equal_oriented_edge_coordinates':22,'angles':'Labels0..5 have theta=0; labels6..10 have theta=2atan(t). Both source formulas use these same oriented firstedges.','chart':'Anchored [0,alpha]^2, coordinates(x_i,y_i,theta_i), angles in radians. Centering the container changes only the common origin and preserves displacement supnorm.','external_source_handling':'The small construction formulas were transcribed and checked against retained packing.py build_in. External project modules were not imported into the older runtime.','source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},'global_optimality_proved':False}
    Path(__file__).with_name('trump-chart-identity.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
