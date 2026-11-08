"""Independent exact typed Ronald delta review. Mutants remain in memory."""
from pathlib import Path
import copy,hashlib,itertools,json,sys,zlib
H=Path(__file__).resolve().parent;W=H.parents[2];Q=H.parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from model import Resource
from common import walk
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def canon(x):
    if isinstance(x,dict):
        x=dict(x)
        if x.get('$type')=='TweakDBID':
            s=str(x['$value']);x['$storage']='uint64';x['$value']=str(int(s))if s.isdigit()else str((len(s.encode())<<32)|zlib.crc32(s.encode()))
        return{k:canon(v)for k,v in x.items()if k not in ['payload_sha256','metadata_sha256']}
    if isinstance(x,list):return[canon(v)for v in x]
    return x
def model(p):return canon(Resource(read(p)).normalize())
def main():
    out=H/'ronald_serialized_01';assert not out.exists();out.mkdir()
    mp=Q/'coordinator/ronald_02/serialized_01/manifest.json';m=read(mp);sp=W/m['plan'];assert sha(sp)==m['plan_sha256'];plan=read(sp)
    approval=read(H/'ronald_architecture_02/review.json');assert plan['source_plan_sha256']==approval['proposal_sha256']==sha(plan['source_plan'])
    rows=m['resources'];assert len(rows)==2
    for r in rows:
        for key,digest in [('input','input_sha256'),('readback_json','readback_json_sha256'),('raw','raw_sha256')]:assert sha(r[key])==r[digest]
    bs=model(W/'prealpha/quest_restoration_qr8/worker_b/readback_01/resource_3.json');bp=model(W/'prealpha/quest_restoration_qr8/worker_b/readback_01/resource_2.json')
    ns=model(Q/'provider_validation_01/sources/037/ep1/quest/main_quests/q302/scenes/q302_05_bar.scene.json');np=model(Q/'provider_validation_01/sources/037/ep1/quest/main_quests/q302/phases/q302_ronald_tree.questphase.json')
    scene=model(rows[0]['readback_json']);phase=model(rows[1]['readback_json']);assert scene==model(rows[0]['input'])and phase==model(rows[1]['input'])
    se=[['1755','0:0','60000','0:1'],['839','0:3','1422','0:0'],['839','0:4','1451','0:0']]
    pe=[['2','Out','203','In'],['203','Out','204','In'],['204','Out','205','In1']]
    ce=[['0','Out','158','In'],['158','False','159','In'],['158','True','154','In'],['154','Out','23','In'],['159','Out','121','NonCallable'],['23','Out','121','NonCallable'],['23','Out','155','In'],['155','Out','156','In'],['121','Out','200','In1'],['159','Out','200','In2'],['156','Out','200','In2'],['200','Out1','201','In']]
    prefix=['0','158','159','154','23','121','155','156'];consent='PTFRQR13_RonaldEnrollment_ConsentEarned';issued='PTFRQR13_RonaldEnrollment_ContactIssued'
    def validate(s,p):
        fail=[]
        def ck(n,b):
            if not b:fail.append(n)
        ck('models_structurally_valid',not s['errors']and not p['errors'])
        ck('scene_graph_scope',set(s['graphs'])=={'scene'})
        sg=s['graphs']['scene'];old=bs['graphs']['scene'];ck('scene_node_id_delta',set(sg['nodes'])==set(old['nodes'])|{'60000'})
        ck('scene_edges_exact',sorted(sg['edges'])==sorted(old['edges']+se));ck('scene_entries_unchanged',sg['entries']==old['entries'])
        ck('scene_metadata_exact',{k:v for k,v in s.items()if k!='graphs'}=={k:v for k,v in bs.items()if k!='graphs'})
        for i,n in old['nodes'].items():
            a=copy.deepcopy(sg['nodes'][i])
            if i=='839':
                for index in [3,4]:ck('native_option'+str(index),a['payload']['options'][index]==ns['graphs']['scene']['nodes']['839']['payload']['options'][index]);a['payload']['options'][index]=n['payload']['options'][index]
                a['payload']['outputSockets']=n['payload']['outputSockets']
                for k in ['reads','conditions','refs','node_refs','journal_paths']:a[k]=n[k]
            elif i=='1755':a['payload']['outputSockets']=n['payload']['outputSockets']
            ck('scene_oldnode_exact_'+i,a==n)
        ck('only_real_yes_writes_private_consent',sg['nodes'].get('60000',{}).get('writes')==[{'$type':'questSetVar_NodeType','factName':consent,'setExactValue':1,'value':1}]and[x for x in sg['edges']if x[2]=='60000']==[se[0]])
        ck('option5_remains_hidden',not any(e[0]=='839'and e[1]=='0:5'for e in sg['edges']))
        pg=p['graphs'];ck('phase_graph_scope',set(pg)==set(bp['graphs'])|{'root/5/205'})
        ck('phase_metadata_exact',{k:v for k,v in p.items()if k!='graphs'}=={k:v for k,v in bp.items()if k!='graphs'})
        for gp in ['root','root/5']:
            g=pg[gp];b=bp['graphs'][gp];ck('phase_IDs_'+gp,set(g['nodes'])==set(b['nodes'])|({'203','204','205'}if gp=='root/5'else set()))
            ck('phase_edges_'+gp,sorted(g['edges'])==sorted(b['edges']+(pe if gp=='root/5'else[])))
            for i,n in b['nodes'].items():
                a=copy.deepcopy(g['nodes'][i])
                if gp=='root'and i=='5':
                    ck('exact_native_bar_lease_before_trigger',a['payload']['phaseInstancePrefabs']==np['metadata']['phasePrefabs'])
                    a['payload']['phaseInstancePrefabs']=n['payload']['phaseInstancePrefabs']
                    for k in ['prefabs','node_refs']:a[k]=n[k]
                ck('phase_oldnode_'+gp+':'+i,a==n)
        contact=pg['root/5/205'];ck('contact_node_scope',set(contact['nodes'])==set(prefix)|{'200','201'});ck('contact_edges_exact',sorted(contact['edges'])==sorted(ce))
        for i in prefix:ck('contact_native_payload_'+i,contact['nodes'][i]==np['graphs']['root/11']['nodes'][i])
        ck('native_3sec_HUD_restore_before_branch_done',contact['nodes']['155']['payload']['condition']['type']['seconds']==3)
        ck('contact_AND_join_exact',contact['nodes']['200']['payload']=={'$type':'questLogicalAndNodeDefinition','id':200,'inputSocketCount':2,'outputSocketCount':1})
        ck('contact_terminates',contact['nodes']['201']['payload']=={'$type':'questOutputNodeDefinition','id':201,'socketName':{'$type':'CName','$storage':'string','$value':'Out1'},'type':'Terminating'})
        cond=pg['root/5']['nodes']['203']['payload']['condition'];terms=cond['conditions'];ck('guard_AND_exact4',cond['operation']=='AND'and len(terms)==4)
        ck('guard_future_consent_and_enabled_and_unissued',[(x['type']['factName'],x['type']['comparisonType'],x['type']['value'])for x in terms[:3]]==[(consent,'GreaterOrEqual',1),('q302_ronald_messages_enabled','GreaterOrEqual',1),(issued,'Equal',0)])
        t=terms[3]['type'];ck('guard_exactInactiveContact',t['path']['realPath']=='ep1/contacts/ronald'and t['path']['className']['$value']=='gameJournalContact'and t['state']=='Inactive'and t['inverted']==0)
        ck('claim_exact1_before_child',pg['root/5']['nodes']['204']['writes']==[{'$type':'questSetVar_NodeType','factName':issued,'setExactValue':1,'value':1}])
        ck('phase205_interface_exact',pg['root/5']['nodes']['205']['sockets']==[{'name':'CutDestination','type':'CutDestination'},{'name':'In1','type':'Input'},{'name':'Out1','type':'Output'}])
        return fail
    failures=validate(scene,phase);assert not failures,failures
    mutants=[]
    def mutation(name,fn):
        s,p=copy.deepcopy(scene),copy.deepcopy(phase);fn(s,p);f=validate(s,p);assert f,name;mutants.append({'fault':name,'detected_by':f})
    mutation('missing native option3 edge',lambda s,p:s['graphs']['scene']['edges'].remove(se[1]))
    mutation('consent receipt bypasses realYes writer',lambda s,p:s['graphs']['scene']['edges'].__setitem__(s['graphs']['scene']['edges'].index(se[0]),['839','0:3','60000','0:1']))
    mutation('contact guard admits alreadyActive',lambda s,p:p['graphs']['root/5']['nodes']['203']['payload']['condition']['conditions'][3]['type'].__setitem__('state','Active'))
    mutation('contact claim rewrites0',lambda s,p:p['graphs']['root/5']['nodes']['204']['writes'][0].__setitem__('value',0))
    mutation('bar lease missing before trigger',lambda s,p:p['graphs']['root']['nodes']['5']['payload'].__setitem__('phaseInstancePrefabs',[]))
    mutation('native HUD delay changed',lambda s,p:p['graphs']['root/5/205']['nodes']['155']['payload']['condition']['type'].__setitem__('seconds',0))
    mutation('premature direct contact termination',lambda s,p:p['graphs']['root/5/205']['edges'].append(['121','Out','201','In']))
    newly=set(scene['graphs']['scene']['reachable'])-set(bs['graphs']['scene']['reachable']);performers=sorted({x['id']for i in newly for x in walk(scene['graphs']['scene']['nodes'][i]['payload'])if x.get('$type')=='scnPerformerId'})
    assert performers==[1281,3841,4294967040]
    assert {x['behaviorMode']for i in newly for x in walk(scene['graphs']['scene']['nodes'][i]['payload'])if x.get('$type')=='scnSectionInternalsActorBehavior'}=={'OnlyIfAlive'}
    epoch=read(W/'prealpha/quest_restoration_qr8/source_epoch_02.json');base=Path(epoch['candidate']);namespace=[]
    for fact in [consent,issued]:
        hits=[str(f)for root in [base/'archive_source',base/'package/r6/scripts']for f in root.rglob('*')if f.is_file()and fact.encode()in f.read_bytes()];assert not hits;namespace.append({'fact':fact,'old_consolidated_raw_and_script_hits':hits})
    protected=r'towercontinued\quest_restoration_qr7\ronald_news_future.questphase';assert sha(base/'archive_source'/protected)==epoch['source_resources'][protected]=='6CEB6AC9FA2909771AEEF09D33A36241E1396D26A072725317374837AB79B0EC'
    result={'status':'APPROVED_ACTUAL_TYPED_RONALD_TWO_RESOURCE_SUCCESSOR_FOR_INTEGRATION','manifest':str(mp),'manifest_sha256':sha(mp),'source_plan':plan['source_plan'],'source_plan_sha256':plan['source_plan_sha256'],'resources':rows,'whole_model_allowlist_failures':failures,'roundtrip_proposal_model_equal':True,'mutation_controls':mutants,'newly_reachable_scene_nodes':len(newly),'newly_reachable_performers':performers,'actor_behaviors_only_if_alive':True,'contact_child_nodes':10,'private_fact_namespace':namespace,'protected_QR8_news_sha256':epoch['source_resources'][protected],'limits':['Exact local graph IDs/sockets preserved; current oldconsolidated raw/script fact literals checked, not a full native/external archived fact-name census.','Source-plan savedprefab/newedge acquisition boundaries and native world/lease/UI scheduling remain LIVE_ONLY.','This approves two actual typed resources, not finalconsolidated package or gameplay/deployment. Coordinator must preserve all other payloads, compile equivalence, XL/registration order and finalreadback.'],'runtime_writes':0,'candidate_changes_by_reviewer':0}
    (out/'review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print({'status':result['status'],'mutations':len(mutants),'scene633plus1':len(scene['graphs']['scene']['nodes']),'new_reachable':len(newly),'contact_nodes':10})
if __name__=='__main__':main()
