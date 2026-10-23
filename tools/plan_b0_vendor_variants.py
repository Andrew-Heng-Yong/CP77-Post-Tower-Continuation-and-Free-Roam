"""Freeze six individually reviewed variants; never broaden the old 25 cohort."""
import hashlib
import math
from plan_b0_ordinary_vendor_batch import ROOT, OUT, read, resource, graph_at, nm, walk
from finalize_b0_ordinary_vendor_batch import ALLOWED
from test_b0_ordinary_vendor_batch import canonical, handles
import json

BASE = ROOT / 'research/b0_vendor_variants'
KEYS = {
    'bls_ina_se1_gunsmith_02': ('badlands_gun', 'Badlands gun shop 02', 28),
    'bls_ina_se5_foodshop_01': ('badlands_food', 'Badlands food shop 01', 14),
    'pac_wwd_melee_01': ('westwind_melee', 'West Wind melee shop', None),
    'std_rcr_clothingshop_01': ('rancho_clothes', 'Rancho Coronado clothing shop', None),
    'std_rcr_medicstore_01': ('rancho_meds', 'Rancho Coronado medical shop', None),
    'wbr_jpn_medic_01': ('japantown_meds', 'Japantown medical shop', None),
}

def main():
    markers = read(BASE / 'marker_evidence.json')
    sites = []
    for r in read(OUT/'owner_audit.json'):
        if r['id'] not in KEYS:
            continue
        key, label, setup = KEYS[r['id']]
        assert r['disposition'] == 'deferred' and len(r['actors']) == 1
        assert len(r['inner_edges']) == 6
        assert set(r['quest_types']) <= ALLOWED
        assert not any(f.startswith(('q0','q1','q2','q3','mq','sq','sts_')) for f in r['scene_fact_writes'])
        root = resource(r['source']); h = handles(root)
        outer = nm(graph_at(root, 'root/node'+str(r['outer'])))
        # No unaccounted phase-prefab ownership may be discarded.
        assert nm(root['graph']['Data'])[r['outer']]['phaseInstancePrefabs'] == []
        assert outer[r['phase']]['phaseInstancePrefabs'] == []
        def resolve(ref):
            rows = [m for m in markers if m['reference'] == ref]
            if not rows: return None
            p = {k: rows[0][k] for k in ('x','y','z')}
            assert all(math.dist(list(p.values()), [m[k] for k in p]) < .1 for m in rows)
            return p
        scene_pos = resolve(r['scene_marker']); assert scene_pos, r['id']
        far_pos = resolve(r['far']['reference'])
        # Use the exact vanilla distance reference where available. Unresolved
        # departure anchors use the documented, previously tested scene fallback.
        position = far_pos or scene_pos
        radius = r['far']['radius'] + (0 if far_pos else 5)
        # Separate rearm threshold prevents boundary chatter and matches the
        # already-tested shared exit-driver pattern.
        rearm = min(radius - 5, r['outer_distance']['radius'] - 5)
        r.update(key=key,label=label,prefix=f'PTFRB0VV{len(sites)+1:02d}_',
                 setup_node=setup, setup_payload=canonical(outer[setup],h) if setup else None,
                 position=position,scene_position=scene_pos,exit_radius=radius,rearm_radius=rearm,
                 anchor_policy='exact original departure reference' if far_pos else 'scene anchor fallback; vanilla departure radius + 5m',
                 teleport_verified=False,disposition='reviewed_variant')
        sites.append(r)
    assert len(sites)==6
    (BASE/'cohort.json').write_text(json.dumps({'schema':1,'sites':sites,'status':'STATIC_REVIEWED_NOT_LIVE_TESTED'},indent=2)+'\n')
    for s in sites:
        print(s['key'],s['position'],'exit',s['exit_radius'],'rearm',s['rearm_radius'],s['anchor_policy'])

if __name__ == '__main__': main()
