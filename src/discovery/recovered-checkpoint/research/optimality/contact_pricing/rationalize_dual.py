#!/usr/bin/env python3
from discover import *
data=np.load(OUT/'pilot1/finite-dual.npz');records=[];poses=[]
for i,(theta,x,y) in enumerate(data['poses']):
 q=Q(float(np.tan(theta/2))).limit_denominator(10**14);c=(1-q*q)/(1+q*q);s=2*q/(1+q*q);r=B/2*float(abs(c)+abs(s));span=L-2*r
 uu=np.clip((x-r)/span,0,1);vv=np.clip((y-r)/span,0,1)
 u=Q(float(uu)).limit_denominator(10**14);v=Q(float(vv)).limit_denominator(10**14)
 poses.append([2*np.arctan(float(q)),r+float(u)*span,r+float(v)*span])
 records.append({'index':i,'half_angle':str(q),'normalized_x':str(u),'normalized_y':str(v),'dual_numerator':int(data['coefficients'][i]),'dual_denominator':2})
mod=np.load(OUT/'pilot1/model.npz');model={k:mod[k].item() if k=='nvar' else mod[k] for k in mod.files if k!='budget'}
rows=capture(model,poses);num=data['coefficients'];excess=num@rows.astype(np.int32)-2*data['budget']
out={'status':'RATIONAL_POSE_PARAMETERS_WITH_FLOATING_PRECHECK_ONLY','coordinate_formula':'c=(1-q^2)/(1+q^2), s=2q/(1+q^2), r=B*(abs(c)+abs(s))/2, x=r+u*(L-2*r), y=r+v*(L-2*r)','L':'191/50','B':'(191/50)/alpha','records':records,'float_changed_entries':int(np.count_nonzero(rows!=data['rows'])),'float_max_excess':float(max(excess))}
(OUT/'pilot1/rationalized-dual-poses.json').write_text(json.dumps(out,indent=2)+'\n');np.savez_compressed(OUT/'pilot1/rationalized-dual-precheck.npz',rows=rows,poses=poses,coefficients=num,budget=data['budget'])
print(json.dumps({k:v for k,v in out.items() if k!='records'},indent=2))
