"""Independent differential controls for the new weighted union coverage layer."""
from pathlib import Path
from fractions import Fraction as F
import sys,random,json,hashlib
HERE=Path(__file__).resolve().parent;AUDIT=HERE.parent/'audit';sys.path.insert(0,str(AUDIT));import independent_weighted_cover as wc
rng=random.Random(773112);P=[(F(0),F(0)),(F(1),F(0)),(F(1),F(1)),(F(0),F(1))];hist=[]
for n in range(120):
 atoms=[];raw=[];xs={F(0),F(1)};ys={F(0),F(1)}
 for k in range(rng.randint(1,6)):
  boxes=[];regions=[];w=rng.randint(1,4)
  for j in range(rng.randint(1,4)):
   xx=sorted(rng.sample(range(9),2));yy=sorted(rng.sample(range(9),2));x0,x1=[F(x,8)for x in xx];y0,y1=[F(y,8)for y in yy];boxes.append((x0,x1,y0,y1));regions.append(wc.rectangle(x0,x1,y0,y1));xs.update([x0,x1]);ys.update([y0,y1])
  if n%5==0:regions.append(regions[0]);boxes.append(boxes[0])
  atoms.append(('union',regions,w));raw.append((boxes,w))
 if n%2==0:
  cut=F(rng.randint(1,7),8);xs.add(cut)
  for box in [(F(0),cut,F(0),F(1)),(cut,F(1),F(0),F(1))]:
   w=rng.randint(1,4);atoms.append(('tiling',[wc.rectangle(*box)],w));raw.append(([box],w))
 xs=sorted(xs);ys=sorted(ys);X=sorted(set(xs+[(a+b)/2 for a,b in zip(xs,xs[1:])]));Y=sorted(set(ys+[(a+b)/2 for a,b in zip(ys,ys[1:])]));threshold=rng.randint(1,5)
 direct=min(sum(w for boxes,w in raw if any(x0<=x<=x1 and y0<=y<=y1 for x0,x1,y0,y1 in boxes)) for x in X for y in Y);observed=wc.weighted_cover(P,atoms,threshold);assert observed['passed']==(direct>=threshold),(n,direct,threshold,observed);hist.append(dict(case=n,direct_minimum=direct,threshold=threshold,passed=observed['passed']))
code=Path(wc.__file__);out=dict(status='PASS_BATCH_SOURCE_REVIEW_AND_RECTANGULAR_UNION_DIFFERENTIAL_CONTROLS',weighted_checker_sha256=hashlib.sha256(code.read_bytes()).hexdigest(),review_checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),cases=len(hist),successful_cover_cases=sum(x['passed']for x in hist),primitive_controls=wc.controls(),findings=['No union double-count: only residual outside pieces are processed by later regions of the same atom.','Discarded zero-area facets are justified by a dense generic-domain lower bound and upper semicontinuity of a finite nonnegative sum of closed-region indicators.','Floor levels k,2k,... implement floor(capture_count/k); each level is an independently additive union atom.','Overlap-summed area appears only in atom ordering and is not used as a coverage estimate.'],limitations=['Differential controls cover rational axis-aligned unions; arbitrary polygon correctness relies on the separately pinned and audited exact clipping primitives.','Extra forbidden polygons require their own caller-side validity proof; standard verify_row passes none.'],global_optimality_proved=False)
(HERE/'weighted-cover-source-review.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
