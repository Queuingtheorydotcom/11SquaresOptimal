from pathlib import Path
from warm_tools import module
SOLVER=Path('/workspace/scratch/6def36ddf53b/work/phase3/shared/fast_solver.py')
def solve(mask,tag,extra,seconds):
 return module(SOLVER).solve(mask,tag,seconds=seconds,iterations=40,extra=extra)
