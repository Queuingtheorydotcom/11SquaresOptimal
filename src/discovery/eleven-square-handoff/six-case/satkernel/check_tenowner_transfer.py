#!/usr/bin/env python3
"""Derive six exact occupancy-mask exclusions from the ten-owner receipt.

The heavyweight exact continuum verifier is replayed separately to produce
mask800_tenowner_independent_replay.json. This script checks its finite
premises, completed angle intervals, source hashes, and the elementary
owner-support transfer to each eleven-cell superset of the ten owners.
"""
import hashlib
import json
import sys
from fractions import Fraction as F
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
HERE=ROOT/'satkernel'
sys.path.insert(0,str(HERE/'upstream'))
from verify_symmetric_cover import run as verify_cover

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def check():
    packet_path=ROOT/'endpoint/mask800_r35_ext195_tenowner.json'
    report_path=HERE/'mask800_tenowner_independent_replay.json'
    cover_path=HERE/'upstream/center-cover-symmetric-exact.json'
    packet=json.loads(packet_path.read_text());report=json.loads(report_path.read_text())
    cover=json.loads(cover_path.read_text());assert verify_cover()==cover
    assert report['status']=='PASS_EXACT_ASYMMETRIC_MASK_EXCLUSION'
    assert report['packet_sha256']==sha(packet_path)
    assert report['cover_sha256']==packet['cover_sha256']==sha(cover_path)
    assert report['mask_index']==packet['mask_index']==800
    assert report['mask']==packet['mask']==cover['canonical_eleven_cell_subsets'][800]
    assert report['parent_Uplus']==packet['parent_Uplus']
    assert report['conditional_ownership']=='cell_owned_points'
    assert report['conditional_owner_support']==packet['conditional_owner_support']
    for relative,digest in report['dependencies'].items():
        assert sha(ROOT/'checkpoint_extract'/relative)==digest
    T=set(packet['conditional_owner_support'])
    assert len(T)==10 and T<=set(packet['mask'])
    gamma=packet['threshold_units']
    active={i for i,v in enumerate(gamma) if v>0}
    assert active<=T and len(gamma)==16
    certificate=packet['certificate']
    family=json.loads((ROOT/'checkpoint_extract/research/optimality/deficit_geometry/physical_features/family.json').read_text())
    selected_indices=packet['source_physical_feature_indices']
    selected_weights=packet['source_integer_weights']
    assert len(selected_indices)==len(selected_weights)==8
    source_features=[family['features'][i] for i in selected_indices]
    source_site_ids=sorted({j for feature in source_features for j in feature['sites']})
    remap={j:i for i,j in enumerate(source_site_ids)}
    assert certificate['sites']==[family['sites'][j] for j in source_site_ids]
    for i,weight,feature in zip(selected_indices,selected_weights,source_features):
        assert feature['capacity']==1
        if feature['kind']=='point':
            assert certificate['point_weights'][remap[feature['sites'][0]]]==weight
        else:
            group=next(g for g in certificate['features'] if g['source_physical_feature']==i)
            assert group['weight']==weight and group['threshold']==feature['threshold']
            assert group['indices']==[remap[j] for j in feature['sites']]
    assert all(g['kind']=='majority_hull' and
               len(g['indices'])==2*g['threshold']-1 for g in certificate['features'])
    budget=sum(certificate['point_weights'])+sum(g['weight'] for g in certificate['features'])
    assert budget==certificate['budget_units']==report['budget_units']==19
    assert sum(gamma[i] for i in T)==report['threshold_sum_units']==20>budget
    checked={c['cell']:c for c in report['cells']}
    assert set(checked)==set(packet['mask']) and len(report['records'])==report['rows']==4030
    for i in active:
        cell=checked[i]
        assert cell['complete'] and not cell['pending'] and not cell['unresolved']
        cursor=F(0)
        for lo,hi in sorted((F(a),F(b)) for a,b in cell['accepted']):
            assert lo==cursor and hi>lo
            cursor=hi
        assert cursor==1
    lookup={tuple(m):i for i,m in enumerate(cover['canonical_eleven_cell_subsets'])}
    derived=[]
    for extra in sorted(set(range(16))-T):
        M=tuple(sorted(T|{extra}))
        assert len(M)==11 and sum(gamma[i] for i in M)==20
        turned=tuple(sorted(15-i for i in M))
        canonical=min(M,turned)
        index=lookup[canonical]
        derived.append(dict(extra_cell=extra,mask=list(M),canonical_index=index,
                            half_turn_used=M!=canonical))
    assert [v['canonical_index'] for v in derived]==[800,2023,2140,2151,2153,1896]
    print('TEN_OWNER_TRANSFER_PASS',len(derived),'canonical masks:',
          [v['canonical_index'] for v in derived],
          'budget',budget,'threshold',sum(gamma[i] for i in T))
    return derived

if __name__=='__main__':check()
