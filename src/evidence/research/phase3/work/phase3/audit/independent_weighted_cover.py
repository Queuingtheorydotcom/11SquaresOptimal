#!/usr/bin/env python3
"""Independent weighted polygon-arrangement coverage, using exact rationals.

All charge atoms have nonnegative integer weight. A TRUE atom is a convex
median-halfplane region. A threshold atom is a union of capture boxes, counted
once. A floor atom is the sum of threshold levels k,2k,... . A cell carries its
accumulated charge; only cells below the required threshold are retained.
No producer sweep, staircase, low-cell routine, or patcher is imported.
"""
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
import hashlib,sys
FROZEN=Path(__file__).resolve().parents[2]/'phase2/audit/independent_patch_cover.py'
need_sha='d8b5d070d0de4027088a69ce8e8f1872d64e88d9cec8e71b669cdb33d6f947a2'
if hashlib.sha256(FROZEN.read_bytes()).hexdigest()!=need_sha:raise ValueError('frozen independent polygon primitives changed')
sys.path.insert(0,str(FROZEN.parent))
from independent_patch_cover import need,area2,convex_hull,clip,intersection,subtract,true_rows,controls as primitive_controls

def rectangle(x0,x1,y0,y1):
 return [(F(1),F(0),x1),(F(-1),F(0),-x0),(F(0),F(1),y1),(F(0),F(-1),-y0)]
def subset_box(points,half):
 return rectangle(max(x for x,y in points)-half,min(x for x,y in points)+half,max(y for x,y in points)-half,min(y for x,y in points)+half)
def apply_atom(pieces,regions,weight,threshold):
 need(type(weight) is int and weight>0,'positive integer atom required')
 out=[]
 for P,charge in pieces:
  outside=[P];inside=[]
  for rows in regions:
   nextoutside=[]
   for Q in outside:
    I=intersection(Q,rows)
    if I:
     if charge+weight<threshold:inside.append((I,charge+weight))
     nextoutside.extend(subtract(Q,rows))
    else:nextoutside.append(Q)
   outside=nextoutside
   if not outside:break
  out.extend(inside);out.extend((Q,charge) for Q in outside)
 return out

def weighted_cover(domain,atoms,threshold,max_pieces=200000):
 need(type(threshold) is int and threshold>=0,'invalid integer threshold')
 need(area2(domain)>0,'independent weighted domain must have positive area')
 if threshold==0:return dict(passed=True,status='NONNEGATIVE_ZERO_THRESHOLD',used_atoms=0,maximum_pieces=1)
 eligible=[]
 for kind,regions,w in atoms:
  need(type(w) is int and w>=0,'negative/noninteger atom weight')
  if not w:continue
  active=[];area=F(0)
  for rows in regions:
   I=intersection(domain,rows)
   if I:active.append(rows);area+=area2(I)
  if active:eligible.append((kind,active,w,area))
 eligible.sort(key=lambda x:(min(x[2],threshold)*x[3]),reverse=True)
 pieces=[(domain,0)];maximum=1;counts={};used=0
 for kind,regions,w,_ in eligible:
  pieces=apply_atom(pieces,regions,w,threshold);used+=1;maximum=max(maximum,len(pieces));counts[kind]=counts.get(kind,0)+1
  if not pieces:break
  if len(pieces)>max_pieces:return dict(passed=False,status='INDEPENDENT_PIECE_LIMIT',remaining_pieces=len(pieces),maximum_pieces=maximum)
 return dict(passed=not pieces,status='PASS_INDEPENDENT_WEIGHTED_COVER' if not pieces else 'UNCOVERED_WEIGHTED_PIECES',
  eligible_atoms=len(eligible),used_atoms=used,used_atom_types=counts,maximum_pieces=maximum,
  remaining_pieces=len(pieces),minimum_retained_charge=min((q for p,q in pieces),default=None))

def controls():
 passed=primitive_controls();P=[(F(0),F(0)),(F(1),F(0)),(F(1),F(1)),(F(0),F(1))]
 allbox=rectangle(0,1,0,1);left=rectangle(0,F(1,2),0,1);right=rectangle(F(1,2),1,0,1)
 need(weighted_cover(P,[('a',[allbox],2)],2)['passed'],'weight2 threshold2 failure')
 need(not weighted_cover(P,[('a',[allbox],2)],3)['passed'],'insufficient weight accepted')
 need(weighted_cover(P,[('a',[left],2),('b',[right],2)],2)['passed'],'weighted adjoining closed cells fail')
 need(not weighted_cover(P,[('a',[allbox,allbox],1)],2)['passed'],'one union atom counted twice')
 need(weighted_cover(P,[('a',[allbox],1),('b',[allbox],1)],2)['passed'],'independent atoms not additive')
 gap=rectangle(F(1,2)+F(1,10**50),1,0,1)
 need(not weighted_cover(P,[('a',[left],7),('b',[gap],7)],7)['passed'],'tiny weighted gap lost')
 # Two captured sites produce floor(count/1)=2, but threshold(count>=1)=1.
 need(not weighted_cover(P,[('threshold',[allbox,allbox],1)],2)['passed'],'threshold capacity incorrectly multiplied')
 need(weighted_cover(P,[('floor1',[allbox,allbox],1),('floor2',[allbox],1)],2)['passed'],'floor threshold-level decomposition fails')
 return passed+['weight and threshold2','insufficient weighted charge rejected','closed weighted adjacency',
  'overlapping union atom counted once','distinct atoms additive','10^-50 weighted gap','floor versus threshold levels']

def row_atoms(packet,row,domain_polygon=None,extra_forbidden_polygons=None):
 i=row['cell'];gamma=packet['threshold_units'][i];U=F(packet['parent_Uplus']);L=F(191,50);B=L/U
 core=F(row['core_side']);t=F(row['reference_half_angle']);c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);half=core/2
 rotate=lambda p:(c*(p[0]-L/2)+s*(p[1]-L/2),-s*(p[0]-L/2)+c*(p[1]-L/2))
 cert=packet['certificate'];D=cert['coordinate_denominator'];sites=[rotate(tuple(F(v,D) for v in p)) for p in cert['sites']];atoms=[]
 for f in cert['features']:
  points=[sites[j] for j in f['indices']];k=f['threshold'];w=f['weight'];kind=f['kind']
  if not w:continue
  if kind=='majority_hull':
   need(len(points)==2*k-1,'invalid TRUE support');atoms.append(('TRUE',[true_rows(points,half)],w))
  elif kind in ('threshold','floor'):
   levels=[k] if kind=='threshold' else range(k,len(points)+1,k)
   for level in levels:atoms.append((kind,[subset_box(part,half) for part in combinations(points,level)],w))
  else:raise ValueError('unknown physical feature kind')
 for p,w in zip(sites,cert['point_weights']):
  if w:atoms.append(('point',[subset_box([p],half)],w))
 for owner in packet.get('conditional_owner_support',packet['mask']):
  if owner!=i:
   for p in packet['ownership_points_field'][owner]:atoms.append(('owned_point',[subset_box([rotate(tuple(map(F,p)))],half)],gamma))
 if extra_forbidden_polygons:
  for P in extra_forbidden_polygons:
   P=convex_hull([rotate(tuple(map(F,p))) for p in P]);rows=[]
   for p,q in zip(P,P[1:]+P[:1]):
    a=q[1]-p[1];b=p[0]-q[0];rows.append((a,b,a*p[0]+b*p[1]))
   atoms.append(('conditional_owned_hull',[rows],gamma))
 return rotate,atoms

def verify_row(packet,cover,row):
 i=row['cell'];gamma=packet['threshold_units'][i];U=F(packet['parent_Uplus']);L=F(191,50);B=L/U;H=F(row['parent_center_halfwidth'])
 world=convex_hull([tuple(L/2+B*(U-1)*(F(v)-F(1,2)) for v in p) for p in cover['cells'][i]['vertices']])
 for a,b in ((F(1),F(0)),(F(0),F(1))):
  world=clip(world,(a,b,L/2+H));world=clip(world,(-a,-b,-L/2+H))
 need(area2(world)>0,'degenerate legal cell envelope')
 rotate,atoms=row_atoms(packet,row);domain=[rotate(p) for p in world];result=weighted_cover(domain,atoms,gamma)
 need(result['passed'],'independent weighted coverage failed: '+str(result))
 return dict(cell=i,interval=row['interval'],threshold_units=gamma,initial_domain_area_twice=str(area2(domain)),**result,
  boundary_argument='Finite nonnegative weighted sum of closed-set indicators is upper semicontinuous. A dense-domain lower bound therefore extends to all closed-domain boundary points.')

if __name__=='__main__':
 print(controls())
