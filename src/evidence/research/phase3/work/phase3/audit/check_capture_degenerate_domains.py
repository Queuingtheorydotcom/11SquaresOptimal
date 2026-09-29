#!/usr/bin/env python3
"""Companion controls and scope check for the frozen branch hull replayer."""
import sys,json,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'hull'))
import audit_capture as ac
F=ac.F
square=[(F(0),F(0)),(F(1),F(0)),(F(1),F(1)),(F(0),F(1))]
point=[(F(1,2),F(1,2))]
segment=[(F(0),F(0)),(F(1),F(1))]
def safe_clip(p,extra):
 if not p:return []
 H=ac.geo.gift_hull(p)
 rows=ac.geo.polygon_rows(H)+[(1,0,max(x for x,y in H)),(-1,0,-min(x for x,y in H)),(0,1,max(y for x,y in H)),(0,-1,-min(y for x,y in H))]
 return ac.geo.intersection_polygon(rows+extra)
assert safe_clip(point,[])==point
assert safe_clip(segment,[])==segment
assert safe_clip(segment,[(1,0,F(1,2))])==[(F(0),F(0)),(F(1,2),F(1,2))]
assert safe_clip(point,[(1,0,F(1,3))])==[]
assert safe_clip(square,[])==square
branch=HERE.parent/'capture/mask438-far15y-gmp.json'
rootaudit=HERE.parent/'hull/mask438-root14-independent-audit.json'
d=json.loads(branch.read_text());source=ac.locate(d['source']['path'],branch)
r=ac.Replay(source,rootaudit)
checked=0;degenerate=[];files=[]
def check(p,label):
 global checked
 checked+=1
 if p and ac.geo.twice_area(ac.poly(p))==0:degenerate.append(label)
for owner,rows in r.initial['cells'].items():
 for i,row in enumerate(rows):check(row['outer_domain'],f'root:{owner}:{i}:outer')
def scan(path):
 d=json.loads(path.read_text());files.append(dict(path=str(path),sha256=ac.sha(path)))
 if d['parent']:scan(ac.locate(d['parent']['path'],path))
 for step in d['steps']:
  for j,row in enumerate(step['rows']):
   for name in ['input_domain','outer_domain']:check(row[name],f"{d['node_id']}:{step['index']}:{j}:{name}")
scan(branch)
out=dict(status='PASS_ACTUAL_FROZEN_CAPTURE_DOMAINS_NONDEGENERATE' if not degenerate else 'DEGENERATE_DOMAINS_REQUIRE_V2_REPLAY',checker_sha256=ac.sha(Path(__file__)),frozen_capture_checker_sha256=ac.sha(Path(ac.__file__)),root_source_sha256=ac.sha(source),root_audit_sha256=ac.sha(rootaudit),branch_files=files,checked_domains=checked,nonempty_degenerate_domains=degenerate,safe_clipping_controls=5,frozen_clipping_point_control_passed=ac.clipped(point,[])==point,frozen_clipping_segment_control_passed=ac.clipped(segment,[])==segment,scope='Companion audit only. A known general degeneracy gap in frozen clipped() is inactive on these exact branch data iff all listed old outer domains are positive area or empty. Root and branch geometric replay remain separate prerequisites.')
(HERE/'capture-degenerate-domains-companion-audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
