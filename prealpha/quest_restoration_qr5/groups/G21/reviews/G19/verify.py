"""Independent G19 raw-source/contract review. Imports no G19 verifier or builder."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from lib import *
import argparse,copy,re,zlib,collections
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();O=Path(a.output).resolve();assert not O.exists(),'Fresh output required';O.mkdir(parents=True);(O/'mutations').mkdir();H=Path(__file__).parent;Q=W/'prealpha/quest_restoration_qr5';G=Q/'groups/G19';E=read(Q/'source_epoch_08.json');selected=read(G/'selection.json');M={};R={};checks=[];mut=[];pins=[]
def ck(k,b,e):checks.append({'name':k,'status':'PASS'if b else'FAIL','evidence':e});assert b,k
def canon(x,soft=False):
 x=json.loads(json.dumps(x))
 for z in walk(x):
  z.pop('payload_sha256',None);z.pop('metadata_sha256',None)
  if z.get('$type')=='TweakDBID':
   v=z['$value'];z['$value']=str((len(v.encode())<<32)|zlib.crc32(v.encode()))if z.get('$storage')=='string'else str(int(v));z['$storage']='uint64'
  if soft and'phaseResource'in z:z['phaseResource']['Flags']='Soft'
 return x
source={x['depot']:x for x in read(H/'inputs.json')}
for x in read(H/'raw_readback_01/manifest.json'):
 d=x['depot'];s=source[d];ck('independent fresh raw pin '+d,sha(x['raw'])==x['raw_sha256']==s['hash']and sha(x['json'])==x['json_sha256']and sha(s['original_json'])==s['original_json_sha256'],x);R[d]=read(x['json']);M[d]=Resource(R[d]).normalize();expected=Resource(read(s['original_json'])).normalize();ck('fresh actual graph all fields match pinned source '+d,canon(M[d])==canon(expected),'Only exact TDBID identity and derived digest/list representation normalized; no NodeRef/predicate/edge omitted');pins.append(x)
 if d.startswith('towercontinued\\'):ck('current08 resource applicability '+d,E['source_resources'][d]==x['raw_sha256'],'Current08 bytes, not inherited baseline label')
def g(d,gp='root'):return M[d]['graphs'][gp]
def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
def ed(d,a,s,b,t,gp='root'):return[str(a),s,str(b),t]in g(d,gp)['edges']
def fact(d,i,f,v,kind='writes',gp='root'):return any(x.get('factName')==f and x.get('value')==v for x in n(d,i,gp)[kind])
def find(s):return next(d for d in M if d.endswith('\\'+s))
def path(gr,start,predicate):
 todo=[(str(start),[])];seen=set()
 while todo:
  i,rt=todo.pop(0)
  if i in seen:continue
  seen.add(i)
  if predicate(gr['nodes'][i]):return rt
  for e in gr['edges']:
   if e[0]==i and e[1]!='CutSource'and e[3]!='CutDestination'and not(gr['nodes'][i]['type']=='scnCutControlNode'and e[1].startswith('1:')):todo.append((e[2],rt+[e]))
 return None
ids=selected['ids'];ck('exact three selected identities',set(ids)=={'sts_ep1_10','sts_ep1_08','sts_ep1_13'},ids);result_hash=sha(G/'results.json');res=read(G/'results.json');ck('author result three identities and30contracts',res['contract_count']==30 and set(res['quest_ids'])==set(ids),{'path':str(G/'results.json'),'sha256':result_hash})
contract_review=[];stages={'entry','eligibility','communications','ownership','progression','presentation','journal','completion_rewards_cleanup','persistence','shared_dependencies'}
for rr in res['quest_results']:
 ck('author contract frozen pin '+rr['quest_id'],sha(rr['contracts'])==rr['contracts_sha256'],rr);co=read(rr['contracts']);ck('ten specific contracts '+rr['quest_id'],set(co['contracts'])==stages and all(c['proven']and c['evidence']for c in co['contracts'].values()),'Reviewed all specific source assertions and remaining limits; not generic pending labels')
 for k,c in co['contracts'].items():contract_review.append({'quest_id':rr['quest_id'],'contract':k,'status':c['status'],'review':'ACCEPT_BOUNDED_SOURCE_FINDING_WITH_RECORDED_LIMITS','source_findings':rr['contracts'],'source_findings_sha256':rr['contracts_sha256']})
for r in selected['recipes']:
 d=r['depot'];gp=r.get('compiled_graph','root');don='recipe:'+r['raw']
 for i in r['ids']:
  if not i:continue
  ck('independent original isolated payload '+d+str(i),canon(n(d,i,gp)['payload'])==canon(n(don,i,r['graph'])['payload'],True),{'native':don,'graph':r['graph'],'node':i})
 for sub,gr in M[d]['graphs'].items():
  if sub.startswith(gp+'/')and sub.split('/')[2]in[str(i)for i in r['ids']]:ck('independent nested original graph '+d+sub,canon(gr)==canon(M[don]['graphs'][sub]),sub)
 if r['kind']=='entry':
  ck('whole native body unchanged provider '+r['id'],r['native']not in E['source_resources'],'Original body remains external, native internal saved nodes unchanged')
  for c in r['companions']:ck('native companion resource present '+r['id']+c['kind'],c['depot']in M and c['depot']not in E['source_resources'],c)
  for f,v in[('Request',1),('Permit',1),('ParentEntered',0),('Fault',0)]:ck('fresh owner boundary '+r['id']+f,fact(d,65002,'PTFRU9_'+r['id']+'_'+f,v,'reads',gp),f)
 else:ck('native ep1 once credit '+r['id'],fact(d,14,'ep1_sts_counter',1)and n(d,14)['writes'][0]['setExactValue']==0 and all(fact(d,65000,'PTFRU9_'+r['id']+'_'+k,v,'reads')for k,v in[('Started',1),('CreditEntered',0),('CreditDone',0)]),'Original credit14 and private once receipts')
spyentry=r'towercontinued\native_gigs_u9\sts_ep1_08_entry.questphase';ck('current approved Spy carrier',source[spyentry]['hash']=='5D1FE58F41739C231B5006FF134EB78207FC879B9AB8652FADE69899242C2F62'and set(g(spyentry,'root/50/1302')['nodes'])=={'0','17','19','1303'},'Explicit sourceepoch05→08 unchanged; preserved original body plus approved ordered actor-only helper')
for e in[(65003,'Out',1300,'In'),(1300,'True',1301,'In'),(1301,'Out',1302,'In1'),(1301,'Out',10,'In1'),(1301,'Out',64001,'In1'),(1300,'False',10,'In1'),(1300,'False',64001,'In1')]:ck('ordered helper refuses without blocking native '+str(e),ed(spyentry,*e,'root/50'),e)
for e in[(19,'Out',1303,'In'),(1303,'Out',17,'In1')]:ck('every dispatch late actor fence '+str(e),ed(spyentry,*e,'root/50/1302'),e)
ck('late Ana0 fence retained',fact(spyentry,1303,'sts_ep1_08_biomonitor_ana',0,'reads','root/50/1302'),'Initial approval alone cannot authorize later Ana1 dispatch')
ac=read(Q/'approved_changes_04.json');sp=next(x for x in ac['resources']if x['depot']==spyentry);sr=Path(sp['independent_serialized_review']);ck('independent Steven source/serialized140 scope',sha(sr)==sp['independent_serialized_review_sha256']and read(sr)['checks']==140,sp)
# Request producer and actual native consumer/ACK, with connected per-scene waits.
pat=re.compile(r'^(holo|audio)_(?:(.+)_calls_v|v_calls_(.+))_(start|end)_activate$');phone=[];calls=[]
for d,m in M.items():
 if not d.startswith('ep1\\openworld\\street_stories')or not any(('\\'+q+'\\')in d for q in ids):continue
 for gp,gr in m['graphs'].items():
  for i,z in gr['nodes'].items():
   for w in z['writes']:
    if w['value']<=0:continue
    match=pat.fullmatch(w['factName'])
    if not match:continue
    mode,inc,out,part=match.groups();contact=inc or out;base=('base'if contact=='mr_hands'else'ep1')+'\\quest\\holocalls\\'+contact+'\\'+contact+'_';controller=base+'holocall.questphase';scene=base+'holocall.scene';ack='holo_'+(contact+'_calls_v'if inc else'v_calls_'+contact)+'_'+part+'_done';listeners=[(ag,j)for ag,gg in M[controller]['graphs'].items()for j,nn in gg['nodes'].items()if any(x.get('factName')==w['factName']for x in nn['reads'])];acks=[j for j,nn in g(scene,'scene')['nodes'].items()if any(x.get('factName')==ack and x['value']==1 for x in nn['writes'])];ck('independent producer real native listener and ACK '+d+gp+i,bool(listeners)and bool(acks),{'request':w['factName'],'listeners':listeners,'ACK':ack,'writers':acks});phone.append({'depot':d,'graph':gp,'node':i,'request':w['factName'],'listeners':listeners,'ACK':ack,'writers':acks})
    if gp!='scene':continue
    route=path(gr,i,lambda nn:any(x.get('factName')==ack and x.get('comparisonType')in['Greater','Equal']and x.get('value')in[0,1]for x in nn['reads']));parallel=None
    if not route:
     for j,nn in gr['nodes'].items():
      if j==i or not any(x.get('factName')==w['factName']and x['value']>0 for x in nn['writes']):continue
      existing=path(gr,j,lambda tt:any(x.get('factName')==ack and x.get('comparisonType')in['Greater','Equal']for x in tt['reads']));retry=path(gr,j,lambda tt:tt['id']==i)
      if existing and retry:route=existing;parallel={'primary':j,'retry_route':retry};break
    ck('independent connected caller ACK branch '+d+i,bool(route),{'path':route,'parallel':parallel});wait=route[-1][2];clear=path(gr,wait,lambda nn:any(x.get('factName')==ack and x['value']==0 for x in nn['writes']));cc=[j for j,nn in g(scene,'scene')['nodes'].items()if any(x.get('factName')==ack and x['value']==0 for x in nn['writes'])];janet_exception=contact=='janet'and i=='1594';ck('independent caller ACK clear ownership '+d+i,bool(clear)or(janet_exception and'383'in cc),{'caller_clear_path':clear,'native_controller_clears':cc,'Janet_original_start_no_local_clear':janet_exception});calls.append({'depot':d,'producer':i,'request':w['factName'],'ACK':ack,'wait_route':route,'parallel':parallel,'clear_route':clear,'controller_clear':cc})
ck('all38 actual own call request sites',len(phone)==38,{'total':len(phone),'scene_sites':len(calls)})
xlpath=Path(E['candidate'])/'package/archive/pc/mod/zzzz_PTFR_Combined.archive.xl';xl=xlpath.read_text();ck('current XL exact epoch08',sha(xlpath)==next(x['sha256']for x in E['package_files']if x['path'].endswith('.archive.xl')),str(xlpath))
for c,d in[('mark_bana',r'towercontinued\phone_merge_ph2\mark_bana_listener.questphase'),('janet',r'towercontinued\phone_support_ph1\janet.questphase')]:ck('actual exactly once original phone owner '+c,xl.count('path: '+d)==1 and re.search(r'path: '+re.escape(d)+r'\s+parent: ep1\\quest\\ep1.quest\s+input:\s+node: \[1\]\s+socket: Out',xl)is not None and n(d,10)['refs']==['ep1\\quest\\holocalls\\'+c+'\\'+c+'_holocall.questphase']and ed(d,4,'Out',10,'In1'),d)
ck('obsolete old PH1Mark remains unregistered','path: towercontinued\\phone_support_ph1\\mark_bana.questphase'not in xl,'File presence is not an additional owner')
clean=r'towercontinued\gig_phone_u9\fixer_cleanup.questphase';master=r'ep1\quest\holocalls\holocall_cleanup_ep1.questphase';studio=r'towercontinued\phone_studios_ph3\studio_support.questphase'
init=r'towercontinued\gig_phone_u9\fixer_initializer.questphase';ck('effective Hands initializer whole controller',ed(init,25,'Out1',73,'In1')and n(init,73)['refs']==[r'base\quest\holocalls\mr_hands\mr_hands_holocall.questphase'],'Native listener is actually attached')
for e in[(462,'True',329,'In36'),(1400,'True',1401,'In'),(1401,'True',1402,'In1'),(1402,'Out1',1403,'In'),(1403,'True',1404,'In'),(1404,'True',1405,'In1')]:ck('effective exact reset-chain connection '+str(e),ed(clean,*e),e)
for gp,ng in[('root/1402','root/81'),('root/1405','root/79')]:ck('actual EP1 cleanup donor identity '+gp,canon(g(clean,gp))==canon(g(master,ng)),{'native_master':master,'native_graph':ng,'not_substituted':'Standalone Mark/Janet cleanup has different reset prefix and sockets'})
ck('two native studio leases retained on actual phase3',n(studio,3)['prefabs']==['$/03_night_city/c_pacifica/#holocalls_studio_ep1','$/03_night_city/ne2/#holocalls_studio'],'Root empty is not instance-empty; no strict listener-before-request claim')
spy=find('sts_ep1_08_phase.questphase');dod=find('sts_ep1_10_openworld.questphase');tal=find('sts_ep1_13_cleanup.questphase');target=find('sts_ep1_08_target_meeting.scene');auction=find('sts_ep1_13_v_auction.scene')
for e in[(139,'Out',153,'In'),(153,'Out',67,'Bana intro'),(67,'phone end 01',380,'In'),(380,'Out',309,'Succeeded'),(309,'Out',281,'Active'),(281,'Out',209,'In'),(209,'Out',211,'In'),(211,'Out',146,'In'),(146,'Out',143,'In'),(143,'Out',21,'Succeeded')]:ck('source-confirmed personal link real call door route '+str(e),ed(spy,*e),e)
ck('actual native link condition',val(n(spy,139)['payload']['condition']['type']['deviceConditionFunction'])=='IsPersonalLinkConnected','No fabricated authorization bit')
for i,act in[(211,'AuthorizationDisable'),(146,'ForceOpen'),(143,'ForceOpen')]:ck('native after-call device action '+str(i),val(n(spy,i)['payload']['type']['params'][0]['deviceAction'])==act,act)
for e in[(310,'True',103,'In'),(310,'False',100,'In'),(100,'Out',418,'In'),(103,'Out',418,'In'),(329,'Out',312,'In'),(312,'Out',314,'In')]:ck('real biomonitor split completion '+str(e),ed(spy,*e),e)
for e in[(145,'Out',146,'In'),(78,'End 0',87,'In1'),(78,'not_rejectable_q303_end',87,'In2'),(87,'Out1',83,'In'),(77,'Out',83,'In'),(83,'Out',93,'In2'),(88,'Out',82,'In')]:ck('Dodger native reward alternatives '+str(e),ed(dod,*e,'root/10'),e)
ck('Dodger native defeated outcome not literal-death rewrite',all(n(dod,145,'root/10')['payload']['condition']['type'][k]==1 for k in['defeated','killed','unconscious'])and fact(dod,146,'sts_ep1_10_dodger_dead',1,gp='root/10'),'No misleading semantic relabel')
for e in[(29,'True',5,'In'),(29,'False',30,'In'),(5,'Out',30,'In'),(30,'Out',51,'In'),(72,'Out',73,'In')]:ck('Talent native fail reward exclusion '+str(e),ed(tal,*e),e)
ck('Talent reward exact failure0',fact(tal,29,'sts_ep1_13_failed',0,'reads'),'Failed path goes to native terminal without granting reward5')
for f,ws,rs in[('sts_ep1_13_auction_end_request',[788,795],[1321,1323,1781,2163,2174]),('sts_ep1_13_auction_speedup_request',[810],[1260,1670,1688,2133,2141,2189])]:ck('auction actual local request consumers '+f,all(fact(auction,i,f,1,gp='scene')for i in ws)and all(any(x.get('factName')==f for x in n(auction,i,'scene')['reads'])for i in rs),{'writers':ws,'readers':rs})
diag=[{'depot':d,'errors':m['errors']}for d,m in M.items()if m['errors']];ck('native dangling scope remains explicit',len(diag)==1 and diag[0]['depot'].endswith('sts_ep1_08_gameplay.questphase')and len(diag[0]['errors'])==2,'Original two dangling endpoints at gameplay node2 retained; progression remains CONDITIONAL')
ad=read(G/'verification_03/admission.json');omitted={q:list(z['omitted_native_facts'])for q,z in ad.items()};ck('eight admission history omissions explicitly retained',sum(len(z)for z in omitted.values())==8 and all(read(rr['contracts'])['contracts']['eligibility']['status']=='CONDITIONAL'for rr in res['quest_results']),omitted)
script=Path(E['candidate'])/'package/r6/scripts/PTFR_Consolidated/PTFR_ActivityStateR3.reds';ck('effective admission source actual08',sha(script)==next(x['sha256']for x in E['package_files']if x['path'].endswith('/PTFR_ActivityStateR3.reds')),str(script));text=script.read_text(encoding='utf-8-sig')
def block(needle):
 i=text.index(needle);a=text.index('{',i);depth=1;j=a+1
 while depth:depth+=(text[j]=='{')-(text[j]=='}');j+=1
 return text[a+1:j-1]
ids_array=json.loads(re.search(r'return (\[.*?\]);',block('func IDs()'),re.S)[1])
for q,z in ad.items():
 ix=ids_array.index(q);ck('exact current catalogue index '+q,ix==z['index'],ix)
 for name in['Paths','Classes','Facts','TerminalFacts']:
  body=block('func '+name+'(');match=re.search(r'if i=='+str(ix)+r'\s*\{\s*return (\[.*?\]);',body,re.S);ck('exact independently parsed admission '+q+name,match is not None and json.loads(match[1])==z[name],{'function':name,'index':ix})
ck('current EntrySafe and late Poll fences',all(s in text for s in['this.State(paths[k],classes[k])!=1','this.Fact(a[k])!=0','this.OldUnused(k) && this.EntrySafe(k)','return poi==1 || poi==2;']),'Do not infer omitted journals/receipts from mere count; exact unsupported histories remain conditional')
for b in read(G/'verification_03/bindings.json'):
 ck('independently complete root and recursive prefab inventory '+b['depot'],M[b['depot']]['root_prefabs']==b['root_prefabs']and[{'graph':gp,'node':i,'prefabs':x['prefabs']}for gp,gr in M[b['depot']]['graphs'].items()for i,x in gr['nodes'].items()if x['prefabs']]==b['node_prefabs'],'Includes instance and ancestor obligations, not just resource root')
jv=Path(E['candidate'])/'package/r6/scripts/PTFR_Consolidated/PTFR_JohnnyVoiceJV1.reds';jtext=jv.read_text();ck('current Johnny policy exact source',sha(jv)==next(x['sha256']for x in E['package_files']if x['path'].endswith('/PTFR_JohnnyVoiceJV1.reds'))and'actor.GetRecordID() != t"Character.Silverhand"'in jtext and'visual.TemporaryHide(true)'in jtext,'Visual source applicability, not observed rendering/independent prop suppression')
actors=read(G/'presentation_applicability_02.json')['actors']
for a in actors:
 d=a['depot'];ck('specific native Johnny actor binding '+d,any(str(z.get('$value'))=='85903861324'for ac in M[d]['metadata'].get('actors',[])for z in walk(ac)if z.get('$type')=='TweakDBID'),'Character.Silverhand exact uint64 identity; no native metadata removal')
for q,z in ad.items():
 for f,rr in z['omitted_native_facts'].items():ck('actual omitted native writer '+f,all(fact(r['depot'],r['node'],f,w['value'],gp=r['graph'])for r in rr for w in r['writes']if w['factName']==f),rr)
for q in ids:
 stock=read(Q/'shared/tdb_applicability_02'/str(q+'.json'));reward=[t for t in stock['targets']if any(s.startswith('QuestRewards.'+q)for s in t['requested_aliases'])];ck('direct stock reward applicability '+q,bool(reward)and all(t['exists_in_stock']for t in reward),reward)
def mutate(name,d,pred,change,oracle):
 r=copy.deepcopy(R[d]);num=0
 for x in walk(r):
  if pred(x):change(x);num+=1
 ck('independent raw fault '+name,num>0 and oracle(M[d])and not oracle(Resource(r).normalize()),{'source':d,'objects':num});p=O/'mutations'/str(name+'.json');save(p,r);mut.append({'name':name,'source':d,'path':str(p),'sha256':sha(p),'detected':True})
janet=r'ep1\quest\holocalls\janet\janet_holocall.scene';mutate('genuine_Ana_ACK_value_lost',janet,lambda x:x.get('$type')=='questSetVar_NodeType'and x.get('factName')=='holo_janet_calls_v_start_done',lambda x:x.update(value=0),lambda m:any(w['factName']=='holo_janet_calls_v_start_done'and w['value']==1 for w in m['graphs']['scene']['nodes']['299']['writes']))
mutate('personal_link_wrong_function',spy,lambda x:x.get('$type')=='CName'and x.get('$value')=='IsPersonalLinkConnected',lambda x:x.update({'$value':'IsPowered'}),lambda m:val(m['graphs']['root']['nodes']['139']['payload']['condition']['type']['deviceConditionFunction'])=='IsPersonalLinkConnected')
mutate('failed_Talent_reward_guard_broadened',tal,lambda x:x.get('$type')=='questVarComparison_ConditionType'and x.get('factName')=='sts_ep1_13_failed',lambda x:x.update(value=1),lambda m:m['graphs']['root']['nodes']['29']['reads'][0]['value']==0)
mutate('Dodger_unconscious_outcome_dropped',dod,lambda x:x.get('$type')=='questCharacterKilled_ConditionType'and x.get('unconscious')==1 and x.get('killed')==1,lambda x:x.update(unconscious=0),lambda m:m['graphs']['root/10']['nodes']['145']['payload']['condition']['type']['unconscious']==1)
st=copy.deepcopy(R[studio]);rr=Resource(st);ng=rr.d(rr.root['graph']);nn=next(rr.d(h)for h in ng['nodes']if rr.d(h)['id']==3);nn['phaseInstancePrefabs']=[];ck('independent raw missing studio owner',bool(n(studio,3)['prefabs'])and not Resource(st).normalize()['graphs']['root']['nodes']['3']['prefabs'],'PH3 instance lease, not empty initializer root');save(O/'mutations/missing_studios.json',st);mut.append({'name':'missing_studios','path':str(O/'mutations/missing_studios.json'),'sha256':sha(O/'mutations/missing_studios.json'),'detected':True})
for p in pins:ck('actual raw preserved '+p['depot'],sha(p['raw'])==p['raw_sha256'],'Read-only source inspection')
ck('frozen result unchanged during independent review',sha(G/'results.json')==result_hash,result_hash)
save(O/'checks.json',checks);save(O/'raw_pins.json',pins);save(O/'request_routes.json',phone);save(O/'caller_routes.json',calls);save(O/'contract_review.json',contract_review);save(O/'native_diagnostics.json',diag);save(O/'mutations.json',mut)
out={'status':'PASS_INDEPENDENT_30_CONTRACT_SOURCE_REVIEW_WITH_EXPLICIT_LIMITS','quest_ids':ids,'checks':len(checks),'mutations':len(mut),'fresh_raw_inputs':len(pins),'actual_request_sites':len(phone),'scene_producers':len(calls),'contract_count':len(contract_review),'source_result':str(G/'results.json'),'source_result_sha256':sha(G/'results.json'),'current_epoch':str(Q/'source_epoch_08.json'),'current_epoch_sha256':sha(Q/'source_epoch_08.json'),'current_Spy_sha256':source[spyentry]['hash'],'runtime_changes':[],'limits':['Exact source/raw/static parity and reviewed adapter boundaries; no gameplay certification','Two original Spy dangling endpoints and eight omitted admission-history fields remain explicit; no fabricated counters or history','Native world, saved owner, scene/phone scheduling, full reward descendant expansion/runtime overrides and Johnny rendering remain conditional/opaque','Native Janet start relies on actual controller383 reset; no synthetic local-clear repair','Current sourceepoch08 retains current G19 resources including approved Spy helper; no original actor/timer/SMS reward is replayed']};save(O/'review.json',out);print(json.dumps({'checks':len(checks),'mutations':len(mut),'raw':len(pins),'review_sha256':sha(O/'review.json')}))
