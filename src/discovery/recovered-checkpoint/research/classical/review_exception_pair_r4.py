"""Independent integer arithmetic/finite-row review of the frozen r4 pair.

No LP, geometry replay, or packing conclusion is performed.
"""
import argparse,hashlib,json
from fractions import Fraction as F
from pathlib import Path
import numpy as np


def need(ok,message):
 if not ok:raise ValueError(message)


def sha(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--packet',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 raw=a.packet.read_bytes();packet=json.loads(raw);fixed=packet['fixed_A'];B=packet['B'];finite=packet['finite_check']
 need(packet['schema']=='conditional-exception-charge-pair-proposal-v1' and fixed['forced_exceptions']==4,'Not the expected r4 packet')
 bindings={fixed['certificate']:fixed['certificate_sha256'],packet['source_certificate']:packet['source_sha256'],finite['rows']:finite['rows_sha256'],finite['experiment']:finite['experiment_sha256'],B['floating_vector']:B['floating_vector_sha256']}
 for path,h in bindings.items():need(sha(path)==h,'Frozen input changed: '+path)
 A=json.loads(Path(fixed['certificate']).read_text());source=json.loads(Path(packet['source_certificate']).read_text())
 fields=lambda c:([p[:2] for p in c['point_orbits']],[{k:v for k,v in g.items() if k!='weight'} for g in c['charge_orbits']])
 need(fields(A)==fields(source),'Feature/site structure mismatch')
 D=A['coordinate_denominator'];L=F(A['L']);edge=L*D;need(edge.denominator==1,'Nonintegral container lattice');edge=int(edge)
 capacities=[]
 for x,y,w in A['point_orbits']:
  orbit={(x,y),(edge-x,y),(x,edge-y),(edge-x,edge-y),(y,x),(edge-y,x),(y,edge-x),(edge-y,edge-x)}
  capacities.append(len(orbit))
 for atom in A['charge_orbits']:
  k=atom['threshold'];need(type(k) is int and k>=1,'Invalid feature threshold');sizes={len(g) for g in atom['sets']};need(len(sizes)==1,'Mixed group sizes')
  m=sizes.pop();need(all(len(set(g))==m for g in atom['sets']),'Repeated sites')
  if atom['kind']=='majority_hull':need(m==2*k-1,'TRUE majority requires exactly2k-1 sites');cap=1
  elif atom['kind']=='floor':cap=m//k
  else:raise ValueError('Unexpected feature kind in this frozen source')
  capacities.append(len(atom['sets'])*cap)
 wa=[p[2] for p in A['point_orbits']]+[g['weight'] for g in A['charge_orbits']];wb=B['weight_units']
 need(len(wa)==len(wb)==len(capacities),'Weight/column dimensions differ')
 need(all(type(w) is int and w>=0 for w in wa+wb),'Nonnegative integer weights required')
 MA=sum(c*w for c,w in zip(capacities,wa));MB=sum(c*w for c,w in zip(capacities,wb))
 need(MA==A['budget_units']==fixed['budget_units'] and MB==B['budget_units'],'Budget recomputation mismatch')
 DA=fixed['weight_denominator'];DB=B['weight_denominator'];need(type(DA) is int and DA>0 and type(DB) is int and DB>0,'Invalid denominator')
 need(A['weight_denominator']==DA and F(packet['proposed_parent_side'])*F(packet['proposed_side'])==L,'Denominator/geometry metadata differs')
 floats=np.load(B['floating_vector'])['weights'];ceil=[]
 for value in floats:
  q=F.from_float(float(value))*DB;ceil.append(-((-q.numerator)//q.denominator))
 need(ceil==wb,'Packet B weights are not the exact claimed ceilings')
 a0=fixed['required_global_baseline_units'];alpha=fixed['strong_cutoff_units'];r=fixed['forced_exceptions']
 need(all(type(v) is int for v in (a0,alpha)) and 0<=a0<=alpha,'A threshold order/type failed')
 need(F(a0,DA)==F(fixed['required_global_baseline']),'A baseline units differ');force=(12-r)*alpha+(r-1)*a0-MA
 need(force>0 and F(force,DA)==F(fixed['forcing_surplus']),'A forcing gate failed')
 rows=np.load(finite['rows'],mmap_mode='r');need(rows.dtype==np.uint8 and rows.shape==(finite['rows_checked'],len(wa)),'Frozen row format differs')
 active=np.array([i for i,(a,b) in enumerate(zip(wa,wb)) if a or b],np.int64);ca=np.array(capacities,np.int64)[active]
 x=np.array(wa,np.int64)[active];y=np.array(wb,np.int64)[active];need(max(MA,MB)<2**50,'Integer accumulation bound exceeded')
 sa=np.empty(len(rows),np.int64);sb=np.empty(len(rows),np.int64)
 for lo in range(0,len(rows),2048):
  z=np.asarray(rows[lo:lo+2048][:,active],dtype=np.int64);need(np.all(z<=ca),'A stored coefficient exceeds its feature budget')
  sa[lo:lo+len(z)]=z@x;sb[lo:lo+len(z)]=z@y
 exceptional=np.flatnonzero(sa<alpha);need(exceptional.tolist()==finite['exception_indices'],'Exact exception classification differs')
 need(int(sa.min())==finite['minimum_A_units'] and np.all(sa>=a0),'A finite baseline mismatch')
 need(int(sb.min())==B['exact_finite_global_minimum_units'] and int(sb[exceptional].min())==B['exact_finite_exception_minimum_units'],'B finite minima mismatch')
 variants=[]
 for v in packet['variants']:
  beta=v['global_units'];delta=v['exception_units'];need(type(beta) is int and type(delta) is int and 0<=beta<=delta,'B threshold order/type failed')
  gap=(11-r)*beta+r*delta-MB;need(gap>0 and gap==v['counting_surplus_units'],'Strict B gate mismatch')
  need(F(beta,DB)==F(v['global_threshold']) and F(delta,DB)==F(v['exception_threshold']),'B threshold units differ')
  need(np.all(sb>=beta) and np.all(sb[exceptional]>=delta),'Finite joint predicate fails')
  variants.append({'label':v['label'],'beta_units':beta,'delta_units':delta,'A_gate_surplus_units':force,'B_gate_surplus_units':gap,'all_stored_rows_pass':True})
 need(sha(a.packet)==hashlib.sha256(raw).hexdigest(),'Packet changed during review')
 for path,h in bindings.items():need(sha(path)==h,'Frozen input changed during review: '+path)
 result={'status':'PASS_INDEPENDENT_R4_INTEGER_AND_STORED_ROW_REVIEW','packet':str(a.packet),'packet_sha256':hashlib.sha256(raw).hexdigest(),
  'source_hashes_checked_before_and_after':True,'A_budget_units':MA,'B_budget_units':MB,'A_denominator':DA,'B_denominator':DB,
  'A_forcing_surplus_units':force,'B_positive_columns':sum(w>0 for w in wb),'exact_ceiling_weights_checked':True,'stored_rows_checked':len(rows),'columns':len(wa),
  'exception_rows':len(exceptional),'minimum_stored_A_units':int(sa.min()),'minimum_stored_B_units':int(sb.min()),'minimum_exceptional_B_units':int(sb[exceptional].min()),
  'variants':variants,'geometry_replayed':False,'global_baselines_proved':False,'global_disjunction_proved':False,'global_bound_proved':False,
  'scope':'Exact arithmetic and supplied finite coefficients only. Budget formulas rely on separately validated point/feature geometry and disjoint-core premises.',
  'review_script_sha256':sha(Path(__file__))}
 a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
