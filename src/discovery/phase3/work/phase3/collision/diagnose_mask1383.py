"""Exact universal-collision membership tests for frozen charge refuters."""
from pathlib import Path
import json,sys,time,hashlib
import validate_collision_kernel as ck
F=ck.F;geo=ck.geo
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'work/phase3/hull'))
from audit_capture_v2 import validate_core
sys.path.insert(0,str(ROOT/'work/phase3/capture/gmp'))
import fast_core_v2 as proposal
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def square(side,t):
    c,s=geo.cs(F(t));q=F(side)/2
    return [(q*(a*c-b*s),q*(a*s+b*c)) for a,b in ((-1,-1),(1,-1),(1,1),(-1,1))]
def main():
    start=time.monotonic();source=ROOT/'work/phase2/geometry/mask1383_conditional_filter_checkpoint.json'
    auditpath=ROOT/'work/phase3/hull/mask1383-full-independent-audit.json';d=json.loads(source.read_text());audit=json.loads(auditpath.read_text())
    assert audit['status']=='PASS_INDEPENDENT_RESIDUAL_KERNEL_AUDIT' and audit['source_sha256']==sha(source) and not audit['branch_condition']
    U=F(d['parent_Uplus']);B=geo.L/U;last={}
    for rnd in d['rounds']:
        for cell in rnd['cells']:
            if cell['complete']:last[cell['owner']]=(rnd['index'],cell)
    partners={}
    for owner,(ridx,cell) in last.items():
        rows=[]
        for index,row in enumerate(cell['rows']):
            domain=[p for P in row['residual_polygons'] for p in ck.parse(P)]
            if not domain:continue
            a,b=map(F,row['interval']);Q=ck.parse(proposal.polygon_core(a,b,U)['vertices']);validate_core(Q,a,b,B)
            rows.append(dict(core=Q,domain=domain,reference=dict(owner=owner,round=ridx,row=index,interval=row['interval'])))
        assert rows;partners[owner]=rows
    records=[]
    names=['mask1383_feedback1_gate.json','mask1383_feedback1_late_gate.json','mask1383_feedback2_main_gate.json']
    for name in names:
        path=ROOT/'work/phase3/geometry'/name;gate=json.loads(path.read_text());row=gate['records'][-1]
        witness=row['pieces'][-1]['parent_witness'];owner=row['cell'];center=tuple(map(F,witness['center']));t=F(witness['half_angle']);assert F(witness['side'])==B
        restriction=row['domain_restriction'];coarse=square(F(restriction['core_side']),F(restriction['reference_half_angle']))
        full=square(B-F(1,10**12),t)
        # Direct strict containment in the actual witness parent, without any
        # assumed orientation interval for the almost-full witness core.
        ct,st=geo.cs(t)
        assert all(abs(ct*x+st*y)<B/2 and abs(-st*x+ct*y)<B/2 for x,y in full)
        for kind,Qi in [('reported_row_core',coarse),('almost_full_witness_core',full)]:
            assert all(abs(ct*x+st*y)<B/2 and abs(-st*x+ct*y)<B/2 for x,y in Qi)
            blocked=[];failures=[];checks=0
            for j,rows in partners.items():
                if j==owner:continue
                violation=None
                for cut in ck.collision_halfplanes(Qi,rows):
                    checks+=1;n=cut['normal'];slack=cut['upper']-n[0]*center[0]-n[1]*center[1]
                    if slack<0:
                        violation=dict(partner=j,slack=slack,**cut);break
                if violation is None:blocked.append(j)
                else:failures.append(violation)
            records.append(dict(witness_source=str(path),witness_sha256=sha(path),owner=owner,core_kind=kind,
                                center=center,half_angle=t,blocking_partners=blocked,checked_facets=checks,first_failure_per_partner=failures))
    out=dict(status='PASS_EXACT_COLLISION_MEMBERSHIP_DIAGNOSTIC',source_sha256=sha(source),source_audit_sha256=sha(auditpath),
             records=records,dependencies={p.name:sha(p) for p in [Path(__file__),Path(ck.__file__),Path(proposal.__file__),Path(geo.__file__),ROOT/'work/phase3/hull/audit_capture_v2.py',ROOT/'work/phase3/hull/rational.py']},
             statement='Each listed blocking partner collides with this strict witness core for every pose in its complete certified residual cover. Empty blocking lists make no feasibility claim.',
             mask_exclusion_proved=False,global_optimality_proved=False,seconds=time.monotonic()-start)
    output=Path(__file__).with_name('mask1383-witness-diagnostics.json');output.write_text(json.dumps(out,default=str,indent=2)+'\n')
    print(json.dumps({**out,'records':[{k:v for k,v in r.items() if k!='first_failure_per_partner'} for r in records]},default=str,indent=2))
if __name__=='__main__':main()
