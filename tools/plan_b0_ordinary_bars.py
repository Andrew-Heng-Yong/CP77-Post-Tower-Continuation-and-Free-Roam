"""Four statically reviewed bar owners; keep full vanilla scene semantics."""
import math,json
from audit_b0_ordinary_bars import DEST,KEYS
from plan_b0_ordinary_vendor_batch import ROOT,read

def main():
    audit=read(DEST/'scene_audit.json');markers=read(DEST/'marker_evidence.json');sites=[]
    for a in audit:
        s=a['owner']; key,label=KEYS[s['id']]
        # Multiple role names bind the SAME spawn set, not additional actors.
        assert {(r['spawn']['reference'],r['spawn']['entryName']) for r in a['actors']}=={(s['spawn']['reference'],s['spawn']['entry'])}
        assert len(s['inner_edges'])==6 and len(s['outer_edges'])==7
        active=[f for f in s['scene_fact_writes'] if f.endswith('_drinking_active')]
        assert len(active)==1
        assignments=[o['value'] for n in a['nodes'] for o in n['ops'] if o.get('factName')==active[0]]
        assert set(assignments)=={0,1},(key,assignments)
        # Scene-controlled activation is only for the scene-owned bottle, never a quest root.
        spawned={p['spawn']['dynamicEntityUniqueName'] for p in a['props'] if p['plan']=='spawnDespawn'}
        for n in a['nodes']:
            for o in n['ops']:
                if o.get('$type')=='questScene_NodeType':
                    assert o['entityReference']['dynamicEntityUniqueName'] in spawned
        m=[m for m in markers if m['reference']==s['scene_marker']];assert m
        pos={k:m[0][k] for k in ('x','y','z')}
        assert all(math.dist(list(pos.values()),[r[k] for k in pos])<.1 for r in m)
        s.update(key=key,label=label,prefix=f'PTFRB0BAR{len(sites)+1:02d}_',setup_node=None,setup_payload=None,
                 position=pos,scene_position=pos,exit_radius=s['far']['radius']+5,rearm_radius=45,
                 drinking_fact=active[0],teleport_verified=False,
                 anchor_policy='original scene anchor; vanilla far radius + 5m; not a verified player landing',
                 expected_spawn_entries=1,disposition='static_reviewed_bar_not_live_tested')
        sites.append(s)
    assert len(sites)==4
    existing=read(ROOT/'research/b0_ordinary_vendor_batch/cohort.json')
    prior=existing['sites']+existing['existing_owners']+read(ROOT/'research/b0_vendor_variants/cohort.json')['sites']
    assert not {(s['spawn']['reference'],s['spawn']['entry']) for s in sites}&{(s['spawn']['reference'],s['spawn']['entry']) for s in prior}
    (DEST/'cohort.json').write_text(json.dumps({'schema':1,'sites':sites,'status':'STATIC_REVIEWED_NOT_LIVE_TESTED'},indent=2)+'\n')
    for s in sites:print(s['key'],s['position'],'exit',s['exit_radius'],'drinking',s['drinking_fact'])

if __name__=='__main__':main()
