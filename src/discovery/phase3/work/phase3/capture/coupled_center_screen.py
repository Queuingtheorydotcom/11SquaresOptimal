"""Noncertifying LP screen of exact coupled necessary center inequalities."""
import capture_engine_v4 as E
import numpy as np
from scipy.optimize import linprog
from pathlib import Path
import json,argparse,time

def build(state):
 mask=state['mask'];domains={};cores={};covers={};pairs=[];ineq=[];D=len(mask)*2
 def add(owner,n,h,other=None,kind='domain'):
  row=[E.F(0)]*D;k=2*mask.index(owner);row[k],row[k+1]=n
  if other is not None:k=2*mask.index(other);row[k],row[k+1]=-n[0],-n[1]
  scale=max(abs(x) for x in row);assert scale
  ineq.append(dict(coefficients=[x/scale for x in row],upper=h/scale,kind=kind,owner=owner,other=other))
 for owner in mask:
  live=[r for r in E.partner_rows(state,owner) if r['domain']];covers[owner]=live
  domains[owner]=E.geo.hull([p for r in live for p in r['domain']]);q=live[0]['core']
  for r in live:
   for n,h in E.geo.rows(r['core']):q=E.geo.clip_linear(q,n,h)
  cores[owner]=q
  for n,h in E.geo.rows(domains[owner]):add(owner,n,h)
 for ix,i in enumerate(mask):
  for j in mask[ix+1:]:
   domain=E.geo.minkowski(domains[i],[(-x,-y) for x,y in domains[j]])
   forbidden=E.geo.minkowski(cores[i],[(-x,-y) for x,y in cores[j]])
   remaining=E.geo.convex_difference(domain,forbidden)
   allowed=E.geo.hull([p for q in remaining for p in q])
   pairs.append(dict(owners=[i,j],difference_domain=domain,forbidden=forbidden,allowed_hull=allowed))
   if not allowed:return dict(contradiction_pair=[i,j],pairs=pairs)
   for n,h in E.geo.rows(allowed):add(i,n,h,j,'pair_difference')
 return dict(mask=mask,domains=domains,common_cores=cores,prior_pose_covers=covers,pairs=pairs,inequalities=ineq)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('--output',type=Path);a=ap.parse_args();start=time.monotonic();s,parent=E.load_state(a.source);d=build(s)
 if 'contradiction_pair' in d:print(d['contradiction_pair']);return
 A=np.array([[float(x) for x in r['coefficients']] for r in d['inequalities']]);b=np.array([float(r['upper']) for r in d['inequalities']]);N=2*len(s['mask']);zero=np.zeros(N);p=linprog(zero,A_ub=A,b_ub=b,bounds=[(None,None)]*N,method='highs');out=dict(status=int(p.status),message=p.message,inequalities=len(A),seconds=time.monotonic()-start,certified=False,mask_capture_proved=False)
 if p.success:
  ranges=[]
  for k in range(N):
   q=zero.copy();q[k]=1;lo=linprog(q,A_ub=A,b_ub=b,bounds=[(None,None)]*N,method='highs');hi=linprog(-q,A_ub=A,b_ub=b,bounds=[(None,None)]*N,method='highs');assert lo.success and hi.success
   ranges.append([(lo.fun/float(s['B'])-float(s['U'])/2),(-hi.fun/float(s['B'])-float(s['U'])/2)])
  out['centered_unit_bounds']={i:ranges[2*k:2*k+2] for k,i in enumerate(s['mask'])};out['max_width']=max(b-a for a,b in ranges)
 if a.output:
  out['source']=parent;out['exact_model']=d;E.save(a.output,out)
 print(json.dumps({k:v for k,v in out.items() if k!='exact_model'},indent=2))
if __name__=='__main__':main()
