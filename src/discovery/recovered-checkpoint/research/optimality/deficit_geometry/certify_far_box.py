"""Exact axis-aligned deficit box and four compatible near-endpoint parents.

This disproves a proposed *single-deficit localization* premise. It neither
constructs eleven squares nor disproves global optimality of Trump's packing.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,json,hashlib,itertools
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'research/stromquist'))
sys.path.insert(0,str(ROOT/'research/majority_patches'))
from fast_exact_parent import FastExactParentModel
from true_parent import ExactParentModel
OUT=Path(__file__).parent
SOURCE=ROOT/'research/true_catalogue/round6-cutround12-surplus-3.8754-full/proposal.json'

def minimum_abs_interval(a,b):
    return max(a,-b,F(0))

def upper_box(model,box):
    """Upper bound every column on the entire closed center rectangle, t=0."""
    D=model.D; B=model.A
    X=(2*D*(box[0][0]-model.L/2),2*D*(box[0][1]-model.L/2))
    Y=(2*D*(box[1][0]-model.L/2),2*D*(box[1][1]-model.L/2))
    possible=[]
    for px,py in model.points:
        possible.append(minimum_abs_interval(X[0]-px,X[1]-px)<=B*D and minimum_abs_interval(Y[0]-py,Y[1]-py)<=B*D)
    row=np.zeros(model.nvar,np.uint8)
    for pid,hit in zip(model.pids,possible):row[pid]+=hit
    for inds,gid,kind,k,mx,my,normals in model.groups:
        if kind!='majority_hull':
            hits=sum(possible[i] for i in inds);row[gid]+=hits//k if kind=='floor' else int(hits>=k)
            continue
        good=True
        for nx,ny,median in [(1,0,mx),(0,1,my)]+normals:
            xx=(nx*X[0],nx*X[1]); yy=(ny*Y[0],ny*Y[1])
            lo=min(xx)+min(yy)-median; hi=max(xx)+max(yy)-median
            if minimum_abs_interval(lo,hi)>B*D*(abs(nx)+abs(ny)):
                good=False;break
        row[gid]+=good
    return row

def main():
    c=json.loads(SOURCE.read_text()); L=F(c['L']); S=F('3.87708359'); P=L/S; B=L/F('3.877084')
    assert B<P
    exact=FastExactParentModel(c).at_side(B)
    box=[(P/2,P/2+F(1,100000)),(F(92038,100000),F(92041,100000))]
    upper=upper_box(exact,box); w=np.array(exact.weights,np.int64); charge=int(upper@w); gamma=c['minimum_units']
    assert charge<gamma,(charge,gamma)
    # Every center in the box supports a full near-endpoint parent, not just B core.
    assert all(P/2<=lo<=hi<=L-P/2 for lo,hi in box)
    center=tuple((lo+hi)/2 for lo,hi in box); core_row=exact.row(0,center)
    slowc=dict(c);slowc['A']=str(B); slow=ExactParentModel(slowc)
    assert np.array_equal(core_row,slow.row(F(0),center));assert np.all(core_row<=upper)
    for xy in itertools.product(*box):assert np.all(exact.row(0,xy)<=upper)
    # Exact conservative distance to every D4 image of every known center.
    # Centers are compared in unit-square coordinates with both containers centered.
    poses=json.loads((ROOT/'work/construction/trump-pose-intervals.json').read_text())
    assert poses['status']=='EXACT_RATIONAL_TRUMP_POSE_ENCLOSURES'
    alpha_lo,alpha_hi=map(F,poses['side_interval'])
    assert S<alpha_lo<=alpha_hi<F('3.877084')
    unit_box=[((lo-L/2)/P,(hi-L/2)/P) for lo,hi in box]
    distance_records=[]
    for pose in poses['poses']:
        cc=[tuple(map(F,z)) for z in pose['centered_center']]
        for swap in (0,1):
            for sx,sy in itertools.product((-1,1),repeat=2):
                vv=cc[::-1] if swap else cc
                ints=[(lo,hi) if sg==1 else (-hi,-lo) for sg,(lo,hi) in zip((sx,sy),vv)]
                gaps=[minimum_abs_interval(lo-b,hi-a) for (lo,hi),(a,b) in zip(unit_box,ints)]
                d=max(gaps); assert d>F(2,5)
                distance_records.append(dict(template=pose['index'],swap=swap,sx=sx,sy=sy,center_supnorm_lower_bound=str(d)))
    # Four reflected center rectangles are pairwise strictly compatible even at
    # their worst choices: same-side vertical gap or opposite-side horizontal gap.
    boxes=[]
    for sx,sy in itertools.product((-1,1),repeat=2):
        boxes.append([(lo,hi) if sg==1 else (L-hi,L-lo) for sg,(lo,hi) in zip((sx,sy),box)])
    separations=[]
    for i,j in itertools.combinations(range(4),2):
        candidates=[]
        for axis in range(2):
            alo,ahi=boxes[i][axis];blo,bhi=boxes[j][axis]
            candidates.append(max(blo-ahi,alo-bhi)-P)
        gap=max(candidates);assert gap>0
        separations.append(dict(pair=[i,j],axis=int(np.argmax(candidates)),minimum_parent_gap=str(gap)))
    reflected_charges=[]
    for b in boxes:
        u=upper_box(exact,b);q=int(u@w);assert q==charge
        reflected_charges.append(q)
    out=dict(status='EXACT_DEFICIT_BOX_AND_FOUR_COMPATIBLE_PARENTS',source=str(SOURCE.relative_to(ROOT)),source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),ambient_L=str(L),strict_core_B=str(B),parent_container_ratio=str(S),parent_side_P=str(P),orientation_half_angle_t='0',center_box=[[str(lo),str(hi)] for lo,hi in box],charge_upper_units=charge,threshold_units=gamma,deficit_lower_units=gamma-charge,midpoint_charge_units=int(core_row@w),minimum_center_distance_to_all_trump_D4_poses=str(min(F(r['center_supnorm_lower_bound']) for r in distance_records)),certified_distance_greater_than='2/5',distance_records=distance_records,four_reflected_boxes=[[[str(a),str(b)] for a,b in box] for box in boxes],four_reflected_upper_charges=reflected_charges,pairwise_parent_separations=separations,independent_exact_midpoint_capture_match=True,global_coverage=False,eleven_square_packing=False,global_optimality=False,scope='Every core in this two-dimensional t=0 domain is deficient and far from every Trump pose orbit. Four reflected whole-parent domains are mutually compatible. This refutes localizing every individual low-charge placement or allowing at most three far-deficit squares on pairwise geometry alone; completion to eleven is not asserted.')
    out['trump_interval_source_sha256']=hashlib.sha256((ROOT/'work/construction/trump-pose-intervals.json').read_bytes()).hexdigest()
    out['exact_core_and_parent_side_order_verified']=True
    (OUT/'exact-far-deficit-box.json').write_text(json.dumps(out,indent=2)+'\n');np.savez_compressed(OUT/'exact-far-deficit-box.npz',upper=upper,midpoint_row=core_row)
    print(json.dumps({k:v for k,v in out.items() if k not in ('distance_records','four_reflected_boxes','pairwise_parent_separations')}))
if __name__=='__main__':main()
