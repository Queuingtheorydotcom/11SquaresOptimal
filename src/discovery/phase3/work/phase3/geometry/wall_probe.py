"""Numerical wall-pose discovery; never a continuum or ownership certificate."""
from pathlib import Path
from fractions import Fraction as F
import argparse,json,os,sys
os.environ['OPENBLAS_NUM_THREADS']='1'
import numpy as np
from scipy.spatial import ConvexHull
from threadpoolctl import threadpool_limits
HERE=Path(__file__).resolve().parent;WORK=HERE.parents[1];ROOT=WORK.parent/'current';BASE=ROOT/'research/optimality/deficit_geometry/physical_features';sys.path.insert(0,str(BASE));from model import PhysicalModel
def main():
 ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();threadpool_limits(limits=1);s=json.loads(a.source.read_text());state=s['final_state'];mask=s['mask'];L=3.82;B=float(F(s['B']));cover=json.loads((ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json').read_text());generators=np.array([[float(F(x)) for x in c['center']] for c in cover['cells']]);pieces=[]
 angle=np.linspace(0,np.pi/2,257,endpoint=True);along=np.linspace(0,L,385);theta,z,eps=np.meshgrid(angle,along,[0,1e-6,.001],indexing='ij');theta,z,eps=[x.ravel() for x in (theta,z,eps)];rad=B/2*(np.cos(theta)+np.sin(theta));z=np.clip(z,rad,L-rad)
 for swap in (False,True):
  for sign in (-1,1):
   x=rad+eps if sign==-1 else L-rad-eps;y=z;pieces.append(np.column_stack([theta,y,x] if swap else [theta,x,y]))
 P=np.unique(np.vstack(pieces),axis=0);normalized=(P[:,1:]-B/2)/(L-B);dist=((normalized[:,None,:]-generators[None,:,:])**2).sum(axis=2);owner=np.argmin(dist,axis=1);keep=np.isin(owner,mask);P=P[keep];owner=owner[keep];print('initial',len(P),flush=True)
 # Keep the entire numerical outer support, including a positive tolerance.
 retained=np.zeros(len(P),bool);halfangle=np.tan(P[:,0]/2)
 for j in mask:
  for row in state['cells'][str(j)]:
   if not row['outer_domain']:continue
   lo,hi=map(lambda x:float(F(x)),row['interval']);ix=np.flatnonzero((owner==j)&(halfangle>=lo-1e-12)&(halfangle<=hi+1e-12));poly=np.array([[float(F(x)) for x in p] for p in row['outer_domain']]);good=np.ones(len(ix),bool)
   for x,y in zip(poly,np.roll(poly,-1,axis=0)):good&=(y[0]-x[0])*(P[ix,2]-x[1])-(y[1]-x[1])*(P[ix,1]-x[0])>=-1e-10
   retained[ix[good]]=True
 P=P[retained];owner=owner[retained];print('outer-retained',len(P),flush=True);co=np.cos(P[:,0]);si=np.sin(P[:,0]);bits=np.zeros(len(P),np.uint16);ownok=np.zeros(len(P),bool)
 for j in mask:
  h=np.array([[float(F(x)) for x in p] for p in state['groups'][str(j)]]);h=h[ConvexHull(h).vertices];gap=np.full(len(P),-1e100);inside=np.ones(len(P),bool)
  for nx,ny in ((co,si),(-si,co)):
   cen=P[:,1]*nx+P[:,2]*ny;proj=h[:,0,None]*nx[None,:]+h[:,1,None]*ny[None,:];gap=np.maximum(gap,np.maximum(cen-B/2-proj.max(axis=0),proj.min(axis=0)-cen-B/2));inside&=(proj.max(axis=0)-cen<=B/2+1e-10)&(cen-proj.min(axis=0)<=B/2+1e-10)
  ownok|=(owner==j)&inside
  for x,y in zip(h,np.roll(h,-1,axis=0)):
   n=np.array([y[1]-x[1],x[0]-y[0]]);n/=np.linalg.norm(n);cen=P[:,1]*n[0]+P[:,2]*n[1];ext=B/2*(abs(co*n[0]+si*n[1])+abs(-si*n[0]+co*n[1]));proj=h@n;gap=np.maximum(gap,np.maximum(cen-ext-proj.max(),proj.min()-cen-ext))
  bits[gap<-1e-10]|=1<<j
 maskbits=sum(1<<j for j in mask);ok=ownok&((bits&(maskbits^(1<<owner)))==0);P=P[ok];owner=owner[ok];print('pose-retained',len(P),flush=True);m=PhysicalModel();R=m.capture(B-1e-10,P);mem=np.zeros((len(P),16),bool);mem[np.arange(len(P)),owner]=True
 np.savez_compressed(a.output,rows=R,poses=P,memberships=mem,legal=np.ones(len(P),bool));print('saved',a.output,flush=True)
if __name__=='__main__':main()
