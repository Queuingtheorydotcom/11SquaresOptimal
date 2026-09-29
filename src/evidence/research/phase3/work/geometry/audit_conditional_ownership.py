#!/usr/bin/env python3
"""Source-distinct exact rectangle-union replay of conditional point ownership.

Uses no upstream charge, sweep, or majority code. Each retained rational angle
row is independently rebuilt as a union of axis-parallel capture rectangles in
the row core's frame. Exact x slabs and merged y intervals cover its complete
clipped center polygon. Closed-set continuity handles event boundaries.
"""
from fractions import Fraction as F
from pathlib import Path
import argparse, hashlib, json, os
if not __debug__:
    raise RuntimeError('Run with assertions enabled; -O is unsupported')
ROOT=Path(os.environ.get('ELEVEN_PACKING_ROOT',str(Path(__file__).resolve().parents[2]/'current'))).resolve()
COVER=ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json'
L=F(191,50)

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def cs(t): return (1-t*t)/(1+t*t),2*t/(1+t*t)
def clip(poly,axis,value,low):
    if not poly:return []
    result=[]
    for p,q in zip(poly,poly[1:]+poly[:1]):
        x=p[axis]-value; y=q[axis]-value
        ip=x>=0 if low else x<=0; iq=y>=0 if low else y<=0
        if ip:result.append(p)
        if ip!=iq:
            t=x/(x-y)
            result.append(tuple(p[k]+t*(q[k]-p[k]) for k in (0,1)))
    return result
def area(poly):
    return abs(sum(p[0]*q[1]-p[1]*q[0] for p,q in zip(poly,poly[1:]+poly[:1])))

def rectangle_cover(poly,sites,side,t):
    c,s=cs(t)
    def rot(p):return c*p[0]+s*p[1],-s*p[0]+c*p[1]
    poly=list(map(rot,poly)); assert area(poly)>0
    rects=[]
    for point in sites:
        x,y=rot(point); rects.append((x-side/2,x+side/2,y-side/2,y+side/2))
    xmin=min(p[0] for p in poly);xmax=max(p[0] for p in poly)
    events=sorted({p[0] for p in poly}|{x for r in rects for x in r[:2] if xmin<x<xmax})
    count=0
    for lo,hi in zip(events,events[1:]):
        strip=clip(clip(poly,0,lo,True),0,hi,False)
        if not strip or area(strip)==0:continue
        yl=min(p[1] for p in strip); yh=max(p[1] for p in strip);mid=(lo+hi)/2
        intervals=sorted((a,b) for x,z,a,b in rects if x<mid<z)
        cursor=yl
        for a,b in intervals:
            if b<cursor:continue
            if a>cursor:break
            cursor=max(cursor,b)
            if cursor>=yh:break
        if cursor<yh:
            return dict(passed=False,x_slab=[str(lo),str(hi)],uncovered_y_lower=str(cursor))
        count+=1
    return dict(passed=True,slabs=count)

def run(receipt):
    d=json.loads(receipt.read_text());cover=json.loads(COVER.read_text())
    assert d['cover_sha256']==sha(COVER)
    U=F(d['parent_Uplus']);B=L/U
    assert F(d['parent_side'])==B and F(19377,5000)<=U<=F(cover['side_upper'])
    mask=d['mask'];owner=d['owner']
    assert mask==cover['canonical_eleven_cell_subsets'][d['mask_index']] and owner in mask
    assert d['conditioned'] and d['uses_learned_points']==False and d['induction_round']==1
    assert d['prior_owner_support']==[j for j in mask if j!=owner]
    polyunit=[[tuple(F(1,2)+(U-1)*F(x) for x in p) for p in c['vertices']] for c in cover['cells']]
    owned=[[tuple(map(F,p)) for p in group] for group in d['prior_owned_points']]
    assert len(owned)==16
    disk_checks=0
    for j,group in enumerate(owned):
        assert group
        for point in group:
            p=tuple(x/B for x in point)
            for v in polyunit[j]:
                assert sum((p[k]-v[k])**2 for k in (0,1))<F(1,4)
                disk_checks+=1
    point=tuple(map(F,d['point']))
    generator=tuple(B*(F(1,2)+(U-1)*F(x)) for x in cover['cells'][owner]['center'])
    assert point==tuple(generator[k]+B*F(d['offset'][k]) for k in (0,1))
    sites=[point]+[p for j in d['prior_owner_support'] for p in owned[j]]
    poly=[tuple(B*x for x in v) for v in polyunit[owner]]
    passes={tuple(map(F,r['interval'])):r for r in d['records'] if r['status'].startswith('PASS')}
    intervals=[tuple(map(F,p)) for p in d['accepted']]
    assert intervals and intervals[0][0]==0 and intervals[-1][1]==1
    assert all(a[1]==b[0] for a,b in zip(intervals,intervals[1:]))
    assert len(intervals)==len(set(intervals))
    checks=[]
    for lo,hi in intervals:
        assert F(0)<=lo<hi<=1
        row=passes[(lo,hi)]; t=(lo+hi)/2;c,s=cs(t)
        widths=[];factors=[]
        for end in (lo,hi):
            ce,se=cs(end);dot=c*ce+s*se;cross=abs(c*se-s*ce)
            assert dot>0 and dot>=cross
            factors.append(dot+cross);widths.append(ce+se)
        core=(B-F(1,10**12))/max(factors)
        assert core==F(row['core_side']) and t==F(row['reference_half_angle'])
        assert core*max(factors)<B
        h=B*min(widths)/2;domain=poly
        for axis in (0,1):domain=clip(clip(domain,axis,h,True),axis,L-h,False)
        ans=rectangle_cover(domain,sites,core,t)
        assert ans['passed'],ans
        checks.append(dict(interval=[str(lo),str(hi)],**ans))
    return dict(status='PASS_INDEPENDENT_CONDITIONAL_OWNERSHIP',
                source_sha256=sha(receipt),cover_sha256=sha(COVER),checker_sha256=sha(Path(__file__)),
                mask_index=d['mask_index'],mask=mask,owner=owner,point=d['point'],
                parent_Uplus=str(U),parent_side=str(B),prior_disk_checks=disk_checks,
                full_angle_rows=len(checks),exact_rectangle_slabs=sum(r['slabs'] for r in checks),
                rows=checks,global_optimality_proved=False,mask_exclusion_proved=False,
                scope='Conditional strict ownership, using only unconditionally disk-owned prior sites; no learned premise and no circular deduction.')

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('receipt',type=Path);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();out=run(args.receipt)
    args.output.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='rows'},indent=2))
