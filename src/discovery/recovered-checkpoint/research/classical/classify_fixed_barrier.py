#!/usr/bin/env python3
"""Classify the eleven non-disjoint parents of the original fixed-family barrier."""
from collections import Counter
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[2]


def main():
    source=ROOT/'research/stromquist/fixed-majority-barrier.json'
    raw=source.read_bytes();c=json.loads(raw)
    profiles=json.loads((ROOT/'research/structure/corner-profiles.json').read_text())
    A=F(c['parent_side']);S=F(c['container_side']);L=A*S;a=A*F('2.707106')
    counts=Counter();individual=[]
    for pose in c['poses']:
        x,y,t=(F(pose[k]) for k in ('x','y','half_angle'))
        co=(1-t*t)/(1+t*t);si=2*t/(1+t*t);h=A*(abs(co)+abs(si))/2
        if not (h<=x<=L-h and h<=y<=L-h):raise ValueError('Parent not contained')
        mask=0
        for bit,(x0,y0) in zip((1,2,4,8),((0,0),(L-a,0),(0,L-a),(L-a,L-a))):
            if x0<=x-h and x+h<=x0+a and y0<=y-h and y+h<=y0+a:mask+=bit
        if mask not in (1,2,4,8,3,12,5,10,15):raise ValueError('Invalid membership')
        counts[mask]+=1
        individual.append({'mask':mask,'center_decimal':[float(x),float(y)],
                           'angle_half_tangent':str(t)})
    order=[1,2,4,8,3,12,5,10,15];profile=[counts[m] for m in order]
    loads=[sum(n for m,n in counts.items() if m&b) for b in (1,2,4,8)]
    out={'status':'EXACT_FIXED_BARRIER_CORNER_CLASSIFICATION',
         'source_sha256':hashlib.sha256(raw).hexdigest(),
         'scaled_container':str(L),'unit_container_side':str(S),'parent_side':str(A),
         'scaled_window_side':str(a),'mask_order':order,'profile':profile,
         'aggregate_single_double_all':[sum(profile[:4]),sum(profile[4:8]),profile[8]],
         'corner_loads_BL_BR_TL_TR':loads,
         'belongs_to_612_surviving_profiles':profile in profiles['all_profiles'],
         'corner_violations':[{'corner':b,'load':z} for b,z in zip((1,2,4,8),loads) if z>4],
         'individual':individual,
         'scope':'Exactly classified non-disjoint fixed-feature barrier; not a packing. Its surviving Trump-like profile blocks purely count-conditioned reuse of those same feature budgets at this side.'}
    target=Path(__file__).with_name('fixed-barrier-corner-classification.json')
    target.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='individual'},indent=2))


if __name__=='__main__':main()
