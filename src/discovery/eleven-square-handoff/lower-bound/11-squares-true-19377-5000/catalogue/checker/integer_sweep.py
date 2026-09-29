import numpy as np
from numba import njit

def need(ok,message):
    if not ok:raise ValueError(message)
def trig(t):return (1-t*t)/(1+t*t),2*t/(1+t*t)

@njit
def add(mn,lazy,k,a,b,lo,hi,w):
    if hi<=a or b<=lo:return
    if lo<=a and b<=hi:
        mn[k]+=w;lazy[k]+=w;return
    mid=(a+b)//2
    add(mn,lazy,2*k,a,mid,lo,hi,w);add(mn,lazy,2*k+1,mid,b,lo,hi,w)
    mn[k]=lazy[k]+min(mn[2*k],mn[2*k+1])
@njit
def query(mn,lazy,k,a,b,lo,hi):
    if hi<=a or b<=lo:return np.int64(2**60)
    if lo<=a and b<=hi:return mn[k]
    mid=(a+b)//2
    return lazy[k]+min(query(mn,lazy,2*k,a,mid,lo,hi),query(mn,lazy,2*k+1,mid,b,lo,hi))
@njit
def accumulate(nv,evindex,atomindex,sign,ylo,yhi,weights,first,last,direct=False):
    n=1
    while n<nv:n*=2
    mn=np.zeros(2*n,np.int64);lazy=np.zeros(2*n,np.int64);masses=np.zeros(nv,np.int64)
    p=0;best=np.int64(2**60);cells=np.int64(0);winner=-1
    for k in range(len(first)):
        while p<len(evindex) and evindex[p]==k:
            j=atomindex[p];w=sign[p]*weights[j]
            if direct:masses[ylo[j]:yhi[j]]+=w
            else:add(mn,lazy,1,0,n,ylo[j],yhi[j],w)
            p+=1
        if first[k]>=0:
            z=np.min(masses[first[k]:last[k]]) if direct else query(mn,lazy,1,0,n,first[k],last[k])
            if z<best:best=z;winner=k
            cells+=last[k]-first[k]
    return best,cells,winner

