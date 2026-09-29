"""Exact controls for optional pair/triple support_sets. No global-bound claim."""
from copy import deepcopy
from fractions import Fraction as F
from hashlib import sha256
from itertools import combinations, product
from pathlib import Path
import argparse, inspect, json, sys, tempfile

import exact_mixed as checker
from charge_geometry import convex_hull, hulls_intersect, clique_coefficients, validate_support_clique


def require(ok,message):
    if not ok: raise ValueError(message)


def reject(fn,*args):
    try: fn(*args)
    except (ValueError,TypeError,KeyError): return
    raise ValueError('Invalid support premise accepted')


def projection_intersection(first,second):
    """Independent separating-axis test, with segment directions for degeneracy."""
    directions=[(1,0),(0,1)]
    for group in (first,second):
        directions.extend((y-v,u-x) for (x,y),(u,v) in combinations(group,2) if (x,y)!=(u,v))
    directions.extend((u-x,v-y) for (x,y),(u,v) in combinations(first+second,2) if (x,y)!=(u,v))
    for nx,ny in directions:
        a=[nx*x+ny*y for x,y in first];b=[nx*x+ny*y for x,y in second]
        if max(a)<min(b) or max(b)<min(a):return False
    return True


def geometry_controls():
    grid=list(product(range(3),repeat=2))
    groups=[list(g) for n in (1,2,3) for g in combinations(grid,n)]
    hulls=[convex_hull(g) for g in groups];tests=0
    for i,first in enumerate(groups):
        for j,second in enumerate(groups):
            require(hulls_intersect(hulls[i],hulls[j]) == projection_intersection(first,second),
                    'Independent hull intersection disagreement')
            tests+=1
    reject(validate_support_clique,list(range(7)),[],4,
           [(0,0),(1,0),(0,1),(10,10),(11,10),(10,11),(11,11)],[(0,1,2)])
    reject(validate_support_clique,list(range(6)),[],None,
           [(0,0),(1,0),(0,1),(10,10),(11,10),(10,11)],[(0,1,2),(3,4,5)])
    return {'independent_hull_comparisons':tests,'invalid_hull_families_rejected':2}


def boolean_controls():
    models=patterns=0
    for n in range(2,8):
        triples=list(combinations(range(n),3));all_edges=list(combinations(range(n),2))
        if n<=5:
            families=[[support for j,support in enumerate(triples) if mask&(1<<j)]
                      for mask in range(1<<len(triples))]
        else:
            families=[[],triples]+[[s] for s in triples]+[list(s) for s in combinations(triples,2)]
        for family in families:
            for edges in ([],all_edges,[(0,i) for i in range(1,n)]):
                for threshold in (None,n//2+1):
                    values=list(clique_coefficients(n,edges,threshold,family))
                    for bit in range(n):
                        for mask in range(1<<n):
                            if mask&(1<<bit): values[mask]+=values[mask^(1<<bit)]
                    for mask,value in enumerate(values):
                        captured={i for i in range(n) if mask&(1<<i)}
                        direct=int((threshold is not None and len(captured)>=threshold) or
                                   any(set(s).issubset(captured) for s in edges+family))
                        require(value==direct,'Pair/triple Boolean inversion failed')
                    models+=1;patterns+=1<<n
    return {'support_models':models,'exhaustive_capture_patterns':patterns,
            'all_triple_families_through_group_size':5}


def fixture():
    """A realizable three-site trigger below the 4-of-7 threshold."""
    seed=[(100,100),(180,100),(140,140),(60,120),(220,120),(132,60),(148,180)]
    LD=382
    def orbit(p):
        x,y=p
        return sorted({(a,b) for u,v in ((x,y),(y,x)) for a in (u,LD-u) for b in (v,LD-v)})
    reps=sorted({orbit(p)[0] for p in seed});physical=[p for r in reps for p in orbit(r)]
    lookup={p:i for i,p in enumerate(physical)};group=[lookup[p] for p in seed]
    images=set()
    for swap,sx,sy in product((False,True),repeat=3):
        mapping={}
        for i in group:
            x,y=physical[i]
            if swap:x,y=y,x
            if sx:x=LD-x
            if sy:y=LD-y
            mapping[i]=lookup[x,y]
        images.add((tuple(sorted(mapping[i] for i in group)),tuple(sorted(mapping[i] for i in group[:3]))))
    images=sorted(images)
    atom={'kind':'convex_clique','threshold':4,'sets':[list(g) for g,s in images],
          'edge_sets':[[] for _ in images],'support_sets':[[list(s)] for g,s in images],'weight':1}
    cert={'L':'191/50','coordinate_denominator':100,'point_orbits':[[x,y,0] for x,y in reps],
          'charge_orbits':[atom],'budget_units':len(images)}
    return cert,group,physical


def fixture_controls():
    cert,group,physical=fixture();data=checker.expand(cert);atom=cert['charge_orbits'][0]
    center=(F(14,10),F(12,10));half=F(9,20)
    captured={i for i,(x,y) in enumerate(physical)
              if abs(F(x,100)-center[0])<=half and abs(F(y,100)-center[1])<=half}
    require(captured.intersection(group)==set(group[:3]),'Fixture must capture exactly its triple')
    logical=sum(int(len(captured.intersection(g))>=4 or any(set(s)<=captured for s in supports))
                for g,supports in zip(atom['sets'],atom['support_sets']))
    expanded=sum(w for support,w in zip(data[2],data[3]) if set(support)<=captured)
    old=deepcopy(cert);old['charge_orbits'][0].pop('support_sets');old_data=checker.expand(old)
    old_charge=sum(w for support,w in zip(old_data[2],old_data[3]) if set(support)<=captured)
    require(logical==expanded and logical>old_charge,'Actual core gains the new triple charge')
    arrays,meta=checker.geometry(*data,F(0),F(9,10),F(1),meta=True)
    z=(int((center[0]-F(191,100))*meta['scale']),int((center[1]-F(191,100))*meta['scale']))
    rectangle_charge=sum(w for (a,b,c,d),w in zip(meta['rect'],meta['weights']) if a<z[0]<b and c<z[1]<d)
    require(rectangle_charge==logical,'Exact capture rectangles agree at actual core')
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'fixed_charge'))
    from verify_witness import check as witness_check
    witness_cert=deepcopy(cert);witness_cert['weight_denominator']=1
    with tempfile.TemporaryDirectory() as directory:
        path=Path(directory)/'fixture.json';path.write_text(json.dumps(witness_cert))
        result=witness_check({'side':'191/45','t':'0','center':['7/5','6/5'],
                              'logical_charge_units':logical},path)
    require(result['charge_units']==logical,'Exact parent witness reader includes triangle triggers')
    invalid=[]
    c=deepcopy(cert);c['charge_orbits'][0]['support_sets'].pop();invalid.append(c)
    c=deepcopy(cert);c['charge_orbits'][0]['support_sets'][0][0].append(c['charge_orbits'][0]['support_sets'][0][0][0]);invalid.append(c)
    c=deepcopy(cert);c['charge_orbits'][0]['support_sets'][0].append(c['charge_orbits'][0]['support_sets'][0][0]);invalid.append(c)
    c=deepcopy(cert);c['charge_orbits'][0]['support_sets'][0][0][0]=1000000;invalid.append(c)
    c=deepcopy(cert);c['charge_orbits'][0]['support_sets'][0]=[];invalid.append(c)
    c=deepcopy(cert);edge=c['charge_orbits'][0]['sets'][0][:2];c['charge_orbits'][0]['edge_sets'][0]=[edge];c['charge_orbits'][0]['support_sets'][0].append(edge);invalid.append(c)
    for c in invalid:reject(checker.expand,c)
    return {'physical_sites':len(physical),'D4_feature_images':len(atom['sets']),
            'captured_seed_sites':3,'threshold':4,'old_charge_at_actual_core':old_charge,
            'new_charge_at_actual_core':logical,'malformed_schema_or_orbits_rejected':len(invalid)}


def legacy_controls():
    root=Path(__file__).resolve().parents[2]
    baseline=json.loads(Path(__file__).with_name('support-legacy-baseline.json').read_text())
    require(sha256(inspect.getsource(checker.geometry).encode()).hexdigest()==baseline['geometry_source_sha256'],
            'Geometry kernel changed')
    require(sha256(Path(__file__).with_name('integer_sweep.py').read_bytes()).hexdigest()==baseline['integer_sweep_sha256'],
            'Integer sweep changed')
    for record in baseline['legacy_expansions']:
        raw=(root/record['certificate_path']).read_bytes()
        require(sha256(raw).hexdigest()==record['certificate_sha256'],'Legacy fixture changed')
        require(sha256(repr(checker.expand(json.loads(raw))).encode()).hexdigest()==record['expansion_sha256'],
                'Existing certificate expansion changed')
    return {'geometry_and_sweep_unchanged':True,'original_and_frozen_warp_expansions_identical':True}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,default=Path(__file__).with_name('support-controls-result.json'))
    args=ap.parse_args()
    result={'status':'PASS_EXACT_PAIR_TRIPLE_SUPPORT_CONTROLS','geometry':geometry_controls(),
            'algebra':boolean_controls(),'fixture':fixture_controls(),'legacy':legacy_controls(),
            'new_global_bound_proved':False}
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
