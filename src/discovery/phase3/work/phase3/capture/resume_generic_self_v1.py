"""Resume a frozen generic exact pose receipt with own-hull containment cuts."""
from pathlib import Path
import argparse,json
import capture_engine_self_v1 as E

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--seconds',type=float,default=180);ap.add_argument('--passes',type=int,default=30);ap.add_argument('--owner',type=int);ap.add_argument('--node-id',required=True);ap.add_argument('--collision-partners',type=int,default=5);a=ap.parse_args()
 d=json.loads(a.source.read_text());assert d['schema']=='exact_generic_owned_hull_v1'
 state,parent=E.load_state(a.source);assert state['mask_index']==d['mask_index'] and not state['guard'] and state['guard_source'] is None
 priority=[a.owner] if a.owner is not None else [state['mask'][0]];assert set(priority)<=set(state['mask'])
 E.run_node(state,a.output,a.seconds,a.passes,priority,True,a.node_id,parent,a.collision_partners)
if __name__=='__main__':main()
