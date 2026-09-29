import sympy as S
from itertools import combinations
u=S.symbols('u'); c=(1-u*u)/(1+u*u); t=2*u/(1+u*u); L=(6*u+4)/(1+2*u-u*u)
r=1-(L-3)*c; b=((1+r)*c-1)/t; v=c-t; w=(L-1)/t-r-(3+b)*c/t
x0=1+2/c-(L-2)*t/c
origins=[(0,0),(L-1,0),(x0,L-1),(0,L-1),(1,L-1),(0,L-2)]
rot=[(0,0),(b,-1),(1,v),(b+1,v-1),(b+2,-w)]
corners=[]
for x,y in origins: corners.append([(x+dx,y+dy) for dx,dy in [(0,0),(1,0),(1,1),(0,1)]])
for x,y in rot: corners.append([(S.cancel(1+c*(x+dx)-t*(y+dy-r)),S.cancel(1+t*(x+dx)+c*(y+dy-r))) for dx,dy in [(0,0),(1,0),(1,1),(0,1)]])
axes=[(1,0),(0,1),(c,t),(-t,c)]
val=lambda x:float(S.sympify(x).subs(u,.365769307604677))
for i,j in combinations(range(11),2):
 for axis in axes:
  p=[S.cancel(x*axis[0]+y*axis[1]) for x,y in corners[i]]
  q=[S.cancel(x*axis[0]+y*axis[1]) for x,y in corners[j]]
  for A,B in [(p,q),(q,p)]:
   a=max(A,key=val); b_=min(B,key=val); gap=S.factor(b_-a)
   if abs(val(gap))<1e-12: print(i,j,axis,'gap=',gap)
