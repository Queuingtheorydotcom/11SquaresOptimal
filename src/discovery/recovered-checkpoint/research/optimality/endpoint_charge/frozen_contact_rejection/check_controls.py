"""Three targeted rejection controls for the saved upper-bound witness."""
from pathlib import Path
import json,tempfile,copy
import verify_rejection as v

def rejected(call):
 try:call()
 except AssertionError:return True
 raise AssertionError('Corrupted proof accepted')

base=Path(__file__).parent;w=json.loads((base/'exact-rejection-witness.json').read_text());packet=json.loads(w['proposal_source_json']);ctx=v.setup(packet,w['pose']);results={}
p=copy.deepcopy(w['separation_proofs'][0]);p['side']=-p['side'];fi,mi=p['member_key'];feat=packet['features'][fi]
results['reversed_separating_halfplane']=rejected(lambda:v.verify_separator(p,feat['sets'][mi],feat['threshold'],ctx))
for name,mutate in [('changed_claimed_upper_bound',lambda x:x.__setitem__('charge_upper_bound_units',x['charge_upper_bound_units']+1)),('changed_embedded_proposal',lambda x:x.__setitem__('proposal_source_json',x['proposal_source_json']+' '))]:
 z=copy.deepcopy(w);mutate(z)
 with tempfile.NamedTemporaryFile(mode='w',suffix='.json') as f:
  json.dump(z,f);f.flush();results[name]=rejected(lambda:v.replay(Path(f.name)))
report={'status':'PASS_TARGETED_REJECTION_CONTROLS','controls':results,'scope':'Targeted proof-integrity controls, not an independent mathematical implementation.'}
(base/'controls.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
