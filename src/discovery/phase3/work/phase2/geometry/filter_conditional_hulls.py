"""Numerical finite-pose filtering by proved conditional owned hulls.
The output is discovery data, not an exact continuum exclusion.
"""
from pathlib import Path
from fractions import Fraction as F
import numpy as np,json,hashlib
from scipy.spatial import ConvexHull
H=Path(__file__).resolve().parent;BASE=H.parents[2]/'current/research/optimality/deficit_geometry/physical_features';source=H/'mask1383_residual_compact.json';raw=source.read_bytes();(H/'mask1383_conditional_filter_checkpoint.json').write_bytes(raw);d=json.loads(raw);P=np.load(BASE/'owned-tight/poses.npy');B=float(F(d['parent_side']))-1e-10;c=np.cos(P[:,0]);s=np.sin(P[:,0]);bits=np.zeros(len(P),np.uint16);counts=[]
for owner in d['mask']:
 vertices=np.array([[float(F(x)) for x in p] for p in d['owned_points'][owner]]);h=vertices[ConvexHull(vertices).vertices];gap=np.full(len(P),-1e100)
 for a,b in zip(h,np.roll(h,-1,axis=0)):
  n=np.array([b[1]-a[1],a[0]-b[0]]);n/=np.linalg.norm(n);q=P[:,1]*n[0]+P[:,2]*n[1];extent=B/2*(abs(c*n[0]+s*n[1])+abs(-s*n[0]+c*n[1]));proj=h@n;gap=np.maximum(gap,np.maximum(q-extent-proj.max(),proj.min()-q-extent))
 for nx,ny in [(c,s),(-s,c)]:
  q=P[:,1]*nx+P[:,2]*ny;proj=h[:,0,None]*nx[None,:]+h[:,1,None]*ny[None,:];gap=np.maximum(gap,np.maximum(q-B/2-proj.max(axis=0),proj.min(axis=0)-q-B/2))
 hit=gap<-1e-10;bits[hit]|=1<<owner;counts.append([owner,int(hit.sum()),len(h)])
np.save(H/'mask1383_conditional_hull_capture_bits.npy',bits);(H/'mask1383_conditional_filter_source.json').write_text(json.dumps(dict(status='NUMERICAL_CONDITIONAL_HULL_POSE_FILTER_ONLY',source_sha256=hashlib.sha256(raw).hexdigest(),source_rounds=len(d['rounds']),owned_points=d['owned_points'],mask=d['mask'],counts=counts,continuum_masks_excluded=0,global_optimality_proved=False),indent=2));print(counts)
