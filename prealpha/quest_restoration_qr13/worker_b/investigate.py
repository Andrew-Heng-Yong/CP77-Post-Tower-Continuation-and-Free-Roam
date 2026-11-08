"""QR13 bounded Brendan earned-final seam evidence. No runtime modifications."""
from pathlib import Path
import collections,copy,gzip,hashlib,json,sys
H=Path(__file__).resolve().parent;W=H.parents[2]
O=H/'revision_02'
sys.path.insert(0,str(W/'tools/parity_audit'))
from model import Resource
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():yield from walk(v)
    elif isinstance(x,list):
        for v in x:yield from walk(v)
def put(name,x):
    p=O/name;assert not p.exists();p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def edge(m,g,a,s,b,t):return [str(a),s,str(b),t]in m['graphs'][g]['edges']
def ev(c,f,j,other=None):
    t=c['$type']
    if t in ('questFactsDBCondition','questJournalCondition'):return ev(c['type'],f,j,other)
    if t=='questLogicalCondition':
        a=[ev(v,f,j,other)for v in c['conditions']]
        return all(a)if c['operation']=='AND'else any(a)if c['operation']=='OR'else not any(a)
    if t=='questVarComparison_ConditionType':
        if c['factName']not in f:return False
        a=f[c['factName']];b=c['value'];return {'Equal':a==b,'Greater':a>b,'Less':a<b,'GreaterOrEqual':a>=b,'LessOrEqual':a<=b,'NotEqual':a!=b}[c['comparisonType']]
    if t=='questJournalEntryState_ConditionType':return c['path']['realPath']in j and((j[c['path']['realPath']]==c['state'])!=bool(c.get('inverted',0)))
    raise ValueError(t)
def main():
    H.mkdir(parents=True,exist_ok=True);assert not O.exists();O.mkdir();pins=[];models={};checks=[]
    for r in read(W/'prealpha/quest_restoration_qr3/agents/agent_c/verification_02/source_pins.json'):
        if r['depot'].startswith('towercontinued'):continue
        for path,key in [('binary','sha256'),('source_json','source_json_sha256'),('normalized_model','normalized_sha256')]:assert sha(r[path])==r[key]
        model=Resource(read(r['source_json'])).normalize();cached=json.loads(gzip.decompress(Path(r['normalized_model']).read_bytes()));cached.setdefault('embedded_files',[]);assert model==cached
        models[r['depot']]=model;pins.append(r)
    N=r'base\quest\minor_quests\mq037\mq037_brendan.questphase';B=r'base\quest\bugfixing\minor_quests\mq037\mq037_quest_bugfixes.questphase';P=r'towercontinued\sidejobs_s23\base_b\mq037.questphase'
    q=W/'prealpha/quest_restoration_qr9/worker_b/resource_readbacks_01/resource_6.json';assert sha(q)=='30EE5C514EF45FE21FC5C122E75BBD63B7BD89D7DB6D395B24B210B996B0660D'
    p=W/'prealpha/quest_restoration_qr8/candidate_01/archive_source'/P.replace('\\','/');epoch=read(W/'prealpha/quest_restoration_qr8/source_epoch_02.json');assert sha(p)==epoch['source_resources'][P]
    models[P]=Resource(read(q)).normalize();pins.append({'depot':P,'binary':str(p),'sha256':sha(p),'source_json':str(q),'source_json_sha256':sha(q)})
    def check(name,ok,evidence):checks.append({'check':name,'pass':bool(ok),'evidence':evidence});assert ok,name
    n=models[N];b=models[B];w=models[P]
    check('current QR3 fresh containment retained',edge(w,'root',1004,'True',1008,'In'),'current root1004.True->1008.Refused')
    check('native final reinjection route',edge(n,'root',68,'Out',28,'CYB-661474_reinject')and edge(n,'root/28',162,'Out',140,'In1'),'root68 ->28.CYBreinject/162->140.In1')
    check('official bugfix guarded injector',edge(b,'root/38',70,'Out',100,'In1')and edge(b,'root/38',100,'inject_out',75,'CYB-661474_reinject'),'root38/70->100->75, no direct actor-absence-only reinjection')
    check('official injector six-way false AND',all(edge(b,'root/38/100',i,'False',7,s)for i,s in [(3,'In1'),(4,'In2'),(5,'In3'),(6,'In4'),(8,'In6'),(9,'In5')])and edge(b,'root/38/100',7,'Out1',1,'In'),'six native scene/section checks, not actor absence alone')
    check('native anti-scene and outside loop preserved in proposal',edge(b,'root/38/100',10,'Out',11,'In')and edge(b,'root/38/100',12,'Out',13,'In')and edge(b,'root/38',101,'Out',100,'In1'),'safe_out abort and loop_out outside/reenter')
    for a,s,c,t in [(4,'bad_news_out',5,'Succeeded'),(5,'Out',6,'Succeeded'),(6,'Out',11,'In'),(11,'Out',9,'In'),(9,'Out',8,'In')]:check('final native reward ordering '+str(a),edge(n,'root/28/140',a,s,c,t),'No reward reached before root quest Succeeded')
    check('native cleanup1h and outside retained',n['graphs']['root/28/140']['nodes']['15']['payload']['condition']['type']['hours']==1 and edge(n,'root/28/140',15,'Out',16,'In'),'native final cleanup after newly completed final dialogue only')
    # Exact source witness rather than original historical generic pending labels.
    root='quests/minor_quest/';co=root+'mq037_brendan';sp=root+'mq037_brendan_hooligan001';du=root+'mq037_brendan_dumpster'
    require={co:'Active',co+'/mq037_brendan/01_go_to_service':'Succeeded',co+'/mq037_brendan/02_find_brendan':'Succeeded',co+'/mq037_brendan/02b_ask_clerk':'Succeeded',co+'/mq037_brendan/02c_destroy_turret':'Inactive',co+'/mq037_brendan/03_talk_brendan':'Succeeded',co+'/mq037_brendan/04_talk_theo':'Active',du:'Succeeded',du+'/mq037_brendan_dumpster/00_push_dumpster':'Succeeded',du+'/mq037_brendan_dumpster/01_talk_brendan':'Succeeded',sp:'Succeeded',sp+'/mq037_brendan_hooligan/00_deal_with_the_hooligan':'Succeeded',sp+'/mq037_brendan_hooligan/01_talk_with_brendan':'Succeeded'}
    condition=w['graphs']['root']['nodes']['1002']['payload']['condition'];f={x['factName']:x['value']for x in walk(condition)if x.get('$type')=='questVarComparison_ConditionType'};j={x['path']['realPath']:x['state']for x in walk(condition)if x.get('$type')=='questJournalEntryState_ConditionType'};f.update(mq037_brendan_introduced=1,mq037_clerk_convinced=1,mq037_kill_token_block_loop=1);j.update(require)
    witness={'facts':f,'journals':j,'frozen_origin':'pre_ending','frozen_stable':True,'frozen_ready_exported':True,'source_native_main_termination':True,'Theo_present':False,'relevant_scene_active':False,'old_clock_pending':False,'current_matches_frozen':True}
    def eligible(s):
        return (s['frozen_origin']=='pre_ending'and s['frozen_stable']and s['frozen_ready_exported']and s['source_native_main_termination']and s['current_matches_frozen']and not s['Theo_present']and not s['relevant_scene_active']and not s['old_clock_pending']and all(s['journals'].get(k)==v for k,v in require.items())and all(s['facts'].get(k)==v for k,v in {'mq037_brendan_introduced':1,'mq037_clerk_convinced':1,'mq037_clerk_aggroed':0,'mq037_kill_token_block_loop':1,'mq037_done':0,'mq037_final_scene_active':0,'PTFRS23_MQ037_Issued':0,'PTFRS23_MQ037_Entered':0,'PTFRS23_MQ037_Finished':0,'PTFRS23_MQ037_Fault':0}.items()))
    # Baseline missing Entered is resolved as an explicit synthetic model value only.
    f['PTFRS23_MQ037_Entered']=0
    check('current generic guard rejects exact earned final witness',not ev(condition,f,j),{'node':1002,'failing_feature':True,'witness':'earned_final_witness.json'})
    check('candidate semantic gate can admit exact final witness',eligible(witness),'Abstract proposal only; root owns resource implementation and serialized proof')
    negatives=[]
    for key,value in [('frozen_origin','post_ending_fallback'),('frozen_stable',False),('frozen_ready_exported',False),('source_native_main_termination',False),('Theo_present',True),('relevant_scene_active',True),('old_clock_pending',True),('current_matches_frozen',False)]:
        q=copy.deepcopy(witness);q[key]=value;negatives.append({'case':key,'detected':not eligible(q)})
    for name,value in [('PTFRS23_MQ037_Issued',1),('PTFRS23_MQ037_Entered',1),('PTFRS23_MQ037_Finished',1),('mq037_done',1),('mq037_final_scene_active',1),('mq037_brendan_introduced',0),('mq037_clerk_aggroed',1),('mq037_kill_token_block_loop',0)]:
        q=copy.deepcopy(witness);q['facts'][name]=value;negatives.append({'case':name,'detected':not eligible(q)})
    for path,value in [(co,'Succeeded'),(co,'Failed'),(du,'Inactive'),(sp,'Failed'),(co+'/mq037_brendan/04_talk_theo','Succeeded'),(co+'/mq037_brendan/03_talk_brendan','Active')]:
        q=copy.deepcopy(witness);q['journals'][path]=value;negatives.append({'case':path+'='+value,'detected':not eligible(q)})
    for q in negatives:check('negative '+q['case'],q['detected'],q)
    parent_review=read(W/'prealpha/quest_restoration_qr2/ancestor_review.json');parent_models={}
    for r in parent_review['inputs'][:4]:
        assert sha(r['source_json'])==r['json_sha256'];parent_models[r['depot']]=Resource(read(r['source_json'])).normalize();pins.append(r)
    main=parent_models[r'base\quest\cyberpunk2077.questphase'];bf=parent_models[r'base\quest\bugfixing.questphase'];qb=parent_models[r'base\quest\bugfixing\quest_bugfixing.questphase']
    check('native Tower journal receipt and terminating ancestor',edge(main,'root',106,'Out',109,'In')and edge(main,'root',109,'Out',107,'In')and main['graphs']['root']['nodes']['107']['payload']['type']=='Terminating','Source containment, not runtime saved-owner introspection')
    check('minorquests owner is under terminated main root',r'base\quest\minor_quests\minorquests.questphase'in main['graphs']['root/82']['nodes']['6']['refs'],'main root82/node6')
    check('bugfix owner is under terminated main root',r'base\quest\bugfixing.questphase'in main['graphs']['root/82']['nodes']['4']['refs'],'main root82/node4')
    check('MQ037 bugfix owns same native family through guarded path',B in qb['graphs']['root/3']['nodes']['55']['refs'],'quest_bugfixing root3/node55')
    deps={'native_root_prefabs':n['root_prefabs'],'native_final_nodes':{i:n['graphs']['root/28/140']['nodes'][i]for i in n['graphs']['root/28/140']['nodes']},'official_actor_gate':b['graphs']['root/38']['nodes']['70']['payload']['condition'],'official_anti_scene_graph':b['graphs']['root/38/100'],'official_loop_wait':b['graphs']['root/38']['nodes']['101']['payload'],'existing_wrapper_node34':w['graphs']['root']['nodes']['34'],'existing_wrapper_common_pause':w['graphs']['root']['nodes']['1003']}
    put('source_pins.json',pins);put('earned_final_witness.json',witness);put('native_final_seam.json',deps)
    put('tests.json',{'status':'PASS_SOURCE_SEAM_WITH_BASELINE_FEATURE_FAILURE','checks':checks,'count':len(checks),'negative_controls':negatives,'runtime_mutations':0,'scope':'The candidate gate is an abstract semantic proposal; no serialized candidate exists in worker output.'})
    put('proposal.json',{'status':'BOUNDED_SOURCE_SUPPORTED_FINAL_THEO_PROPOSAL_REQUIRES_COORDINATOR_REVIEW','affected_quest':'mq037_brendan','scope':'Only peaceful-clerk earned final-Theo pending dialogue; Spray earlier stages remain held.',
        'runtime_resource':P,'before_sha256':sha(p),'native_body':N,'existing_node':34,'new_external_input_socket':'CYB-661474_reinject','exact_native_input_source':'bugfix root/38 node75 socket + native root68/root28/162','required_earned_journals':require,
        'required_fact_equalities':{'mq037_brendan_introduced':1,'mq037_clerk_convinced':1,'mq037_clerk_aggroed':0,'mq037_kill_token_block_loop':1,'mq037_done':0,'mq037_final_scene_active':0,'PTFRS23_MQ037_Issued':0,'PTFRS23_MQ037_Entered':0,'PTFRS23_MQ037_Finished':0,'PTFRS23_MQ037_Fault':0},
        'certificate':'Ready/exported/stable frozen HS1 originpre_ending must prove same earned final gate; reject post_ending_fallback. Match paths/facts by name because HS1 and S23 ordering differs. No persistent field/schema/fingerprint change.',
        'common_gate':'Reuse all existing native ancestor54/80/55, Tower/common/safe/PA2/support predicates; q307killed flags alone are insufficient. Verify current successor retains native root106->109->107Terminating containing both mainroot82/6 and/4.',
        'producer_changes':['S23 Read(13): recognize final witness as union with existing fresh case; preserve full sampled arrays/stable two-pass/settled journal gates. Existing Permit must never revoke an Issued owner.','HS1 additive read-only method for exact pre_ending earned final certificate; no new persistent fields or snapshot schema.'],
        'wrapper_changes':['Keep original fresh quarantine: new fresh route must still end existing1008Refused, never nativeIn1.','Allow old1002pause and1004recheck to accept OLD_FRESH_OR_EARNED_FINAL; add branch selecting earned vs fresh, retaining old1005/1006andtheir In1 saved edges untouched.','Before claim, copy exact official bugfixphase100 scene/section guards and6second wait/outside loop, add strict current stage recheck and actor<=0 check. safe_out defers; it must not inject.','Use new internal claim nodes writing existing private Issued/Entered1, then existing34 on newly declared CYBreinject socket. Do not route via1005/1006fullIn1.','Do not copy CYB one-time global receipt/reset or broad nativebugfix journal normalization graphs. Keep native final/body/cleanup resources exact.'],
        'preserve':['All existing node/field/resource identities and existing saved descendants','Native reward order and questSucceeded-before-reward excludes already-paid completed state','Native cleanup1h/outside wait after this newly completed final dialogue','Original choicefacts, nativeSCN and rootprefabs; no resets, item grants or player teleport','No second actor-owner/XLregistration; extend same existing private phase34interface.'],
        'remaining_risks':['Current queued pause predicate refresh on old saves remains engine-dependent; future unclaimed supported entries only until transitions validated.','Current user has no such pre_ending earned final certificate; no immediate live test.','No runtime executing-owner API exists; source lineage and exact authored retirement are evidence, not per-save liveness proof. If this is insufficient for the deployment commitment, hold this case rather than weakening guards.'],
        'blocked_cases':[{'case':'SprayPaint new admission after earned Dumpster','reason':'Native girlfriend12h and earlier8h handoff clocks/phase position not recorded by available markers; rootHooliganinput replays startup/encounter and cannot adopt pending saved timers.'},{'case':'SprayPaint active combat/talk resume','reason':'Native root25 alternatives enter initial scene/cut bugfix paths; no already-earned late input in current native interface. Must establish encounter retirement and add reviewed precise late seam rather than Reactivate/killed resets.'},{'case':'Coin service_point/girlfriend_final debug inputs','reason':'Native initializer rewrites journals/choicefacts and service_point parent teleports player; not a conservative resume.'},{'case':'Already privateIssued/Entered histories','reason':'Potential existing descendants preserved; no cancellation or adoption.'},{'case':'Failed Spray or hostile clerk final histories','reason':'Native outcomes preserved but excluded from this narrow peaceful-final case until independent branch review.'}]})
    print({'checks':len(checks),'negative_controls':len(negatives),'proposal':'earned finalTheo only','runtime_changes':0})
if __name__=='__main__':main()
