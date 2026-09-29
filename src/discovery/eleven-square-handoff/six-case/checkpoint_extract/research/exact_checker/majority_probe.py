"""Build rigorously valid selected target rows; never a full certificate."""
from copy import deepcopy
from fractions import Fraction as F
from pathlib import Path
import json
from majority_mixed import validate
from integer_sweep import trig,need

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'source/11-squares-certified-bound-main/global-certificate.json'

def load_probe(path):
    c=json.loads(Path(path).read_text());old=json.loads(SOURCE.read_text())
    # Validate every feature, budget, site orbit, and the original row cover.
    proxy=deepcopy(c);proxy['A']=old['A'];proxy['entries']=old['entries']
    data,jobs,margin=validate(proxy)
    return c,old,data,jobs,margin

def target_job(c,old,oldjobs,margin,row):
    A=F(c['A']);oldA=F(old['A']);L=F(c['L'])
    need(0<margin<A<=oldA,'Invalid probe target')
    a,b,t,oldB=map(F,old['entries'][row]);B=oldB*(A-margin)/(oldA-margin)
    cc,ss=trig(t);g=[];f=[]
    for endpoint in (a,b):
        ec,es=trig(endpoint);g.append(cc*ec+ss*es+abs(ss*ec-cc*es));f.append(ec+es)
    need(A-B*max(g)>=margin,'Target core containment fails')
    r=A*min(f)/2;need(B*(cc+ss)/2<=r<L/2,'Target parent envelope fails')
    return t,B,L/2-r

def interval_job(A,L,a,b,margin):
    """A new exact strict core for one explicitly supplied angle subinterval."""
    A,L,a,b,margin=map(F,(A,L,a,b,margin));t=(a+b)/2
    need(0<=a<b<1 and 0<margin<A,'Invalid probe interval')
    cc,ss=trig(t);g=[];f=[]
    for endpoint in (a,b):
        ec,es=trig(endpoint);dot=cc*ec+ss*es;cross=abs(ss*ec-cc*es)
        need(dot>0 and dot>=cross,'Invalid relative angle range')
        g.append(dot+cross);f.append(ec+es)
    B=(A-margin)/max(g);r=A*min(f)/2
    need(0<B<A and A-B*max(g)==margin,'Core is not strictly contained')
    need(B*(cc+ss)/2<=r<L/2,'Parent envelope fails')
    return t,B,L/2-r
