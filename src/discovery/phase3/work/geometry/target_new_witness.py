from wall_kernel import *
from fractions import Fraction as F
import sys
path=Path(sys.argv[1]);d=json.loads(path.read_text());r=[r for r in d['records'] if 'parent_witness' in r][-1];w=r['parent_witness'];q=np.array([float(F(x)/B) for x in w['center']]);t=float(F(w['half_angle']));c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);ns=[np.array([c,s]),np.array([-s,c])];D=json.load(open('work/geometry/wall_kernel_discovery.json'));sites=[]
for row in D:
 i=row['cell']
 if i not in d['mask'] or i==r['cell']:continue
 kw=np.array(row['polygon'])
 for n in ns:
  for sign in [-1,1]:kw=clip(kw,sign*n,.5+q@(sign*n))
 if len(kw):
  p=[str(round(sum(v[k] for v in kw)/len(kw)*10**10))+'/10000000000' for k in range(2)];sites.append({'owner':i,'unit_point':p});print(i,len(kw),p)
json.dump({'sites':sites},open('work/geometry/wall_next_candidates.json','w'),indent=2)
print('total',len(sites),'witness',r['cell'],w['half_angle'])
