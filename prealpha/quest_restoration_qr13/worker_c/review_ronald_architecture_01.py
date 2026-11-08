"""Independent exact-source Ronald architecture review; no candidate/runtime writes."""
from pathlib import Path
import collections,hashlib,itertools,json,sys
H=Path(__file__).resolve().parent;W=H.parents[2];A=H.parent/'worker_a'
sys.path.insert(0,str(W/'tools/parity_audit'))
from model import Resource
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def main():
    out=H/'ronald_architecture_01';assert not out.exists();out.mkdir()
    proposal=read(A/'proposal_01.json');manifest=read(H.parent/'provider_validation_01/manifest.json');sources={r['depot']:r for r in manifest['resources']};pins=[];models={}
    for depot,r in sources.items():
        assert sha(r['raw'])==r['sha256']and sha(r['json'])==r['json_sha256'];pins.append(r)
        if depot.endswith('.questphase'):models[depot]=Resource(read(r['json'])).normalize()
    tree=models[r'ep1\quest\main_quests\q302\phases\q302_ronald_tree.questphase'];bar=models[r'ep1\quest\main_quests\q302\phases\q302_05_bar.questphase'];main=models[r'ep1\quest\main_quests\q302\q302.questphase']
    checks=[]
    def ck(n,b):checks.append({'check':n,'pass':bool(b)});assert b,n
    def edge(m,g,a,s,b,t):return[str(a),s,str(b),t]in m['graphs'][g]['edges']
    ck('native contact starts after enabled wait and native approach',edge(tree,'root',2,'Out',12,'In')and edge(tree,'root',12,'Out',11,'In1')and tree['graphs']['root']['nodes']['12']['reads'][0]['factName']=='q302_ronald_messages_enabled')
    ck('native spatial contact branch input',edge(tree,'root/11',0,'Out',158,'In'))
    required=[[0,'Out',158,'In'],[158,'False',159,'In'],[158,'True',154,'In'],[154,'Out',23,'In'],[159,'Out',121,'NonCallable'],[23,'Out',121,'NonCallable'],[23,'Out',155,'In'],[155,'Out',156,'In']]
    ck('proposal retains native8node contact prefix exactly',all(edge(tree,'root/11',*r)for r in required)and proposal['phase_operations'][1]['205']['keep_internal_edges_exact']==required)
    ck('native contact notification true/false and3secHUD preserved',tree['graphs']['root/11']['nodes']['23']['payload']['type']['params'][0]['sendNotification']==1 and tree['graphs']['root/11']['nodes']['159']['payload']['type']['params'][0]['sendNotification']==0 and tree['graphs']['root/11']['nodes']['155']['payload']['condition']['type']['seconds']==3)
    ck('both ordinary native main/bar Out1 are nonterminating',main['graphs']['root']['nodes']['44']['payload']['type']=='NonTerminating'and bar['graphs']['root']['nodes']['1']['payload']['type']=='NonTerminating')
    ck('bar handoff deactivates old Ronald phase before tree receipt',edge(bar,'root/128',2,'Out',3,'In')and bar['graphs']['root/128']['nodes']['2']['payload']['actions'][0]['type']['action']=='Deactivate'and bar['graphs']['root/128']['nodes']['3']['writes'][0]['factName']=='q302_ronald_tree')
    ck('bar lease still exists after tree receipt until delayed termination',edge(bar,'root/128',3,'Out',4,'In')and edge(bar,'root/128',9,'Out',7,'In')and bar['graphs']['root/128']['nodes']['7']['payload']['condition']['type']['seconds']==1 and edge(bar,'root/128',7,'Out',1,'In')and edge(bar,'root',128,'Out1',28,'In')and bar['graphs']['root']['nodes']['28']['payload']['type']=='Terminating')
    late=[bar['graphs']['root/128']['nodes'][str(i)]for i in [4,5,6,9,7,1]]
    ck('no additional actor/community commands after native tree receipt',all(n['type']not in ['questSpawnManagerNodeDefinition','questCharacterManagerNodeDefinition','questAICommandNodeDefinition']for n in late))
    ck('native exact same bar prefab is shared by original tree/mainbar',tree['root_prefabs']==['#q302_pr_bar']and'#q302_pr_bar'in bar['root_prefabs'])
    sectorpin=read(W/'prealpha/quest_restoration_qr8/worker_b/enrollment_verification_03/evidence.json')['source_pins'][-1];assert sectorpin['depot'].endswith('quest_7abca2b8d18f8562.streamingsector')and sha(sectorpin['json'])==sectorpin['json_sha256']
    sector=Resource(read(sectorpin['json']));defs=[sector.d(h)for h in sector.root['nodes']];types=dict(collections.Counter(n['$type']for n in defs));ck('exact75bar definitions have no autonomous entity/puppet/community spawner',len(defs)==75 and set(types)=={'worldAISpotNode','worldTriggerAreaNode','worldVehicleForbiddenAreaNode','worldPhysicalDestructionNode','worldGuardAreaNode'})
    guard=next(n for n in defs if n['$type']=='worldGuardAreaNode');ck('guard area community lists empty',not guard['communityEntries']and not guard['combatCommunityEntries'])
    ck('bar lease proposed before trigger in existing guardedchild5',proposal['phase_operations'][0]['node_path']=='root/5'and proposal['phase_operations'][0]['do_not_add_to_resource_root']and proposal['phase_operations'][0]['do_not_delay_until_inside_trigger_or_contact_child'])
    ck('only2existingresources and no news/XL/REDS changes',len(proposal['runtime_allowlist'])==2 and proposal['preservation_allowlist']['no_new_depot_or_archivexl_registration_required']and proposal['preservation_allowlist']['no_redscript_change_expected'])
    # New contact child requires an actual end; native prefix-only proposal does not have one.
    prefix_ids=set(proposal['phase_operations'][1]['205']['keep_node_ids']);has_terminal=any(tree['graphs']['root/11']['nodes'][str(i)]['type']=='questOutputNodeDefinition'for i in prefix_ids)
    ck('native terminating and AND templates exist',tree['graphs']['root/11']['nodes']['1']['payload']['type']=='Terminating'and tree['graphs']['root/11']['nodes']['67']['type']=='questLogicalAndNodeDefinition')
    cases=[]
    for branch,second in [('outside','159.Out'),('inside','156.Out_after_3s_HUDrestore')]:
        for order in itertools.permutations(['121.Out_contactNonCallable',second]):
            seen=set();at=None
            for index,event in enumerate(order,1):
                seen.add('contact'if event.startswith('121')else'branch')
                if seen=={'contact','branch'}:at=index
            assert at==2;cases.append({'branch':branch,'arrival_order':order,'terminate_after_both':at==2,'HUD_restore_not_cancelled':branch!='inside'or second in order})
    result={'status':'REQUEST_SMALL_CONTACT_CHILD_CLEANUP_REVISION','proposal':str(A/'proposal_01.json'),'proposal_sha256':sha(A/'proposal_01.json'),'checks':checks,'source_pins':pins,'sector_source':sectorpin,'bar_definition_types':types,
        'supported_architecture':['Restore onlynative839options3/4withtheirpredicates, keep5hidden; receipt onlyactual1755Yes path.','Reuse exactsharednativebarprefab inexistingguardedchild5, no clones/newactors/IDs. Nativehandoff demonstrably permits sharedbarlease, so exclusive barretirement is not required.','ExactInactive+futureconsent+ContactIssued0 guard; originalnative spatial/HUD contact prefix; no old news/timers/adoption.'],
        'blocking_implementation_revision':{'id':'CONTACT_CHILD_MISSING_TERMINATION','observed_prefix_has_terminating_output':has_terminal,'reason':'Eight-node prefix has no terminating output or completionjoin; child205 remains open after contact/HUD operations. Need explicit bounded cleanup, not earlytermination thatcancels3secondHUDrestore.','source_templates':{'AND':'native tree/root11/node67, change5inputs to2innewlocalscope','output':'native tree/root11/node1 TerminatingOut1'},'required_added_edges':[[121,'Out','join','In1'],[159,'Out','join','In2'],[156,'Out','join','In2'],['join','Out','end','In']],'independent_branch_interleavings':cases},
        'limits':['This is architecture/source review, not actual JSON/serialized package approval.','Old savedB0child acquiring newlydeclaredprefab/newedge refresh remainsunproved.','Vehicle forbidden/deescalation notifier persistent state and actualsharedlease execution remainLIVE_ONLY.','OriginalnativeRonaldTree retirement must retain exact ep1additional cut4 ancestry; killedflagalone notproof.','ContactIssued prevents futureattempts; no unsupported partialbootstrap replay or syntheticconsentrecovery.']}
    assert has_terminal is False
    (out/'review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print({'status':result['status'],'source_checks':len(checks),'bar_nodes':len(defs),'cleanup_interleavings':len(cases)})
if __name__=='__main__':main()
