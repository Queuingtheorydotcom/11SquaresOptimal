"""Exhaustive finite checks of the threshold charge identities and packing budgets."""

if not __debug__:
    raise SystemExit("Verification requires Python assertions; remove -O/-OO and unset PYTHONOPTIMIZE.")
from itertools import combinations,product
from math import comb,prod
from pathlib import Path
import json
records=[]
for n in (3,5):
 for k in range(1,n+1):
  identities=0
  for bits in product((0,1),repeat=n):
   value=sum((-1)**(j-k)*comb(j-1,k-1)*sum(prod(bits[i] for i in part) for part in combinations(range(n),j)) for j in range(k,n+1))
   assert value==int(sum(bits)>=k);identities+=1
  capacity=n//k;assignments=0
  for assignment in product(range(capacity+2),repeat=n):
   # A site is unassigned (0) or belongs to one of capacity+1 disjoint cores.
   qualifying=sum(assignment.count(core)>=k for core in range(1,capacity+2))
   assert qualifying<=capacity;assignments+=1
  records.append({'sites':n,'threshold':k,'budget':capacity,'boolean_patterns':identities,'disjoint_assignments':assignments,'absolute_coefficient_sum':sum(comb(n,j)*comb(j-1,k-1) for j in range(k,n+1))})
r={'status':'PASS_EXHAUSTIVE_THRESHOLD_IDENTITIES_AND_BUDGETS','records':records};(Path(__file__).resolve().parent/'threshold-algebra.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
