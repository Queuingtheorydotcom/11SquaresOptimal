"""Exact finite controls of polygon patches, including cancelling boundaries."""
from fractions import Fraction as F
from pathlib import Path
import json
from majority_patches import PatchVerifier,clip,clean,feature_status
from majority_geometry import median_strips,require

def build(groups,half,weights,rectangles,domain):
    uv=[];majority=[]
    for group,w in zip(groups,weights):
        indices=tuple(range(len(uv),len(uv)+len(group)));uv.extend(group)
        majority.append((indices,(len(group)+1)//2,w))
    data=(uv,[0]*len(uv),[],[],1,majority)
    meta=dict(uv=uv,half=half,poly=domain,feature_rectangles=rectangles)
    return data,meta

def exhaustive_faces(data,meta,domain):
    """Independent full arrangement of all true facets, irrespective of charge."""
    lines=[]
    for group,k,w in data[-1]:
        for a,b,lo,hi in median_strips([meta['uv'][i] for i in group],meta['half']):
            lines.extend([(a,b,hi),(-a,-b,-lo)])
    faces=[[tuple(map(F,p)) for p in domain]]
    for line in set(lines):
        a,b,rhs=line;new=[]
        for poly in faces:
            values=[a*x+b*y-rhs for x,y in poly]
            if min(values)<0<max(values):
                new.extend([clip(poly,line),clip(poly,(-a,-b,-rhs))])
            else:new.append(poly)
        faces=new
    oracle=PatchVerifier(data,meta,1)
    values=[oracle.charge(oracle.generic_point(poly)) for poly in faces]
    return min(values),len(faces)

def main():
    domain=[(-2,-2),(2,-2),(2,2),(-2,2)]
    groupsets=[
        [[(-1,-1)],[(-1,1)],[(1,-1)],[(1,1)]],
        [[(-2,-1),(0,-1),(-1,1)],[(0,-1),(2,-1),(1,1)],
         [(-1,0),(1,0),(0,2)]],
        [[(-2,0),(-1,-1),(0,0)],[(0,0),(1,1),(2,0)]],
        [[(-2,-1),(-1,-2),(0,-1),(0,1),(-1,0)],
         [(0,-1),(1,-2),(2,-1),(2,1),(1,0)]],
    ]
    cases=faces=counterexamples=proofs=0
    for groups in groupsets:
        for half in (1,2,3):
            weights=list(range(1,len(groups)+1));data,meta=build(groups,half,weights,[[] for _ in groups],domain)
            minimum,nfaces=exhaustive_faces(data,meta,domain);faces+=nfaces
            for cutoff in (1,max(1,minimum),minimum+1,sum(weights)+1):
                verifier=PatchVerifier(data,meta,cutoff)
                result=verifier.verify_cell((-2,2,-2,2),0)
                expected=minimum>=cutoff
                require(result['status'].startswith('PASS')==expected,'Patch differs from full arrangement')
                cases+=1;proofs+=int(expected);counterexamples+=int(not expected)
    # Two identical true regions, complementary proxies. Total proxy=1,
    # true total=2. Individual proxy changes cancel on the interior x=0 line.
    data,meta=build([[(0,0)],[(0,0)]],2,[1,1],
                    [[(-2,0,-2,2)],[(0,2,-2,2)]],domain)
    verifier=PatchVerifier(data,meta,2)
    result=verifier.verify_cell((-2,2,-2,2),1)
    require(result['status']=='PASS','Cancelled proxy boundary control failed')
    require(verifier.stats['splits']>=1,'Cancelled proxy boundary was not resolved')
    cases+=1;proofs+=1
    cancelled_splits=verifier.stats['splits']
    # This triangle has a singleton TRUE-majority center region at (1,5)
    # for half-side 7. The initial centroid lands exactly on its three slanted
    # facets, away from every site-capture axis. It must trigger a fresh generic
    # point, not abort the witness recheck after discarding a zero-area feature.
    domain2=[(0,4),(2,4),(2,6),(0,6)]
    data,meta=build([[(-16,-8),(16,0),(0,24)]],7,[1],[[]],domain2)
    verifier=PatchVerifier(data,meta,1)
    require(verifier.charge((F(1),F(5)))==1,'Degenerate true feature fixture is inactive')
    require(feature_status(domain2,verifier.features[0][1])[0]==0,'Feature is not generically inactive')
    result=verifier.verify_cell((0,2,4,6),0)
    require(result['status']=='COUNTEREXAMPLE' and result['true_charge_units']==0,'Degenerate facet retry failed')
    require(verifier.stats['generic_facet_retries']==1,'Degenerate point did not exercise retry')
    cases+=1;counterexamples+=1
    out=dict(status='PASS_EXACT_POLYGON_PATCH_CONTROLS',cases=cases,
             independent_full_arrangement_faces=faces,certified_cases=proofs,
             directly_checked_counterexamples=counterexamples,
             cancelled_boundary_splits=cancelled_splits,degenerate_facet_retry_controls=1)
    Path(__file__).with_name('patch-controls-result.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':main()
