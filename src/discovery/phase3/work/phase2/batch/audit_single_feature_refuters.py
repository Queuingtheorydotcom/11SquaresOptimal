"""Reuse one exact legal-parent refuter for identical finite charge proposals.
This refutes proposals, not mask feasibility, and proves no case exclusion.
"""
from pathlib import Path
from fractions import Fraction as F
import json,hashlib
import run_batch as b
P=b.HERE/'mask234-p2batch14-packet.json';G=b.HERE/'mask234-p2batch14-gate.json';p=json.loads(P.read_text());g=json.loads(G.read_text());r=g['records'][-1];assert r['status']=='REFUTED_BY_LEGAL_PARENT';w=r['parent_witness'];cell=r['cell'];t=F(w['half_angle']);c=(1-t*t)/(1+t*t);s=2*t/(1+t*t);X,Y=map(F,w['center']);B=F(w['side']);assert F(w['charge_units'])<p['threshold_units'][cell]
def captures(pt):
 x,y=map(F,pt);return max(abs(c*(x-X)+s*(y-Y)),abs(-s*(x-X)+c*(y-Y)))<B/2
captured=[j for j,gg in enumerate(b.groups)if any(captures(pt)for pt in gg)];D=p['certificate']['coordinate_denominator'];site_capture=[captures([F(x,D),F(y,D)])for x,y in p['certificate']['sites']];assert sum(site_capture)//2==0
radius=B*(c+s)/2;L=F(p['certificate']['L']);assert radius<=X<=L-radius and radius<=Y<=L-radius
indices=[198,199,211,231,233,234,236,237,238,239,240,241,242,243,244];results=[]
for i in indices:
 q=b.packet(i);assert q['certificate']==p['certificate'] and q['threshold_units']==p['threshold_units'];assert cell in q['mask'];assert not ((set(q['mask'])-{cell})&set(captured));results.append(dict(mask=i,charge_units=0,required_units=q['threshold_units'][cell],conditional_owned_points_captured=[]))
output=dict(status='PASS_EXACT_REUSED_SINGLE_PARENT_PROPOSAL_REFUTERS',source_packet_sha256=b.sha(P),source_gate_sha256=b.sha(G),checker_sha256=b.sha(Path(__file__)),cell=cell,witness=w,captured_owned_cell_groups=captured,captured_physical_sites=site_capture,refuted_proposals=results,continuum_masks_excluded=0,global_optimality_proved=False,scope='Each listed finite LP certificate fails on the same exact legal single square. No packing existence or mask exclusion follows.')
(b.HERE/'single-feature-proposal-refuter-audit.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output))
