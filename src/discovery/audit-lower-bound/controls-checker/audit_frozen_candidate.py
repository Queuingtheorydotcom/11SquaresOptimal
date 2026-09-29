"""Audit frozen weights and every strict containment row; never a sweep proof."""
from fractions import Fraction as F
from hashlib import sha256
from pathlib import Path
import argparse,json,time
from audit_captured_proxy import structural_fingerprint
from exact_mixed import validate
from charge_geometry import require


def cs(t):
    denominator=1+t*t
    return (1-t*t)/denominator,2*t/denominator


def audit(path,source,output,expected_target=None):
    start=time.monotonic();raw=Path(path).read_bytes();c=json.loads(raw)
    source_raw=Path(source).read_bytes();source_c=json.loads(source_raw)
    structure=structural_fingerprint(c)
    require(structure==structural_fingerprint(source_c),'Features or coordinates changed from audited source')
    data,jobs,checker_margin=validate(c)
    L,A=F(c['L']),F(c['A']);target=L/A
    require(F(c['bound'])==target,'Reported target differs from L/A')
    if expected_target is not None:require(target==F(expected_target),'Unexpected exact target side')
    # Recompute budget independently of expansion and of the stated metadata.
    D=c['coordinate_denominator'];LD=int(L*D);budget=0
    for x,y,w in c['point_orbits']:
        require(type(w) is int and w>=0,'Invalid point weight')
        orbit={(a,b) for u,v in ((x,y),(y,x)) for a in (u,LD-u) for b in (v,LD-v)}
        budget+=len(orbit)*w
    for atom in c['charge_orbits']:
        w=atom['weight'];require(type(w) is int and w>=0,'Invalid feature weight')
        kind=atom.get('kind','threshold');capacity=(1 if kind in ('edge_or','convex_clique')
                                                else len(atom['sets'][0])//atom['threshold'])
        budget+=len(atom['sets'])*capacity*w
    require(budget==c['budget_units'],'Independent budget mismatch')
    require(11*c['minimum_units']>budget,'Counting surplus is not strict')
    cursor=F(0);margins=[];widths=[];core_sizes=[]
    for index,row in enumerate(c['entries']):
        a,b,t,B=map(F,row)
        require(a==cursor and 0<=a<b<1 and 0<=t<1 and 0<B<A,'Invalid angle interval')
        ct,st=cs(t);containment=[];envelopes=[]
        for endpoint in (a,b):
            ce,se=cs(endpoint);dot=ct*ce+st*se;cross=abs(ct*se-st*ce)
            require(dot>0 and dot>=cross,'Relative angle exceeds pi/4')
            containment.append(A-B*(dot+cross));envelopes.append(A*(ce+se)/2)
        margin=min(containment);radius=min(envelopes)
        require(margin>0,'Non-strict core row')
        require(B*(ct+st)/2<=radius<L/2,'Invalid center envelope')
        require(jobs[index]==(t,B,L/2-radius),'Checker job differs from independent row geometry')
        margins.append(margin);widths.append(b-a);core_sizes.append(B);cursor=b
    require(margins and cursor*cursor+2*cursor>1,'Angular catalogue does not pass pi/4')
    require(min(margins)==checker_margin,'Independent strict margin mismatch')
    out=dict(status='PASS_FROZEN_FEATURE_WEIGHT_AND_STRICT_CONTAINMENT_AUDIT',
             certificate_sha256=sha256(raw).hexdigest(),audited_feature_source_sha256=sha256(source_raw).hexdigest(),
             feature_structure_sha256=structure,exact_target_side=str(target),rows=len(jobs),
             physical_sites=len(data[0]),signed_terms=len(data[2]),budget_units=budget,
             minimum_required_units=c['minimum_units'],required_counting_surplus_units=11*c['minimum_units']-budget,
             absolute_expanded_units=sum(data[1])+sum(map(abs,data[3])),
             minimum_strict_core_margin=str(min(margins)),minimum_core_side=str(min(core_sizes)),
             maximum_halfangle_interval_width=str(max(widths)),angular_cover_endpoint=str(cursor),
             all_charge_sweeps_checked=False,new_bound_proved=False,
             scope='Exact weights, feature identity, geometry premises, budgets, overflow and all containment rows; a complete successful charge replay is still required',
             seconds=time.monotonic()-start)
    Path(output).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('certificate',type=Path)
    parser.add_argument('--feature-source',type=Path,required=True)
    parser.add_argument('--target',help='Expected exact target side, decimal or fraction')
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    audit(args.certificate,args.feature_source,args.output,args.target)
