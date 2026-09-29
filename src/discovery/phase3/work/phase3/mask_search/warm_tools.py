"""Warm orchestration only; all geometric decisions use unchanged pinned code."""
from pathlib import Path
import sys,importlib.util,contextlib,json,hashlib,argparse,time
from threadpoolctl import threadpool_limits
TOP=Path('/workspace/scratch/6def36ddf53b');ROOT=TOP/'current';OUT=ROOT/'research/optimality/deficit_geometry/physical_features';WORK=Path(__file__).parent
sys.path.insert(0,str(OUT));sys.path.insert(0,str(TOP/'work/audit/deps'))
threadpool_limits(limits=1)
CACHE={}
def module(path):
 path=Path(path).resolve();key=str(path)
 if key not in CACHE:
  name='phase3_warm_'+hashlib.sha256(key.encode()).hexdigest()[:16];spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);CACHE[key]=m
 return CACHE[key]
def entry(path,args,log):
 m=module(path);prior=sys.argv
 try:
  sys.argv=[str(path),*map(str,args)]
  with Path(log).open('w') as f,contextlib.redirect_stdout(f),contextlib.redirect_stderr(f):m.main()
 finally:sys.argv=prior

def gate(packet,output,log,seconds=120,bins=64,max_depth=16,max_rows=16000):
 adapter_path=TOP/'work/geometry/verify_wall_aware_mask.py';m=module(adapter_path);m.OWNERSHIP_RECEIPTS.clear()
 a=argparse.Namespace(packet=Path(packet),output=Path(output),cells=None,bins=bins,max_depth=max_depth,max_rows=max_rows,seconds=seconds,patch_nodes=5000)
 with Path(log).open('w') as f,contextlib.redirect_stdout(f),contextlib.redirect_stderr(f):m.av.run(a)
 out=json.loads(Path(output).read_text());out['ownership_proof']='Strict wall-aware ownership by complete rational half-angle interval envelopes and exact trigonometric support extrema; disk bounds used when sufficient.';out['ownership_receipts']=m.OWNERSHIP_RECEIPTS.copy()
 out['adapter_dependencies']={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in [m.UPSTREAM,adapter_path,Path(m.wall.__file__)]}
 out['scope']='This adapter supplies a new wall-aware ownership validator. The upstream geometric verifier is unchanged. Every ownership point has an exact continuum certificate. Only complete eleven-cell coverage plus the counting gap excludes the stated mask; no global optimality claim.'
 if out['status']=='PASS_EXACT_ASYMMETRIC_MASK_EXCLUSION':out['status']='PASS_EXACT_WALL_AWARE_ASYMMETRIC_MASK_EXCLUSION'
 m.av.typed.save(Path(output),out)
 Path(str(output)+'.orchestration.json').write_text(json.dumps({'driver':str(Path(__file__)),'driver_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'gate_sha256':hashlib.sha256(Path(output).read_bytes()).hexdigest(),'scope':'Warm orchestration provenance only; the gate JSON is ordinary-adapter compatible.'},indent=2)+'\n')
 return json.loads(Path(output).read_text())

def passed_pattern(packet,gatefile):
 p=Path(packet);d=json.loads(p.read_text());g=json.loads(Path(gatefile).read_text())
 assert g['status']=='PASS_EXACT_WALL_AWARE_ASYMMETRIC_MASK_EXCLUSION'
 assert g['packet_sha256']==hashlib.sha256(p.read_bytes()).hexdigest()
 assert str(g['parent_Uplus'])=='387708359002281417731/100000000000000000000'
 assert g['mask']==d['mask'] and g['budget_units']==d['certificate']['budget_units']
 assert len(g['cells'])==11 and all(c['complete'] for c in g['cells']) and set(c['cell'] for c in g['cells'])==set(d['mask'])
 P={i for i,x in enumerate(d['threshold_units']) if x};O=set(d.get('conditional_owner_support',d['mask']));T=P|O
 assert T<=set(d['mask']) and sum(d['threshold_units'][i] for i in d['mask'])>d['certificate']['budget_units']
 return {'status':'PASS_EXACT_WALL_AWARE_ASYMMETRIC_MASK_EXCLUSION','required_cells':sorted(T),'positive_cells':sorted(P),'owner_support':sorted(O),'packet':str(p),'gate':str(gatefile),'packet_sha256':g['packet_sha256'],'mask_index':d['mask_index'],'rows':g['rows'],'budget':d['certificate']['budget_units'],'forced_charge':sum(d['threshold_units'][i] for i in d['mask']),'parent_Uplus':g['parent_Uplus']}

if __name__=='__main__':
 p=TOP/'work/phase2/mask_search/mask232-omit10-packet.json';old=json.loads((TOP/'work/phase2/mask_search/mask232-omit10-gate.json').read_text());out=WORK/'warm-control-ordinary-gate.json';g=gate(p,out,WORK/'warm-control.log');assert g['rows']==old['rows'];assert g['cells']==old['cells'];assert [r['status'] for r in g['records']]==[r['status'] for r in old['records']];assert g['packet_sha256']==old['packet_sha256'];
 def norm(x):
  if isinstance(x,dict):return {k:norm(v) for k,v in x.items() if k!='seconds'}
  if isinstance(x,list):return [norm(v) for v in x]
  return x
 assert norm(g)==norm(old),'Full normalized ordinary-adapter receipt mismatch';(WORK/'warm-control-ordinary-result.json').write_text(json.dumps({'status':'PASS_EXACT_REPLAY_MATCH','rows':g['rows'],'packet_sha256':g['packet_sha256'],'all_cell_partitions_match':True,'all_row_statuses_match':True,'full_json_except_seconds_match':True},indent=2)+'\n');print(json.dumps({'status':'PASS_EXACT_REPLAY_MATCH','rows':g['rows'],'seconds':g['seconds']}))
