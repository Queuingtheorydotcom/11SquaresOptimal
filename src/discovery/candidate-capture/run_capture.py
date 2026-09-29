"""Portable invocation of immutable supplied capture engines, with hash checks.

This wrapper remaps historical absolute paths only when a source file is absent.
It never changes archive receipts. New receipts remain conditional on the archived
root certificate; independent replay is still required before a theorem claim.
"""
from pathlib import Path
import argparse, hashlib, json, sys

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE.parent / 'phase3'
sys.path[:0] = [str(HERE/'deps'), str(ARCHIVE/'work/phase3/capture')]
import capture_engine_self_v1 as E

def resolve_historical(p):
    p = Path(p)
    if p.exists():
        return p
    text = str(p)
    for marker in ('/work/', '/current/'):
        if marker in text:
            q = ARCHIVE / text.split(marker,1)[1]
            q = ARCHIVE / marker.strip('/') / text.split(marker,1)[1]
            if q.exists():
                return q
    raise FileNotFoundError(p)

def mapped_sha(p):
    return hashlib.sha256(resolve_historical(p).read_bytes()).hexdigest()

E.sha = mapped_sha

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source',type=Path,default=ARCHIVE/'work/phase2/conditional/mask438-adaptive.json')
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--seconds',type=float,default=180)
    ap.add_argument('--passes',type=int,default=8)
    ap.add_argument('--resume',action='store_true')
    ap.add_argument('--owner',type=int,default=15)
    ap.add_argument('--axis',type=int,default=1)
    ap.add_argument('--bound')
    ap.add_argument('--keep',choices=['le','ge'],default='le')
    ap.add_argument('--partners',type=int,default=3)
    args=ap.parse_args()
    source=args.source.resolve()
    if args.resume: state,parent=E.load_state(source)
    else: state,parent=E.root_state(source),None
    if args.bound is not None:
        sign=1 if args.keep=='le' else -1
        n=[0,0];n[args.axis]=sign
        state['constraints'].append(dict(owner=args.owner,normal=n,upper_field=sign*state['B']*(state['U']/2+E.F(args.bound)),axis=args.axis,bound_centered_unit=E.F(args.bound),keep=args.keep))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    E.run_node(state,args.output,args.seconds,args.passes,[args.owner],True,args.output.stem,parent,args.partners)
    receipt=json.loads(args.output.read_text())
    provenance=dict(wrapper=str(Path(__file__).resolve()),wrapper_sha256=mapped_sha(__file__),
                    archive_root=str(ARCHIVE),source=str(source),source_sha256=mapped_sha(source),
                    receipt=str(args.output.resolve()),receipt_sha256=mapped_sha(args.output),
                    closed=receipt['closed'],independent_replay_complete=False,
                    global_optimality_proved=False)
    args.output.with_suffix('.provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(json.dumps(provenance),flush=True)

if __name__=='__main__':main()
