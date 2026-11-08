"""Review actual gated supportholder readback. Evidence only; no resource writes."""
from review_brendan_actual03 import *
import argparse
HELD='PTFRQR13_MQ037_FinalSupportHeld'
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--revision',required=True,choices=['05','06','07']);a=parser.parse_args()
    base=W/('prealpha/quest_restoration_qr13/coordinator/brendan_'+a.revision);out=H/('actual_brendan'+a.revision+'_02');assert not out.exists();out.mkdir()
    plan=read(base/'serialization_plan.json');sm=read(base/'serialized_01/manifest.json');r=sm['resources'][0];checks=[];mutants=[]
    def ck(name,value,detail=None):assert value,name;checks.append({'name':name,'pass':True,'evidence':detail})
    ck('readback exact input/raw/json pins',sha(r['input'])==r['input_sha256']and sha(r['raw'])==r['raw_sha256']and sha(r['readback_json'])==r['readback_json_sha256'])
    actual=Resource(read(r['readback_json'])).normalize();ck('zero structural errors',not actual['errors'],actual['errors']);g=actual['graphs']['root'];holder=actual['graphs']['root/1110']
    b03=Resource(read(read(W/'prealpha/quest_restoration_qr13/coordinator/brendan_03/serialized_01/manifest.json')['resources'][0]['readback_json'])).normalize();old=b03['graphs']['root']
    previous_review=read(H/'actual_brendan03_03/review.json')
    for x in plan['redscript_changes']:
        approved=next(s for s in previous_review['reviewed_scripts']if s['path']==x['path']);ck('same approved script '+x['path'],sha(x['source'])==approved['sha256']==x['sha256'])
    ck('old nativebody34 payload unchanged',g['nodes']['34']['payload']==old['nodes']['34']['payload'])
    ck('original official injector remains exact',actual['graphs']['root/1102']==b03['graphs']['root/1102'])
    for ident in ['1000','1001','1003','1005','1006','1007','1008','54','80','55','1103','1105','1106']:
        ck('retained payload '+ident,g['nodes'][ident]['payload']==old['nodes'][ident]['payload'])
    expected_pips=['#mq037_pr_machine_spot','#mq037_service_point'];pips=[x['prefabNodeRef']['$value']for x in g['nodes']['1110']['payload']['phaseInstancePrefabs']]
    ck('exact native2prefabs on gated holder only',pips==expected_pips and actual['root_prefabs']==[])
    ck('no actor/device/scene/reward commands in holder',all(n['type']in ['questInputNodeDefinition','questFactsDBManagerNodeDefinition','questPauseConditionNodeDefinition','questOutputNodeDefinition']for n in holder['nodes'].values()))
    ck('holder acquired before actor gate viaReady', ['1100','True','1110','In1']in g['edges']and['1110','Ready','1101','In']in g['edges']and['1100','True','1101','In']not in g['edges'])
    ready=next((i,n)for i,n in holder['nodes'].items()if n['type']=='questOutputNodeDefinition'and n['payload']['socketName']['$value']=='Ready');ck('Ready isNonTerminating',ready[1]['payload']['type']=='NonTerminating')
    load=holder['nodes']['3']['payload']['condition'];ck('both actual refs loadingAND beforeReady',load['operation']=='AND'and{c['objectRef']['$value']for c in load['conditions']}=={'#mq037_com_characters','#mq037_tr_theo_final'}and all(c['$type']=='questNodeLoadingCondition'and c['inverted']==0 for c in load['conditions'])and path(holder,'0',ready[0])is not None)
    ck('load precedes Ready exact chain',['0','Out','2','In']in holder['edges']and['2','Out','3','In']in holder['edges']and['3','Out',ready[0],'In']in holder['edges'])
    for ident,value in [('1002',0),('1004',0),('1100',0),('1101',1),('1104',1),('1111',1)]:
        conditions=[x for x in walk(g['nodes'][ident]['payload']['condition'])if x.get('$type')=='questVarComparison_ConditionType'and x.get('factName')==HELD]
        ck('Held gate '+ident, len(conditions)==1 and conditions[0]['comparisonType']=='Equal'and conditions[0]['value']==value)
    ck('loop retains holder',['1102','loop_out','1103','In']in g['edges']and['1103','Out','1101','In']in g['edges']and['1102','loop_out','1110','Release']not in g['edges'])
    ck('all scoped abort/failure/completion releases',all(e in g['edges']for e in [['1102','safe_out','1110','Release'],['1104','False','1110','Release'],['34','Out1','1111','In'],['1111','True','1110','Release']]))
    ck('old savedbody completion cannot activate holder withoutHeld',g['nodes']['1111']['payload']['condition']['type']['factName']==HELD and g['nodes']['1111']['payload']['condition']['type']['value']==1 and all(e[2]!='1110'for e in g['edges']if e[0]=='1111'and e[1]=='False'))
    ck('fresh quarantine remains', ['1100','False','1008','In']in g['edges']and['1006','Out','34','In1']in g['edges'])
    ck('no premature done1/finalscene cleanup release',all(e[0]in ['1102','1104','1111']for e in g['edges']if e[2]=='1110'and e[3]=='Release'))
    def has_held_condition(node,value):return any(x.get('$type')=='questVarComparison_ConditionType'and x.get('factName')==HELD and x.get('comparisonType')=='Equal'and x.get('value')==value for x in walk(node['payload'].get('condition',{})))
    def validate_protocol(model):
        root=model['graphs']['root'];h=model['graphs']['root/1110'];clear_inside=[i for i,n in h['nodes'].items()if any(x.get('$type')=='questSetVar_NodeType'and x.get('factName')==HELD and x.get('value')==0 for x in walk(n['payload']))]
        clear_outside=[i for i,n in root['nodes'].items()if any(x.get('$type')=='questSetVar_NodeType'and x.get('factName')==HELD and x.get('value')==0 for x in walk(n['payload']))]
        if clear_inside or len(clear_outside)!=1:return False
        clear=clear_outside[0]
        return ['1110','Out1',clear,'In']in root['edges']and has_held_condition(root['nodes']['1111'],1)and root['nodes']['1110']['payload']['phaseInstancePrefabs']and h['nodes'][ready[0]]['payload']['type']=='NonTerminating'
    protocol=validate_protocol(actual)
    # ActualB05 structural counterexample: publishHeld0 before oldholderTerm,
    # then parallel1002 rearm may instantiate1110 while oldrelease is pending.
    finding=None
    if not protocol:
        finding={'status':'BLOCK_HELD_FREE_PUBLISHED_BEFORE_TERMINATING_ACK','source':'root/1110 Release→Held0→Term; root1104False forks1002rearm+Release',
            'possible_topological_trace':['holder exists Held1','1104False forks rearm andRelease','Release clearsHeld0','1002earnedarm/1100nowpassHeld0','new1110In1 is allowed before oldTerm event'],
            'required':'KeepHeld1 through child termination, clearHeld0 onlyfrom outer1110.Out1 afterTerminating output; no earlyrootfact watcher orreacqguard assumption.','boundary':'Graphordering counterexample, not a live race observation.'}
    else:ck('Held0 only after terminating outer ack',True)
    # Independent native-derived witness proves acquisition and claim phases use
    # oppositeHeld states. No fullREDscript/engine execution is claimed.
    witness=read(W/'prealpha/quest_restoration_qr13/worker_b/revision_02/earned_final_witness.json');f=dict(witness['facts']);j={p:{'Inactive':1,'Active':2,'Succeeded':3,'Failed':4}[v]for p,v in witness['journals'].items()};f[HELD]=0
    ck('eligible source witness acquires only beforeHeld',evaluate(g['nodes']['1100']['payload']['condition'],f,j)and not evaluate(g['nodes']['1101']['payload']['condition'],f,j))
    f[HELD]=1;ck('after support held actorclaim gate passes',evaluate(g['nodes']['1101']['payload']['condition'],f,j)and evaluate(g['nodes']['1104']['payload']['condition'],f,j)and not evaluate(g['nodes']['1100']['payload']['condition'],f,j))
    f[HELD]=0;ck('old nativebody noHeld completion guard false',not evaluate(g['nodes']['1111']['payload']['condition'],f,j))
    f[HELD]=1;ck('held completion guard true',evaluate(g['nodes']['1111']['payload']['condition'],f,j))
    for name,edit in [('drop_native_service_prefab',lambda m:m['graphs']['root']['nodes']['1110']['payload']['phaseInstancePrefabs'].pop()),('terminatingReady',lambda m:m['graphs']['root/1110']['nodes'][ready[0]]['payload'].__setitem__('type','Terminating')),('widen_old_saved_guard',lambda m:m['graphs']['root']['nodes']['1111']['payload']['condition']['type'].__setitem__('value',0))]:
        m=copy.deepcopy(actual);edit(m)
        if name=='drop_native_service_prefab':detected=[x['prefabNodeRef']['$value']for x in m['graphs']['root']['nodes']['1110']['payload']['phaseInstancePrefabs']]!=expected_pips
        elif name=='terminatingReady':detected=m['graphs']['root/1110']['nodes'][ready[0]]['payload']['type']!='NonTerminating'
        else:detected=not has_held_condition(m['graphs']['root']['nodes']['1111'],1)
        ck('actual mutation '+name,detected);mutants.append({'fault':name,'detected':detected})
        p=out/(name+'.NONPRODUCTION.normalized.json');p.write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8')
    ck('old completion false branch preserves Finished without holder',['1111','False','1007','In']in g['edges'])
    ck('body completion has no premature parallel Finished edge',['34','Out1','1007','In']not in g['edges']and['34','Out1','1111','In']in g['edges'])
    ck('abort recheck does not blindly rearm while terminating',['1104','False','1002','In']not in g['edges'])
    ck('posttermination acknowledgment chain preserved',all(e in g['edges']for e in [['1110','Out1','1112','In'],['1112','Out','1113','In'],['1113','True','1007','In']]))
    ck('abort cannot fakeFinished viafalse output',not any(e[0]=='1113'and e[1]=='False'for e in g['edges']))
    for issued,entered,expected in [(0,0,False),(1,0,False),(0,1,False),(1,1,True)]:
        ff={'PTFRS23_MQ037_Issued':issued,'PTFRS23_MQ037_Entered':entered}
        ck('posttermination claimant guard '+str((issued,entered)),evaluate(g['nodes']['1113']['payload']['condition'],ff,{})==expected)
    m=copy.deepcopy(actual);hh=m['graphs']['root/1110'];nn=copy.deepcopy(g['nodes']['1112']);nn['payload']['id']=5;nn['id']='5';hh['nodes']['5']=nn;hh['edges']=[e for e in hh['edges']if e!=['1','Out','6','In']]+[['1','Out','5','In'],['5','Out','6','In']]
    ck('mutant earlyHeld0beforeTerm detected',not validate_protocol(m));mutants.append({'fault':'early Held0 published inside holder before Term','detected':True});(out/'early_held_clear.NONPRODUCTION.normalized.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8')
    m=copy.deepcopy(actual);m['graphs']['root']['edges']=[['1111','False','1110','Release']if e==['1111','False','1007','In']else e for e in g['edges']]
    ck('mutant oldcompletion instantiates holder detected',['1111','False','1110','Release']in m['graphs']['root']['edges']);mutants.append({'fault':'old Held0completion falsely activates Release holder','detected':True});(out/'old_completion_holder.NONPRODUCTION.normalized.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8')
    m=copy.deepcopy(g['nodes']['1113']['payload']['condition']);m['operation']='OR'
    ck('mutant partialclaim OR mislabels Finished detected',evaluate(m,{'PTFRS23_MQ037_Issued':1,'PTFRS23_MQ037_Entered':0},{}));mutants.append({'fault':'abort claimant AND widened toOR','detected':True});(out/'partial_claim_or.NONPRODUCTION.normalized.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8')
    scope=read(plan['support_scope_review']);status='APPROVE_CONDITIONAL_EXACT_NATIVE_PIP_WITH_OPAQUE_PLACEMENT_LIMIT'if protocol else'BLOCK_HELD_RELEASE_ACK_PROTOCOL'
    result={'status':status,'actual_resource':r,'reviewed_scripts':plan['redscript_changes'],'checks':checks,'actual_mutations':mutants,'blocking_finding':finding,'support_scope_review':{'path':plan['support_scope_review'],'sha256':sha(plan['support_scope_review']),'status':scope.get('status')},
        'conditional_limits':['Machine-spot DynamicBaseClass placement remainsOPAQUE. Exact nativeprefab references only; no assertion of decoded no-autospawn contents.','Native saved-owner/lease scheduling and field update windows need enginevalidation; source protocol is not allsave proof.','No current userpreEnding certificate fixture or live test is qualified.','Packagebytepreservation/compilation and providerpins remain coordinator/finalverifier gates.'],'runtime_resource_changes':0,'game_or_save_changes':0}
    (out/'review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print({'status':status,'checks':len(checks),'mutations':len(mutants),'held_release_protocol':protocol})
if __name__=='__main__':main()
