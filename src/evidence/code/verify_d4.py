"""Run the frozen symmetry checker with package-local default paths."""
from pathlib import Path
import runpy
import sys
if not __debug__:raise SystemExit("Assertions must be enabled")
base=Path(__file__).resolve().parents[1]
source=base/'research/finalization/global-composition/audit_d4_bridge.py'
arguments=sys.argv[1:]
if '--workspace' not in arguments:arguments=['--workspace',str(base),*arguments]
if '--output' not in arguments:arguments=['--output',str(base/'results/d4-bridge.json'),*arguments]
sys.argv=[str(source),*arguments]
runpy.run_path(str(source),run_name='__main__')
