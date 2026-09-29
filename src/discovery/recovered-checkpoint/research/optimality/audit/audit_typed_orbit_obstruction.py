#!/usr/bin/env python3
"""Exact D4 witness orbits and a fixed-weight per-cell counting obstruction."""
from pathlib import Path
from fractions import Fraction as F
import hashlib,json,sys,numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'research/stromquist'))
from fast_exact_parent import FastExactParentModel

def need(ok,msg):
    if not ok:raise ValueError(msg)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    packet=ROOT/'research/optimality/deficit_geometry/typed_masks/mask2045-round3-packet.json'
    coverpath=ROOT/'research/optimality/global_capture/center-cover-symmetric-exact.json'
    proposal=json.loads(packet.read_text());cover=json.loads(coverpath.read_text())
    L=F(191,50);U=F(969271,250000);A=L/U
    model=FastExactParentModel(proposal['certificate']).at_side(A)
    alpha_lower=F(387708359002281417730789706010096270637645566846,10**47)
    points=[tuple(map(F,c['center'])) for c in cover['cells']]
    seeds=[];source_hashes={}
    for suffix in ('pilot','cell5-pilot','cell6-pilot'):
        path=ROOT/f'research/optimality/typed_coverage/mask2045-{suffix}.json';data=json.loads(path.read_text())
        need(data['packet_sha256']==sha(packet),'pilot proposal mismatch')
        failed=[r for r in data['records'] if r['status']=='REFUTED_BY_LEGAL_PARENT']
        need(len(failed)==1,'expected one parent refutation')
        r=failed[0];w=r['parent_witness']
        need(F(w['side'])==A,'wrong parent side')
        seeds.append((f"cell{r['cell']}",tuple(map(F,w['center'])),F(w['half_angle']),w['charge_units'],r['cell']))
        source_hashes[str(path.relative_to(ROOT))]=sha(path)
    # Place a corner parent slightly inside both walls so it also fits strictly
    # below alpha, avoiding dependence on the Uplus-alpha outer frame sliver.
    seeds.append(('rational_corner',(A/2+F(1,10**6),A/2+F(1,10**6)),F(0),None,0))
    records=[];rows=[];summary=[]
    for name,base,t0,expected,original_cell in seeds:
        orbit_cells=set();charges=set();start=len(records)
        for swap in (False,True):
            for sx in (False,True):
                for sy in (False,True):
                    x,y=base
                    if swap:x,y=y,x
                    if sx:x=L-x
                    if sy:y=L-y
                    t=t0 if (swap+sx+sy)%2==0 else (1-t0)/(1+t0)
                    cosine=(1-t*t)/(1+t*t);sine=2*t/(1+t*t);h=A*(cosine+sine)/2
                    need(h<=x<=L-h and h<=y<=L-h,'parent not contained')
                    row=model.row(t,(x,y));charge=sum(int(a)*int(b) for a,b in zip(row,model.weights))
                    if expected is not None:need(charge==expected,'independent seed or D4 charge mismatch')
                    normal=((x-L/2)/(A*(U-1))+F(1,2),(y-L/2)/(A*(U-1))+F(1,2))
                    need(all(0<=v<=1 for v in normal),'normalized center not in cover')
                    distances=[sum((a-b)**2 for a,b in zip(normal,p)) for p in points];minimum=min(distances)
                    cells=[i for i,v in enumerate(distances) if v==minimum]
                    if not swap and not sx and not sy:need(original_cell in cells,'original claimed cell mismatch')
                    required_side=(2*max(abs(x-L/2),abs(y-L/2))+A*(cosine+sine))/A
                    need(required_side<=alpha_lower,'witness only legal above alpha')
                    orbit_cells.update(cells);charges.add(charge);rows.append(row)
                    records.append({'seed':name,'symmetry':{'swap':swap,'reflect_x':sx,'reflect_y':sy},
                                    'center':[str(x),str(y)],'half_angle':str(t),'closed_cell_memberships':cells,
                                    'charge_units':charge,'required_concentric_unit_side':str(required_side),
                                    'also_contained_at_alpha':True})
        need(len(charges)==1,'D4 symmetry did not preserve charge')
        summary.append({'seed':name,'charge_units':next(iter(charges)),'cells':sorted(orbit_cells),'record_indices':list(range(start,len(records)))})
    upper=[min((r['charge_units'] for r in records if i in r['closed_cell_memberships']),default=None) for i in range(16)]
    need(all(v is not None for v in upper),'some cell has no exact witness')
    mask=proposal['mask'];minimum_sum_upper=sum(upper[i] for i in mask);budget=proposal['certificate']['budget_units']
    need(minimum_sum_upper<=budget,'witnesses do not prove a fixed-weight obstruction')
    eligible=[{'mask_index':j,'mask':J,'minimum_sum_upper_units':sum(upper[i] for i in J)}
              for j,J in enumerate(cover['canonical_eleven_cell_subsets']) if sum(upper[i] for i in J)>budget]
    corner_masks=[J for J in cover['canonical_eleven_cell_subsets'] if set(J)&{0,3,12,15}]
    need(len(eligible)==6 and all(not(set(row['mask'])&{0,3,12,15}) for row in eligible),'unexpected all-mask obstruction classification')
    out={'status':'PASS_EXACT_FIXED_WEIGHT_TYPED_MASK_OBSTRUCTION','packet_sha256':sha(packet),
         'cover_sha256':sha(coverpath),'pilot_sha256':source_hashes,'mask_index':2045,'mask':mask,
         'budget_units':budget,'per_cell_minimum_upper_units':upper,
         'mask_minimum_sum_upper_units':minimum_sum_upper,'budget_minus_minimum_sum_upper_units':budget-minimum_sum_upper,
         'canonical_masks_whose_threshold_sum_method_is_obstructed':2184-len(eligible),
         'canonical_masks_not_obstructed_by_these_witnesses':eligible,
         'maximum_minimum_sum_upper_among_masks_occupying_a_corner_cell':max(sum(upper[i] for i in J) for J in corner_masks),
         'orbits':summary,'records':records,'columns':model.nvar,
         'all_witnesses_also_legal_at_exact_alpha':True,
         'interpretation':'Each exact individual parent bounds its cell infimum from above. Therefore any valid per-cell thresholds for these unchanged weights sum to at most this witness sum on mask2045, which is no greater than the fixed budget. Threshold relaxation alone cannot repair the strict counting contradiction.',
         'scope':'Obstruction for the frozen weight vector and per-cell threshold-sum method. These individually legal witnesses are not asserted compatible, and no packing bound or mask exclusion is proved.'}
    (HERE/'typed-fixed-weight-obstruction.json').write_text(json.dumps(out,indent=2)+'\n')
    np.savez_compressed(HERE/'typed-fixed-weight-obstruction.npz',rows=np.stack(rows),weights=np.array(model.weights,dtype=np.int64),budget=model.budget)
    print(json.dumps({k:v for k,v in out.items() if k not in ('records','pilot_sha256')},indent=2))

if __name__=='__main__':main()
