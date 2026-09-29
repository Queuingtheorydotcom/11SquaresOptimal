#!/usr/bin/env python3
"""Exact source-bound halfplanes for use as necessary initial branch constraints."""
from fractions import Fraction as F
from pathlib import Path
import hashlib,json,math
D=Path(__file__).resolve().parent
HULLS=D/'all-overlay-support-253/supported-center-hulls.json'
OUTPUT=D/'all-overlay-support-253/field-halfplanes.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def canonical_halfplanes(vertices,L,U):
 """CCW polygon in positive unit-square frame -> primitive normal in field frame.
 Return (n_x,n_y,h) with n_x*x+n_y*y <= h for field coordinates x,y.
 """
 vertices=[tuple(map(F,v)) for v in vertices]; B=F(L)/F(U)
 if len(vertices)<3:raise ValueError('Expected full-dimensional hull')
 result=[]
 for p,q in zip(vertices,vertices[1:]+vertices[:1]):
  nx,ny=q[1]-p[1],p[0]-q[0]
  if nx==0 and ny==0:raise ValueError('Repeated edge vertex')
  den=math.lcm(nx.denominator,ny.denominator);ix=int(nx*den);iy=int(ny*den)
  div=math.gcd(abs(ix),abs(iy));nx,ny=ix//div,iy//div
  upper=F(nx)*p[0]+F(ny)*p[1]
  if any(nx*v[0]+ny*v[1]>upper for v in vertices):raise ValueError('Invalid CCW convex hull')
  result.append((nx,ny,upper*B))
 return result

def load_checked_hulls(path=HULLS):
 path=Path(path);p=json.load(open(path));parent=path.with_name('independent-replay.json')
 if p['parent_independent_replay_sha256']!=sha(parent):raise ValueError('Support receipt drift')
 a=json.load(open(parent))
 if a['status']!='PASS_INDEPENDENT_FINITE_SUPPORT_REPLAY':raise ValueError('Missing exhaustive replay')
 geom=D/'overlay-geometry-independent-replay.json'
 if p['parent_geometry_replay_sha256']!=sha(geom):raise ValueError('Geometry receipt drift')
 g=json.load(open(geom))
 if g['status']!='PASS_INDEPENDENT_EXACT_OVERLAY_GEOMETRY':raise ValueError('Missing geometry replay')
 for key in ['cover','overlay','distance']:
  if a['sources'][key]['sha256']!=g['sources'][key]['sha256']:raise ValueError('Mismatched geometry sources')
 # Pin the concrete baseline; its prior source-distinct1931 proof replay is a premise.
 if a['sources']['snapshot']['sha256']!='bc3563a0c9955a561f99cbefe7278e027feff085ff6d97bc338e347f97514545':raise ValueError('Wrong baseline')
 return p

def necessary_constraints(mask_index,L=F(191,50),path=HULLS):
 p=load_checked_hulls(path);U=F(p['U']);out=[]
 for owner,row in p['hulls'][str(mask_index)].items():
  for nx,ny,h in canonical_halfplanes(row['positive_cover_frame_vertices'],F(L),U):
   out.append((int(owner),(F(nx),F(ny)),h))
 return out

def verify_constraints(mask_index,constraints,L=F(191,50),path=HULLS):
 """Each requested constraint must be one of the exact necessary hull planes.
 This permits a subset and equivalent positive rational rescaling.
 """
 expected=necessary_constraints(mask_index,L,path)
 def normalise(c):
  owner,n,h=c;nx,ny=map(F,n);h=F(h)
  if nx==0 and ny==0:raise ValueError('Zero constraint normal')
  s=abs(nx) if nx else abs(ny)
  return int(owner),nx/s,ny/s,h/s
 allowed={normalise(c) for c in expected}
 for c in constraints:
  if normalise(c) not in allowed:raise ValueError('Constraint is not a certified necessary hull plane')
 return True

if __name__=='__main__':
 p=load_checked_hulls();L=F(191,50);out={}
 for idx in p['hulls']:
  cc=necessary_constraints(int(idx),L)
  verify_constraints(int(idx),cc,L)
  out[idx]=[{'owner':i,'normal':[str(x) for x in n],'upper':str(h)} for i,n,h in cc]
 # A tighter inequality and a reversed inequality must both be refused.
 first=int(next(iter(out)));good=necessary_constraints(first,L);i,n,h=good[0]
 controls=[]
 for bad in [(i,n,h-F(1,10**12)),(i,tuple(-x for x in n),-h)]:
  try:verify_constraints(first,[bad],L)
  except ValueError:controls.append(True)
  else:raise ValueError('Unsound necessary-constraint control accepted')
 record={'status':'PASS_EXACT_NECESSARY_FIELD_HALFPLANES','L':str(L),'U':p['U'],'B':str(L/F(p['U'])),'source_hulls_sha256':sha(HULLS),'checker_sha256':sha(Path(__file__)),'mask_count':len(out),'constraint_count':sum(map(len,out.values())),'negative_controls_rejected':len(controls),'scope':'Every listed halfplane is necessary under the authoritative1931 excluded-mask baseline and audited D4 overlay support theorem. Constraints may be added as branch antecedents; a contradiction conditional on them excludes that mask under the same explicit baseline.','constraints':out}
 OUTPUT.write_text(json.dumps(record,indent=2)+'\n')
 print(json.dumps({k:v for k,v in record.items() if k!='constraints'},indent=2))
