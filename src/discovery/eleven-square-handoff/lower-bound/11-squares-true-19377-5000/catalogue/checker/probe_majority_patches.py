"""Selected-row exact true-polygon patch experiment; not a global proof."""
from pathlib import Path
from fractions import Fraction as F
import argparse,json,sys,time,hashlib
from majority_probe import load_probe,target_job,interval_job
from majority_mixed import geometry
from majority_patches import PatchVerifier

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'research/majority_patches'))
from low_cells import extract_low_cells

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate',type=Path,default=ROOT/'research/majority_patches/true-majority-probe.json')
    parser.add_argument('--row',type=int,default=0)
    parser.add_argument('--refinement',type=int,default=1,
                        help='Check only the first 1/N of this row; a selected subinterval, not the entire row')
    parser.add_argument('--subdivisions',type=int,default=4)
    parser.add_argument('--max-cells',type=int,default=0)
    parser.add_argument('--max-nodes',type=int,default=1000000)
    parser.add_argument('--unconditional',action='store_true')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();start=time.monotonic()
    c,old,data,jobs,margin=load_probe(args.certificate)
    job=target_job(c,old,jobs,margin,args.row)
    a,b=map(F,old['entries'][args.row][:2])
    if args.refinement<1:raise ValueError('Positive refinement factor required')
    if args.refinement>1:
        b=a+(b-a)/args.refinement;job=interval_job(c['A'],c['L'],a,b,margin)
    arrays,meta=geometry(*data,*job,meta=True,subdivisions=args.subdivisions,
                         domain_conditional=not args.unconditional)
    print('GEOMETRY',round(time.monotonic()-start,3),'seconds',len(meta['rect']),'rectangles',flush=True)
    low=extract_low_cells(arrays,meta,c['minimum_units'])
    print('LOW',json.dumps(low.stats),flush=True)
    verifier=PatchVerifier(data,meta,c['minimum_units'],args.max_nodes)
    answer={'status':('PASS_SELECTED_SUBINTERVAL_TRUE_MAJORITY_PATCHES_NOT_A_GLOBAL_PROOF'
                       if args.refinement>1 else
                       'PASS_SELECTED_ROW_TRUE_MAJORITY_PATCHES_NOT_A_GLOBAL_PROOF')}
    # Worst surrogate cells first makes failures reviewable sooner.
    boxes=sorted(low.merged_boxes(),key=lambda box:box[-1])
    for index,cell in enumerate(boxes):
        if args.max_cells and index>=args.max_cells:
            answer={'status':'INCOMPLETE_CELL_LIMIT'};break
        x0,x1,y0,y1,z=cell
        result=verifier.verify_cell((x0,x1,y0,y1),z)
        if not result['status'].startswith('PASS'):
            answer=result;answer['merged_box_index']=index;answer['surrogate_units']=z
            if 'point' in result:
                u,v=result['point'];C,S,R,scale=(meta[k] for k in ('C','S','R','scale'))
                x=F(c['L'])/2+(C*u-S*v)/(R*R*scale)
                y=F(c['L'])/2+(S*u+C*v)/(R*R*scale)
                answer['center_xy']=[str(x),str(y)]
                answer['center_xy_decimal']=[float(x),float(y)]
                answer['point']=list(map(str,result['point']))
            break
        if (index+1)%100==0:print('PATCHED',index+1,'NODES',verifier.stats['nodes'],
                                  'SECONDS',round(time.monotonic()-start,2),flush=True)
    answer.update(scope=('One rigorously contained first subinterval of a catalogue row at the proposed target; no full row or global angular certificate'
                         if args.refinement>1 else
                         'One rigorously contained catalogue row at the proposed target; no global angular certificate'),
                  row=args.row,target_side=str(F(c['L'])/F(c['A'])),core_halfangle=str(job[0]),
                  halfangle_interval=[str(a),str(b)],first_subinterval_refinement=args.refinement,
                  core_side=str(job[1]),budget_units=c['budget_units'],threshold_units=c['minimum_units'],
                  certificate_sha256=hashlib.sha256(args.certificate.read_bytes()).hexdigest(),
                  low_cells=low.stats,patch_statistics=verifier.stats,seconds=time.monotonic()-start)
    args.output.write_text(json.dumps(answer,indent=2)+'\n');print(json.dumps(answer,indent=2))

if __name__=='__main__':main()
