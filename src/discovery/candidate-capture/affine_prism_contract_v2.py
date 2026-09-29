"""Exact affine SAT and angle-row prism contraction, portable CLI."""
import affine_contract_v2 as A
import pose_prism_cuts_v2 as P

original_build=A.S.build
def build(*args,**kwargs):
    model=original_build(*args,**kwargs)
    P.add(model)
    return model
A.S.build=build

if __name__=='__main__':A.main()
