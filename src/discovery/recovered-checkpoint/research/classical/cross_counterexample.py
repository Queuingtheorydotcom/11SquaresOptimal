"""Exact rational counterexample to a proposed cross capacity-four lemma."""
from pathlib import Path
from fractions import Fraction as F
from math import tan
import json
P=Path(__file__).resolve().parent;j=json.loads((P/'cross-probe.json').read_text());S=F(3877084,1000000);a=F(2707106,1000000)
squares=[]
for i,(xy,angle) in enumerate(zip(j['centers'],j['angles'])):
 t=F(0) if i in (1,4) else F(round(tan(angle/2)*10**12),10**12)
 c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);w=c+s
 x,y=map(lambda f:F(round(f*10**10),10**10),xy)
 if i==0:y-=F(1,100000)
 if i==1:x=a-F(1,2)
 if i==3:x=w/2
 if i==4:x=S-F(1,2)
 squares.append((x,y,c,s,t))
masks=[]
for x,y,c,s,t in squares:
 w=c+s;lo=[x-w/2,y-w/2];hi=[x+w/2,y+w/2]
 assert min(lo)>=0 and max(hi)<=S
 membership=[hi[0]<=a,lo[0]>=S-a,hi[1]<=a,lo[1]>=S-a]
 masks.append(sum((1<<k) for k,(xx,yy) in enumerate(((0,2),(1,2),(0,3),(1,3))) if membership[xx] and membership[yy]))
assert masks==[3,3,12,5,10],masks
gaps=[]
for i in range(5):
 for k in range(i):
  x,y,c,s,_=squares[i];u,v,d,e,_=squares[k];dx=x-u;dy=y-v;support=(1+abs(c*d+s*e)+abs(c*e-s*d))/2
  gap=max(abs(dx*c+dy*s),abs(dy*c-dx*s),abs(dx*d+dy*e),abs(dy*d-dx*e))-support
  assert gap>0;gaps.append(gap)
result={'status':'PASS_EXACT_RATIONAL_FIVE_CROSS_SQUARES','outer_side':str(S),'window_side':str(a),'membership_masks':masks,'squares':[{'center':[str(x),str(y)],'halfangle':str(t),'cosine':str(c),'sine':str(s)} for x,y,c,s,t in squares],'minimum_separating_gap':str(min(gaps)),'minimum_separating_gap_decimal':float(min(gaps)),'scope':'Five unit squares in pair-type arms, none in center; refutes capacity4 for their union. This is not eleven squares and does not improve an upper/lower bound.'}
(P/'cross-counterexample.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='squares' and k!='minimum_separating_gap'},indent=2))
