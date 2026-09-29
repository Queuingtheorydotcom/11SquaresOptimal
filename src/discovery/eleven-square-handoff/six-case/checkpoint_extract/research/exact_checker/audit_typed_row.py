"""Independent raw logical charge and actual-type audit of recorded parents."""
from fractions import Fraction as F
from hashlib import sha256
from pathlib import Path
import argparse,json


def audit(directory,row=0):
    base=Path(directory);reports=[]
    for role in ('A','B'):
        raw=(base/f'vector-{role}.json').read_bytes();c=json.loads(raw)
        record=json.loads((base/f'row-{row:05d}-{role}.json').read_text())
        r=record['exact_parent_domain_probe']
        t=F(r['half_angle_t']);cc=(1-t*t)/(1+t*t);ss=2*t/(1+t*t)
        L,A=F(c['L']),F(c['A']);D=c['coordinate_denominator'];LD=int(L*D)
        radius=A*(abs(cc)+abs(ss))/2
        window=A*F(c['conditional_type_probe']['window_side_unit'])
        points=[];weights=[]
        for x,y,w in c['point_orbits']:
            orbit=sorted({(a,b) for u,v in ((x,y),(y,x)) for a in (u,LD-u) for b in (v,LD-v)})
            points.extend(orbit);weights.extend([w]*len(orbit))
        for domain in r['domains']:
            for stored in domain.get('parent_diagnostics',[])[:1]:
                x,y=map(F,stored['center'])
                if not(radius<=x<=L-radius and radius<=y<=L-radius):raise ValueError('Parent not contained')
                count=sum(ox<=x-radius and x+radius<=ox+window and oy<=y-radius and y+radius<=oy+window
                    for ox,oy in ((0,0),(L-window,0),(0,L-window),(L-window,L-window)))
                kind={1:'single',2:'double',4:'all4'}[count]
                inside=[]
                for px,py in points:
                    dx=F(px,D)-x;dy=F(py,D)-y
                    inside.append(abs(cc*dx+ss*dy)<=A/2 and abs(-ss*dx+cc*dy)<=A/2)
                total=sum(w for w,b in zip(weights,inside) if b)
                for atom in c['charge_orbits']:
                    w=atom['weight']
                    if not w:continue
                    groups=atom['sets'];rule=atom.get('kind','threshold');k=atom.get('threshold')
                    for j,group in enumerate(groups):
                        hits=sum(inside[i] for i in group)
                        if rule=='floor':value=hits//k
                        elif rule=='threshold':value=int(hits>=k)
                        else:
                            if rule not in ('edge_or','convex_clique'):raise ValueError('Unsupported logical rule')
                            supports=atom.get('edge_sets',[[] for _ in groups])[j]+atom.get('support_sets',[[] for _ in groups])[j]
                            value=int((rule=='convex_clique' and hits>=k) or
                                      any(all(inside[i] for i in s) for s in supports))
                        total+=w*value
                if kind!=stored['actual_type'] or total!=stored['charge_units']:
                    raise ValueError('Independent type or charge differs')
                gates=c['conditional_type_probe']['thresholds']
                threshold=(gates['single'] if kind=='single' else None) if role=='A' else gates['global' if kind=='single' else 'multi']
                deficit=threshold is not None and total<threshold
                if deficit!=stored['genuine_parent_deficit']:raise ValueError('Deficit classification differs')
                reports.append(dict(role=role,domain=domain['domain'],certificate_sha256=sha256(raw).hexdigest(),
                    actual_type=kind,closed_window_memberships=count,charge_units=total,
                    applicable_threshold_units=threshold,genuine_parent_deficit=deficit))
    if not reports:raise ValueError('No recorded parent witnesses checked')
    result=dict(status='PASS_INDEPENDENT_RAW_LOGICAL_PARENT_AND_TYPE_AUDIT',source_row=row,parents=reports,
        method='Rational raw-site projections and logical feature predicates, independent of signed expansion and sweep')
    output=base/f'independent-row{row}-parent-audit.json'
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path)
    p.add_argument('--row',type=int,default=0);a=p.parse_args();audit(a.directory,a.row)
