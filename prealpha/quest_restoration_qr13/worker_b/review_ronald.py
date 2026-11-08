"""Independent source-level Ronald proposal review. Not a runtime/serialization test."""
from pathlib import Path
import copy,hashlib,json,sys
H=Path(__file__).resolve().parent;W=H.parents[2]
sys.path.insert(0,str(W/'tools/parity_audit'));from model import Resource
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():yield from walk(v)
    elif isinstance(x,list):
        for v in x:yield from walk(v)
def main():
    out=H/'reviews/ronald_proposal_02';assert not out.exists();out.mkdir(parents=True)
    a=W/'prealpha/quest_restoration_qr13/worker_a';proposal=read(a/'proposal_01.json');contract=read(a/'enrollment_contract_01.json');models={};pins=[];checks=[]
    for r in contract['source_pins']:
        assert sha(r['json'])==r['json_sha256']and sha(r['raw'])==r['raw_sha256'];models[r['depot']]=Resource(read(r['json'])).normalize();pins.append({'path':r['json'],'sha256':r['json_sha256']})
    rn=models[r'ep1\quest\main_quests\q302\phases\q302_ronald_tree.questphase'];native=models[r'ep1\quest\main_quests\q302\scenes\q302_05_bar.scene'];current=models[r'towercontinued\b0_story_eight\ronald.scene'];owner=models[r'towercontinued\b0_story_eight\ronald.questphase'];ng=native['graphs']['scene'];cg=current['graphs']['scene'];prefix=rn['graphs']['root/11']
    def check(name,ok,evidence):checks.append({'check':name,'pass':bool(ok),'evidence':evidence});assert ok,name
    required=[['839','0:3','1422','0:0'],['839','0:4','1451','0:0']]
    check('native missing two topic outputs exact',all(x in ng['edges']and x not in cg['edges']for x in required),required)
    op=proposal['scene_operations'][0];check('topic predicates and outputs copied together',op['option_indices']==[3,4]and op['preserve_native_conditions']and op['keep_option_5_hidden']and op['native_destinations']==[[839,'0:3',1422,'0:0'],[839,'0:4',1451,'0:0']],'keep exact known<1 vs known>=1 predicates')
    check('actual Yes route exact',all(x in ng['edges']for x in [['1746','0:0','1750','0:0'],['1750','2:0','1755','0:1']]),'Yes leads real native enabled writer')
    writes=ng['nodes']['1755']['writes'];check('real enabled native write exact1',len(writes)==1 and writes[0]['factName']=='q302_ronald_messages_enabled'and writes[0]['setExactValue']==1 and writes[0]['value']==1,writes)
    check('consent private receipt solely after1755',proposal['scene_operations'][1]['native_writer_node']==1755 and proposal['scene_operations'][1]['edge']==[1755,'0:0',60000,'0:1']and proposal['scene_operations'][1]['no_other_receipt_writer'],'no root/startup/oldenabled receipt adoption')
    check('No/offered/counter payloads already native',all(cg['nodes'][i]['payload']==ng['nodes'][i]['payload']for i in ['1730','1731','1769','1751']),'must remain exact in actual candidate')
    lease=proposal['phase_operations'][0];check('lease belongs guarded full child5 lifetime',lease['node_path']=='root/5'and lease['prefab']=='#q302_pr_bar'and lease['do_not_add_to_resource_root']and lease['do_not_delay_until_inside_trigger_or_contact_child'],'acquisition before approach and retained during outside/cut loop')
    bridge=proposal['phase_operations'][1];check('bridge attaches repeated existing approach',bridge['source']==[2,'Out']and any(e[0]=='2'and e[1]=='Out'for e in owner['graphs']['root/5']['edges']),'no actor owner/restart created')
    conditions=bridge['203']['conditions'];check('strict prospective consent subscription claim and Inactive',conditions==[{'fact':'PTFRQR13_RonaldEnrollment_ConsentEarned','comparison':'GreaterOrEqual','value':1},{'fact':'q302_ronald_messages_enabled','comparison':'GreaterOrEqual','value':1},{'fact':'PTFRQR13_RonaldEnrollment_ContactIssued','comparison':'Equal','value':0},{'journal':'ep1/contacts/ronald','class':'gameJournalContact','state':'Inactive','inverted':False}],conditions)
    check('claim before contact child',bridge['new_edges']==[[2,'Out',203,'In'],[203,'Out',204,'In'],[204,'Out',205,'In1']]and bridge['204']['fact']=='PTFRQR13_RonaldEnrollment_ContactIssued'and bridge['204']['value']==1,'private sticky receipt excludes normal duplicate reentry')
    ids=set(map(str,bridge['205']['keep_node_ids']));exact=[e for e in prefix['edges']if e[0]in ids and e[2]in ids]
    check('contact prefix exact source8nodes',ids=={'0','158','159','154','23','121','155','156'}and {tuple(x)for x in bridge['205']['keep_internal_edges_exact']}=={(int(a),b,int(c),d)for a,b,c,d in exact},exact)
    check('spatial notification branch retained',prefix['nodes']['158']['payload']['condition']['type']=='IsInside'and prefix['nodes']['158']['payload']['condition']['triggerAreaRef']['$value']=='#q302_tr_ronald_area_02_closer','outside silent159, inside showHUD154 then notified23')
    check('both AddContact actions exactRonald notification flags',all(prefix['nodes'][i]['payload']['type']['params'][0]['addContact']==1 and prefix['nodes'][i]['payload']['type']['params'][0]['contact']['realPath']=='ep1/contacts/ronald'for i in ['159','23'])and prefix['nodes']['159']['payload']['type']['params'][0]['sendNotification']==0 and prefix['nodes']['23']['payload']['type']['params'][0]['sendNotification']==1,'do not simplify spatial branch')
    check('native HUD restore remains3seconds',prefix['nodes']['155']['payload']['condition']['type']['seconds']==3 and prefix['nodes']['154']['payload']['type']['visibility']=='ForceShow'and prefix['nodes']['156']['payload']['type']['visibility']=='TierVisibility','preserve identical HUDentry list and payload')
    check('NonCallable state native socket retained',['159','Out','121','NonCallable']in exact and ['23','Out','121','NonCallable']in exact,'normal native Ronald contact is noncallable; Active contact journal is separate')
    src=next(r['json']for r in contract['source_pins']if r['depot']==r'towercontinued\b0_story_eight\ronald.scene');root=read(src)['Data']['RootChunk'];johnny=next(x for x in root['actors']if x['actorId']['id']==0)
    check('private Johnny remains disabled at acquisition',johnny['spawnDespawnParams']['isEnabled']==0 and johnny['spawnDespawnParams']['spawnOnStart']==0 and johnny['spawnDespawnParams']['alwaysSpawned']==0,'actual candidate must retain all current actor/binding definitions')
    check('newly reached performers onlyRonald andV',set(contract['reenabled_scope']['new_performer_ids'])=={1281,3841,4294967040},'1281 actor5Ronald,3841 playeractor15,4294967040 sentinel; OnlyIfAlive metadata is not an extra spawn')
    check('native current topic names fact renames preserved',proposal['preservation_allowlist']['no_new_depot_or_archivexl_registration_required']and proposal['preservation_allowlist']['no_redscript_change_expected'],'future-news protocol/timers/Armed/sent require byte equality in root package gate')
    mutations=[]
    for fault,detect in [('drop topic3 output',required[0]not in [e for e in ng['edges']if e!=required[0]]),('widen contactInactive toFailed',({**conditions[-1],'state':'Failed'})!=conditions[-1]),('remove consent provenance',len(conditions[1:])!=4),('remove onceonly claim',conditions[2]['value']==0),('movebarlease to205',lease['node_path']!='root/5/205'),('changeHUDdelay',prefix['nodes']['155']['payload']['condition']['type']['seconds']!=4)]:
        mutations.append({'fault':fault,'detected_by_exact_source_constraint':detect});assert detect
    result={'status':'APPROVED_SOURCE_LEVEL_PROPOSAL_WITH_REQUIRED_SERIALIZED_REVIEW','checks':checks,'count':len(checks),'mutations':mutations,'source_pins':pins,'proposal_path':str(a/'proposal_01.json'),'proposal_sha256':sha(a/'proposal_01.json'),
        'required_before_final_acceptance':['Actual typed/readback delta allowlist and exact contact-payload/socket comparison','Global new fact/local node collision checks','Native bar75definition scope and shared ownership review already assigned separately; this review does not recount all placement nodes','Old running-child acquiring new prefab/edge and interruption during3second HUD path remain LIVE_ONLY; preserve limitation','No upgrade blanketPASS from fresh entry sourceproof','Exact unchanged future-news/gig resource byte preservation and Core package proof'],
        'limits':'Concept/source review, not candidate serialized, compile or gameplay verification. Repeated approach/node pause reentry scheduling is engine-dependent; private once-only claim and exactInactive are required, no stronger atomics claim.',
        'runtime_changes':0}
    (out/'review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print({'status':result['status'],'checks':len(checks),'mutation_controls':len(mutations)})
if __name__=='__main__':main()
