"""Exact low-charge open-cell extraction, complementing integer_sweep.py.

The list is an outer cover after taking closures: an event point with logical
charge below cutoff is in closure of at least one generic low-charge cell.
Coordinates are exact integers in geometry()'s transformed axes.
"""
from pathlib import Path
import sys,json,time
import numpy as np
from numba import njit
from fractions import Fraction as F
SOURCE=Path(__file__).resolve().parents[2]/'source/11-squares-certified-bound-main'
sys.path.insert(0,str(SOURCE))
from exact_mixed import expand,geometry
from integer_sweep import accumulate

@njit
def update(mn,mx,lazy,k,a,b,lo,hi,w):
 if hi<=a or b<=lo:return
 if lo<=a and b<=hi:
  mn[k]+=w;mx[k]+=w;lazy[k]+=w;return
 mid=(a+b)//2
 update(mn,mx,lazy,2*k,a,mid,lo,hi,w)
 update(mn,mx,lazy,2*k+1,mid,b,lo,hi,w)
 mn[k]=lazy[k]+min(mn[2*k],mn[2*k+1])
 mx[k]=lazy[k]+max(mx[2*k],mx[2*k+1])

@njit
def collect(mn,mx,lazy,k,a,b,lo,hi,carry,cut,out):
 if hi<=a or b<=lo or carry+mn[k]>=cut:return
 if mn[k]==mx[k]:
  out.append((max(a,lo),min(b,hi),carry+mn[k]));return
 mid=(a+b)//2
 collect(mn,mx,lazy,2*k,a,mid,lo,hi,carry+lazy[k],cut,out)
 collect(mn,mx,lazy,2*k+1,mid,b,lo,hi,carry+lazy[k],cut,out)

@njit
def extract(nv,evindex,atomindex,sign,ylo,yhi,weights,first,last,cut):
 n=1
 while n<nv:n*=2
 mn=np.zeros(2*n,np.int64);mx=np.zeros(2*n,np.int64);lazy=np.zeros(2*n,np.int64)
 p=0;out=[(np.int64(-1),np.int64(-1),np.int64(-1),np.int64(-1))];out.pop()
 for i in range(len(first)):
  while p<len(evindex) and evindex[p]==i:
   j=atomindex[p];update(mn,mx,lazy,1,0,n,ylo[j],yhi[j],sign[p]*weights[j]);p+=1
  if first[i]>=0:
   found=[(np.int64(-1),np.int64(-1),np.int64(-1))];found.pop()
   collect(mn,mx,lazy,1,0,n,first[i],last[i],np.int64(0),cut,found)
   for lo,hi,z in found:out.append((i,lo,hi,z))
 return out

def selfcheck():
 rng=np.random.default_rng(317)
 for _ in range(20):
  nv=19;nx=12;m=31
  xl=rng.integers(0,nx-1,m);xh=np.array([rng.integers(x+1,nx+1) for x in xl]);yl=rng.integers(0,nv-1,m);yh=np.array([rng.integers(y+1,nv+1) for y in yl]);w=rng.integers(-100,101,m)
  ev=np.array(sorted([(int(xl[j]),j,1) for j in range(m)]+[(int(xh[j]),j,-1) for j in range(m)]),np.int64)
  first=np.zeros(nx,np.int64);last=np.full(nx,nv,np.int64)
  rows=extract(nv,ev[:,0],ev[:,1],ev[:,2],yl,yh,w,first,last,0)
  got={(i,j):z for i,lo,hi,z in rows for j in range(lo,hi)}
  expected={(i,j):sum(int(w[q]) for q in range(m) if xl[q]<=i<xh[q] and yl[q]<=j<yh[q]) for i in range(nx) for j in range(nv)}
  expected={k:z for k,z in expected.items() if z<0}
  assert got==expected
 return True

if __name__=='__main__':
 selfcheck();start=time.monotonic()
 c=json.load(open(SOURCE/'global-certificate.json'));data=expand(c);L=F(c['L']);target=F(3877084,1000000);A=L/target;B=A-F(1,10**12);H=(L-A)/2
 arr,meta=geometry(*data,F(0),B,H,meta=True)
 rows=extract(*arr,c['minimum_units']);m,ncells,_=accumulate(*arr)
 assert min(z for i,lo,hi,z in rows)==m
 # Merge adjacent intervals irrespective of their individual charge. They form
 # an exact generic low-region union; minimum charge recorded conservatively.
 slab={}
 for i,lo,hi,z in rows:
  row=slab.setdefault(i,[])
  if row and row[-1][1]==lo:row[-1]=(row[-1][0],hi,min(row[-1][2],z))
  else:row.append((lo,hi,z))
 merged=[];active={}
 for i in sorted(slab):
  nxt={}
  for lo,hi,z in slab[i]:
   key=(lo,hi)
   if key in active and active[key][1]==i:
    a,_,oldz=active[key];nxt[key]=(a,i+1,min(z,oldz))
   else:nxt[key]=(i,i+1,z)
  for key,v in active.items():
   if key not in nxt or nxt[key][0]!=v[0]:merged.append((*v[:2],*key,v[2]))
  active=nxt
 for (lo,hi),(a,b,z) in active.items():merged.append((a,b,lo,hi,z))
 xe,ye=meta['xe'],meta['ye'];scale=meta['scale']
 boxes=[[str(L/2+F(xe[a],scale)),str(L/2+F(xe[b],scale)),str(L/2+F(ye[lo],scale)),str(L/2+F(ye[hi],scale)),int(z)] for a,b,lo,hi,z in merged]
 result={'status':'EXACT_AXIS_DEFECT_OUTER_COVER_ONLY','target_side':str(target),'parent_side':str(A),'core_side':str(B),'core_halfangle':'0','cutoff_units':c['minimum_units'],'minimum_units':int(m),'total_generic_cells':int(ncells),'low_generic_cells':sum(hi-lo for i,lo,hi,z in rows),'low_run_count':len(rows),'merged_box_count':len(boxes),'boxes':[{'x0':r[0],'x1':r[1],'y0':r[2],'y1':r[3],'minimum_units':r[4]} for r in boxes],'seconds':time.monotonic()-start,'scope':'Axis orientation only; closures of boxes cover every legal axis core with charge strictly less than cutoff. Not a global angle cover and not a nonexistence proof.'}
 path=Path(__file__).with_name('axis-low-cells.json');path.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k!='boxes'},indent=2))
