#!/usr/bin/env python3
"""Independent exhaustive finite support replay; underlying exclusions are premises."""
from pathlib import Path
import json,hashlib,time
from fractions import Fraction
D=Path(__file__).resolve().parent
R=D.parent/'phase3'
paths={
 'snapshot':R/'work/phase3/audit/overall-union-snapshot-bc3563a0c995.json',
 'cover':R/'current/research/optimality/global_capture/center-cover-symmetric-exact.json',
 'overlay':R/'work/phase2/geometry/cover_overlay_exact.json',
 'distance':R/'work/phase2/geometry/overlay_distance_pairs.json',
 'discovery':D/'candidate-overlay-support-253/results.json',
}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
snapshot=json.load(open(paths['snapshot'])); cover=json.load(open(paths['cover']))
overlay=json.load(open(paths['overlay'])); distance=json.load(open(paths['distance']))
if sha(paths['snapshot'])!='bc3563a0c9955a561f99cbefe7278e027feff085ff6d97bc338e347f97514545':
 raise ValueError('Unexpected snapshot')
if overlay['cover_sha256']!=sha(paths['cover']) or distance['overlay_sha256']!=sha(paths['overlay']):
 raise ValueError('Geometry dependency hash mismatch')
if snapshot['cover_sha256']!=sha(paths['cover']):raise ValueError('Snapshot cover mismatch')
labels=[tuple(r['labels']) for r in overlay['regions']]
if len(labels)!=220 or len(set(labels))!=220:raise ValueError('Unexpected overlay labels')
mask=lambda J:sum(1<<j for j in J)
allowed=[]
for idx in snapshot['remaining_canonical_mask_indices']:
 J=cover['canonical_eleven_cell_subsets'][idx]
 allowed.extend([mask(J),mask([15-j for j in J])])
if len(set(allowed))!=506:raise ValueError('Unexpected surviving raw mask count')
contains=[sum(1<<k for k,M in enumerate(allowed) if M&(1<<j)) for j in range(16)]
alltargets=(1<<len(allowed))-1
initial=[sum(1<<r for r,l in enumerate(labels) if l[0]==j) for j in range(16)]
compat=[0]*len(labels)
banned={tuple(sorted(e['regions'])) for e in distance['pairs']}
for a in range(len(labels)):
 for b in range(len(labels)):
  if (min(a,b),max(a,b)) not in banned and all(labels[a][g]!=labels[b][g] for g in range(4)):
   compat[a]|=1<<b

def bits(M):
 while M:
  low=M&-M;r=low.bit_length()-1;M-=low;yield r

def solve(idx,forced):
 cells=cover['canonical_eleven_cell_subsets'][idx]
 dom={j:(1<<forced if j==labels[forced][0] else initial[j]) for j in cells}
 nodes=0
 def dfs(dom,targets):
  nonlocal nodes;nodes+=1
  if not dom:return []
  filtered={}
  for j,domain in dom.items():
   filtered[j]=sum(1<<r for r in bits(domain) if all(targets[g]&contains[labels[r][g]] for g in range(4)))
   if not filtered[j]:return None
  j=min(filtered,key=lambda k:filtered[k].bit_count())
  for r in bits(filtered[j]):
   nd={k:v&compat[r] for k,v in filtered.items() if k!=j}
   if any(v==0 for v in nd.values()):continue
   nt=tuple(targets[g]&contains[labels[r][g]] for g in range(4))
   ans=dfs(nd,nt)
   if ans is not None:return [r]+ans
  return None
 sol=dfs(dom,(alltargets,)*4)
 return sol,nodes

def validate_witness(idx,forced,sol):
 if len(sol)!=11 or forced not in sol:raise ValueError('Missing forced region')
 if set(labels[r][0] for r in sol)!=set(cover['canonical_eleven_cell_subsets'][idx]):raise ValueError('Wrong cells')
 for g in range(4):
  ls=[labels[r][g] for r in sol]
  if len(set(ls))!=11 or mask(ls) not in allowed:raise ValueError('Excluded view')
 for a in sol:
  for b in sol:
   if a<b and (a,b) in banned:raise ValueError('Distance conflict')

start=time.time();rows=json.load(open(paths['discovery']))['rows'];receipts=[]
for row in rows:
 idx,r=row['mask'],row['region']
 if row['status']=='SURVIVES':
  validate_witness(idx,r,row['witness']);receipts.append({'mask':idx,'region':r,'result':'WITNESS_CHECKED'});continue
 if row['status']!='EXCLUDED':raise ValueError('Unresolved query')
 sol,nodes=solve(idx,r)
 if sol is not None:raise ValueError(f'Discovery exclusion refuted: {idx},{r},{sol}')
 receipts.append({'mask':idx,'region':r,'result':'INDEPENDENT_EXHAUSTIVE_EXCLUSION','nodes':nodes})

# Exact new coordinate bounds in the same positive cover frame [0,U]^2.
U=Fraction(distance['U']);scale=U-1
bounds={}
for idx in [438,999,1462,1659]:
 bounds[idx]={}
 for cell in cover['canonical_eleven_cell_subsets'][idx]:
  rr=[r['region'] for r in rows if r['mask']==idx and r['cell']==cell and r['status']=='SURVIVES']
  pts=[(Fraction(v[0])*scale+Fraction(1,2),Fraction(v[1])*scale+Fraction(1,2)) for r in rr for v in overlay['regions'][r]['vertices']]
  bounds[idx][cell]={'regions':rr,'x':[str(min(x for x,y in pts)),str(max(x for x,y in pts))], 'y':[str(min(y for x,y in pts)),str(max(y for x,y in pts))]}
record={'status':'PASS_INDEPENDENT_FINITE_SUPPORT_REPLAY','scope':'Conditional only on exact cover, exact overlay/distance lemma, and independently established1931 exclusions. Does not replay those geometric or exclusion premises. No global capture established.','sources':{k:{'path':str(p),'sha256':sha(p)} for k,p in paths.items()},'checker_sha256':sha(Path(__file__)),'queries':len(rows),'excluded_region_alternatives':sum(r['result']=='INDEPENDENT_EXHAUSTIVE_EXCLUSION' for r in receipts),'surviving_witnesses':sum(r['result']=='WITNESS_CHECKED' for r in receipts),'receipts':receipts,'positive_cover_frame_bounds':bounds,'seconds':time.time()-start}
(D/'candidate-overlay-support-253/independent-replay.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k not in ['sources','receipts','positive_cover_frame_bounds']},indent=2))
