"""Exact connected components of axis low-cell closed rectangle cover."""
import json
from fractions import Fraction as F
from pathlib import Path
p=Path(__file__).resolve().parent
j=json.loads((p/'axis-low-cells.json').read_text());boxes=[[F(r[k]) for k in ['x0','x1','y0','y1']] for r in j['boxes']];parent=list(range(len(boxes)))
def root(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
for i,a in enumerate(boxes):
 for k,b in enumerate(boxes[:i]):
  if max(a[0],b[0])<=min(a[1],b[1]) and max(a[2],b[2])<=min(a[3],b[3]):parent[root(i)]=root(k)
comps={}
for i in range(len(boxes)):comps.setdefault(root(i),[]).append(i)
res=[]
for inds in comps.values():
 region=[min(boxes[i][0] for i in inds),max(boxes[i][1] for i in inds),min(boxes[i][2] for i in inds),max(boxes[i][3] for i in inds)]
 res.append({'box_indices':inds,'outer_rectangle':list(map(str,region)),'outer_rectangle_decimal':list(map(float,region)),'minimum_units':min(j['boxes'][i]['minimum_units'] for i in inds)})
res.sort(key=lambda x:x['outer_rectangle_decimal'])
out={'status':'EXACT_COMPONENT_COVER_AXIS_ONLY','component_count':len(res),'source':'axis-low-cells.json','components':res,'scope':'Closed-box connectivity and outer bounding rectangles. Over-approximates low-charge set at event boundaries. No claim that a hypothetical eleven-square packing contains an axis square.'}
(p/'axis-components.json').write_text(json.dumps(out,indent=2)+'\n')
print('components',len(res))
for c in res:print(len(c['box_indices']),c['outer_rectangle_decimal'],c['minimum_units'])
