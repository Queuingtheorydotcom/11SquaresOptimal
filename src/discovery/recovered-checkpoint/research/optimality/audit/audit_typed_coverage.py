#!/usr/bin/env python3
"""Independent targeted controls for the conditional-mask coverage controller.

Mock row outcomes below test orchestration only; they certify no geometric mask.
"""
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations
from math import lcm
from types import SimpleNamespace
import contextlib,copy,hashlib,importlib.util,io,json,sys,tempfile
import numpy as np

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
SOURCE=ROOT/'research/optimality/typed_coverage/verify.py'
SOURCE_SHA256=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('typed_coverage_under_audit',SOURCE)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
from majority_patches import true_charge
sys.path.insert(0,str(ROOT/'research/stromquist'))
from fast_exact_parent import FastExactParentModel

def require(ok,msg):
    if not ok:raise ValueError(msg)

def quadratic_nonnegative(a,b,c,left,right):
    vals=[a+b*x+c*x*x for x in (left,right)]
    if c>0 and left<-b/(2*c)<right:
        x=-b/(2*c);vals.append(a+b*x+c*x*x)
    return min(vals)>=0

def independent_clip(poly,axis,bound,greater):
    out=[]
    for p,q in zip(poly,poly[1:]+poly[:1]):
        a=p[axis]-bound;b=q[axis]-bound
        ia=a>=0 if greater else a<=0;ib=b>=0 if greater else b<=0
        if ia:out.append(p)
        if ia!=ib:
            r=F(a,a-b);out.append(tuple(p[k]+r*(q[k]-p[k]) for k in range(2)))
    return out

def area(poly):return abs(sum(p[0]*q[1]-p[1]*q[0] for p,q in zip(poly,poly[1:]+poly[:1]))) if poly else F(0)

def main():
    controls=[];angular_intervals=0
    for bins in (2,3,4,7,32):
        for i in range(bins):
            lo=F(i,bins);hi=F(i+1,bins);t,core,H=m.row_parameters(lo,hi);c,s=m.trig(t)
            maximum=(m.PARENT-F(1,10**12))/core
            # Exact polynomial proof over BOTH full subintervals, not samples.
            require(quadratic_nonnegative(maximum-c-s,2*(c-s),maximum+c+s,lo,t),'left angular factor bound')
            require(quadratic_nonnegative(maximum-c+s,-2*(c+s),maximum+c-s,t,hi),'right angular factor bound')
            width=(m.L-2*H)/m.PARENT
            require(quadratic_nonnegative(1-width,2,-1-width,lo,hi),'minimum parent width')
            require(core*maximum<m.PARENT,'strict containment lost')
            angular_intervals+=1
    controls.append('Exact full-interval quadratic proofs for all angular core/envelope bounds')
    for lo,hi in ((F(-1,10),F(0)),(F(1),F(11,10)),(F(1,2),F(1,2))):
        try:m.row_parameters(lo,hi)
        except ValueError:pass
        else:raise ValueError('invalid angular interval accepted')
    controls.append('Invalid and zero-width angular intervals rejected')

    # This sliver was missed by binary-float slopes if integer vertices were
    # accepted without Fraction coercion. The logical signed sum is -1 there.
    bottom=F(1,3)-F(1,10**18);top=F(1,3)
    meta={'rect':[(0,1,bottom,top)],'weights':[-1],
          'xe':[0,1,3],'ye':[0,bottom,top,1]}
    arrays,grid=m.restrict_arrays(meta,[(0,0),(3,1),(3,0)])
    require(int(m.accumulate(*arrays)[0])==-1,'integer-vertex signed sliver lost')
    controls.append('Signed 10^-18 sliver with integer polygon vertices retained exactly')

    rng=np.random.default_rng(55183);queried=0;intersections=0
    polygons=[[(F(-2),F(-1)),(F(2),F(-1)),(F(2),F(2)),(F(-2),F(2))],
              [(F(-2),F(0)),(F(0),F(-3,2)),(F(5,2),F(1,2)),(F(0),F(5,2))],
              [(F(-7,3),F(-2)),(F(7,3),F(-1,3)),(F(1,2),F(8,3))]]
    for poly in polygons:
        rect=[];weights=[]
        for _ in range(9):
            x=sorted(set(F(int(v),3) for v in rng.integers(-12,13,2)))
            y=sorted(set(F(int(v),3) for v in rng.integers(-12,13,2)))
            if len(x)==2 and len(y)==2:rect.append((*x,*y));weights.append(int(rng.integers(-8,9)))
        meta={'rect':rect,'weights':weights,'xe':sorted({F(-5),F(5)}|{v for r in rect for v in r[:2]}),
              'ye':sorted({F(-5),F(5)}|{v for r in rect for v in r[2:]})}
        arrays,grid=m.restrict_arrays(meta,poly);xe=grid['xe'];ye=grid['ye'];expected=[]
        for i,(xl,xh) in enumerate(zip(xe,xe[1:])):
            for j,(yl,yh) in enumerate(zip(ye,ye[1:])):
                inside=arrays[-2][i]>=0 and arrays[-2][i]<=j<arrays[-1][i]
                if inside:
                    x=(xl+xh)/2;y=(yl+yh)/2
                    expected.append(sum(w for r,w in zip(rect,weights) if r[0]<x<r[1] and r[2]<y<r[3]));queried+=1
                clipped=poly
                for axis,bound,greater in ((0,xl,True),(0,xh,False),(1,yl,True),(1,yh,False)):
                    clipped=independent_clip(clipped,axis,bound,greater)
                if area(clipped)>0:
                    require(inside,'positive-area polygon/grid intersection omitted');intersections+=1
        require(min(expected)==int(m.accumulate(*arrays)[0])==int(m.accumulate(*arrays,direct=True)[0]),'signed sweep mismatch')
    controls.append('Restricted signed sweep agrees with independent exact sums and covers every positive-area polygon/grid intersection')

    family=ROOT/'research/stromquist/candidate-true-enriched-round6.json'
    c=json.loads(family.read_text());data=m.expand_features(c)
    core=m.PARENT-F(1,10**8);model=FastExactParentModel(c).at_side(core)
    points,pw,subsets,coefficients,D,majority=data;LD=int(m.L*D)
    scale=lcm(2*D,(core/2).denominator);factor=scale//(2*D);pose_count=0
    for t in (F(0),F(1,7),F(2,5),F(1,2),F(3,4),F(1)):
        p,q=t.numerator,t.denominator;C=q*q-p*p;S=2*p*q;R=q*q+p*p
        uv=[(factor*(C*(2*x-LD)+S*(2*y-LD)),factor*(-S*(2*x-LD)+C*(2*y-LD))) for x,y in points]
        half=int(core*scale/2)*R
        for center in (model.clamp(t,(F(0),F(0))),(m.L/2,m.L/2)):
            point=(scale*(C*(center[0]-m.L/2)+S*(center[1]-m.L/2)),scale*(-S*(center[0]-m.L/2)+C*(center[1]-m.L/2)))
            logical=true_charge(data,uv,half,point)
            raw=sum(int(x)*int(w) for x,w in zip(model.row(t,center),model.weights))
            require(logical==raw,'expanded logical features differ from raw complete parent model');pose_count+=1
    controls.append('TRUE replacement / discrete expansion agrees with independent complete feature rows across the full quarter turn')

    # This is deliberately a controller test with mocked row outcomes; none of
    # its temporary PASS outputs is a geometric certificate or retained artifact.
    cover=json.loads(m.COVER.read_text());mask=cover['canonical_eleven_cell_subsets'][0]
    synthetic={'L':str(m.L),'coordinate_denominator':100,'weight_denominator':1,
               'point_orbits':[[191,191,1]],'charge_orbits':[],'budget_units':1}
    packet={'certificate':synthetic,'cover_sha256':m.sha(m.COVER),'parent_Uplus':str(m.U),
            'mask_index':0,'mask':mask,'threshold_units':[1]*16}
    original=m.verify_interval
    try:
        with tempfile.TemporaryDirectory(prefix='typed-control-') as temp:
            dest=Path(temp);p=dest/'packet.json';out=dest/'result.json'
            def execute(changes=None,cells=None,max_rows=100,mode='pass',all_cells=False):
                data=copy.deepcopy(packet)
                if changes:data.update(changes)
                p.write_text(json.dumps(data))
                def row(data,prepared,world,lo,hi,threshold,node_limit):
                    if mode=='refuted':return {'status':'REFUTED_BY_LEGAL_PARENT','interval':[lo,hi]}
                    good=(mode=='pass') or (mode=='first-half' and hi<=F(1,2))
                    return {'status':'PASS_CONTROL_STUB' if good else 'UNRESOLVED_CONTROL_STUB','interval':[lo,hi]}
                m.verify_interval=row
                args=SimpleNamespace(packet=p,output=out,cells=cells,bins=2,max_depth=0,max_rows=max_rows,seconds=30,patch_nodes=10,all_cells=all_cells)
                with contextlib.redirect_stdout(io.StringIO()):m.run(args)
                return json.loads(out.read_text())
            reps=sorted({min(i,15-i) for i in mask})
            require(execute()['status']=='PASS_EXACT_MASK_EXCLUSION','positive controller control fails')
            require(execute(cells=','.join(map(str,reps[:-1])))['status']=='INCOMPLETE_CONDITIONAL_COVERAGE','missing representative accepted')
            require(execute(max_rows=2*len(reps)-1)['status']=='INCOMPLETE_CONDITIONAL_COVERAGE','row-limited quarter turn accepted')
            require(execute(mode='first-half')['status']=='INCOMPLETE_CONDITIONAL_COVERAGE','half-quarter-only coverage accepted')
            require(execute(mode='none')['status']=='INCOMPLETE_CONDITIONAL_COVERAGE','unresolved coverage accepted')
            refuted=execute(mode='refuted')
            require(refuted['status']=='INCOMPLETE_CONDITIONAL_COVERAGE' and refuted['rows']==1 and refuted['excluded_mask_indices']==[],'legal-parent refutation did not stop without excluding a mask')
            for changes in ({'cover_sha256':'0'*64},{'mask_index':-1},{'threshold_units':[0]*16},{'parent_Uplus':'4'}):
                try:execute(changes)
                except ValueError:pass
                else:raise ValueError('invalid packet accepted')
            try:execute(cells=','.join(map(str,reps+[reps[0]])))
            except ValueError:pass
            else:raise ValueError('duplicate selected representative accepted')
            gamma=[0]*16;gamma[0]=1;gamma[1]=1;gamma[14]=2;gamma[15]=5
            one=execute({'threshold_units':gamma})
            require(one['representative_threshold_units']['0']==1,'unoccupied partner threshold was used in single-mask mode')
            all_result=execute({'threshold_units':gamma},all_cells=True)
            require(all_result['representative_threshold_units']['0']==5 and all_result['representative_threshold_units']['1']==2,'half-turn threshold dominance not enforced')
            expected=[i for i,J in enumerate(cover['canonical_eleven_cell_subsets']) if sum(gamma[j] for j in J)>1]
            require(all_result['excluded_mask_indices']==expected,'all-cells aggregate filtering differs')
            require(0<len(expected)<2184,'all-cells control did not exercise both outcomes')
            require(all_result['half_turn_transfer']=={str(i):min(i,15-i) for i in range(16)},'half-turn mapping differs')
            partial=execute({'threshold_units':gamma},cells='0,1,2,3,4,5,6',all_cells=True)
            require(partial['status']=='INCOMPLETE_CONDITIONAL_COVERAGE' and partial['excluded_mask_indices']==[],'seven-of-eight representative cover excluded masks')
    finally:m.verify_interval=original
    controls.append('Mocked orchestration controls: complete positive control; missing-cell, partial-angle, row-limit, unresolved, digest, index, count, side and duplicate-cell rejection')
    controls.append('Half-turn max-threshold transfer and all-sixteen-cell mask filtering; seven-of-eight representatives cannot exclude a mask')
    line=[(m.L/2-F(1,10),m.L/2),(m.L/2+F(1,10),m.L/2)]
    require(m.verify_interval(None,None,line,F(0),F(1,32),1,10)['status']=='UNRESOLVED_DEGENERATE_DOMAIN','line domain incorrectly accepted')
    point=[(m.L/2,m.L/2)]
    require(m.verify_interval(None,None,point,F(0),F(1,32),1,10)['status']=='UNRESOLVED_DEGENERATE_DOMAIN','point domain incorrectly accepted')
    controls.append('Closed point and segment center domains remain unresolved')
    # Exercise the actual new full-parent path, including conversion from the
    # core's integer lattice to the parent's potentially rational halfwidth.
    toy={'L':str(m.L),'coordinate_denominator':100,'weight_denominator':1,
         'point_orbits':[[191,191,0]],'budget_units':1,
         'charge_orbits':[{'kind':'majority_hull','sets':[[0]],'threshold':1,'weight':1}]}
    toy_data=m.expand_features(toy);toy_prepared=m.prepare_majority(toy_data)
    world=[(F(3,5),F(3,5)),(F(7,10),F(3,5)),(F(7,10),F(7,10)),(F(3,5),F(7,10))]
    refuted=m.verify_interval(toy_data,toy_prepared,world,F(0),F(1,32),1,100)
    require(refuted['status']=='REFUTED_BY_LEGAL_PARENT','exact deficient full parent was not recaptured')
    require(refuted['parent_witness']['charge_units']==0 and refuted['parent_witness']['side']==m.PARENT,'parent witness has wrong charge or side')
    controls.append('Actual TRUE-feature deficient-core patch produces a legally contained full-parent refutation with exact zero charge')
    require(m.sha(SOURCE)==SOURCE_SHA256,'controller changed during audit; rerun against the new snapshot')
    result={'status':'PASS_INDEPENDENT_TYPED_COVERAGE_CONTROLS','controller_sha256':SOURCE_SHA256,
            'cover_sha256':m.sha(m.COVER),'control_groups':controls,'angular_intervals_proved':angular_intervals,
            'direct_signed_query_cells':queried,'positive_area_grid_intersections_covered':intersections,
            'independent_feature_pose_checks':pose_count,'geometry_masks_excluded_by_this_audit':0,
            'scope':'Audits the controller and its premises. Mocked row controls do not prove any geometric mask exclusion.'}
    (HERE/'typed-coverage-independent-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
