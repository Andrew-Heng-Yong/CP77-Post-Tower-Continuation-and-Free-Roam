"""Ronald QR13 source/contract inspection; writes only worker_a evidence."""
from pathlib import Path
import collections,copy,hashlib,json,sys
H=Path(__file__).resolve().parent;W=H.parents[2]
sys.path.insert(0,str(W/'tools/parity_audit'))
from model import Resource
RN=r'ep1\quest\main_quests\q302\phases\q302_ronald_tree.questphase'
NS=r'ep1\quest\main_quests\q302\scenes\q302_05_bar.scene'
BO=r'towercontinued\b0_story_eight\ronald.questphase';BS=BO.replace('.questphase','.scene')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():yield from walk(v)
    elif isinstance(x,list):
        for v in x:yield from walk(v)
def reach(g,seeds):
    seen=set(seeds);todo=list(seen)
    while todo:
        n=todo.pop()
        for e in g['edges']:
            if e[0]==n and e[2]not in seen and e[1]!='CutSource'and e[3]!='CutDestination':seen.add(e[2]);todo.append(e[2])
    return seen
def path(g,a,b):
    q=collections.deque([(a,[])]);seen=set()
    while q:
        n,p=q.popleft()
        if n in seen:continue
        seen.add(n)
        if n==b:return p
        for e in g['edges']:
            if e[0]==n:q.append((e[2],p+[e]))
def save(name,data):
    p=H/name;assert not p.exists();p.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
def main():
    pins=read(W/'prealpha/quest_restoration_qr7/worker_b/readback_01/manifest.json');models={};sources=[]
    candidate=W/'prealpha/quest_restoration_qr8/candidate_01/archive_source'
    for r in pins:
        if r['depot']not in [RN,NS,BO,BS]:continue
        assert sha(r['json'])==r['json_sha256']and sha(r['raw'])==r['raw_sha256']
        if r['depot']in[BO,BS]:assert sha(candidate/Path(r['depot'].replace('\\','/')))==r['raw_sha256']
        models[r['depot']]=Resource(read(r['json'])).normalize();sources.append(r)
    native=models[NS]['graphs']['scene'];before=models[BS]['graphs']['scene'];proposed=copy.deepcopy(before)
    restored=[e for e in native['edges']if e[0]=='839'and e[1]in['0:3','0:4']]
    assert len(restored)==2
    proposed['edges']+=restored
    base=reach(before,['920']);expanded=reach(proposed,['920']);added=expanded-base
    assert '1755'not in base and '1755'in expanded
    assert any(v.get('factName')=='q302_ronald_messages_enabled'and v.get('value')==1 for v in walk(native['nodes']['1755']['payload']))
    contact=models[RN]['graphs']['root/11'];contact_ids=['0','158','159','154','23','121','155','156']
    assert contact['nodes']['159']['payload']['type']['params'][0]['addContact']==1
    assert contact['nodes']['23']['payload']['type']['params'][0]['sendNotification']==1
    nativeTree=models[RN]['graphs']['root'];b0=models[BO]['graphs']
    contract={'status':'MISSING_MENU_AND_CONTACT_BOOTSTRAP_PROVEN_OWNER_LEASE_REVIEW_PENDING','source_pins':sources,
        'critical_failures':{'choice839_options_3_4':{'native_edges':restored,'current_edges':[e for e in before['edges']if e[0]=='839'and e[1]in['0:3','0:4']],'native_option_conditions':[native['nodes']['839']['payload']['options'][i]['questCondition']for i in[3,4]],'current_option_conditions':[before['nodes']['839']['payload']['options'][i]['questCondition']for i in[3,4]]},
        'current_subscription_writer_reachable':False,'candidate_subscription_writer_reachable':True,'contact_bootstrap_current_missing':all(i not in b0['root/5']['nodes']for i in['11','12']),
        'native_bootstrap_order':[['2','Out','12','In'],['12','Out','11','In1']],'native_contact_child_nodes':{i:contact['nodes'][i]['payload']for i in contact_ids},
        'native_contact_child_edges':[e for e in contact['edges']if e[0]in contact_ids and e[2]in contact_ids]},
        'native_yes_and_no':{'choice1746':native['nodes']['1746']['payload'],'yes1750_writer':path(native,'1746','1755'),'offered_history_writer1769':native['nodes']['1769']['payload'],'already_offered_guard1730':native['nodes']['1730']['payload']},
        'reenabled_scope':{'current_reachable':len(base),'candidate_reachable':len(expanded),'new_node_count':len(added),'new_node_ids':sorted(added,key=int),'new_performer_ids':sorted({v['id']for i in added for v in walk(native['nodes'][i]['payload'])if v.get('$type')=='scnPerformerId'}),'native_fact_writes':{i:native['nodes'][i]['writes']for i in added if native['nodes'][i]['writes']},'new_non_performer_actor_ids':'ActorId fields must be reviewed in event context; performer IDs are not an entire binding proof.'},
        'bar_prefab':{'native_root':models[RN]['root_prefabs'],'current_root':models[BO]['root_prefabs'],'current_child_phase_prefabs':b0['root']['nodes']['5']['payload']['phaseInstancePrefabs'],'current_runtime_ownership':'NOT_PROVEN_BY_CURRENT_MISSING_LEASE'},
        'saved_reachability':{'current_repeated_approach_edges':[e for e in b0['root/5']['edges']if e[0]=='2'],'future_bridge_entry':'Existing root/5 node2.Out repeated approach event, not a new root input. Old scene already past2 would wait until a later genuine approach. No old owner restart. Engine refresh remains LIVE_ONLY.'},
        'implementation_direction_not_approved':{'scene':'Restore exact native839 options3/4 only; keep5hidden. Retain current private LookAt/Dialogue/Reminder renames, current actor binding policy and all native consent/refusal/counter conditions. Real Yes writer1755.Out may append additive private consent receipt; do not set native enrollment outside nativeYes route.',
        'contact':'Native enabled-wait causal order/spatial158/HUDshow/AddContact/NonCallable/3secHUDrestore must be retained. Bootstrap gated by newly earned private consent only, one-time receipt, genuinely Inactive contact. Active/Failed/Succeeded contacts must not be re-added. Do not adopt oldmessages_enabled1.',
        'timers':'QR7/8 future-news source untouched. No original native news141-node subtree copied or olddone/sent/pending clocks adopted.',
        'support':'Exact native bar/full support lease or filtered fresh supported subset requires resolved native mainbar owner retirement, exact placement/resource scope and saved B0 applicability. No wholebar lease approved yet.'},
        'unresolved':['Main q30205bar owner retirement separate from native persistent-Ronald cut.','Fullbar vs filtered prefab ownership/placement scope.','Adding prefab to already-running existing B0 owner may not retrospectively acquire it; supported successor admission must be exact.','Native saved-node connection refresh is engine-dependent.']}
    save('enrollment_contract_01.json',contract)
    # Current connected source proves failure; prospective model demonstrates exact cut restoration only.
    save('static_controls_01.json',{'status':'PASS_IDENTIFIED_MISSING_SOURCE_ROUTE','checks':[
        {'name':'native actual1746Yes reaches1755 nativeenabled writer','pass':path(native,'1746','1755')is not None},
        {'name':'current920 cannot reach1755','pass':'1755'not in base},
        {'name':'only exact839native3/4 edges restore1755reachability','pass':'1755'in expanded},
        {'name':'currentB0 has no native12to11 contact path','pass':all(i not in b0['root/5']['nodes']for i in['11','12'])},
        {'name':'currentroot missing nativebarprefab','pass':models[BO]['root_prefabs']==[]and models[RN]['root_prefabs']==['#q302_pr_bar']}],
        'limits':'Prospective model-only source reachability; no resource produced, no safe fullfeature verdict.'})
    print({'status':contract['status'],'current_reachable':len(base),'restored_reachable':len(expanded),'newnodes':len(added),'contact_nodes':len(contact_ids)})
if __name__=='__main__':main()
