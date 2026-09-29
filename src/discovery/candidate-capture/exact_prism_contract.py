"""Exact contraction with verified supports of the full pose-prism union."""
import exact_angle_contract as C
import pose_prism_cuts as P
from pathlib import Path

original_build=C.S.build
def build(*args,**kwargs):
    model=original_build(*args,**kwargs)
    P.add(model)
    return model
C.S.build=build

if __name__=='__main__':C.main()
