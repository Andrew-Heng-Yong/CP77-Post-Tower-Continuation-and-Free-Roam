"""Independent actual-readback review of the four prospective late-completion gates."""
from pathlib import Path
import sys,argparse,copy,itertools
from prepare import ROOT,HERE,Q7,read,sha,write
sys.path.insert(0,str(ROOT/'tools/parity_audit'))
from model import Resource

CASES=[('12',200,210,2,35,10,110),('08',201,211,37,45,38,115),('03',202,212,47,55,48,117),('01',203,213,57,65,58,119)]
NEWS=r'towercontinued\quest_restoration_qr7\ronald_news_future.questphase'
RN=r'ep1\quest\main_quests\q302\phases\q302_ronald_tree.questphase'

def evaluate(c,f):
    if c['$type']=='questLogicalCondition':
        a=[evaluate(x,f)for x in c['conditions']];assert c['operation'] in ('AND','OR');return all(a)if c['operation']=='AND' else any(a)
    assert c['$type']=='questFactsDBCondition';x=c['type'];a,b=f[x['factName']],x['value'];op=x['comparisonType']
    return {'Equal':a==b,'GreaterOrEqual':a>=b}[op]

def reach(g,seed):
    seen=set();todo=[seed]
    while todo:
        i=todo.pop()
        if i in seen:continue
        seen.add(i);todo.extend(x[2]for x in g['edges']if x[0]==i and x[1]!='CutSource' and x[3]!='CutDestination')
    return seen

def main(out):
    assert out.resolve().is_relative_to(HERE) and not out.exists();out.mkdir(parents=True)
    checks=[];pins=[];fixtures=[];controls=[]
    def ck(n,v,ev=None):checks.append({'check':n,'pass':bool(v),'evidence':ev});assert v,n
    def pin(p,h=None):
        p=Path(p);actual=sha(p);ck('Exact source pin '+p.name,h is None or actual==h);pins.append({'path':str(p.resolve()),'sha256':actual});return p
    b=ROOT/'prealpha/quest_restoration_qr8/worker_b'
    plan=read(pin(b/'late_future_plan_01.json','044C3AA43946A2EA417199C1CFCFDA4A1DD03DF79919CCE507D8EC5D4B45D8DA'))
    proposal=read(pin(b/'proposal_late_future_03/NOT_FOR_INTEGRATION.json','7135F6120707B88AEEE34BD47E62F95CFB803F7F121A8448A8F4E8E02EFC898D'))
    pin(proposal['raw'],'6CEB6AC9FA2909771AEEF09D33A36241E1396D26A072725317374837AB79B0EC');pin(proposal['json'],proposal['json_sha256'])
    rd=read(pin(HERE/'reviews/late_future_01/readback/manifest.json'));models={};docs={}
    for r in rd['resources']:
        pin(r['raw'],r['raw_sha256']);pin(r['json'],r['json_sha256']);docs[r['depot']]=read(r['json']);models[r['depot']]=Resource(docs[r['depot']]).normalize()
    ck('Fresh independent serialized proposal readback equals supplied readback semantically',models['PRIVATE_PROPOSAL']==Resource(read(proposal['json'])).normalize())
    old,new=models[NEWS],models['PRIVATE_PROPOSAL'];g,ng=old['graphs']['root/202'],new['graphs']['root/202'];native=models[RN]['graphs']['root/11']
    ck('Root once-claim guard/edges/receipts byte-semantically unchanged',old['graphs']['root']==new['graphs']['root'])
    ck('Resource metadata and root prefabs unchanged',{k:v for k,v in old.items()if k!='graphs'}=={k:v for k,v in new.items()if k!='graphs'})
    ck('Every graph identity unchanged',set(old['graphs'])==set(new['graphs']))
    changed=[]
    for gp,graph in old['graphs'].items():
        nn=new['graphs'][gp];ck('All graph sockets, edges, reachability and identities unchanged '+gp,{k:v for k,v in graph.items()if k!='nodes'}=={k:v for k,v in nn.items()if k!='nodes'} and set(graph['nodes'])==set(nn['nodes']))
        for i,node in graph['nodes'].items():
            if node==nn['nodes'][i]:continue
            ck('Only four gate node objects differ',gp=='root/202' and i in {'200','201','202','203'})
            restored=copy.deepcopy(nn['nodes'][i]);restored['payload']['condition']=copy.deepcopy(node['payload']['condition'])
            for derived in ['payload_sha256','reads','conditions']:restored[derived]=copy.deepcopy(node[derived])
            ck('Only actual condition differs in changed node '+i,restored==node);changed.append(i)
    ck('Exactly four intended condition changes',set(changed)=={'200','201','202','203'})
    spec=read(pin(Q7/'worker_b/future_protocol_spec_01.json'));kept={str(i)for i in spec['kept_native_ids']}
    ck('All73 inherited native protocol node objects unchanged',len(kept)==73 and all(g['nodes'][i]==ng['nodes'][i]for i in kept))
    ck('Authored child loading pause precedes first four gates',g['nodes']['220']['payload']['condition']['$type']=='questLogicalCondition' and len(g['nodes']['220']['payload']['condition']['conditions'])==2 and all(x['$type']=='questNodeLoadingCondition' for x in g['nodes']['220']['payload']['condition']['conditions']) and ['0','Out','220','In'] in g['edges'])
    fresh=read(pin(HERE/'reviews/late_future_01/current_providers/manifest.json'));native_paths=[d for d in models if d.startswith('ep1\\openworld')]
    ck('Six native main/completion providers captured independently',len(native_paths)==6)
    for d in native_paths:
        matches=[x for x in fresh['resources']if x['depot']==d];r=next(x for x in rd['resources']if x['depot']==d)
        ck('Unique current native provider equals actual completion source '+d,len(matches)==1 and matches[0]['raw_sha256']==r['raw_sha256']);pin(matches[0]['raw'],matches[0]['raw_sha256'])
    owner_routes=[]
    for code,gid,wid,did,sid,pid,cid in CASES:
        q='sts_ep1_'+code;arm='PTFRQR7_RonaldNews_Armed_'+q;parent='PTFRU9_'+q+'_ParentEntered';done=q+'_done';sent='q302_msg_ronald_'+q
        oc,nc=g['nodes'][str(gid)]['payload']['condition'],ng['nodes'][str(gid)]['payload']['condition'];expected=copy.deepcopy(oc)
        ck(q+' original guard has exact native-done0 first term',oc['operation']=='AND' and oc['conditions'][0]=={'$type':'questFactsDBCondition','type':{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':done,'value':0}})
        expected['conditions'][0]={'$type':'questLogicalCondition','conditions':[copy.deepcopy(oc['conditions'][0]),{'$type':'questFactsDBCondition','type':{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':arm,'value':1}}],'operation':'OR'}
        ck(q+' new gate exactly done0 OR own genuine Armed1, other terms identical',nc==expected)
        ck(q+' actual incoming/outgoing routes do not replay a processed gate',[x for x in ng['edges']if x[2]==str(gid)]==[['220','Out',str(gid),'In']] and [str(gid),'True',str(wid),'In']in ng['edges'] and ['0','Out','220','In']in ng['edges'])
        wait=ng['nodes'][str(wid)]['payload']['condition'];ck(q+' unchanged future wait requires own exact Armed1',wait=={'$type':'questFactsDBCondition','type':{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':arm,'value':1}})
        ck(q+' native done listener is still actual >=1',native['nodes'][str(did)]['reads']==[{'$type':'questVarComparison_ConditionType','comparisonType':'GreaterOrEqual','factName':done,'value':1}])
        ck(q+' native sent1 claim remains before unchanged two-day clock',[str(sid),'Out',str(pid),'In'] in native['edges'] and [str(pid),'Out',str(cid),'In']in native['edges'] and native['nodes'][str(sid)]['writes']==[{'$type':'questSetVar_NodeType','factName':sent,'setExactValue':1,'value':1}] and native['nodes'][str(cid)]['payload']['condition']['type']=={'$type':'questGameTimeDelay_ConditionType','days':2,'hours':0,'minutes':0,'seconds':0})
        entry=models['towercontinued\\native_gigs_u9\\'+q+'_entry.questphase']['graphs']['root/50'];main_depot='ep1\\openworld\\street_stories\\'+q+'\\phases\\'+q+'_phase.questphase';main_model=models[main_depot]
        ck(q+' only actual fresh-admission input enters arm writer',[x for x in entry['edges']if x[2]=='65007']==[['65002','Out','65007','In']] and [x for x in entry['edges']if x[2]=='65003']==[['65007','Out','65003','In']] and entry['nodes']['65007']['writes']==[{'$type':'questSetVar_NodeType','factName':arm,'setExactValue':1,'value':1}])
        ck(q+' original fresh history guards still required',all(any(x.get('factName')==f and x.get('comparisonType')=='Equal'and x.get('value')==0 for x in entry['nodes']['65002']['reads'])for f in [parent,q+'_start',q+'_finished']))
        child_refs=[i for i,n in entry['nodes'].items()if main_depot in n['refs']];ck(q+' armed then ParentEntered reaches real native child',len(child_refs)==1 and child_refs[0]in reach(entry,'65003'))
        writers=[{'depot':d,'graph':gp,'node':i,'value':w['value']}for d,model in models.items()if d.startswith('ep1\\openworld\\street_stories\\'+q+'\\')for gp,graph in model['graphs'].items()for i,n in graph['nodes'].items()for w in n['writes']if w['factName']==done]
        ck(q+' exact completion writer has one selected native owner',len(writers)==1 and writers[0]['value']==1 and writers[0]['node']in models[writers[0]['depot']]['graphs'][writers[0]['graph']]['reachable'],writers)
        if writers[0]['depot']!=main_depot:ck(q+' actual parent references actual completion child',any(writers[0]['depot']in n['refs']for graph in main_model['graphs'].values()for n in graph['nodes'].values()))
        dependency_reads=[x.get('factName','')for d,mm in models.items()if d.startswith(('towercontinued\\native_gigs_u9\\'+q,'ep1\\openworld\\street_stories\\'+q+'\\'))for graph in mm['graphs'].values()for n in graph['nodes'].values()for x in n['reads']]
        ck(q+' producer/native completion has no authored wait on NEWS loading or receipt',not any('PTFRQR7_RonaldNews' in f or f.startswith('q302_msg_ronald')for f in dependency_reads))
        for dv,sv,av,pv in itertools.product((0,1,2),(0,1),(0,1),(0,1)):
            f={done:dv,sent:sv,arm:av,parent:pv};before=evaluate(oc,f);after=evaluate(nc,f);live_path=after and evaluate(wait,f) and evaluate(native['nodes'][str(did)]['payload']['condition'],f)
            ck(q+' independent receipt eligibility '+str((dv,sv,av,pv)),live_path==(dv>=1 and sv==0 and av==1) and (before==after or(dv>=1 and sv==0 and av==1)))
            fixtures.append({'quest_id':q,'done':dv,'sent':sv,'Armed':av,'ParentEntered':pv,'before_first_gate':before,'after_first_gate':after,'after_native_dispatch_eligibility':live_path})
        owner_routes.append({'quest_id':q,'actual_native_writer':writers[0],'private_producer_route':['65002.Out','65007 Armed1','65003 ParentEntered1',child_refs[0]],'parallel_helper_hold':'root/202 input0→NodeLoading220 before first case gate','source_partial_order':'No authored dependency in these executing owner paths requires220/NEWS progress before genuine private Armed/native done. Engine scheduling/streaming reachability is not measured.'})
    # Actual JSON counter-control: revert one changed gate; known future receipt is again rejected.
    doc=copy.deepcopy(docs['PRIVATE_PROPOSAL']);rr=Resource(doc);rootg=rr.d(rr.root['graph']);phase=next(rr.d(x)for x in rootg['nodes']if rr.d(x)['id']==202);child=rr.d(phase['phaseGraph']);target=next(rr.d(x)for x in child['nodes']if rr.d(x)['id']==200);outer=rr.d(target['condition']);outer['conditions'][0]=copy.deepcopy(rr.d(outer['conditions'][0])['conditions'][0])
    mm=Resource(doc).normalize()['graphs']['root/202'];f={'sts_ep1_12_done':1,'q302_msg_ronald_sts_ep1_12':0,'PTFRQR7_RonaldNews_Armed_sts_ep1_12':1,'PTFRU9_sts_ep1_12_ParentEntered':1}
    ck('Actual serialized-document gate-reversion mutant fails earned late-completion fixture',not evaluate(mm['nodes']['200']['payload']['condition'],f) and evaluate(ng['nodes']['200']['payload']['condition'],f));write(out/'mutant_reverted_gate200.json',doc);controls.append({'name':'actual gate200 reversion','detected':True,'fixture':f})
    write(out/'source_pins.json',pins);write(out/'fixtures.json',fixtures)
    write(out/'review.json',{'status':'APPROVED_MINIMAL_SOURCE_CONFIRMED_FOUR_GATE_REPAIR_FOR_COORDINATOR_INTEGRATION','checks':checks,'checks_passed':len(checks),'independent_actual_readbacks':len(rd['resources']),'fixtures':len(fixtures),'actual_resource_controls':controls,'owner_routes':owner_routes,'approved_proposal':{'manifest':str(b/'proposal_late_future_03/NOT_FOR_INTEGRATION.json'),'raw_sha256':proposal['raw_sha256'],'json_sha256':proposal['json_sha256']},
        'approved_delta':'Only the first four existing case guards change done0 to(done0 OR own genuine QR7 Armed1). No registration, resource/node/field/socket identity, receipt writer, sent history, two-day timer, root Issued gate, future-arm wait or old processed-branch re-entry changes.',
        'scope':['Actual future Armed producer remains dominated by original fresh U9 admission, before ParentEntered, then native completion.','First case evaluation sees genuine future receipt and native sent0; already-Issued helper is not restarted.','Already skipped/processed cases are not replayed. Sent1 pending clocks and Armed0 historical jobs remain excluded.','Existing earned enrollment and Active contact still required by unchanged root. No first-time contact/menu/physical-owner extension.'],
        'limits':['Source partial order establishes an authored independent completion/loading boundary; actual latency and save scheduler behavior are LIVE_ONLY. No measured duplicate/missed-message occurrence is claimed.','An existing saved owner before first case evaluation is not force-reentered; applicability of changed resource predicates on specific saved handlers still needs an authorized transition fixture.','No old timer adoption/reset, synthetic ACK, native enrollment rewrite, actor/trigger availability claim or all-history support.','Coordinator must integrate alone into a fresh successor, serialize/read back final affected package and run preservation/package/compile gates.'],
        'runtime_changes':[],'candidate_writes':0,'code_sha256':sha(__file__)})
    print({'checks':len(checks),'readbacks':len(rd['resources']),'fixtures':len(fixtures),'controls':len(controls),'out':str(out)})

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);main(ap.parse_args().output)
