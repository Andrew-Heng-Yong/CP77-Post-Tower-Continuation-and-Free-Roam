"""Independent narrow source review of Brendan revision02; no runtime output."""
from investigate import *
def main():
    base=W/'prealpha/quest_restoration_qr13/worker_b/revision_02';proposal=read(base/'proposal.json');pins=read(base/'source_pins.json');checks=[]
    def ck(name,ok,detail):
        assert ok,name
        checks.append({'name':name,'pass':True,'evidence':detail})
    models={}
    for r in pins:
        p=Path(r['source_json']);expected=r.get('source_json_sha256',r.get('json_sha256'));ck('jsonpin '+r['depot'],sha(p)==expected,str(p))
        if r.get('binary'):ck('rawpin '+r['depot'],sha(r['binary'])==r['sha256'],r['sha256'])
        models[r['depot']]=Resource(read(p)).normalize()
    native=models[r'base\quest\minor_quests\mq037\mq037_brendan.questphase'];bug=models[r'base\quest\bugfixing\minor_quests\mq037\mq037_quest_bugfixes.questphase'];current=models[proposal['runtime_resource']]
    ck('current quarantine remains connected',['1004','True','1008','In']in current['graphs']['root']['edges'],'1004 True→1008Refused; no unchanged freshIn1 admission')
    ck('exact native external reinjection name',native['graphs']['root']['nodes']['68']['payload']['socketName']['$value']==proposal['new_external_input_socket'],'native root68CYB-661474_reinject')
    ck('native reinjection path bypasses early initializer',['68','Out','28','CYB-661474_reinject']in native['graphs']['root']['edges']and['162','Out','140','In1']in native['graphs']['root/28']['edges'],'root68→28/162→140In1; not service_point/girlfriend debug setup')
    final=native['graphs']['root/28/140'];ck('only prospective native Theo spawn retained',final['nodes']['10']['payload']['actions'][0]['type']['communityEntryPhaseName']['$value']=='brendan_found','native final0→10 activatesgirlfriend brendan_found; actor absence guard mandatory')
    without_success=copy.deepcopy(final);without_success['edges']=[e for e in final['edges']if e[0]!='6']
    ck('root questSucceeded dominates reward11', '11'not in reach(without_success,['0']), 'Native5objectiveSucceeded→6rootSucceeded→11QuestRewards.mq037_done→9done1; completed root rejected by gate')
    ck('cleanup native1h andoutside retained',final['nodes']['15']['payload']['condition']['type']['hours']==1 and final['nodes']['16']['payload']['condition']['type']=='IsOutside','native scene bad_news_out→15timer1h→16outside→17despawn, join completion checkpoint')
    seam=read(base/'native_final_seam.json');gate=seam['official_actor_gate'];ck('actor gate exact absence ANDactive final objective',gate['operation']=='AND'and gate['conditions'][0]['type']['comparisonParams']['comparisonType']=='LessOrEqual'and gate['conditions'][0]['type']['comparisonParams']['count']==0 and gate['conditions'][1]['type']['state']=='Active','No actor-absence-only claim; 04talkTheo must remain Active')
    anti=bug['graphs']['root/38/100'];ck('official anti-scene sixfalse AND',all([str(i),'False','7',f'In{slot}']in anti['edges']for i,slot in[(3,1),(4,2),(5,3),(6,4),(8,6),(9,5)]),'NoTrue scene branch toinject_out; safe_out defers')
    ck('official sixsecond delay before scene conditions',anti['nodes']['14']['payload']['condition']['type']['seconds']==6,'root38/10014 sixseconds')
    ck('proposal contains fresh containment and refusal preservation',any('1008' in s for s in proposal['wrapper_changes'])and any('safe_out' in s for s in proposal['wrapper_changes']),'No synthetic freshDumpster entitlement or safe_out reinjection')
    ck('gate rejects all prior private admissions',all(proposal['required_fact_equalities'][f]==0 for f in ['PTFRS23_MQ037_Issued','PTFRS23_MQ037_Entered','PTFRS23_MQ037_Finished','PTFRS23_MQ037_Fault']),'Existing/potential descendants neveradopted/reset')
    ck('preEnding certificate mandatory and matched byname','pre_ending'in proposal['certificate']and'reject post_ending_fallback'in proposal['certificate'],'Current userfallback/Issued1fixture unqualified; no immediate gameplay test')
    scene=models[r'base\quest\minor_quests\mq037\scenes\mq037_01_brendan_scenes.scene']['graphs']['scene'];reachable=reach(scene,[scene['entries']['bad_news_in']]);performers=sorted({v['id']for i in reachable for v in walk(scene['nodes'][i]['payload'])if v.get('$type')=='scnPerformerId'})
    ck('native final scene no explicitJohnny reference','johnny'not in json.dumps([scene['nodes'][i]['payload']for i in reachable]).lower(),{'reachable_nodes':len(reachable),'performerIDs':performers,'scope':'Native exact bad_news_in subtree only; packaged effectiveprovider remains coordinator gate.'})
    result={'status':'APPROVE_BOUNDED_REVISION02_IMPLEMENTATION_BOUNDARY_PENDING_TYPED_GATE_REVIEW','checks':checks,
        'proposal_pin':{'path':str(base/'proposal.json'),'sha256':sha(base/'proposal.json')},'witness_pin':{'path':str(base/'earned_final_witness.json'),'sha256':sha(base/'earned_final_witness.json')},
        'not_a_runtime_pass':['Synthetic witness includes source/absence/no-pending booleans as assumptions, not engine observations. Implementation must derive gates from actual pinned sources and exact certificate/current reads; never add a runtime fact pretending owner proof.',
            'The finalTheo actor absence + six officialscene gates must be evaluated at admission and rechecked before claim after delay, preserving safe_out abort/outside reenter.',
            'HS1 preEnding read-only method must compare selected named facts/journals without changing persistent fields/schema or interpreting absent records as0.',
            'Source retirement main106→109→107Terminating must still contain both minorquest82/6 andbugfix82/4 in final source/package; killedflag alone insufficient.',
            'No finalquest starts if rootSucceeded/Failed, active scene, actorpresent, wrong clerk outcome, missing earned Dumpster/Spray progression, old privateIssued/Entered, fallbackcertificate, stale current/frozen mismatch or unsupported clocks.',
            'No all-Spray/earlierCoin implementation claimed; inherited save-node refresh and engineowner liveness remain LIVE_ONLY.'],
        'coordinator_readback_requirements':['Exact native CYB input added to existing34interface; oldsaved edges1005/1006 unchanged.', 'Full13named earned stage requirements and allfactequalities in both producer/certificate and final graph recheck; no Permit-forged bypass.', 'Nativebody/finalscene/cleanup/reward resources remain exact and effectiveprovider pinned.', 'Regression controls for completed/rewarded state, allguards, fresh containment, originalpendingowner and allunmodifiedQR3–QR8resources.'],
        'runtime_resource_changes':0}
    save('review_brendan_revision_02.json',result);print({'status':result['status'],'checks':len(checks)})
if __name__=='__main__':main()
