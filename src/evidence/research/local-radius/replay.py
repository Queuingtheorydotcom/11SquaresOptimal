"""Replay archived local checker, redirecting only its output receipt."""
from pathlib import Path
import runpy
import sys

if not __debug__:raise SystemExit('Assertions must remain enabled.')

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent/'recovered-checkpoint'
name=sys.argv[1] if len(sys.argv)>1 else 'audit_weighted_coordinate_radius.py'
script=(ROOT/'research/classical'/name if name=='replay_trump_local.py'
        else ROOT/'work/continuation'/name)
targets={
    'weighted-coordinate-radius-independent-audit.json':HERE/'fresh-weighted-coordinate-radius.json',
    'local-radius-independent-audit.json':HERE/'fresh-baseline-radius.json',
    'trump-local-independent-replay.json':HERE/'fresh-local-algebra.json',
}
original=Path.write_text
def write(self,*args,**kwargs):
    if self.parent==script.parent and self.name in targets:
        return original(targets[self.name],*args,**kwargs)
    return original(self,*args,**kwargs)
Path.write_text=write
sys.argv=[str(script)]
runpy.run_path(str(script),run_name='__main__')
