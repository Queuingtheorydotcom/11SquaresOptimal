"""Continue an exact generic collision trace without changing frozen engines."""
from pathlib import Path
import argparse,hashlib,json,sys
if not __debug__:raise RuntimeError('Assertions must be enabled')
WORK=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(WORK/'phase3/deps'));sys.path.insert(0,str(WORK/'phase3/generic'))
import generic1383_refined_engine as g
def main():
 p=argparse.ArgumentParser();p.add_argument('parent',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--seconds',type=float,default=180);p.add_argument('--passes',type=int,default=5);p.add_argument('--partners',type=int,default=3);p.add_argument('--priority',default='4,6');p.add_argument('--node',default='generic1383r2');a=p.parse_args()
 d=json.loads(a.parent.read_text());assert d['schema']=='exact_generic_owned_hull_v1' and d['terminal'] and not d['closed']
 for path,digest in d['dependencies'].items():assert g.sha(path)==digest
 raw=d['final_state'];state=dict(raw);state['U']=g.F(raw['U']);state['B']=g.F(raw['B']);state['world']=[g.poly(P) for P in raw['world']];state['groups']={int(k):g.poly(P) for k,P in raw['groups'].items()};state['guard']={int(k):v for k,v in raw['guard'].items()};state['cells']={}
 for owner,rows in raw['cells'].items():state['cells'][int(owner)]=[dict(interval=list(map(g.F,r['interval'])),residual_polygons=[g.poly(P) for P in r['residual_polygons']],outer_domain=g.poly(r['outer_domain']),outer_bounds=r['outer_bounds'],reference=r['reference']) for r in rows]
 parent=dict(path=str(a.parent.resolve()),sha256=g.sha(a.parent));g.run_node(state,a.output,seconds=a.seconds,passes=a.passes,priority=[int(x) for x in a.priority.split(',') if x],node_id=a.node,parent=parent,collision_partners=a.partners)
if __name__=='__main__':main()
