"""Source-linked ancestry controls using copies of a small fresh three-node case."""
from pathlib import Path
from copy import deepcopy
import json,time
from strict_generic_inventory import Validator,sha
HERE=Path(__file__).resolve().parent
OUT=HERE/'ancestry-inventory-mutations';OUT.mkdir(exist_ok=True)
ORIGINAL=HERE.parent/'frontier/mask455-independent.json'
audit=json.loads(ORIGINAL.read_text())
terminal=json.loads(Path(audit['nodes'][-1]['path']).read_text())
parent=json.loads(Path(audit['nodes'][-2]['path']).read_text())

def write(name,a,t,p=None):
    if p is not None:
        pp=OUT/(name+'-parent.json');pp.write_text(json.dumps(p,separators=(',',':'))+'\n')
        ph=sha(pp);a['nodes'][-2].update(path=str(pp),sha256=ph)
        t['parent'].update(path=str(pp),sha256=ph)
    tp=OUT/(name+'-terminal.json');tp.write_text(json.dumps(t,separators=(',',':'))+'\n')
    th=sha(tp);a['nodes'][-1].update(path=str(tp),sha256=th);a['source_sha256']=th
    ap=OUT/(name+'-audit.json');ap.write_text(json.dumps(a,indent=2)+'\n')
    return ap

def main():
    began=time.monotonic();controls=[]
    clone=write('unchanged-relocated-copy',deepcopy(audit),deepcopy(terminal))
    Validator().validate(clone)
    changes=[('wrong_parent_hash',lambda a,t,p:t['parent'].update(sha256='0'*64),False),
             ('missing_parent_source',lambda a,t,p:t['parent'].update(path=str(OUT/'absent-source.json')),False),
             ('conditional_ancestor',lambda a,t,p:p.update(constraints=[{'owner':p['mask'][0],'normal':[1,0],'upper_field':'0'}]),True),
             ('ancestor_wrong_scale',lambda a,t,p:p.update(B='1'),True),
             ('ancestor_wrong_seed_hash',lambda a,t,p:p['source'].update(sha256='0'*64),True),
             ('ancestor_wrong_final_guard',lambda a,t,p:p['final_state'].update(guard={'unexpected':1}),True)]
    for name,change,copy_parent in changes:
        a,t,p=deepcopy(audit),deepcopy(terminal),deepcopy(parent)
        change(a,t,p)
        ap=write(name,a,t,p if copy_parent else None)
        try:Validator().validate(ap)
        except (ValueError,KeyError,FileNotFoundError) as e:
            controls.append(dict(name=name,rejected=True,reason=type(e).__name__+': '+str(e),audit_sha256=sha(ap)))
        else:raise AssertionError('Accepted corrupted source ancestry: '+name)
        print(name,'REJECTED',flush=True)
    result=dict(status='PASS_ANCESTRY_SOURCE_MUTATION_CONTROLS',source_receipt_sha256=sha(ORIGINAL),
                relocated_identical_semantics_control_accepted=True,controls=controls,
                controls_rejected=len(controls),validator_sha256=sha(HERE/'strict_generic_inventory.py'),
                seconds=time.monotonic()-began,scope='All source and receipt alterations are isolated copies; geometry is not replayed.')
    (HERE/'ancestry-inventory-mutation-controls.json').write_text(json.dumps(result,indent=2)+'\n')
    print('ALL CONTROLS PASS',flush=True)
if __name__=='__main__':main()
