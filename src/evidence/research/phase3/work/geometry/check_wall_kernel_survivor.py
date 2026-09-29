"""Exact finite necessary-parent intersection refuting common-point repairs.
Each selected legal parent in owner cell contains every mandatory ownership
point for that cell. An empty intersection with the supplied deficit parent
therefore proves that deficit parent avoids the complete ownership kernel.
"""
from pathlib import Path
from fractions import Fraction as F
import json,argparse,hashlib,sys
import validate_wall_sites as w
if not __debug__:raise SystemExit('Exact checker requires assertions.')

def dot(a,b):return sum(x*y for x,y in zip(a,b))
def clip(poly,n,b):
 out=[]
 for p,q in zip(poly,poly[1:]+poly[:1]):
  a=dot(p,n)-b;c=dot(q,n)-b;ina=a<=0;inc=c<=0
  if ina:out.append(p)
  if ina!=inc:
   r=a/(a-c);out.append(tuple(x+r*(y-x) for x,y in zip(p,q)))
 clean=[]
 for p in out:
  if not clean or p!=clean[-1]:clean.append(p)
 if len(clean)>1 and clean[0]==clean[-1]:clean.pop()
 return clean

def main():
 ap=argparse.ArgumentParser();ap.add_argument('result',type=Path);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
 assert hashlib.sha256(w.COVER.read_bytes()).hexdigest()==w.EXPECTED_COVER
 cover=json.loads(w.COVER.read_text());d=json.loads(args.result.read_text());row=[r for r in d['records'] if 'parent_witness' in r][-1];parent=row['parent_witness'];q=tuple(F(v)/w.B for v in parent['center']);c,s=w.trig(F(parent['half_angle']));witness=[(q[0]+a*c/2-b*s/2,q[1]+a*s/2+b*c/2) for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]]
 assert F(parent['side'])==w.B and d['parent_Uplus']==str(w.U)
 records=[]
 # Early cardinals and diagonal, then increasingly fine rational halfangles.
 angles=list(dict.fromkeys([F(0),F(1),F(2,5),F(1,2)]+[F(i,32) for i in range(33)]+[F(i,1000) for i in range(1001)]))
 for j in d['mask']:
  if j==row['cell']:continue
  ownerpoly=[tuple(F(1,2)+(w.U-1)*F(v) for v in p) for p in cover['cells'][j]['vertices']]
  intersection=witness[:];cuts=[]
  for t in angles:
   centers=w.envelope(ownerpoly,t,t);ct,st=w.trig(t)
   if not centers:continue
   for n in [(ct,st),(-ct,-st),(-st,ct),(st,-ct)]:
    center=min(centers,key=lambda p:dot(p,n));bound=F(1,2)+dot(center,n)
    before=intersection;intersection=clip(intersection,n,bound)
    if intersection!=before:cuts.append(dict(half_angle=t,legal_center=center,normal=n,bound=bound))
    if not intersection:break
   if not intersection:break
  record=dict(owner=j,disjoint=not intersection,cuts=cuts,remaining_polygon=intersection)
  records.append(record);print(j,'disjoint',not intersection,'cuts',len(cuts),flush=True)
 out=dict(status='PASS_EXACT_COMPLETE_OWNERSHIP_KERNEL_SURVIVOR' if all(r['disjoint'] for r in records) else 'UNRESOLVED',witness_source=str(args.result),witness_source_sha256=hashlib.sha256(args.result.read_bytes()).hexdigest(),checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),ownership_checker_sha256=hashlib.sha256(Path(w.__file__).read_bytes()).hexdigest(),cover_sha256=w.EXPECTED_COVER,U=w.U,parent_side=w.B,witness_cell=row['cell'],witness=parent,records=records,scope='Every listed cut is supported by a legal unit parent centered in the owner cell. Every universally mandatory point lies in each such parent. Empty intersection proves the deficit parent avoids the entire wall-aware mandatory-point kernel of that owner. This is an obstruction for this frozen one-body field, not a feasible multi-square packing.',global_optimality_proved=False,continuum_masks_excluded=0)
 args.output.write_text(json.dumps(out,indent=2,default=str))
if __name__=='__main__':main()
