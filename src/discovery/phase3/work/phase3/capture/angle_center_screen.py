"""Exact necessary affine SAT relaxation; floating LP is discovery ONLY.

Each trig component has |a''(t)|<=4 since c''^2+s''^2=16/(1+t^2)^3.
All retained inequalities are upper affine bounds on necessary slacks. This
module does not certify LP optimization/infeasibility or packing antecedents.
"""
import capture_engine_self_v1 as E
from pathlib import Path
from scipy.optimize import linprog
import numpy as np,json,time,argparse
F=E.F

def fold(a,b):
 q=F(1,2);out=[]
 if a<=q:out.append((a,min(b,q)))
 if b>=q:
  u=max(a,q);out.append(((u-1)/(u+1),(b-1)/(b+1)))
 return out

def build(state,override=None):
 owners=state['mask'];N=3*len(owners);pos={i:3*k for k,i in enumerate(owners)};mid=[];rad=[];domains={};angle_ranges={};pose_covers={}
 for i in owners:
  live=[r for r in E.partner_rows(state,i) if r['domain']];assert live
  pose_covers[i]=live;D=E.geo.hull([p for r in live for p in r['domain']]);domains[i]=D
  aa=[p for r in live for p in fold(*r['interval'])];lo=min(a for a,b in aa);hi=max(b for a,b in aa);angle_ranges[i]=[lo,hi]
  for k in (0,1):
   x=min(p[k] for p in D);y=max(p[k] for p in D);mid.append((x+y)/2);rad.append((y-x)/2)
  mid.append((lo+hi)/2);rad.append((hi-lo)/2)
 initial_box=[[m-r,m+r] for m,r in zip(mid,rad)]
 if override is not None:
  assert len(override)==N
  for k,(a,b) in enumerate(override):
   lo=max(F(a),mid[k]-rad[k]);hi=min(F(b),mid[k]+rad[k]);assert lo<=hi
   mid[k],rad[k]=(lo+hi)/2,(hi-lo)/2
 rows=[];pair_report=[]
 def vec():return [F(0)]*N
 def trig(i,comp):
  t=mid[pos[i]+2];r=rad[pos[i]+2];c,s=E.geo.cs(t);cp=-4*t/(1+t*t)**2;sp=2*(1-t*t)/(1+t*t)**2
  a,ap=(c,cp) if comp==0 else (s,sp);err=2*r*r;return a,ap,err,abs(ap)*r+err
 def td(i,comp,terms,constant=F(0)):
  a,ap,e,v=trig(i,comp);d0=constant+sum(q*mid[k] for k,q in terms.items());rho=sum(abs(q)*rad[k] for k,q in terms.items());z=vec()
  for k,q in terms.items():z[k]+=a*q
  z[pos[i]+2]+=ap*d0
  return a*d0,z,e*abs(d0)+v*rho
 def tt(i,ci,j,cj):
  a,ap,ea,va=trig(i,ci);b,bp,eb,vb=trig(j,cj);z=vec();z[pos[i]+2]+=ap*b;z[pos[j]+2]+=a*bp
  return a*b,z,ea*abs(b)+eb*abs(a)+va*vb
 def combine(items,constant=F(0)):
  c=constant;z=vec();err=F(0)
  for scale,(a,v,e) in items:
   c+=scale*a;err+=abs(scale)*e
   for k,x in enumerate(v):z[k]+=scale*x
  return c+err,z
 def add_upper(c,z,kind,**meta):
  # c + z.dot(delta) >= 0 is necessary.
  scale=max((abs(x) for x in z),default=F(0)) or F(1)
  rows.append(dict(coefficients=[-x/scale for x in z],upper=c/scale,kind=kind,**meta))
 for k,r in enumerate(rad):
  z=vec();z[k]=1;add_upper(r,z,'box',coordinate=k,side='lower');z=vec();z[k]=-1;add_upper(r,z,'box',coordinate=k,side='upper')
 for i in owners:
  k=pos[i]
  for n,h in E.geo.rows(domains[i]):
   z=vec();z[k],z[k+1]=-n[0],-n[1];add_upper(h-n[0]*mid[k]-n[1]*mid[k+1],z,'center_domain',owner=i)
  c,cp,ec,_=trig(i,0);s,sp,es,_=trig(i,1)
  for axis in (0,1):
   for wallside in (-1,1):
    for sign in (-1,1):
     z=vec();z[k+axis]=wallside;z[k+2]=-state['B']*(cp+sign*sp)/2
     constant=(mid[k+axis] if wallside==1 else E.L-mid[k+axis])-state['B']*(c+sign*s)/2+state['B']*(ec+es)/2
     add_upper(constant,z,'wall',owner=i,axis=axis,wallside=wallside,sine_sign=sign)
  for p in state['groups'][i]:
   for axis in (0,1):
    for sign in (-1,1):
     # axis0=(c,s), axis1=(-s,c), displacement owned point minus center.
     if axis==0:terms=[(-sign,td(i,0,{k:-1},p[0])),(-sign,td(i,1,{k+1:-1},p[1]))]
     else:terms=[(sign,td(i,1,{k:-1},p[0])),(-sign,td(i,0,{k+1:-1},p[1]))]
     constant,z=combine(terms,state['B']/2);add_upper(constant,z,'owned_point',owner=i,point=p,axis=axis,sign=sign)
 for ix,i in enumerate(owners):
  for j in owners[ix+1:]:
   I,J=angle_ranges[i],angle_ranges[j];sig=1 if J[0]>=I[1] else -1 if J[1]<=I[0] else 0
   support=[(-state['B']/2,tt(i,0,j,0)),(-state['B']/2,tt(i,1,j,1))]
   if sig:support.extend([(-state['B']*sig/2,tt(i,0,j,1)),(state['B']*sig/2,tt(i,1,j,0))])
   cases=[];eliminated=[]
   for axowner in (i,j):
    for axis in (0,1):
     for sign in (-1,1):
      dx={pos[i]:1,pos[j]:-1};dy={pos[i]+1:1,pos[j]+1:-1}
      if axis==0:terms=[(sign,td(axowner,0,dx)),(sign,td(axowner,1,dy))]
      else:terms=[(-sign,td(axowner,1,dx)),(sign,td(axowner,0,dy))]
      c,z=combine(terms+support,-state['B']/2);upper=c+sum(abs(x)*r for x,r in zip(z,rad));case=dict(axis_owner=axowner,axis=axis,sign=sign,constant=c,coefficients=z,box_upper=upper)
      (cases if upper>=0 else eliminated).append(case)
   if not cases:
    add_upper(F(-1),vec(),'pair_no_possible_axis',owners=[i,j]);pair_report.append(dict(owners=[i,j],live_cases=[],eliminated=eliminated));continue
   # An affine majorant of the union. Average gradients retain common first
   # order angle/center information; exact box support bounds cover every case.
   base=[sum(c['coefficients'][k] for c in cases)/len(cases) for k in range(N)]
   constant=max(c['constant']+sum(abs(x-y)*r for x,y,r in zip(c['coefficients'],base,rad)) for c in cases)
   add_upper(constant,base,'pair_sat_union',owners=[i,j],sine_sign=sig)
   pair_report.append(dict(owners=[i,j],live_cases=cases,eliminated=eliminated,majorant_constant=constant,majorant_coefficients=base))
 return dict(mask=owners,initial_box=initial_box,box_override=override,midpoints=mid,radii=rad,center_domains=domains,folded_half_angle_ranges=angle_ranges,pose_covers=pose_covers,inequalities=rows,pairs=pair_report,coordinate_order='For each mask owner: field center x,y, quarter-turn-folded half-angle t')

def solve(model,state):
 N=len(model['midpoints']);A=np.array([[float(v) for v in r['coefficients']] for r in model['inequalities']]);b=np.array([float(r['upper']) for r in model['inequalities']]);z=np.zeros(N);p=linprog(z,A_ub=A,b_ub=b,bounds=[(None,None)]*N,method='highs');out=dict(status=int(p.status),message=p.message,certified=False)
 if not p.success:return out
 ranges=[];solves=[]
 for k in range(N):
  q=z.copy();q[k]=1;lo=linprog(q,A_ub=A,b_ub=b,bounds=[(None,None)]*N,method='highs');hi=linprog(-q,A_ub=A,b_ub=b,bounds=[(None,None)]*N,method='highs');assert lo.success and hi.success
  ranges.append([float(model['midpoints'][k])+lo.fun,float(model['midpoints'][k])-hi.fun]);solves.append(dict(coordinate=k,lower_dual=lo.ineqlin.marginals.tolist(),upper_dual=hi.ineqlin.marginals.tolist()))
 out['field_center_halfangle_bounds']=ranges;out['duals_for_discovery']=solves
 out['max_center_width_unit']=max((ranges[3*k+a][1]-ranges[3*k+a][0])/float(state['B']) for k in range(len(state['mask'])) for a in (0,1))
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();start=time.monotonic();s,parent=E.load_state(a.source);model=build(s);built=time.monotonic();answer=solve(model,s);out=dict(source=parent,model=model,discovery=answer,build_seconds=built-start,seconds=time.monotonic()-start,global_optimality_proved=False,mask_capture_proved=False);E.save(a.output,out)
 print(json.dumps(dict(source=parent,rows=len(model['inequalities']),build_seconds=out['build_seconds'],seconds=out['seconds'],**{k:v for k,v in answer.items() if k!='duals_for_discovery'}),indent=2))
if __name__=='__main__':main()
