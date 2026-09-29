#!/usr/bin/env python3
"""Independent arithmetic and proof-chain audit for mask800 and six-case transfer.

The rational event sweep is independently rerun in the paired replay receipts;
this script checks hashes, all accepted angular partitions, the geometric
owner premises, capacity arithmetic, and the Trump algebraic bound. It does
not substitute for the audited exact geometric verifier.
"""
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
import hashlib,json
import check_alpha_upper

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
EXTRACT=ROOT/'checkpoint_extract'
COVER=EXTRACT/'research/optimality/global_capture/center-cover-symmetric-exact.json'
ALGEBRA=EXTRACT/'research/optimality/endpoint_charge/exact-trump-endpoint-rows.json'
T=[1,2,4,5,6,7,9,10,11,13]
S=[1,5,6,9,11]
EXPECTED_IDS=[800,2023,2140,2151,2153,1896]

def need(ok,msg):
    if not ok:raise ValueError(msg)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def trig(t):return (1-t*t)/(1+t*t),2*t/(1+t*t)
def without_seconds(x):
    if isinstance(x,dict):return {k:without_seconds(v) for k,v in x.items() if k!='seconds'}
    if isinstance(x,list):return [without_seconds(v) for v in x]
    return x
def quadratic_min_nonnegative(a,b,c,lo,hi):
    at=[lo,hi]
    if c>0 and lo<-b/(2*c)<hi:at.append(-b/(2*c))
    return min(a+b*x+c*x*x for x in at)>=0
def interval_poly(coeffs,a,b):
    # Coefficients in descending order; exact rational interval Horner.
    lo=hi=F(coeffs[0])
    for v in coeffs[1:]:
        candidates=(lo*a,lo*b,hi*a,hi*b)
        lo,hi=min(candidates)+v,max(candidates)+v
    return lo,hi

def algebraic_target_below(U):
    source=json.loads(ALGEBRA.read_text())
    a,b=map(F,source['root_interval'])
    M=[5,-10,-2,14,12,-6,2,2,-1]
    derivative=[M[i]*(8-i) for i in range(8)]
    def eval_poly(coeffs,x):
        z=F(0)
        for v in coeffs:z=z*x+v
        return z
    need(F(36,100)<a<b<F(37,100),'Trump root bracket outside construction interval')
    need(eval_poly(M,a)<0<eval_poly(M,b),'Trump polynomial endpoint signs fail')
    need(interval_poly(derivative,a,b)[0]>0,'Trump polynomial not monotone in root bracket')
    # Construction side alpha=(6t+4)/(1+2t-t^2), with t the unique M-root.
    # N(t)=U(1+2t-t^2)-(6t+4) is concave, hence minimized at an endpoint.
    N=lambda t:U*(1+2*t-t*t)-(6*t+4)
    need(1+2*a-a*a>0 and 1+2*b-b*b>0,'construction denominator not positive')
    need(N(a)>0 and N(b)>0,'rational U does not exceed algebraic Trump side')
    return dict(root_interval=[str(a),str(b)],polynomial_endpoint_signs=['negative','positive'],
                derivative_interval_lower=str(interval_poly(derivative,a,b)[0]),
                minimum_U_gap_numerator_bound=str(min(N(a),N(b))),alpha_below_U=True)

def audit_one(label,packet_path,producer_path,replay_path,cover,expected_support):
    packet=json.loads(packet_path.read_text());a=json.loads(producer_path.read_text());b=json.loads(replay_path.read_text())
    need(without_seconds(a)==without_seconds(b),label+': fresh geometric replay differs')
    need(b['packet_sha256']==sha(packet_path) and b['cover_sha256']==sha(COVER),label+': premise hash mismatch')
    for rel,digest in b['dependencies'].items():need(sha(EXTRACT/rel)==digest,label+': source dependency changed '+rel)
    mask=packet['mask'];gamma=packet['threshold_units'];U=F(packet['parent_Uplus']);L=F(191,50);A=L/U
    need(packet['mask_index']==800 and mask==cover['canonical_eleven_cell_subsets'][800],label+': wrong canonical mask')
    need(packet['conditional_owner_support']==expected_support,label+': wrong owner support')
    need(b['conditional_owner_support']==expected_support and b['conditional_ownership']=='cell_owned_points',label+': wrong replay owner condition')
    need(b['status']=='PASS_EXACT_ASYMMETRIC_MASK_EXCLUSION' and b['continuum_masks_excluded']==1,label+': exact replay incomplete')
    need(F(b['parent_Uplus'])==U and F(b['parent_side'])==A,label+': parent scale mismatch')
    need(b['full_quarter_turn'] and not b['within_field_symmetry_transfer'],label+': missing angle scope')
    c=packet['certificate'];D=c['coordinate_denominator'];points=c['sites']
    need(F(c['L'])==L and c['weight_denominator']==1,label+': wrong fixed field')
    need(len(points)==39 and len(set(map(tuple,points)))==39,label+': field sites duplicate or missing')
    need(all(len(p)==2 and all(type(v) is int and 0<=v<=L*D for v in p) for p in points),label+': field site out of range')
    need(all(type(w) is int and w>=0 for w in c['point_weights']),label+': point weight malformed')
    positive_points=[w for w in c['point_weights'] if w]
    need(positive_points==[1],label+': expected one unit point resource')
    budget=sum(c['point_weights']);arities=[];group_weights=[]
    for atom in c['features']:
        group=atom['indices'];k=atom['threshold'];w=atom['weight']
        need(atom['kind']=='majority_hull' and len(group)==2*k-1 and len(set(group))==len(group),label+': invalid odd TRUE majority')
        need(all(type(i) is int and 0<=i<len(points) for i in group) and type(w) is int and w>=0,label+': invalid TRUE support')
        budget+=w;arities.append(len(group));group_weights.append(w)
    need(len(arities)==7 and budget==c['budget_units']==b['budget_units']==19,label+': resource budget mismatch')
    need([i for i in mask if gamma[i]>0]==S and all(gamma[i]==4 for i in S),label+': charged cells mismatch')
    need(sum(gamma[i] for i in mask)==b['threshold_sum_units']==20 and budget<20,label+': counting gap fails')
    offsets=[tuple(map(F,p)) for p in packet['ownership_offsets_unit']]
    need(set(offsets)=={(F(0),F(0)),(F(1,200),F(0)),(-F(1,200),F(0)),(F(0),F(1,200)),(F(0),-F(1,200))},label+': unexpected owner offsets')
    ownership_checks=0;diameters=[]
    for i,cell in enumerate(cover['cells']):
        center=tuple(map(F,cell['center']))
        vertices=[tuple((U-1)*(F(v)-F(1,2)) for v in p) for p in cell['vertices']]
        for j,offset in enumerate(offsets):
            owned=tuple((U-1)*(g-F(1,2))+z for g,z in zip(center,offset))
            field=tuple(L/2+A*v for v in owned)
            need(field==tuple(map(F,b['owned_points'][i][j])),label+': owned point mismatch')
            for vertex in vertices:
                need(sum((v-z)**2 for v,z in zip(vertex,owned))<F(1,4),label+': point not owned strictly')
                ownership_checks+=1
        diameters.extend(sum((v-w)**2 for v,w in zip(p,q)) for p in vertices for q in vertices)
    need(max(diameters)<1,label+': a cell can hold two centers')
    accepted={};status_counts=Counter()
    for row in b['records']:
        status=row['status'];status_counts[status]+=1
        if not status.startswith('PASS'):continue
        cell=row['cell'];lo,hi=map(F,row['interval']);key=(cell,lo,hi)
        need(key not in accepted and F(0)<=lo<hi<=F(1),label+': invalid accepted angle')
        if status=='PASS_STAIRCASE':
            need(row['proxy_minimum']>=gamma[cell],label+': failed staircase threshold')
        elif status=='PASS_TRUE_PATCH':
            patch=row['patches'];stats=patch['statistics']
            need(patch['status']=='PASS' and stats['nodes']==stats['pruned'] and stats['cells']>0,label+': incomplete TRUE patch')
        else:raise ValueError(label+': unexpected accepted method '+status)
        t=(lo+hi)/2;ct,st=trig(t);factors=[];widths=[]
        for endpoint in (lo,hi):
            ce,se=trig(endpoint)
            factors.append(ct*ce+st*se+abs(ct*se-st*ce));widths.append(ce+se)
        factor=max(factors);core=(A-F(1,10**12))/factor;H=L/2-A*min(widths)/2
        need(F(row['reference_half_angle'])==t and F(row['core_side'])==core and F(row['parent_center_halfwidth'])==H,label+': parent/core parameters mismatch')
        need(quadratic_min_nonnegative(factor-ct-st,2*(ct-st),factor+ct+st,lo,t),label+': left orientation core bound')
        need(quadratic_min_nonnegative(factor-ct+st,-2*(ct+st),factor+ct-st,t,hi),label+': right orientation core bound')
        width=min(widths)
        need(quadratic_min_nonnegative(1-width,2,-1-width,lo,hi),label+': wall envelope fails')
        need(core*factor<A,label+': core not strictly contained')
        accepted[key]=True
    done=b['cells'];need(len(done)==11 and {x['cell'] for x in done}==set(mask),label+': missing physical cell')
    matched=set()
    for cell in done:
        i=cell['cell'];need(cell['complete'] and not cell['pending'] and not cell['unresolved'],label+': incomplete cell')
        cursor=F(0)
        for lo,hi in sorted(tuple(map(F,ab)) for ab in cell['accepted']):
            need(lo==cursor and (i,lo,hi) in accepted,label+': missing or unproved angular interval')
            cursor=hi;matched.add((i,lo,hi))
        need(cursor==1,label+': incomplete quarter turn')
    need(matched==set(accepted),label+': orphan accepted row')
    return dict(packet=str(packet_path.relative_to(ROOT)),packet_sha256=sha(packet_path),
                producer_sha256=sha(producer_path),replay_sha256=sha(replay_path),
                exact_rows=len(b['records']),accepted_leaves=len(accepted),status_counts=dict(status_counts),
                ownership_vertex_checks=ownership_checks,owner_support=expected_support,
                physical_sites=len(points),point_resource_weights=positive_points,
                TRUE_arities=arities,TRUE_weights=group_weights,budget=budget,threshold_sum=20)

def main():
    cover=json.loads(COVER.read_text())
    full=audit_one('eleven_owner',HERE/'mask800_r35_ext195.json',
                   HERE/'mask800_r35_ext195_attempt.json',HERE/'mask800_r35_ext195_fresh_replay.json',
                   cover,[0,*T])
    ten=audit_one('ten_owner',HERE/'mask800_r35_ext195_tenowner.json',
                  HERE/'mask800_r35_ext195_tenowner_attempt.json',
                  HERE/'mask800_r35_ext195_tenowner_fresh_replay.json',cover,T)
    U=F(json.loads((HERE/'mask800_r35_ext195_tenowner.json').read_text())['parent_Uplus'])
    need(U==check_alpha_upper.U,'algebraic checker uses a different gate')
    check_alpha_upper.main()
    target=algebraic_target_below(U)
    cases=[];canonical=cover['canonical_eleven_cell_subsets']
    for extra in sorted(set(range(16))-set(T)):
        raw=sorted(T+[extra]);halfturn=sorted(15-i for i in raw)
        if raw in canonical:idx=canonical.index(raw);rotated=False
        else:idx=canonical.index(halfturn);rotated=True
        cases.append(dict(extra_cell=extra,raw_mask=raw,canonical_index=idx,
                          canonical_by_halfturn=rotated))
    need([x['canonical_index'] for x in cases]==EXPECTED_IDS,'six-case canonical map mismatch')
    result=dict(status='PASS_INDEPENDENT_SIX_CASE_TRANSFER_AUDIT',
                cover_sha256=sha(COVER),algebraic_source_sha256=sha(ALGEBRA),
                algebraic_checker_sha256=sha(HERE/'check_alpha_upper.py'),
                parent_Uplus=str(U),exact_target=target,eleven_owner_audit=full,
                ten_owner_audit=ten,common_charged_cells=S,common_ten_owner_cells=T,
                six_cases=cases,canonical_masks_excluded=len(cases),
                global_optimality_proved=False,
                scope='The ten-owner exact field excludes these six raw supersets of T at S<=U, hence at S<=alpha. The remaining occupancy cases are not settled by this audit.')
    out=HERE/'mask800-sixmask-independent-audit.json'
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('eleven_owner_audit','ten_owner_audit')},indent=2))

if __name__=='__main__':main()
