"""Orientation-independent exact normals and medians for majority features.

If M=[[C,S],[-S,C]], then M^T M=R^2 I. For each fixed world
normal n and centered integer site X, (M n) dot (factor*M X) equals
factor*R^2*(n dot X). Thus the pair-normal median is computed only once.
The two core-axis medians still use the rotated site coordinates per row.
"""
from fractions import Fraction as F
from itertools import combinations
from math import gcd
from majority_geometry import require


def prepare_majority(data):
    points,pw,subsets,coefficients,D,majority=data
    LD=int(F(191,50)*D);prepared=[]
    for group,k,w in majority:
        sites=[points[i] for i in group];normals=set()
        for (x,y),(u,v) in combinations(sites,2):
            a,b=v-y,x-u
            if not a and not b:continue
            divisor=gcd(abs(a),abs(b));a//=divisor;b//=divisor
            if a<0 or (a==0 and b<0):a,b=-a,-b
            normals.add((a,b))
        values=[]
        for a,b in sorted(normals):
            median=sorted(a*(2*x-LD)+b*(2*y-LD) for x,y in sites)[len(sites)//2]
            values.append((a,b,median))
        prepared.append(tuple(values))
    return prepared


def row_strips(prepared,points,half,C,S,R,factor):
    require(C*C+S*S==R*R and factor>0,'Invalid rotated integer lattice')
    middle=len(points)//2
    umedian=sorted(x for x,y in points)[middle]
    vmedian=sorted(y for x,y in points)[middle]
    strips=[(0,1,vmedian-half,vmedian+half),(1,0,umedian-half,umedian+half)]
    multiplier=factor*R*R
    for a,b,median in prepared:
        u,v=C*a+S*b,-S*a+C*b
        if not u or not v:continue  # Redundant with one of the two axis strips.
        value=multiplier*median
        if u<0:u,v,value=-u,-v,-value
        radius=half*(abs(u)+abs(v))
        strips.append((u,v,value-radius,value+radius))
    return strips
