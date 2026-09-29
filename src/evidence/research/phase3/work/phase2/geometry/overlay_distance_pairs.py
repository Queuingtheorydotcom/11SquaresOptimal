from pathlib import Path
from fractions import Fraction as F
import json,hashlib,numpy as np
if not __debug__:raise SystemExit('Exact checker requires assertions.')
H=Path(__file__).resolve().parent;d=json.loads((H/'cover_overlay_exact.json').read_text());R=d['regions'];U=F(387708359002281417731,10**20)
verts=[[tuple(map(F,p)) for p in r['vertices']] for r in R];V=[np.array([[float(x) for x in p] for p in v]) for v in verts];pairs=[]
for i in range(len(R)):
 for j in range(i):
  if any(x==y for x,y in zip(R[i]['labels'],R[j]['labels'])):continue
  vv=V[i][:,None,:]-V[j][None,:,:]
  if np.max(np.sum(vv*vv,axis=2))*float((U-1)**2)>1+1e-8:continue
  maximum=max(sum((x-y)**2 for x,y in zip(p,q)) for p in verts[i] for q in verts[j])*(U-1)**2
  if maximum<1:pairs.append(dict(regions=[j,i],maximum_squared_center_distance=maximum))
print('certified distance incompatibilities',len(pairs),flush=True)
out=dict(status='PASS_EXACT_OVERLAY_DISTANCE_INCOMPATIBILITIES',U=U,overlay_sha256=hashlib.sha256((H/'cover_overlay_exact.json').read_bytes()).hexdigest(),checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),pairs=pairs,scope='Every listed pair has maximum center distance strictly below1 and cannot contain two unit square centers. Numeric screening only omits candidate exclusions; all accepted exclusions use exact vertex comparisons.')
(H/'overlay_distance_pairs.json').write_text(json.dumps(out,indent=2,default=str))
cover=json.loads((H.parents[2]/'current/research/optimality/global_capture/center-cover-symmetric-exact.json').read_text());patterns=[[1,2,4,5,6,7,11],[1,2,4,5,8,9,13]];patterns += [[15-i for i in p] for p in patterns[:]]
with (H/'overlay_csp_input.txt').open('w') as f:
 f.write(f'{len(R)} {len(pairs)} {len(cover["canonical_eleven_cell_subsets"])} {len(patterns)}\n')
 for p in patterns:f.write(str(sum(1<<j for j in p))+'\n')
 for r in R:f.write(' '.join(map(str,r['labels']))+'\n')
 for p in pairs:f.write(' '.join(map(str,p['regions']))+'\n')
 for m in cover['canonical_eleven_cell_subsets']:f.write(str(sum(1<<j for j in m))+'\n')
