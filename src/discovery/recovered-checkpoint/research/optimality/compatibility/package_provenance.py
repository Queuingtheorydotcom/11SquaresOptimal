"""Freeze a digest manifest for this bounded compatibility/chain experiment."""
import hashlib,json
from pathlib import Path


def main():
    root=Path(__file__).parent; research=root.parents[1]
    paths=[p for p in root.iterdir() if p.is_file() and p.name!='PROVENANCE.json']
    paths += [root.parent/'global_capture'/name for name in
              ['center-cover-symmetric-exact.json','verify_center_cover.py','verify_symmetric_cover.py',
               'compatibility-kernel-independent-review.json','audit_compatibility_kernel.py']]
    files={str(p.relative_to(research)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
           for p in sorted(paths)}
    out={'status':'FROZEN_BOUNDED_COMPATIBILITY_RESEARCH_PACKET',
         'global_optimality_proved':False,'new_lower_bound_proved':False,'whole_geometric_masks_excluded':0,
         'active_jobs':0,'scope':'Necessary compatibility and checked conditional longitudinal refinements only.',
         'coordinate_convention':'Closed cells; concentric embedding in U_plus container, translated to [0,U_plus]^2.',
         'fine_graph':{'domains':1956,'pairs_checked':1720967,'all_pairs':1793206,'forbidden_pairs':296821,
                       'untested_pairs_treated_as_compatible':72239,'independent_full_graph_replay':False},
         'fine_mask_search':{'canonical_total':2184,'abstract_assignments':1452,'not_reached':732,'whole_masks_excluded':0},
         'chain_mask2045':{'verified_inferences':179,'deleted_states':9,'whole_masks_excluded':0},
         'dependency_root':'research','files':files}
    (root/'PROVENANCE.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'files':len(files),'bytes':sum(v['bytes'] for v in files.values())}))


if __name__=='__main__':main()
