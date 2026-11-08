"""Fresh-provider Ronald retirement/shared-lease route evidence; no resource writes."""
from investigate import *
def main():
    providers=read(W/'prealpha/quest_restoration_qr13/provider_validation_01/manifest.json')['resources'];by={r['depot']:r for r in providers}
    assert len(by)==10
    models={}
    for d,r in by.items():
        assert sha(r['raw'])==r['sha256']and sha(r['json'])==r['json_sha256']
        if not d.endswith('.streamingsector'):models[d]=Resource(read(r['json'])).normalize()
    ep=r'ep1\quest\ep1.questphase';ad=r'ep1\quest\ep1_additional_game_elements.questphase';pc=r'ep1\quest\ep1_persistent_content.questphase';bar=r'ep1\quest\main_quests\q302\phases\q302_05_bar.questphase';cal=r'ep1\quest\main_quests\q302\phases\q302_caliente_persistent_content.questphase';pro=r'ep1\quest\main_quests\q302\phases\q302_protest.questphase'
    g=models[ep]['graphs']['root/10'];assert ['8','Out','9','In']in g['edges']and ['9','Out','10','In']in g['edges']
    assert all(['9','CutSource',str(i),'CutDestination']in g['edges']for i in[3,4,5])
    assert g['nodes']['9']['type']=='questCutControlNodeDefinition'
    assert g['nodes']['10']['payload']['type']['factName']=='q307_ep1_killed'
    assert g['nodes']['4']['payload']['phaseResource']['DepotPath']['$value']==ad
    a=models[ad]['graphs']['root'];assert a['nodes']['2']['payload']['phaseResource']['DepotPath']['$value']==pc
    p=models[pc]['graphs']['root/30'];assert p['nodes']['26']['payload']['phaseResource']['DepotPath']['$value']==RN
    assert p['nodes']['25']['payload']['phaseResource']['DepotPath']['$value']==cal
    assert p['nodes']['33']['payload']['phaseResource']['DepotPath']['$value']==pro
    late=models[bar]['graphs']['root/128'];assert late['nodes']['2']['payload']['actions'][0]['type']['action']=='Deactivate'
    assert late['nodes']['2']['payload']['actions'][0]['type']['communityEntryName']['$value']=='scav_hobo'
    assert late['nodes']['3']['payload']['type']['factName']=='q302_ronald_tree'
    assert late['nodes']['1']['payload']['type']=='Terminating'
    post=reach(late,['3']);assert all(late['nodes'][n]['type']!='questSpawnManagerNodeDefinition'for n in post)
    assert ['128','Out1','28','In']in models[bar]['graphs']['root']['edges']
    assert models[bar]['graphs']['root']['nodes']['28']['payload']['type']=='Terminating'
    sector=next(r for d,r in by.items()if d.endswith('.streamingsector'));rr=Resource(read(sector['json']));defs=[rr.d(x)for x in rr.root['nodes']];types=dict(collections.Counter(x['$type']for x in defs))
    assert types=={'worldAISpotNode':45,'worldTriggerAreaNode':26,'worldVehicleForbiddenAreaNode':2,'worldPhysicalDestructionNode':1,'worldGuardAreaNode':1}
    owners={d:models[d]['root_prefabs']for d in[RN,bar,cal,pro]};assert all('#q302_pr_bar'in v for v in owners.values())
    historical=read(W/'prealpha/quest_restoration_qr7/worker_b/readback_01/manifest.json');same=[]
    for r in historical:
        if r['depot']in by:same.append({'depot':r['depot'],'current_raw_sha256':by[r['depot']]['sha256'],'historical_raw_sha256':r['raw_sha256'],'matches':by[r['depot']]['sha256']==r['raw_sha256']})
    assert all(r['matches']for r in same)
    result={'status':'PASS_EXACT_PERSISTENT_CUT_AND_NATIVE_SHARED_BAR_HANDOFF_SOURCE','provider_pins':providers,'historical_raw_equivalence':same,
        'native_original_news_retirement':{'owner':RN,'cut_resource':ep,'graph':'root/10','condition_node8':g['nodes']['8']['payload'],'cut_node9':g['nodes']['9']['payload'],'receipt_node10':g['nodes']['10']['payload'],'edges':[e for e in g['edges']if e[0]in['8','9','10']],
            'ancestor_chain':[{'depot':ep,'graph':'root/10','node':'4','child':ad},{'depot':ad,'graph':'root','node':'2','child':pc},{'depot':pc,'graph':'root/30','node':'26','child':RN}],
            'scope':'Exact original persistent Ronald/news subtree is descendant of native cut4 before receipt10. No assertion that killedflag alone proves every installed/saved original owner retired; provider and genuine native route matter.'},
        'native_shared_bar_handoff':{'depot':bar,'graph':'root/128','edges':late['edges'],'nodes':{i:n['payload']for i,n in late['nodes'].items()},'post_tree_signal_nodes':sorted(post,key=int),
            'parent_terminating_edge':['128','Out1','28','In'],'parent_terminating_output':models[bar]['graphs']['root']['nodes']['28']['payload'],
            'shared_prefab_owners':owners,'conclusion':'Native bar cleanup deactivates scav_hobo a before writing q302_ronald_tree1, then only finishedfact/vehicleoff/railvariant/1second/end remain. Native persistent RonaldTree can acquire samebar before mainbar finishes; coownership is authored, not an exclusive bar retirement claim.'},
        'exact_bar_sector_scope':{'provider':sector,'definitions':len(defs),'type_counts':types,'definition_payloads':defs,'placement_evidence':'QR7/worker_b/bar_check_02/evidence.json and raw buffer973EF5...:75current-layout setup/global-ID mappings from same rawsector bytes18FA2E...; independentQR13 reviewer rechecks definitions/setup scope.',
            'scope_limit':'One exact native compiledsector, not a claim every world node under a high-level prefab has been semantically audited. No new/cloned AISpot, actor or global node identities proposed.'},
        'lease_proposal_location':'Existing guarded B0 topnode5.PhaseInstancePrefabs append exactnative#q302_pr_bar entry. Acquire before internaltrigger2, hold for existingchildlifetime. No new global IDs or community.',
        'remaining_limits':['Already-running savedB0 child acquiring newlydeclared prefab remainsLIVE_ONLY.','Closedengine saved cut/lease interpretation and notification/UI timing remainruntime boundaries.','No general oldmessages_enabled1/contactInactive adoption.']}
    save('provider_routes_01.json',result);print({'status':result['status'],'current_providers':len(providers),'historical_matches':len(same),'sector_definitions':len(defs),'mainbar_exclusive_retirement_claimed':False})
if __name__=='__main__':main()
