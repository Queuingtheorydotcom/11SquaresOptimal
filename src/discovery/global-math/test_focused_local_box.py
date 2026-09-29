"""Negative controls for the independent focused rectangle auditor."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,subprocess,hashlib,copy,sys,time
D=Path(__file__).resolve().parent;R=D.parent;O=D/'focused-box-negative-controls';O.mkdir(exist_ok=True)
checker=D/'audit_focused_local_box.py';proposal=R/'candidate-capture/focused1024-local-certificate.json';receipt=D/'focused1024-local-box-independent.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=json.loads(proposal.read_text());p={k:p[k] for k in ['source','source_sha256','radius_by_coordinate']};original=json.loads(Path(p['source']).read_text());state=original['final_state']
source={'mask_index':original['mask_index'],'final_state':{k:state[k] for k in ['U','B','mask']}}
source['final_state']['cells']={owner:[{k:row[k] for k in ['interval','residual_polygons']} for row in rows] for owner,rows in state['cells'].items()}
del original,state
fixture=O/'compact-pose-fixture.json';fixture.write_text(json.dumps(source));p['source']=str(fixture.resolve());p['source_sha256']=sha(fixture);cases=[]
q=copy.deepcopy(p);q['source_sha256']='0'*64;cases.append(('changed_source_hash',q,None))
q=copy.deepcopy(p);q['radius_by_coordinate'][0]='0';cases.append(('zero_radius',q,None))
q=copy.deepcopy(p);q['radius_by_coordinate'][0]='1/10000000000';cases.append(('narrow_radius',q,None))
q=copy.deepcopy(p);q['radius_by_coordinate'][0]='100';cases.append(('outside_old_chart',q,None))
q=copy.deepcopy(p);ss=copy.deepcopy(source);ss['final_state']['B']='1';cases.append(('wrong_field_frame',q,ss))
q=copy.deepcopy(p);ss=copy.deepcopy(source);owner=next(iter(ss['final_state']['cells']));del ss['final_state']['cells'][owner];cases.append(('missing_owner',q,ss))
q=copy.deepcopy(p);ss=copy.deepcopy(source);row=next(r for r in ss['final_state']['cells']['3'] if r['residual_polygons']);row['interval']=['1/3','2/3'];cases.append(('remote_axis_angle',q,ss))
q=copy.deepcopy(p);ss=copy.deepcopy(source);row=next(r for r in ss['final_state']['cells']['3'] if r['residual_polygons']);row['residual_polygons'][0][0]=['0','0'];cases.append(('outside_center_rectangle',q,ss))
start=time.monotonic()
def run(case):
 name,q,ss=case
 if ss is not None:
  sp=O/f'{name}-source.json';sp.write_text(json.dumps(ss));q['source']=str(sp.resolve());q['source_sha256']=sha(sp)
 pp=O/f'{name}.json';pp.write_text(json.dumps(q));op=O/f'{name}-result.json';args=[sys.executable,str(checker),str(pp),'--output',str(op)]
 result=subprocess.run(args,capture_output=True,text=True);tail=result.stderr.strip().splitlines()[-1] if result.stderr.strip() else ''
 if result.returncode==0:raise RuntimeError('Negative control accepted: '+name)
 return {'name':name,'rejected':True,'reason':tail}
results=[]
for case in cases:
 result=run(case);results.append(result);print(json.dumps(result),flush=True)
for opt in ['-O','-OO']:
 result=subprocess.run([sys.executable,opt,str(checker),str(proposal),'--output',str(O/'forbidden.json')],capture_output=True,text=True)
 if result.returncode==0:raise RuntimeError('Optimized mode accepted')
 results.append({'name':opt,'rejected':True,'reason':result.stderr.strip()})
out={'status':'PASS_FOCUSED_LOCAL_BOX_NEGATIVE_CONTROLS','checker_sha256':sha(checker),'positive_receipt_sha256':sha(receipt),'test_driver_sha256':sha(__file__),'controls':results,'seconds':time.monotonic()-start}
(O/'review.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
