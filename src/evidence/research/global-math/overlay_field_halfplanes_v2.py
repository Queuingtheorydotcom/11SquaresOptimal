#!/usr/bin/env python3
"""Source-bound necessary D4 support halfplanes with direct original-vertex audit."""
from fractions import Fraction as F
from pathlib import Path
from functools import lru_cache
import hashlib,json,math,copy,time
D=Path(__file__).resolve().parent
HULLS=D/'all-overlay-support-253/supported-center-hulls.json'
OUTPUT=D/'all-overlay-support-253/field-halfplanes-v2.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def canonical_halfplanes(vertices,L,U):
 vertices=[tuple(map(F,v)) for v in vertices];B=F(L)/F(U)
 if len(vertices)<3:raise ValueError('Expected full-dimensional hull')
 result=[]
 for p,q in zip(vertices,vertices[1:]+vertices[:1]):
  nx,ny=q[1]-p[1],p[0]-q[0]
  if not nx and not ny:raise ValueError('Repeated edge vertex')
  den=math.lcm(nx.denominator,ny.denominator);ix=int(nx*den);iy=int(ny*den)
  div=math.gcd(abs(ix),abs(iy));nx,ny=ix//div,iy//div;upper=nx*p[0]+ny*p[1]
  if any(nx*v[0]+ny*v[1]>upper for v in vertices):raise ValueError('Nonconvex or non-CCW hull')
  result.append((nx,ny,upper*B))
 return result

@lru_cache(maxsize=4)
def checked_context(path=HULLS):
 path=Path(path);p=json.load(open(path));parent=path.with_name('independent-replay.json');a=json.load(open(parent));geom=D/'overlay-geometry-independent-replay.json';g=json.load(open(geom))
 if p['parent_independent_replay_sha256']!=sha(parent) or p['parent_geometry_replay_sha256']!=sha(geom):raise ValueError('Parent binding mismatch')
 if a['status']!='PASS_INDEPENDENT_FINITE_SUPPORT_REPLAY' or g['status']!='PASS_INDEPENDENT_EXACT_OVERLAY_GEOMETRY':raise ValueError('Wrong parent status')
 for receipt in [a,g]:
  for row in receipt['sources'].values():
   if row['sha256']!=sha(row['path']):raise ValueError('Live dependency hash drift')
 for key in ['cover','overlay','distance']:
  if a['sources'][key]['sha256']!=g['sources'][key]['sha256']:raise ValueError('Different geometry source')
 if a['sources']['snapshot']['sha256']!='bc3563a0c9955a561f99cbefe7278e027feff085ff6d97bc338e347f97514545':raise ValueError('Wrong1931 baseline')
 snapshot=json.load(open(a['sources']['snapshot']['path']));cover=json.load(open(a['sources']['cover']['path']));overlay=json.load(open(a['sources']['overlay']['path']));distance=json.load(open(a['sources']['distance']['path']))
 if p['U']!=distance['U']:raise ValueError('Wrong physical side')
 remaining=snapshot['remaining_canonical_mask_indices'];labels=[r['labels'] for r in overlay['regions']]
 expected={(idx,r) for idx in remaining for r,ls in enumerate(labels) if ls[0] in cover['canonical_eleven_cell_subsets'][idx]}
 observed=[(r['mask'],r['region']) for r in a['receipts']]
 if len(set(observed))!=len(observed) or set(observed)!=expected:raise ValueError('Incomplete independent support inventory')
 if set(p['hulls'])!={str(i) for i in remaining}:raise ValueError('Incomplete hull mask inventory')
 supported={idx:{cell:[] for cell in cover['canonical_eleven_cell_subsets'][idx]} for idx in remaining}
 for row in a['receipts']:
  if row['result']=='WITNESS_CHECKED':supported[row['mask']][labels[row['region']][0]].append(row['region'])
  elif row['result']!='INDEPENDENT_EXHAUSTIVE_EXCLUSION':raise ValueError('Unknown support result')
 for idx,bycell in supported.items():
  if set(p['hulls'][str(idx)])!={str(cell) for cell in bycell}:raise ValueError('Incomplete hull owner inventory')
  for cell,rr in bycell.items():
   if not rr:raise ValueError('Unexpected empty feasible owner support')
   if set(p['hulls'][str(idx)][str(cell)]['regions'])!=set(rr):raise ValueError('Hull region inventory drift')
 vertices=[[tuple(map(F,v)) for v in r['vertices']] for r in overlay['regions']]
 return p,a,g,supported,vertices

def verify_constraints(mask_index,constraints,L=F(191,50),path=HULLS):
 """Check necessary inequality on ALL independently surviving original vertices.
 Positive field coordinates are B*(1/2+(U-1)*normalized_coordinate).
 The trusted proof premise is the separately replayed1931 exclusion baseline.
 """
 p,a,g,supported,vertices=checked_context(path);U=F(p['U']);B=F(L)/U
 if B<=0 or U<=1:raise ValueError('Invalid scale')
 if mask_index not in supported:raise ValueError('Mask outside audited frontier')
 for owner,normal,h in constraints:
  owner=int(owner);nx,ny=map(F,normal);h=F(h)
  if owner not in supported[mask_index] or (nx==0 and ny==0):raise ValueError('Bad constraint owner or normal')
  upper=(h/B-(nx+ny)/2)/(U-1)
  for r in supported[mask_index][owner]:
   if any(nx*x+ny*y>upper for x,y in vertices[r]):raise ValueError('Constraint removes an independently surviving region vertex')
 return True

def necessary_constraints(mask_index,L=F(191,50),path=HULLS):
 p,*_=checked_context(path);U=F(p['U']);out=[]
 for owner,row in p['hulls'][str(mask_index)].items():
  for nx,ny,h in canonical_halfplanes(row['positive_cover_frame_vertices'],F(L),U):out.append((int(owner),(F(nx),F(ny)),h))
 verify_constraints(mask_index,out,L,path)
 return out

if __name__=='__main__':
 start=time.time();p,a,g,supported,vertices=checked_context();L=F(191,50);out={}
 for idx in supported:
  cc=necessary_constraints(idx,L);out[idx]=[{'owner':i,'normal':[str(x) for x in n],'upper':str(h)} for i,n,h in cc]
 # Reject a narrower plane, its reverse, and an omitted hull extreme vertex.
 first=next(iter(supported));cc=necessary_constraints(first,L);i,n,h=cc[0];rejected=[]
 for name,bad in [('narrower_plane',(i,n,h-F(1,10**12))),('reversed_plane',(i,tuple(-x for x in n),-h))]:
  try:verify_constraints(first,[bad],L)
  except ValueError:rejected.append(name)
  else:raise ValueError('Invalid plane accepted')
 row=p['hulls'][str(first)][str(i)];vv=row['positive_cover_frame_vertices']
 if len(vv)>3:
  badplanes=[(i,(F(nx),F(ny)),b) for nx,ny,b in canonical_halfplanes(vv[1:],L,F(p['U']))]
  try:verify_constraints(first,badplanes,L)
  except ValueError:rejected.append('deleted_extreme_vertex')
  else:raise ValueError('Deleted hull extreme vertex accepted')
 record={'status':'PASS_DIRECT_ORIGINAL_VERTEX_NECESSITY_AUDIT','L':str(L),'U':p['U'],'B':str(L/F(p['U'])),'source_hulls_sha256':sha(HULLS),'support_replay_sha256':sha(HULLS.with_name('independent-replay.json')),'geometry_replay_sha256':sha(D/'overlay-geometry-independent-replay.json'),'checker_sha256':sha(Path(__file__)),'mask_count':len(out),'owner_count':sum(len(v) for v in supported.values()),'constraint_count':sum(map(len,out.values())),'negative_controls_rejected':rejected,'seconds':time.time()-start,'scope':'All253 masks and all11 owners covered. Every listed plane checked on every independently supported original normalized region vertex. Added branch constraints are necessary under the authoritative1931 exclusion baseline.','constraints':out}
 OUTPUT.write_text(json.dumps(record,indent=2)+'\n')
 print(json.dumps({k:v for k,v in record.items() if k!='constraints'},indent=2))
