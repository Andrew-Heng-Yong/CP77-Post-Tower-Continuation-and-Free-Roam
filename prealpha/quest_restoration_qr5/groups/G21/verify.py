"""Read-only deep contracts for three EP1 U9 entries; no builder imports."""
from lib import *
import argparse,copy,re,zlib,collections
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();O=Path(a.output).resolve();assert not O.exists(),'Fresh output required';O.mkdir(parents=True);(O/'mutations').mkdir()
P=Path(__file__).parent;Q=W/'prealpha/quest_restoration_qr5';EP=read(Q/'source_epoch_00.json');recipes=read(P/'recipes_01.json');M=read(P/'source_models_01.json')|read(P/'shared_models_01.json')|read(P/'donor_models_01.json');pins=read(P/'source_pins_01.json')+read(P/'shared_pins_01.json')+read(P/'donor_pins_01.json');rows=read(P/'raw_exports_01/manifest.json');tests=[];mutations=[];findings={};protocols=[];handler_inventory=[]
IDS=['sts_ep1_07','sts_ep1_04','sts_ep1_01'];NATIVE=r'ep1\openworld\street_stories\ep1_street_stories.questphase';HC=r'base\quest\holocalls\mr_hands\mr_hands_holocall.questphase';HS=HC.replace('.questphase','.scene');CL=HC.replace('mr_hands_holocall.questphase','mr_hands_cleanup.questphase');TG=r'towercontinued\special_gigs_u9\ep1_tier3_gate.questphase'
def ck(name,b,e):
 tests.append({'name':name,'status':'PASS'if b else'FAIL','evidence':e});assert b,name
def canon(x,soft=False):
 x=json.loads(json.dumps(x))
 for z in walk(x):
  z.pop('payload_sha256',None);z.pop('metadata_sha256',None)
  if z.get('$type')=='TweakDBID':
   v=z['$value'];z['$value']=str((len(v.encode())<<32)|zlib.crc32(v.encode()))if z.get('$storage')=='string'else str(int(v));z['$storage']='uint64'
  if soft and 'phaseResource'in z and z['phaseResource'].get('Flags')=='Embedded':z['phaseResource']['Flags']='Soft'
 return x
def g(d,gp='root'):return M[d]['graphs'][gp]
def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
def edge(d,e,gp='root'):return [str(e[0]),e[1],str(e[2]),e[3]]in g(d,gp)['edges']
def has(node,f,v,op='Equal',kind='reads'):return any(x.get('factName')==f and x.get('value')==v and(kind=='writes'or x.get('comparisonType')==op)for x in node[kind])
def path(gr,start,pred):
 todo=[(str(start),[])];seen=set()
 while todo:
  i,route=todo.pop(0)
  if i in seen:continue
  seen.add(i)
  if pred(gr['nodes'][i]):return route
  for e in gr['edges']:
   if e[0]==i and e[1]!='CutSource':todo.append((e[2],route+[e]))
 return None
raw={}
for r in rows:
 d=r['depot'];ck('fresh raw and JSON pins '+d,sha(r['raw'])==r['raw_sha256']and sha(r['json'])==r['json_sha256'],r);raw[d]=read(r['json']);fresh=Resource(raw[d]).normalize();fresh.setdefault('embedded_files',[]);ck('fresh actual raw equals pinned model '+d,canon(fresh)==canon(M[d]),'Only exact TDBID identity/storage and derived digests/tuple-list normalization; no graph, NodeRef or predicate ignored');ck('decoded native graph diagnostics '+d,not fresh['errors'],fresh['errors'])
for p in pins:
 ck('original source pin '+p['depot'],sha(p['binary'])==p['resource_sha256']and sha(p['json'])==p['json_sha256'],p['binary'])
core=Q/'groups/G03/shared_core.json';ck('shared Hands core exact pin',sha(core)=='89BC7C750DE2F832512EA6EED2DB97DD411691708BD9298BAB9DAC2F633DCD40',str(core))
for s in read(core)['sources']:
 if s['depot']in M:ck('per-case core applicability '+s['depot'],next(p for p in pins if p['depot']==s['depot'])['resource_sha256']==s['sha256'],s['sha256'])
script=W/'prealpha/quest_restoration_qr4/candidate_01/package/r6/scripts/PTFR_Consolidated/PTFR_ActivityStateR3.reds';rel='r6/scripts/PTFR_Consolidated/PTFR_ActivityStateR3.reds';ck('effective admission source exact epoch00',sha(script)==next(x['sha256']for x in EP['package_files']if x['path']==rel),str(script));src=script.read_text(encoding='utf-8-sig')
def block(text,needle):
 k=text.index(needle);a=text.index('{',k);depth=1;j=a+1
 while depth:depth+=(text[j]=='{')-(text[j]=='}');j+=1
 return text[a+1:j-1]
data=block(src,'public abstract class NativeGigDataU9');driver=block(src,'public class NativeGigsU9');idlist=json.loads(re.search(r'return (\[.*?\]);',block(data,'func IDs()'),re.S)[1])
def arr(name,i):
 b=block(data,'func '+name+'(');m=re.search(r'if i=='+str(i)+r'\s*\{\s*return (\[.*?\]);',b,re.S)
 if m:return json.loads(m[1])
 m=re.search(r'let a: array<[^>]+>=(\[.*?\]);',b,re.S);return json.loads(m[1])[i]if m else None
ck('EntrySafe all native facts zero','this.Fact(a[k])!=0'in block(driver,'func EntrySafe('),'Actual consolidated implementation, not CR2W guard fact occurrences')
ck('EntrySafe all generated journals inactive','this.State(paths[k],classes[k])!=1'in block(driver,'func EntrySafe('),'Missing journal state is not treated as Inactive')
ck('Poll late revalidation','this.OldUnused(k) && this.EntrySafe(k)'in block(driver,'func Poll('),'Permit requires snapshot and native-history review')
ck('current certified fresh snapshot path','snapshot.FreshU9(id)'in block(driver,'func RestoreSnapshot('),'No synthetic old native counters')
MAIN={'sts_ep1_07':(22,9,18,'start'),'sts_ep1_04':(20,8,14,'In1'),'sts_ep1_01':(11,8,12,'In1')}
for q in IDS:
 er=next(r for r in recipes if r['id']==q and r['kind']=='entry');ed=er['depot'];gp=er['compiled_graph'];donor='vanilla_recipe:'+er['raw'];main,inline,poi,inp=MAIN[q];body=er['native'];idx=idlist.index(q);paths=arr('Paths',idx);classes=arr('Classes',idx);facts=arr('Facts',idx);legacy=arr('LegacyTags',idx);terminal=arr('TerminalFacts',idx)
 ck('catalogue exact binding '+q,idlist[idx]==q and len(paths)==len(classes),{'index':idx,'paths':paths,'classes':classes})
 for i in er['ids']:
  if i in [0,9]and q=='sts_ep1_07':continue
  if i==0:continue
  ck('native isolated entry payload '+q+' '+str(i),canon(n(ed,i,gp)['payload'])==canon(n(donor,i,er['graph'])['payload'],True),{'node':i,'native_graph':er['graph'],'deviation':'phaseResource.Flags Embedded to Soft only'})
 for sub,gr in M[ed]['graphs'].items():
  if sub.startswith(gp+'/')and not(q=='sts_ep1_07'and sub==gp+'/9'):ck('native inline prerequisites exact '+q+sub,canon(gr)==canon(M[donor]['graphs'][sub]),sub)
 for e in er['edges']:ck('actual complete entry route '+q+str(e),edge(ed,e,gp),{'graph':gp,'edge':e})
 ck('actual native body resource/socket '+q,n(ed,main,gp)['refs']==[body]and inp in g(body)['entries'],{'main':main,'input':inp,'native':body})
 ck('native body no packaged override '+q,body not in EP['source_resources'],'Native external body remains provider-pinned')
 ck('native parent instance no omitted prefab '+q,not n(NATIVE,main,'root/50')['prefabs'],n(NATIVE,main,'root/50')['prefabs'])
 ck('native ancestor root no hidden root prefabs '+q,not M[NATIVE]['root_prefabs']and all(not n(NATIVE,i)['prefabs']for i in[50,51,52,53]),'Original main/cleanup/bugfix/aftergig parents inspected; child leases separately inventoried')
 for gp2,gr in M[body]['graphs'].items():
  embedded='embedded/'+body+'/'+gp2
  if embedded in M[donor]['graphs']:ck('embedded donor external body exact '+q+gp2,canon(gr,True)==canon(M[donor]['graphs'][embedded],True),embedded)
 for k,c in enumerate(er['companions']):
  own=64000+k;original=canon(n(NATIVE,c['source_node'],c['source_graph'])['payload'],True);original['id']=own;ck('native companion exact '+q+c['kind'],canon(n(ed,own,gp)['payload'])==original,{'current':own,'native':c['source_node'],'graph':c['source_graph'],'depot':c['depot'],'approved_copy_identity':'Private companion clone gets distinct64000+ local node; native resource and its saved identities unchanged'})
 guard=n(ed,65002,gp);f={x['factName']:x['value']for x in guard['reads']if'factName'in x};ck('actual fresh wrapper admission '+q,evaluate(guard['payload']['condition'],f,{})is True,f)
 for k in['ParentEntered','Fault']:ck('used owner refuses '+q+k,evaluate(guard['payload']['condition'],f|{'PTFRU9_'+q+'_'+k:1},{})is False,k)
 ck('shared controller owner required '+q,has(guard,'PTFRU9_Support_Issued',1)and has(guard,'PTFRU9_Support_Fault',0),'Effective U9 owner receipts, not fake real ACK')
 cr=next(r for r in recipes if r['id']==q and r['kind']=='credit');cd=cr['depot'];co='vanilla_recipe:'+cr['raw']
 for i in cr['ids']:
  if i:ck('original credit node '+q+str(i),n(cd,i)['payload']==n(co,i,cr['graph'])['payload'],{'native':co,'graph':cr['graph'],'node':i})
 for e in cr['edges']:ck('native credit route '+q+str(e),edge(cd,e),e)
 ck('one exact EP1 district increment '+q,has(n(cd,14),'ep1_sts_counter',1,kind='writes')and n(cd,14)['writes'][0]['setExactValue']==0,'Native fixed node14 adds1; no duplicate scripted reward')
 ck('credit once receipt fences '+q,all(has(n(cd,65000),'PTFRU9_'+q+'_'+k,v)for k,v in[('Started',1),('CreditEntered',0),('CreditDone',0)]),'Saved receipts preserved')
 own=[d for d in M if ('\\'+q+'\\')in d and not d.startswith('vanilla_recipe:')];nativejs=sorted({jp for d in own for gr in M[d]['graphs'].values()for x in gr['nodes'].values()for jp in x['journal_paths']if jp.startswith('ep1/quests/')});omissions=sorted(set(nativejs)-set(paths));rewards=[];outputs=[];actors=[];sms=[]
 for d in own:
  for ag,gr in M[d]['graphs'].items():
   for i,x in gr['nodes'].items():
    ev={'depot':d,'graph':ag,'node':i,'type':x['type'],'incoming':[e for e in gr['edges']if e[2]==i],'outgoing':[e for e in gr['edges']if e[0]==i],'reads':x['reads'],'writes':x['writes'],'refs':x['refs'],'prefabs':x['prefabs'],'journal_paths':x['journal_paths'],'node_refs':x['node_refs']}
    if x['reads']or x['writes']or x['refs']or x['journal_paths']or x['reward']or x['sms']or x['prefabs']:handler_inventory.append(ev)
    if x['reward']:rewards.append(ev|{'payload':x['payload']})
    if x['sms']:sms.append(ev)
    if x['type']=='questOutputNodeDefinition':outputs.append(ev|{'lifetime':x['payload'].get('type')})
  if d.endswith('.scene'):actors.append({'depot':d,'actors':M[d]['metadata'].get('actors',[]),'root_prefabs':M[d]['root_prefabs']})
 # Exact connected caller request -> native real controller ACK -> caller wait -> clear.
 for d in own:
  if not d.endswith('.scene'):continue
  gr=g(d,'scene')
  for i,x in gr['nodes'].items():
   for w in x['writes']:
    fact=w.get('factName','')
    if w.get('value')!=1 or not fact.startswith(('holo_mr_hands_calls_v_','holo_v_calls_mr_hands_'))or not fact.endswith('_activate'):continue
    ack=fact[:-9]+'_done';route=path(gr,i,lambda z:any(t.get('factName')==ack and t.get('comparisonType')=='Greater'and t.get('value')==0 for t in z['reads']));retry=None
    if route is None:
     for j,z in gr['nodes'].items():
      if j==i or not any(w2.get('factName')==fact and w2.get('value')==1 for w2 in z['writes']):continue
      armed=path(gr,j,lambda z2:any(t.get('factName')==ack and t.get('comparisonType')=='Greater'and t.get('value')==0 for t in z2['reads']));loop=path(gr,j,lambda z2:z2['id']==i)
      if armed and loop:route=armed;retry={'primary_producer':j,'primary_path_to_this_retry':loop,'kind':'Native parallel retry branch; original ACK wait remains separately armed, not a serial wait after retry'};break
    native_no_wait=q=='sts_ep1_01'and d.endswith('sts_ep1_01_holocall_prebrief.scene')and i=='192'and fact=='holo_mr_hands_calls_v_end_activate'
    ck('connected real ACK waiter or exact native no-wait exception '+q+d+i,bool(route)or native_no_wait,{'producer':i,'request':fact,'ack':ack,'route':route,'retry':retry,'native_no_wait':native_no_wait})
    wait=route[-1][2]if route else None;clear=path(gr,wait or i,lambda z:any(t.get('factName')==ack and t.get('value')==0 for t in z['writes']));ck('connected ACK reset '+q+d+i,bool(clear),{'wait':wait,'path':clear})
    master=[j for j,z in g(HS,'scene')['nodes'].items()if any(t.get('factName')==ack and t.get('value')==1 for t in z['writes'])];ck('native master actual ACK writer '+q+d+i,bool(master),master)
    protocols.append({'quest_id':q,'scene':d,'producer':i,'request':fact,'ack':ack,'wait':wait,'path_to_wait':route,'parallel_retry':retry,'path_to_clear':clear,'master_actual_ack_nodes':master,'native_no_wait_exception':'Exact original prebrief192→125 interrupts-off→190 clear0→209 questcallactive0→2 output; no ACK wait in this native route. Preserved, not silently repaired.'if native_no_wait else None})
 target=Q/'shared/tdb_applicability_02'/str(q+'.json');tdb=read(target);used={str(val(x))for d in own for x in walk(M[d])if x.get('$type')=='TweakDBID'};verified=[]
 for t in tdb['targets']:
  uses=[u for u in tdb['uses']if str(u.get('id'))==t['id']]
  # Target collector retains native aliases; exact numeric identity independently checked below.
  applicable=t['id']in used or any(str((len(v.encode())<<32)|zlib.crc32(v.encode()))==t['id']for v in used if not v.isdecimal())
  if applicable:ck('actual stock target '+q+t['id'],t['exists_in_stock'],t);verified.append(t)
 findings[q]={'entry':ed,'graph':er['compiled_graph'],'main_node':main,'native_body':body,'native_prefabs':{d:M[d]['root_prefabs']for d in own if d.endswith('.questphase')},'native_instances':[{ 'depot':d,'graph':ag,'node':i,'prefabs':x['prefabs']}for d in own for ag,gr in M[d]['graphs'].items()for i,x in gr['nodes'].items()if x['prefabs']],'admission':{'index':idx,'paths':paths,'classes':classes,'facts':facts,'legacy':legacy,'terminal':terminal,'native_journal_paths_not_in_EntrySafe':omissions},'root_entry_predicates':guard['payload']['condition'],'original_entry':{'graph':er['graph'],'nodes':er['ids'],'inline':inline,'poi':poi,'main_input':inp},'companions':er['companions'],'credit':cr,'outputs':outputs,'rewards':rewards,'sms_handlers':sms,'scene_actors':actors,'stock_applicability':{'path':str(target),'sha256':sha(target),'applicable_verified_targets':verified,'collector_targets':len(tdb['targets']),'limits':tdb['limits']}}
# Explicit selected entry/adapters and phone-controller routes, independently named from native raw evidence.
ck('Roads native outside-content predicate preserved',n(NATIVE,21,'root/50')['payload']==n(findings['sts_ep1_07']['entry'],21,'root/50')['payload']and val(n(NATIVE,21,'root/50')['payload']['condition']['triggerAreaRef'])=='#sts_ep1_07_content_init','IsOutside native predicate, not an invented proximity bypass; trigger placement remains opaque')
ck('Roads tier listener is actual intermediate pause',has(n(findings['sts_ep1_07']['entry'],2,'root/50/9'),'PTFRU9_EP1Tier3_Ready',1),'0→2Pause→1, cannot skip intermediate')
h=read(P/'tier_cohort_hypothesis_01.json');ck('rejected tier cohort hypothesis retained',h['status']=='REJECTED_FLATTENED_FACT_OCCURRENCE_HYPOTHESIS',str(P/'tier_cohort_hypothesis_01.json'))
gate=n(TG,65000,'root/50')['payload']['condition'];base={x['factName']:x['value']for x in n(TG,65000,'root/50')['reads']};pairs=['PTFRU9_sts_ep1_06_Request','PTFRU9_sts_ep1_06_Permit','PTFRU9_sts_ep1_07_Request','PTFRU9_sts_ep1_07_Permit']
for a6,a7,want in[(0,1,True),(1,0,True),(0,0,False),(1,1,True)]:ck('whole nested tier OR fixture '+str((a6,a7)),evaluate(gate,base|dict(zip(pairs,[a6,a6,a7,a7])),{})is want,'Actual serialized OR of two AND pairs')
for i in[3,4,5,32,36]:ck('native Hands listener exists '+str(i),n(HC,i)['type']=='questPauseConditionNodeDefinition',n(HC,i)['reads'])
for e in[(32,'Out',33,'In'),(36,'Out',28,'In'),(4,'Out',30,'In'),(3,'Out',11,'In'),(5,'Out',13,'In')]:ck('native Hands connected listener '+str(e),edge(HC,e),e)
for i,ack in[(41,'holo_mr_hands_calls_v_start_done'),(42,'holo_mr_hands_calls_v_end_done'),(43,'holo_v_calls_mr_hands_start_done'),(44,'holo_v_calls_mr_hands_end_done')]:ck('master actual real ACK '+ack,has(n(HS,i,'scene'),ack,1,kind='writes'),i)
for e in[(4,'True',6,'In'),(4,'False',5,'In'),(5,'True',7,'In')]:ck('native bidirectional interrupted cleanup '+str(e),edge(CL,e),e)
ck('Prototype real outgoing producer applicability',any(x['quest_id']=='sts_ep1_04'and x['request']=='holo_v_calls_mr_hands_start_activate'and x['scene'].endswith('hasan_final.scene')for x in protocols),'Actual Hasan-final route, not inherited generic incoming-only proof')
support=read(P/'followup_support_models_01.json');supportpins=read(P/'followup_support_pins_01.json');G16=Q/'groups/G16/shared_core.json';ck('exact independently reviewed Hasan core',sha(G16)=='2F4661F97B80F15D9F5B3C15052DF798640269994D4F85A1875A57B6277A7EFC','311 primary/118 independent source controls remain scoped to earned Hasan outcomes')
for s in read(G16)['source_pins']:
 if s.get('depot')in support:ck('Hasan reused source applicability '+s['depot'],next(p for p in supportpins if p['depot']==s['depot'])['resource_sha256']==s['sha256'],s['sha256'])
hd=r'towercontinued\sidejobs_s23\ep1\hasan_boot.questphase';hnode=support[hd]['graphs']['root']['nodes']['2'];ck('Hasan future earned-outcome applicability',all(has(hnode,f,v,op)for f,v,op in[('hasan_default_on',1,'GreaterOrEqual'),('sts_ep1_04_blueprints_corpo',1,'GreaterOrEqual'),('sts_ep1_04_mr_hands_holo_convinced',1,'GreaterOrEqual')])and not any(x.get('factName','').startswith('PTFRU9_sts_ep1_04_')for x in hnode['reads']),'Actual native cleanup12 default_on writer reaches an existing earned-state owner; no Steven-like U9zero exclusion')
ck('Prototype earned default writer native',has(n(r'ep1\openworld\street_stories\sts_ep1_04\phases\sts_ep1_04_cleanup.questphase',12),'hasan_default_on',1,kind='writes'),'Native cleanup22→12→11 debrief-completed pause; outcome-specific S23 guard is not replaced')
rc=r'ep1\openworld\street_stories\sts_ep1_07\phases\sts_ep1_07_cleanup.questphase';ck('Roads native future outcomes both retained',has(n(rc,11),'wst_ep1_08_active',1,kind='writes')and has(n(rc,14),'wst_ep1_09_active',1,kind='writes')and edge(rc,(48,'Out',9,'In'))and edge(rc,(48,'Out',12,'In')),'Normal cleanup live producer separate from one-shot CP77-63925 migration')
ck('Roads cleanup output explicitly nonterminating',n(rc,1)['payload']['type']=='NonTerminating','OwnerFinished callback cannot be equated with all descendant retirement')
wd=r'towercontinued\sidejobs_s29\entries\wst_ep1_09.questphase';ck('One Way or Another existing earned consumer',any(has(x,'wst_ep1_09_active',1)for x in support[wd]['graphs']['root']['nodes'].values()),'Selected Q10, full deep followup deferred; wst_ep1_08 has no selected catalogue identity and is not silently restored')
# Faults are applied to freshly decoded original binary inputs, then re-normalized.
def mutate(name,d,predicate,change,oracle):
 fixture=copy.deepcopy(raw[d]);count=0
 for x in walk(fixture):
  if predicate(x):change(x);count+=1
 ck('raw mutation oracle original '+name,oracle(Resource(raw[d]).normalize()),d);bad=Resource(fixture).normalize();ck('raw mutation detected '+name,count>0 and not oracle(bad),{'changed_objects':count,'source':d});f=O/'mutations'/str(name+'.json');save(f,fixture);mutations.append({'name':name,'source':d,'source_raw_sha256':next(r['raw_sha256']for r in rows if r['depot']==d),'fixture':str(f),'sha256':sha(f),'detected':True})
mutate('missing_outgoing_real_ACK',HS,lambda x:x.get('$type')=='questSetVar_NodeType'and x.get('factName')=='holo_v_calls_mr_hands_start_done',lambda x:x.update(value=0),lambda m:any(w['factName']=='holo_v_calls_mr_hands_start_done'and w['value']==1 for w in m['graphs']['scene']['nodes']['43']['writes']))
for q in IDS:
 d=findings[q]['entry'];gp=findings[q]['graph'];mutate('changed_native_entry_journal_'+q,d,lambda x:x.get('$type')=='gameJournalPath'and x.get('realPath')=='ep1/points_of_interest/street_stories/'+q,lambda x:x.update(realPath='ep1/points_of_interest/street_stories/WRONG'),lambda m:'ep1/points_of_interest/street_stories/'+q in m['graphs'][gp]['nodes'][str(MAIN[q][2])]['journal_paths'])
 cd=findings[q]['credit']['depot'];mutate('double_district_credit_'+q,cd,lambda x:x.get('$type')=='questSetVar_NodeType'and x.get('factName')=='ep1_sts_counter',lambda x:x.update(value=2),lambda m:m['graphs']['root']['nodes']['14']['writes'][0]['value']==1)
scene=next(x['scene']for x in protocols if x['quest_id']=='sts_ep1_04'and x['request']=='holo_v_calls_mr_hands_start_activate');mutate('lost_Hasan_outgoing_request',scene,lambda x:x.get('$type')=='questSetVar_NodeType'and x.get('factName')=='holo_v_calls_mr_hands_start_activate',lambda x:x.update(value=0),lambda m:any(w['factName']=='holo_v_calls_mr_hands_start_activate'and w['value']==1 for x in m['graphs']['scene']['nodes'].values()for w in x['writes']))
save(O/'findings.json',findings);save(O/'protocols.json',protocols);save(O/'handler_inventory.json',handler_inventory);save(O/'source_pins.json',pins+supportpins);save(O/'tests.json',tests);save(O/'mutations.json',mutations);save(O/'summary.json',{'status':'PASS_SOURCE_CHECKS_WITH_EXPLICIT_CONTRACT_LIMITS','quests':IDS,'checks':len(tests),'mutations':len(mutations),'fresh_raw_exports':len(rows),'source_models':len(M)+len(support),'handler_rows':len(handler_inventory),'protocol_producers':len(protocols),'no_runtime_edits':True});print(json.dumps({'checks':len(tests),'mutations':len(mutations),'handlers':len(handler_inventory),'protocols':len(protocols)}))
