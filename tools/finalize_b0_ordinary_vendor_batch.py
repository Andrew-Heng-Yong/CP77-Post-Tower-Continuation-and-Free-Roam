"""Freeze the reviewed cohort and its dialogue/world-position evidence."""
from __future__ import annotations
import json
import math
from plan_b0_ordinary_vendor_batch import OUT, read

# Reachable service nodes reviewed across this cohort. Rebuild fails on any new
# quest operation; scene resources themselves are never rewritten or packaged.
ALLOWED = set('''questBuild_ConditionType questCameraFocus_ConditionType questConditionNodeDefinition
questDistanceComparison_ConditionType questDistanceCondition questFactsDBCondition
questFactsDBManagerNodeDefinition questGameTimeDelay_ConditionType questLookAtDrivenTurnsNode
questObjectDistance questPauseConditionNodeDefinition questPlayVoiceset_NodeType
questPlayVoiceset_NodeTypeParams questRealtimeDelay_ConditionType questSetVar_NodeType
questSocketDefinition questStatsCondition questSwitchToScenario_NodeType questSystemCondition
questTimeCondition questTriggerCondition questUIManagerNodeDefinition questUniversalRef
questUseWorkspotNodeDefinition questUseWorkspotParamsV1 questUseWorkspotPlayerParams
questValueDistance questVarComparison_ConditionType questVendorPanel_NodeType
questVoicesetManagerNodeDefinition'''.split())


def main():
    audit, markers = read(OUT/'owner_audit.json'), read(OUT/'marker_evidence.json')
    sites, deferred = [], []
    for r in audit:
        if r['disposition'] != 'review':
            continue
        rows = [m for m in markers if m['reference'] == r['scene_marker']]
        if not rows:
            deferred.append({'id': r['id'], 'reason': 'Scene marker position unresolved; no guessed teleport/exit anchor'})
            continue
        first = rows[0]
        assert all(math.dist([first[k] for k in ('x','y','z')], [m[k] for k in ('x','y','z')]) < .1 for m in rows), r['id']
        assert len(r['actors']) == 1, r['id']
        assert set(r['quest_types']) <= ALLOWED, (r['id'], set(r['quest_types'])-ALLOWED)
        assert not any(f.startswith(('q0','q1','q2','q3','mq','sq','sts_')) for f in r['scene_fact_writes']), r['id']
        r.update(prefix=f'PTFRB0OV{len(sites)+1:02d}_',position={k:first[k] for k in ('x','y','z')},
                 marker_evidence=rows, disposition='included',
                 exit_anchor_policy='Vanilla scene-marker position, same tested 55/45m fallback; original native approach NodeRef retained')
        sites.append(r)
    assert len(sites) == 25, len(sites)
    manifest={'schema':1,'status':'REVIEWED_OPT_IN_COHORT_PENDING_BUILD', 'sites':sites,
              'existing_owners':[r for r in audit if r['disposition']=='existing'],
              'deferred':[{'id':r['id'],'reason':'; '.join(r['reasons'])} for r in audit if r['disposition']=='deferred']+deferred,
              'dialogue_contract':'Original scene files referenced unchanged, original entry/socket/location, no reset of dialogue facts. User reports unique dialogue preserved in prior representatives.'}
    (OUT/'cohort.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'{len(sites)} new owners, {len(manifest["existing_owners"])} existing owners kept separate, {len(manifest["deferred"])} simple-shaped candidates deferred')
    for s in sites:
        print(s['prefix'],s['id'],s['category'],s['position'])


if __name__=='__main__': main()
