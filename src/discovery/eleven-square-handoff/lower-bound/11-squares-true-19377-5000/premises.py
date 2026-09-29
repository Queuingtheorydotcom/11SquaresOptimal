"""Portable full-catalogue premises and frozen dependency validation."""
if not __debug__:raise SystemExit('Do not run with -O or -OO.')
from copy import deepcopy
from fractions import Fraction as F
from hashlib import sha256
import importlib,json,re,sys
from pathlib import Path


def need(ok,message):
 if not ok:raise ValueError(message)


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def digest(raw):return sha256(raw).hexdigest()
def read(path):return json.loads(Path(path).read_bytes())
def filehash(path):return digest(Path(path).read_bytes())
def checker_hashes(directory):return {p.name:filehash(p) for p in sorted(Path(directory).glob('*.py'))}


def intervals(template):
 result=[];cursor=F(0)
 for row in template['entries']:
  need(len(row)==4,'Malformed template entry');lo,hi=map(F,row[:2])
  need(lo==cursor and 0<=lo<hi<1,'Template has angular gap/overlap');result.append((lo,hi));cursor=hi
 need(result and cursor*cursor+2*cursor>1,'Template does not cover pi/4 exactly');return result


def core_job(A,L,lo,hi,margin):
 t=(lo+hi)/2
 def trig(u):return (1-u*u)/(1+u*u),2*u/(1+u*u)
 c,s=trig(t);turn=[];width=[]
 for u in (lo,hi):
  cu,su=trig(u);dot=c*cu+s*su;cross=abs(c*su-s*cu)
  need(dot>0 and dot>=cross,'Invalid relative-angle range');turn.append(dot+cross);width.append(cu+su)
 B=(A-margin)/max(turn);H=L/2-A*min(width)/2
 need(0<B<A and A-B*max(turn)==margin>0,'Invalid strict core containment')
 need(0<=H<L/2 and B*(c+s)/2<=L/2-H,'Invalid complete center envelope')
 return t,B,H


def inspect_catalogue(directory):
 """Validate full receipt structure. This does not replay geometry."""
 root=Path(directory);run=read(root/'run.json');result=read(root/'RESULT.json')
 need(result.get('status')=='PASS_FULL_EXACT_ADAPTIVE_TRUE_CATALOGUE','Catalogue lacks a complete full PASS')
 context=dict(run);context.pop('context_sha256',None)
 need(digest(canonical(context))==run['context_sha256']==result['context_sha256'],'Context hash mismatch')
 need(filehash(root/'build_used.py')==run['builder_sha256'],'Frozen builder hash mismatch')
 need(checker_hashes(root/'checker')==run['checker_sha256'],'Frozen checker hashes differ')
 need(all(re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*\.py',name) for name in run['checker_sha256']),'Unsafe checker filename')
 proposal=read(root/'proposal.json');template=read(root/'template.json');candidate=read(root/'candidate.json')
 need(digest(canonical(proposal))==run['fixed_proposal_sha256'],'Fixed proposal hash mismatch')
 need(digest(canonical(template))==run['template_sha256'],'Template hash mismatch')
 need(filehash(root/'input-proposal.json')==run['input_proposal_sha256'],'Original proposal hash mismatch')
 initial=read(root/'input-proposal.json');initial.pop('exploratory_only',None);initial['entries']=[]
 need(initial==proposal,'Fixed proposal differs from recorded input transformation')
 if run['proxy_sha256'] is not None:need(filehash(root/'proxy.json')==run['proxy_sha256'],'Captured proxy hash mismatch')
 need(filehash(root/'candidate.json')==result['certificate_sha256'],'Final candidate hash mismatch')
 fixed=deepcopy(candidate);fixed['entries']=[];need(fixed==proposal,'Final candidate changes frozen charge data')
 spans=intervals(template);n=len(spans);expected=list(range(n))
 need(run['selected_rows']==expected and run['total_source_rows']==n,'Source selection is not complete')
 need(result['completed_source_intervals']==result['selected_source_intervals']==result['total_source_intervals']==n,'Full coverage counts differ')
 need(not result['unresolved'] and not result['missing_source_intervals'] and result['exact_deficient_parents']==0,'Unresolved or deficient source jobs remain')
 need(set(result['root_receipt_sha256'])==set(map(str,expected)),'Root hash inventory is incomplete')
 A,L=F(candidate['A']),F(candidate['L']);margin=F(run['margin'])
 need(A>0 and L>0 and 0<margin<A and F(candidate['bound'])==L/A==F(result['exact_target_side']),'Target/core metadata mismatch')
 required=candidate['minimum_units'];budget=candidate['budget_units'];den=candidate['weight_denominator']
 need(type(den) is int and den>0 and type(required) is int and required>=0 and type(budget) is int and budget>=0,'Invalid integer charge metadata')
 need(result['required_units']==required and result['budget_units']==budget and 11*required>budget,'Strict charge-count premise failed')
 leaves=[];keys=set();paths=['run.json','RESULT.json','build_used.py','proposal.json','input-proposal.json','template.json','candidate.json']
 if run['proxy_sha256'] is not None:paths.append('proxy.json')
 for i,(lo,hi) in enumerate(spans):
  name=f'roots/{i}.json';receipt=read(root/name);paths.append(name)
  need(filehash(root/name)==result['root_receipt_sha256'][str(i)],'Root receipt hash mismatch')
  need(receipt['context_sha256']==run['context_sha256'] and receipt['row']==i and receipt['status']=='PASS' and not receipt['failed'],'Unproved/wrong source root')
  need((F(receipt['a']),F(receipt['b']))==(lo,hi) and receipt['accepted_keys'],'Root domain mismatch')
  local=[]
  for key in receipt['accepted_keys']:
   need(isinstance(key,str) and re.fullmatch('[0-9a-f]{64}',key) and key not in keys,'Duplicate or invalid leaf key');keys.add(key)
   name=f'nodes/{key}.json';node=read(root/name);paths.append(name)
   identity={k:node[k] for k in ('context_sha256','entry','job')}
   need(node['key']==key==digest(canonical(identity)) and node['context_sha256']==run['context_sha256'],'Leaf identity hash mismatch')
   entry=node['entry'];need(len(entry)==4 and len(node['job'])==3,'Malformed leaf job')
   a,b,t,B=map(F,entry);need(lo<=a<b<=hi,'Leaf escapes source interval')
   job=core_job(A,L,a,b,margin);need((t,B)==job[:2] and tuple(map(F,node['job']))==job,'Leaf core differs from strict generated job')
   r=node['receipt'];need(node['outcome']=='PASS' and r['status']=='PASS','Unproved leaf receipt')
   need(all(type(r.get(k)) is int and r[k]>=0 for k in ('minimum_units','cells','slabs')),'Invalid receipt integers')
   need(r['minimum_units']>=required,'Recorded leaf misses required threshold')
   local.append(node)
  cursor=lo
  for node in sorted(local,key=lambda x:F(x['entry'][0])):
   a,b=map(F,node['entry'][:2]);need(a==cursor,'Leaf gap or overlap');cursor=b
  need(cursor==hi,'Source interval has missing leaf coverage');leaves.extend(local)
 leaves.sort(key=lambda x:F(x['entry'][0]));need([x['entry'] for x in leaves]==candidate['entries'],'Candidate entries differ from complete proved leaves')
 minimum=min(x['receipt']['minimum_units'] for x in leaves)
 need(result['proved_leaf_intervals']==len(leaves) and result['certified_minimum_units']==minimum,'Leaf count/minimum mismatch')
 need(result['counting_surplus_units']==11*minimum-budget>0 and F(result['strict_core_margin'])==margin,'Final counting/margin metadata mismatch')
 paths.extend('checker/'+name for name in run['checker_sha256'])
 info={'candidate':candidate,'run':run,'result':result,'paths':paths,'jobs':[tuple(map(F,x['job'])) for x in leaves],'leaves':len(leaves),'source_intervals':n}
 if 'receipt_transfer' in run:
  from reuse_premises import validate_reuse
  reuse=validate_reuse(root,info,leaves);info['paths'].extend(reuse['paths']);info['reuse']=reuse
 return info


def load_checker(directory):
 checker=Path(directory).resolve()/'checker';sys.path.insert(0,str(checker))
 names=checker_hashes(checker)
 for filename in names:
  name=filename[:-3]
  if name in sys.modules:need(Path(getattr(sys.modules[name],'__file__','')).resolve()==checker/filename,'External cached checker module: '+name)
 staged=importlib.import_module('majority_staged');discrete=importlib.import_module('exact_mixed');sweep=importlib.import_module('integer_sweep')
 for filename in names:
  name=filename[:-3]
  if name in sys.modules:need(Path(getattr(sys.modules[name],'__file__','')).resolve()==checker/filename,'External imported checker module: '+name)
 return staged,discrete,sweep


def make_proxy(c,optional):
 out=deepcopy(c)
 if optional is not None:
  need(F(optional['L'])==F(c['L']) and len(optional['point_orbits'])==len(c['point_orbits']),'Proxy container/site count differs')
  for p,q in zip(c['point_orbits'],optional['point_orbits']):
   need(all(F(p[i],c['coordinate_denominator'])==F(q[i],optional['coordinate_denominator']) for i in (0,1)),'Proxy moves a site')
  need(len(optional['charge_orbits'])==len(c['charge_orbits']),'Proxy feature count differs')
 for i,atom in enumerate(c['charge_orbits']):
  if atom.get('kind')!='majority_hull':
   if optional is not None:
    q=deepcopy(optional['charge_orbits'][i]);q['weight']=atom['weight'];need(q==atom,'Proxy changes a non-majority feature')
   continue
  q=deepcopy(atom if optional is None else optional['charge_orbits'][i])
  if optional is None:q['kind']='threshold'
  need(q.get('kind','threshold') in ('threshold','convex_clique') and q['sets']==atom['sets'] and q['threshold']==atom['threshold'] and not q.get('multiset',False),'Invalid majority lower proxy')
  q['weight']=atom['weight'];out['charge_orbits'][i]=q
 return out


def validate_geometry_premises(directory,info=None):
 root=Path(directory);info=inspect_catalogue(root) if info is None else info
 staged,discrete,sweep=load_checker(root);c=info['candidate'];data,jobs,margin=staged.validate(c)
 need(jobs==info['jobs'] and margin==F(info['run']['margin']),'Independent candidate validation gives different jobs/margin')
 optional=read(root/'proxy.json') if info['run']['proxy_sha256'] is not None else None
 proxy=make_proxy(c,optional);pdata,pjobs,_=discrete.validate(proxy);need(pjobs==jobs,'Proxy job mismatch')
 staged.FIRST_PATCH_NODE_LIMIT=info['run']['first_patch_node_limit'];staged.FINAL_PATCH_NODE_LIMIT=info['run']['final_patch_node_limit']
 need(all(type(x) is int and x>=0 for x in (staged.FIRST_PATCH_NODE_LIMIT,staged.FINAL_PATCH_NODE_LIMIT)),'Invalid patch resource limits')
 return staged,discrete,sweep,data,pdata,jobs
