"""Exact polygon-sweep checker for supported charges on <=7 site slots.

An atom's optional kind is 'threshold' (the backward-compatible default) or
'floor'. Its charge is respectively w*[h>=k] or w*floor(h/k), for h captured
sites. Both have global budget floor(m/k)*w. Optional multiset:true permits
repeated site slots for these two kinds. Geometric kinds edge_or and
convex_clique have unit budget after exact support-intersection checks. Optional
support_sets add captured pairs/triples through their full convex hulls.
Geometry and sweep kernels are unchanged from the supplied pinned checker.
"""
from fractions import Fraction as F
from pathlib import Path
from math import lcm
from bisect import bisect_left,bisect_right
import sys,json,time,hashlib
import numpy as np
from integer_sweep import accumulate,trig,need
from charge_geometry import clique_coefficients,validate_support_clique
ROOT=Path(__file__).resolve().parent

def feature_coefficients(n,k,kind='threshold'):
 """Binomial-basis coefficients for the logical captured-site charge."""
 from math import comb
 need(type(n) is int and 1<=n<=7 and type(k) is int and 1<=k<=n,'unsupported charge size/threshold')
 need(kind in ('threshold','floor'),'unsupported charge kind')
 if kind=='threshold':return tuple(0 if j<k else (-1)**(j-k)*comb(j-1,k-1) for j in range(n+1))
 return tuple(sum((-1)**(j-h)*comb(j,h)*(h//k) for h in range(j+1)) for j in range(n+1))

def expand(c):
 from itertools import combinations
 D=c['coordinate_denominator'];L=F(c['L']);need(type(D) is int and D>0 and (L*D).denominator==1,'invalid coordinate scale');LD=int(L*D)
 points=[];weights=[]
 for x,y,w in c['point_orbits']:
  need(all(type(v) is int for v in (x,y,w)) and 0<=x<=LD and 0<=y<=LD and w>=0,'invalid point orbit')
  oo=sorted({(a,b) for u,v in [(x,y),(y,x)] for a in (u,LD-u) for b in (v,LD-v)});points+=oo;weights.extend([w]*len(oo))
 need(len(set(points))==len(points),'duplicate sites');lookup={p:i for i,p in enumerate(points)}
 if 'charge_orbits' in c:
  need('threshold_orbits' not in c,'ambiguous charge schema');orbits=c['charge_orbits']
 else:orbits=[{'sets':g['triples'],'threshold':2,'weight':g['weight']} for g in c['threshold_orbits']]
 subsets=[];coefficients=[];budget=sum(weights)
 for atom in orbits:
  groups=atom['sets'];w=atom['weight'];kind=atom.get('kind','threshold')
  need(groups and type(w) is int and w>=0,'invalid charge weight')
  n=len(groups[0]);need(1<=n<=7,'unsupported charge size')
  need(kind in ('threshold','floor','edge_or','convex_clique'),'unsupported charge kind')
  multiset=atom.get('multiset',False);need(type(multiset) is bool,'invalid multiset flag')
  if kind in ('edge_or','convex_clique'):need(not multiset,'geometric support groups must have distinct sites')
  for inds in groups:need(len(inds)==n and (multiset or len(set(inds))==n) and all(type(i) is int and 0<=i<len(points) for i in inds),'invalid charge sites')
  transforms=[]
  for swap in (False,True):
   for sx in (False,True):
    for sy in (False,True):
     mapping={}
     for i in groups[0]:
      x,y=points[i]
      if swap:x,y=y,x
      if sx:x=LD-x
      if sy:y=LD-y
      mapping[i]=lookup[x,y]
     transforms.append(mapping)
  if kind in ('threshold','floor'):
   r=atom['threshold'];basis=feature_coefficients(n,r,kind)
   expected={tuple(sorted(mapping[i] for i in groups[0])) for mapping in transforms}
   need(expected==set(map(tuple,groups)) and len(expected)==len(groups),'incomplete charge orbit')
   budget+=len(groups)*(n//r)*w
   for inds in groups:
    for j in range(r,n+1):
     coefficient=basis[j]*w
     if not coefficient:continue
     for part in combinations(inds,j):subsets.append(part);coefficients.append(coefficient)
  else:
   r=atom.get('threshold') if kind=='convex_clique' else None
   if kind=='convex_clique':need(type(r) is int and 1<=r<=n and 2*r>n,'invalid majority threshold')
   edge_sets=atom.get('edge_sets',[[] for _ in groups]);need(len(edge_sets)==len(groups),'edge_sets must align with sets')
   support_sets=atom.get('support_sets',[[] for _ in groups]);need(len(support_sets)==len(groups),'support_sets must align with sets')
   normalized=[];normalized_supports=[]
   for inds,edges,supports in zip(groups,edge_sets,support_sets):
    canon=[]
    for edge in edges:
     need(len(edge)==2 and all(type(i) is int and i in inds for i in edge) and edge[0]!=edge[1],'invalid support edge')
     canon.append(tuple(sorted(edge)))
    need(len(set(canon))==len(canon),'duplicate support edge')
    extra=[]
    for support in supports:
     need(len(support) in (2,3) and len(set(support))==len(support) and all(type(i) is int and i in inds for i in support),'invalid convex support')
     extra.append(tuple(sorted(support)))
    need(len(set(extra))==len(extra) and not set(canon).intersection(extra),'duplicate convex support')
    need(bool(canon or extra) or kind=='convex_clique','empty edge-OR support')
    normalized.append(tuple(sorted(canon)))
    normalized_supports.append(tuple(sorted(extra)))
   expected={(tuple(sorted(mapping[i] for i in groups[0])),
              tuple(sorted(tuple(sorted((mapping[i],mapping[j]))) for i,j in normalized[0])),
              tuple(sorted(tuple(sorted(mapping[i] for i in support)) for support in normalized_supports[0])))
             for mapping in transforms}
   actual=[(tuple(sorted(inds)),edges,supports) for inds,edges,supports in zip(groups,normalized,normalized_supports)]
   need(expected==set(actual) and len(expected)==len(actual),'incomplete geometric charge orbit')
   budget+=len(groups)*w
   for inds,edges,supports in zip(groups,normalized,normalized_supports):
    validate_support_clique(inds,edges,r,points,supports)
    local={site:i for i,site in enumerate(inds)}
    basis=clique_coefficients(n,[(local[i],local[j]) for i,j in edges],r,
                              [tuple(local[i] for i in support) for support in supports])
    for mask,coefficient in enumerate(basis):
     if coefficient and w:
      subsets.append(tuple(inds[i] for i in range(n) if mask&(1<<i)))
      coefficients.append(coefficient*w)
 absolute=sum(weights)+sum(map(abs,coefficients));need(budget==c['budget_units'] and absolute<2**50,'budget/overflow')
 return points,weights,subsets,coefficients,D

def geometry(points,pw,triples,tw,D,t,B,H,meta=False):
 p,q=t.numerator,t.denominator;C=q*q-p*p;S=2*p*q;R=q*q+p*p
 LD=int(F(191,50)*D);scale=lcm(2*D,(B/2).denominator,H.denominator);factor=scale//(2*D)
 h=int(H*scale);half=int(B*scale/2)*R
 uv=[(C*(2*x-LD)*factor+S*(2*y-LD)*factor,-S*(2*x-LD)*factor+C*(2*y-LD)*factor) for x,y in points]
 rect={}
 def insert(indices,w):
  if not w:return
  xx=[uv[i][0] for i in indices];yy=[uv[i][1] for i in indices]
  z=(max(xx)-half,min(xx)+half,max(yy)-half,min(yy)+half)
  if z[0]<z[1] and z[2]<z[3]:rect[z]=rect.get(z,0)+w
 for i,w in enumerate(pw):insert([i],w)
 for subset,w in zip(triples,tw):insert(subset,w)
 rect={r:w for r,w in rect.items() if w};rr=list(rect);ww=np.array(list(rect.values()),np.int64)
 poly=[(C*x+S*y,-S*x+C*y) for x,y in [(-h,-h),(h,-h),(h,h),(-h,h)]]
 xe=sorted({p[0] for p in poly}|{v for r in rr for v in r[:2]});ye=sorted({p[1] for p in poly}|{v for r in rr for v in r[2:]})
 xi={v:i for i,v in enumerate(xe)};yi={v:i for i,v in enumerate(ye)}
 ev=np.array(sorted([(xi[r[0]],i,1) for i,r in enumerate(rr)]+[(xi[r[1]],i,-1) for i,r in enumerate(rr)]),np.int64)
 yl=np.array([yi[r[2]] for r in rr],np.int64);yh=np.array([yi[r[3]] for r in rr],np.int64)
 first=np.full(len(xe)-1,-1,np.int64);last=first.copy();edges=[]
 for k,(u,v) in enumerate(poly):
  z,w=poly[(k+1)%4]
  if z==u:continue
  if z<u:u,v,z,w=z,w,u,v
  edges.append((u,z,w-v,v*(z-u)-u*(w-v),z-u))
 left=min(p[0] for p in poly);right=max(p[0] for p in poly)
 for k,(a,b) in enumerate(zip(xe,xe[1:])):
  if a<left or b>right:continue
  crossings=[]
  for u,z,m,n,d in edges:
   if u<=a and b<=z:crossings.extend([(m*a+n,d),(m*b+n,d)])
  need(len(crossings)==4,'polygon edge count');bn,bd=crossings[0];tn,td=bn,bd
  for n,d in crossings[1:]:
   if n*bd<bn*d:bn,bd=n,d
   if n*td>tn*d:tn,td=n,d
  first[k]=bisect_right(ye,bn//bd)-1;last[k]=bisect_left(ye,-((-tn)//td))
  need(0<=first[k]<last[k]<=len(ye)-1,'query range')
 arrays=(len(ye)-1,ev[:,0],ev[:,1],ev[:,2],yl,yh,ww,first,last)
 if meta:return arrays,dict(poly=poly,xe=xe,ye=ye,rect=rr,weights=list(map(int,ww)),C=C,S=S,R=R,scale=scale)
 return arrays

def validate(c):
 L=F(c['L']);A=F(c['A']);need(L==F(191,50) and 0<A<L,'wrong container/parent');den=c['weight_denominator'];need(type(den) is int and den>0,'denominator')
 need(type(c['minimum_units']) is int and c['minimum_units']>=0 and type(c['budget_units']) is int and c['budget_units']>=0,'integral nonnegative charge units required')
 data=expand(c);jobs=[];margins=[];cursor=F(0)
 for row in c['entries']:
  a,b,t,B=map(F,row);need(a==cursor and 0<=a<b<1 and 0<=t<1 and 0<B<A,'catalogue coverage')
  cc,ss=trig(t);f=[];g=[]
  for u in (a,b):
   c0,s0=trig(u);dot=cc*c0+ss*s0;cross=abs(cc*s0-ss*c0);need(dot>0 and dot>=cross,'angle range');f.append(c0+s0);g.append(dot+cross)
  margin=A-B*max(g);need(margin>0,'core not strict');margins.append(margin);r=A*min(f)/2
  need(B*(cc+ss)/2<=r<L/2,'parent envelope');jobs.append((t,B,L/2-r));cursor=b
 need(cursor*cursor+2*cursor>1,'angle gap');need(11*c['minimum_units']>c['budget_units'],'counting budget')
 return data,jobs,min(margins)

def main():
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('certificate');ap.add_argument('--output',required=True);ap.add_argument('--direct',action='store_true');args=ap.parse_args()
 raw=Path(args.certificate).read_bytes();c=json.loads(raw);data,jobs,margin=validate(c);rows=[];start=time.monotonic()
 for k,job in enumerate(jobs):
  arrays=geometry(*data,*job);m,cells,win=accumulate(*arrays,direct=args.direct)
  need(m>=c['minimum_units'],'coverage fails at '+str(k));rows.append({'row':k,'minimum_units':int(m),'cells':int(cells),'slabs':int(np.count_nonzero(arrays[-2]>=0))})
  if k%100==0:print(k,int(m),round(time.monotonic()-start,1),flush=True)
 from collections import Counter
 result={'status':'PASS_EXACT_MOVABLE_SUPPORT_CERTIFICATE','certificate_sha256':hashlib.sha256(raw).hexdigest(),'bound':str(F(c['L'])/F(c['A'])),'intervals':len(rows),'minimum_units':min(r['minimum_units'] for r in rows),'budget_units':c['budget_units'],'minimum_margin':str(margin),'histogram':dict(Counter(r['minimum_units'] for r in rows)),'slabs':sum(r['slabs'] for r in rows),'cells':sum(r['cells'] for r in rows),'seconds':time.monotonic()-start,'rows':rows}
 Path(args.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
if __name__=='__main__':main()
