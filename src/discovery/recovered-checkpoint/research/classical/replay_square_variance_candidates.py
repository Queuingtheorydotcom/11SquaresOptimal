#!/usr/bin/env python3
"""Replay saved finite-support conflict witnesses without numerical discovery.

Moments are recomputed as E|X|²-|EX|², using no discovery/moment helper.
The existing exact convex-hull predicates are reused and hash-bound.
"""
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
from hashlib import sha256
from math import isqrt
from collections import Counter
import argparse,json,sys,time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'research/exact_checker'))
import charge_geometry as geom


def need(ok,message):
    if not ok:raise ValueError(message)


def moments(ps):
    n=len(ps);need(n>0,'empty support')
    mu=tuple(sum(p[j] for p in ps)/n for j in range(2))
    var=sum(x*x+y*y for x,y in ps)/n-sum(x*x for x in mu)
    need(var>=0,'negative variance')
    return mu,var


def root_upper(q):
    need(q>=0,'negative radicand')
    scale=2**60
    k=isqrt((q.numerator*scale*scale)//q.denominator)+1
    ans=F(k,scale)
    need(ans*ans>q,'invalid independent upper square root')
    return ans


def orientation_maximum(integer_points,A,coordinate_denominator):
    """Independently enumerate all feasible boundary intersections using integers.

    If u=A*D*z, the orientation inequalities become n.z<=1 with integral n.
    This verifier does not call the polygon clipper used by discovery.
    """
    normals=set()
    for p,q in combinations(integer_points,2):
        x,y=p[0]-q[0],p[1]-q[1]
        if x or y:normals.update(((x,y),(-x,-y),(-y,x),(y,-x)))
    need(normals,'a singleton is not impossible')
    maximum=F(0);vertices=0
    for (a,b),(c,d) in combinations(sorted(normals),2):
        det=a*d-b*c
        if not det:continue
        x,y=d-b,a-c
        if det<0:det,x,y=-det,-x,-y
        if any(n*x+m*y>det for n,m in normals):continue
        vertices+=1
        maximum=max(maximum,(A*coordinate_denominator)**2*F(x*x+y*y,det*det))
    need(vertices>=3,'bounded positive-area orientation polygon missing vertices')
    return maximum


def replay(path):
    started=time.monotonic();saved=json.loads(path.read_bytes())
    source=ROOT/saved['source'];raw=source.read_bytes();c=json.loads(raw)
    need(sha256(raw).hexdigest()==saved['source_sha256'],'source hash differs')
    A=F(saved['maximum_core_side']);D=c['coordinate_denominator'];LD=F(c['L'])*D
    need(LD.denominator==1,'nonlattice container');LD=int(LD)
    points=[]
    for x,y,_ in c['point_orbits']:
        points.extend(sorted({(a,b) for u,v in ((x,y),(y,x))
                              for a in (u,LD-u) for b in (v,LD-v)}))
    need(len(points)==len(set(points)),'duplicate source sites')
    counts=Counter();kinds=Counter();margins=[];rule_kinds=Counter();seen=set();boolean=0;orientation_cache={};pattern_fit_cache={}
    for rule in saved['rules']:
        atom=c['charge_orbits'][rule['orbit']];ids=atom['sets'][0];n=len(ids);k=atom['threshold']
        need(n in (5,7) and n==2*k-1,'wrong majority group')
        need(ids==rule['sites'],'source group mismatch')
        pat=tuple(rule['pattern_local']);need(len(set(pat))==len(pat),'repeated pattern site')
        need(all(0<=i<n for i in pat) and 2<=len(pat)<k,'invalid pattern')
        need([ids[i] for i in pat]==rule['pattern_global'],'global pattern mismatch')
        key=(rule['orbit'],pat);need(key not in seen,'duplicate rule');seen.add(key)
        if saved.get('orientation_polygon_test',False):
            pkey=tuple(sorted(ids[i] for i in pat))
            if pkey not in pattern_fit_cache:
                pattern_fit_cache[pkey]=orientation_maximum([points[i] for i in pkey],A,D)
            need(pattern_fit_cache[pkey]>=1,'proposed activation itself is impossible')
        q=[tuple(F(z,D) for z in points[i]) for i in ids]
        proofs={tuple(v['threshold_local']):v['proof'] for v in rule['proofs']}
        need(len(proofs)==len(rule['proofs']),'duplicate conflict witness')
        used=set();local_kinds=set()
        for threshold in combinations(range(n),k):
            counts['threshold_comparisons']+=1
            if set(pat)&set(threshold):counts['shared_site']+=1;continue
            hp=geom.convex_hull([q[i] for i in pat]);ht=geom.convex_hull([q[i] for i in threshold])
            if geom.hulls_intersect(hp,ht):counts['intersecting_hulls']+=1;continue
            need(threshold in proofs,'unproved disjoint-hull pair')
            p=proofs[threshold];used.add(threshold);kind=p['kind'];kinds[kind]+=1;local_kinds.add(kind)
            if kind=='impossible_threshold':
                sub=p['subset'];need(set(sub)<=set(threshold) and len(set(sub))==len(sub),'bad impossible subset')
                need(moments([q[i] for i in sub])[1]>A*A/2,'possible threshold marked impossible')
            elif kind=='orientation_polygon':
                sub=p['subset'];need(set(sub)<=set(threshold) and len(set(sub))==len(sub),'bad polygon subset')
                key=tuple(sorted(ids[i] for i in sub))
                if key not in orientation_cache:
                    orientation_cache[key]=orientation_maximum([points[i] for i in key],A,D)
                maximum=orientation_cache[key]
                need(maximum<1,'orientation support is not impossible')
                cert=p['certificate']
                need(F(cert['A'])==A and cert['fits'] is False,'invalid polygon certificate scope')
                need(F(cert['maximum_squared_radius'])==maximum,'polygon maximum differs from independent enumeration')
            elif kind=='variance_disks':
                ii=p['first_local_subset'];jj=p['second_local_subset']
                need(set(ii)<=set(pat) and set(jj)<=set(threshold),'bad disk subsets')
                need(len(set(ii))==len(ii) and len(set(jj))==len(jj),'repeated disk sites')
                mu,v=moments([q[i] for i in ii]);nu,w=moments([q[i] for i in jj])
                dist=sum((a-b)**2 for a,b in zip(mu,nu));r=A*A/2-v;s=A*A/2-w
                need(r>=0 and s>=0,'invalid nonnegative radius')
                for name,computed in [('first_variance',v),('second_variance',w),
                                     ('distance_squared',dist),('first_radius_squared',r),('second_radius_squared',s)]:
                    need(F(p[name])==computed,'stored '+name+' mismatch')
                need(tuple(map(F,p['first_mean']))==mu and tuple(map(F,p['second_mean']))==nu,'stored means differ')
                need(F(p['A'])==A,'stored side differs')
                upper=root_upper(dist)+root_upper(r)+root_upper(s)
                need(upper<A,'independent strict disk bound failed');margins.append(A-upper)
            else:raise ValueError('unknown conflict witness kind '+kind)
        need(used==set(proofs),'extraneous or unused conflict witness')
        need(local_kinds,'no novelty relative to convex hull admissibility')
        rule_kinds['with_variance_disks' if 'variance_disks' in local_kinds else 'impossible_only']+=1
        if 'orientation_polygon' in local_kinds:rule_kinds['with_orientation_polygon']+=1
        coefficients=geom.clique_coefficients(n,[],k,[pat]);pm=sum(1<<i for i in pat)
        for mask in range(1<<n):
            need(sum(v for part,v in enumerate(coefficients) if part&mask==part)
                 ==int(mask.bit_count()>=k or mask&pm==pm),'Boolean expansion mismatch')
            boolean+=1
    need(len(seen)==saved['candidate_rules'],'candidate count mismatch')
    return dict(status='PASS_EXACT_SQUARE_VARIANCE_CANDIDATE_REPLAY',source=saved['source'],
                source_sha256=saved['source_sha256'],candidate_sha256=sha256(path.read_bytes()).hexdigest(),
                checker_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                hull_boolean_module_sha256=sha256(Path(geom.__file__).read_bytes()).hexdigest(),
                maximum_core_side=str(A),rules_checked=len(seen),distinct_orbits=len({i for i,p in seen}),
                rule_kinds=dict(rule_kinds),comparisons=dict(counts),nongeometric_witnesses=dict(kinds),
                independently_enumerated_orientation_supports=len(orientation_cache),
                independently_verified_capturable_patterns=len(pattern_fit_cache),
                boolean_masks_checked=boolean,minimum_disk_margin=str(min(margins)),
                seconds=time.monotonic()-started,
                scope='Independent exact moment/disk replay and integer enumeration of orientation-polygon vertices, reusing the hash-bound exact convex-hull and Boolean module. Each rule separately has budget1; no mutual-support or TRUE-OR-support claim, no LP or packing bound.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    result=replay(args.input);args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
