"""Independent G17 peer: actual binaries, native branches and all20 contracts.
Only pure parity model helpers are imported. Author verifiers are not imported.
"""
from pathlib import Path
import sys,json,copy,re,zlib,argparse,collections
H=Path(__file__).resolve().parent;W=H.parents[4];F=W/'prealpha/quest_restoration_qr5';G=F/'groups/G17'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk
from model import Resource

def canon(x):
 x=json.loads(json.dumps(x))
 for z in walk(x):
  z.pop('payload_sha256',None);z.pop('metadata_sha256',None)
  if z.get('$type')=='TweakDBID':
   t=z['$value'];z['$value']=str((len(t.encode())<<32)|zlib.crc32(t.encode()))if z['$storage']=='string'else str(int(t));z['$storage']='uint64'
 return x

def route(g,a,b):
 a=str(a);b=str(b);todo=[a];seen=set()
 while todo:
  u=todo.pop(0)
  if u==b:return True
  if u in seen:continue
  seen.add(u)
  todo.extend(e[2]for e in g['edges']if e[0]==u and e[1]!='CutSource'and e[3]!='CutDestination'and not(g['nodes'][u]['type']=='scnCutControlNode'and e[1].startswith('1:')))
 return False

def ev(x,f,j):
 t=x['$type']
 if t=='questLogicalCondition':
  v=[ev(z,f,j)for z in x['conditions']]
  return all(v)if x['operation']=='AND'else any(v)if x['operation']=='OR'else not any(v)if x['operation']=='NOR'else False
 if t in ['questFactsDBCondition','questJournalCondition']:return ev(x['type'],f,j)
 if t=='questVarComparison_ConditionType':
  a=f.get(x['factName'],0);b=x['value']
  return {'Equal':a==b,'NotEqual':a!=b,'Greater':a>b,'GreaterOrEqual':a>=b,'Less':a<b,'LessOrEqual':a<=b}[x['comparisonType']]
 if t=='questJournalEntryState_ConditionType':
  if x['path']['realPath']not in j:return False
  v=j[x['path']['realPath']]==x['state'];return not v if x.get('inverted')else v
 raise ValueError(t)

def run(O):
 assert not O.exists();tests=[];pins=[];M={};R={};mut=[];reviewed=[]
 def ck(k,v,e):
  tests.append({'name':k,'status':'PASS'if v else'FAIL','evidence':e})
  if not v:write(O/'failed_tests.json',tests);raise AssertionError(k)
 for p in read(G/'verification_01/source_pins.json'):
  if not p.get('depot'):
   ck('documentary/source pin '+p['path'],sha(p['path'])==p['sha256'],p);pins.append(p);continue
  d=p['depot'];ck('binary+JSON exact pin '+d,sha(p['raw'])==p['raw_sha256']and sha(p['json'])==p['json_sha256'],p)
  R[d]=read(p['json']);M[d]=Resource(R[d]).normalize();ck('graph decode '+d,not M[d]['errors'],M[d]['errors']);pins.append(p)
  if p.get('original'):
   z=p['original'];ck('independent original donor bytes '+d,sha(z['raw'])==z['raw_sha256']==p['raw_sha256']and sha(z['json'])==z['json_sha256'],z)
 for p in read(H/'readback_01/manifest.json'):
  ck('independent fresh binary export '+p['name'],sha(p['binary'])==p['sha256']and sha(p['json'])==p['json_sha256'],p)
  mm=Resource(read(p['json'])).normalize();ck('independent readback normalization '+p['depot'],canon(mm)==canon(M[p['depot']]),'Only numeric TDB identity, derived digest removal, tuple/list storage normalization')
  R[p['depot']]=read(p['json']);M[p['depot']]=mm;pins.append(p)
 def find(t):return next(d for d in M if d.endswith('\\'+t))
 def g(d,p='root'):return M[d]['graphs'][p]
 def n(d,i,p='root'):return g(d,p)['nodes'][str(i)]
 def edge(d,a,s,b,t,p='root'):return[str(a),s,str(b),t]in g(d,p)['edges']
 parent=find('ep1_minor_quests.questphase');m305=find('mq305.questphase');m306=find('mq306.questphase');out=find('mq305_outcome.questphase');intro=find('mq306_01_intro.questphase');expo=find('mq306_02_tech_expo.questphase');ar=find('mq306_04a_aaron_meeting.questphase');b23=find('mq306_boot.questphase');o23=find('mq306_owner.questphase');a23=find('mq306_aaron.questphase');hc=find('mr_hands_holocall.questphase');hs=find('mr_hands_holocall.scene');init=find('fixer_initializer.questphase');cl=find('fixer_cleanup.questphase')
 # Establish applicability to promoted candidate03 without turning immutable epoch00 into current metadata.
 epoch=F/'source_epoch_08.json';ee=read(epoch);C=Path(ee['candidate']);pins.append({'path':str(epoch),'sha256':sha(epoch)})
 for d in M:
  if d in ee['source_resources']:
   pp=C/'archive_source'/Path(d.replace('\\','/'));ck('candidate03 unchanged case/common resource '+d,sha(pp)==ee['source_resources'][d]==next(p['raw_sha256']for p in pins if p.get('depot')==d and'raw_sha256'in p),str(pp))
 sources={}
 for name in ['PTFR_SideJobsS23.reds','PTFR_SideJobsS24.reds','PTFR_HistorySnapshotHS1.reds','PTFR_JohnnyVoiceJV1.reds']:
  p=C/'package/r6/scripts/PTFR_Consolidated'/name;rel=p.relative_to(C/'package').as_posix();want=next(z['sha256']for z in ee['package_files']if z['path']==rel);ck('effective source package pin '+name,sha(p)==want,str(p));pins.append({'path':str(p),'sha256':want});sources[name]=p.read_text(encoding='utf8')
 own=[x for x in read(W/'prealpha/sidejobs_s24/ep1/contract02.json')['owners']if x['id']in ['mq305_combat_zone_report','mq306_dumpster']]
 ck('two source-specific fresh contracts',len(own)==2,[x['key']for x in own])
 for o in own:
  d=o['depot'];sl=o['parent_slice'];ids=set(map(str,sl['ids']));ng=g(parent,sl['graph']);cg=g(d,'root/100')
  ck('exact native fresh entry payloads '+o['key'],set(cg['nodes'])==ids|{'0'}and all(canon(cg['nodes'][i])==canon(ng['nodes'][i])for i in ids),{'current':d,'graph':'root/100','native':parent,'selected':sorted(ids)})
  ck('exact native fresh entry sockets '+o['key'],cg['edges']==sorted([e for e in ng['edges']if e[0]in ids and e[2]in ids]+[['0','Out',str(sl['entry']),sl['socket']]]),cg['edges'])
  for ni in [2,3,90]:
   nn=n(d,ni);f={x['factName']:x['value']for x in nn['reads']if x.get('comparisonType')=='Equal'};j={x['path']['realPath']:x['state']for x in nn['reads']if x['$type']=='questJournalEntryState_ConditionType'};f.setdefault('mq306_active',0)
   ck('actual serialized guard positive '+o['key']+str(ni),ev(nn['payload']['condition'],f,j),{'resource':d,'node':ni,'facts':f,'journal_count':len(j)})
   for fact,val in [('q307_done',0),('q307_finished',0),('q307_2079',0),('PTFRU9_Support_Issued',0),('mq305_started'if'MQ305'in o['key']else'mq306_started',1)]:ck('positive provenance fence '+o['key']+str(ni)+fact,not ev(nn['payload']['condition'],f|{fact:val},j),{'fact':fact,'bad':val})
   if ni!=90:ck('durable issued prevents restart '+o['key']+str(ni),not ev(nn['payload']['condition'],f|{o['tag']+'_Issued':1},j),o['tag'])
   if ni==2:
    if'MQ306'in o['key']:
     ck('native passive active0or1 fence',all(ev(nn['payload']['condition'],f|{'mq306_active':v},j)for v in[0,1])and not ev(nn['payload']['condition'],f|{'mq306_active':2},j),'main30 passive active1 does not prove accepted/started')
     ck('fresh rejects existing S23 issued',not ev(nn['payload']['condition'],f|{'PTFRS23_MQ306_Issued':1},j),'no old resume adoption/restart')
    zero=next(k for k,v in f.items()if v==0);f0=dict(f);f0.pop(zero);ck('scalar missing-zero semantics '+o['key'],ev(nn['payload']['condition'],f0,j),{'missing':zero,'semantics':'normal scalar absent0; no history proof'})
    jp=next(iter(j));jj=dict(j);jj.pop(jp);ck('missing journal is unknown '+o['key'],not ev(nn['payload']['condition'],f,jj),jp)
  ck('native progress not reset by adapter '+o['key'],all(w['factName'].startswith('PTFR')for gr in M[d]['graphs'].values()for nn in gr['nodes'].values()for w in nn['writes']),d)
 ck('native branch requires tier and retains OR',n(parent,8)['reads'][0]['factName']=='sts_ep1_tier_1'and n(parent,8)['reads'][0]['value']==1 and n(parent,27)['payload']['condition']['operation']=='OR'and edge(parent,12,'True',14,'In1')and edge(parent,12,'False',27,'In'),{'native_node8':n(parent,8)['reads'],'node27':n(parent,27)['reads']})
 for ee0 in[(0,'Out',3,'In'),(3,'Out',4,'In'),(4,'Out',5,'In'),(5,'Out',6,'In'),(6,'Out',7,'In'),(6,'out_failed',7,'In_failed'),(7,'out_bree_sold_data',19,'In')]:ck('MQ305 exact stage/Netwatch socket '+str(ee0),edge(m305,*ee0),ee0)
 ck('MQ305 exact native terminal values',all(n(out,i)['writes'][0]['factName']==f and n(out,i)['writes'][0]['value']==v for i,f,v in[(140,'mq305_done',1),(141,'mq305_finished',1),(142,'mq305_active',0)])and edge(out,140,'Out',141,'In')and edge(out,141,'Out',142,'In'),'done→finished→active0')
 ck('MQ305 distinct native rewards/failure',n(out,128)['type']==n(out,188)['type']=='questRewardManagerNodeDefinition'and canon(n(out,128)['payload'])!=canon(n(out,188)['payload'])and n(out,134)['writes'][0]['factName']=='mq305_failed',{'128':n(out,128)['payload'],'188':n(out,188)['payload'],'failed134':n(out,134)['writes']})
 for ee0 in[(5,'mq306_aaron',7,'In1'),(5,'mq306_angie',8,'In1'),(10,'Out1',9,'In1'),(32,'Out',31,'In'),(31,'Out',33,'In'),(3,'Out2',35,'In1'),(35,'Out1',39,'In1'),(39,'Out1',32,'In')]:ck('MQ306 exact outcome/failure/terminal '+str(ee0),edge(m306,*ee0),ee0)
 ck('MQ306 joins exact XOR not AND',n(m306,10)['type']=='questLogicalXorNodeDefinition',n(m306,10)['payload'])
 ck('MQ306 refusal and expo abandonment retained',edge(intro,50,'True',51,'Failed')and edge(expo,8,'Out',12,'Failed','root/58')and edge(m306,4,'failed',35,'In1'),'no new failure conversion')
 # Saved reply seam: exact retained nodes/cleanup and only native-donor edge entry change.
 for gp,gr in M[o23]['graphs'].items():
  if gp=='root/9':ck('S23 full native cleanup and reward',canon(gr)==canon(g(m306,gp)),{'resource':o23,'graph':gp})
  else:ck('S23 stable native retained owner identities',all(canon(nn)==canon(n(m306,i))for i,nn in gr['nodes'].items()if i not in ['0','7']),sorted(gr['nodes']))
 for gp,gr in M[a23]['graphs'].items():
  ng=g(ar,gp);ids=set(gr['nodes']);ck('S23 Aaron actual selected native payloads '+gp,all(canon(nn)==canon(ng['nodes'][i])for i,nn in gr['nodes'].items()),sorted(ids))
  wanted=[e for e in ng['edges']if e[0]in ids and e[2]in ids]
  if gp=='root/25':wanted=[e for e in wanted if e[0]!='0']+[['0','Out','24','In']]
  ck('S23 Aaron exact selected native edges '+gp,gr['edges']==sorted(wanted),gr['edges'])
 ck('S23 no original message resend at reply seam',edge(a23,0,'Out',24,'In','root/25')and len(n(a23,24,'root/25')['journal_paths'])==2 and all('/02a_ch_dive_reply/ch_'in z for z in n(a23,24,'root/25')['journal_paths']),n(a23,24,'root/25')['journal_paths'])
 rr=[r for r in n(b23,2)['reads']if r.get('path',{}).get('realPath')=='ep1/quests/minor_quest/mq306_dumpster'];s=sources['PTFR_SideJobsS23.reds'];aa=json.loads(re.search(r'func StatesA16\(\).*?return (\[.*?\]);',s)[1]);bb=json.loads(re.search(r'func StatesB16\(\).*?return (\[.*?\]);',s)[1]);ck('current S23 rootInactive raw+effective code',len(rr)==2 and all(r['state']=='Inactive'for r in rr)and aa[0]==bb[0]==1,{'historical_contract':'[1,4] is not current compiled behavior','serialized_root_states':[r['state']for r in rr]})
 ck('S23 requires real progressed positives and terminal0',all(any(r.get('factName')==f and r['value']==v for r in n(b23,2)['reads'])for f,v in [('mq306_started',1),('mq306_quest_accepted',1),('mq306_intimidate',1),('mq306_truth',1),('mq306_done',0),('mq306_finished',0)]),'unsupported missing-message histories parked, not reset')
 ep=find('ep1.questphase');ck('original parent retirement exact cut path',parent in n(ep,3,'root/10')['refs']and edge(ep,9,'CutSource',3,'CutDestination','root/10')and edge(ep,9,'Out',10,'In','root/10')and n(ep,10,'root/10')['writes'][0]['factName']=='q307_ep1_killed','receipt supplements actual cut, not receipt-only owner proof')
 # Direction-aware full producer inventory, plus positive custom family and typed communication actions.
 req=[];custom=[];typed=[];rx=re.compile(r'^(holo|audio)_(?:(.+)_calls_v|v_calls_(.+))_(start|end)_activate$')
 for d,m in M.items():
  if not d.startswith('ep1\\quest\\minor_quests\\mq'):continue
  for gp,gr in m['graphs'].items():
   for i,nn in gr['nodes'].items():
    if nn['sms']or nn['type']=='questPhoneManagerNodeDefinition':typed.append({'resource':d,'graph':gp,'node':i,'type':nn['type'],'journals':nn['journal_paths']})
    for w in nn['writes']:
     if w['value']!=1:continue
     ma=rx.fullmatch(w['factName'])
     if not ma:
      if w['factName'].startswith('new_')and any(z in w['factName'].lower()for z in['call','brief','end']):custom.append({'resource':d,'graph':gp,'node':i,'fact':w['factName']})
      continue
     mode,inc,outgoing,kind=ma.groups();contact=inc or outgoing;ack='holo_'+(contact+'_calls_v'if inc else'v_calls_'+contact)+'_'+kind+'_done'
     listeners=[j for j,v in g(hc)['nodes'].items()if any(r.get('factName')==w['factName']for r in v['reads'])];acks=[j for j,v in g(hs,'scene')['nodes'].items()if any(z.get('factName')==ack and z['value']==1 for z in v['writes'])];row={'resource':d,'graph':gp,'node':i,'request':w['factName'],'direction':'incoming'if inc else'outgoing','real_ACK':ack,'listeners':listeners,'ACK_writers':acks}
     ck('actual request controller+real ACK '+d+gp+i,contact=='mr_hands'and bool(listeners)and bool(acks),row)
     if gp=='scene':
      waits=[j for j,v in gr['nodes'].items()if any(r.get('factName')==ack for r in v['reads'])];clears=[j for j,v in gr['nodes'].items()if any(z.get('factName')==ack and z['value']==0 for z in v['writes'])]
      direct=any(route(gr,i,w0)for w0 in waits);fork=any(route(gr,j,i)and any(route(gr,j,w0)for w0 in waits)for j in gr['nodes']if len([e for e in gr['edges']if e[0]==j])>1)
      ck('real caller ACK wait+clear path '+d+i,(direct or fork)and any(route(gr,w0,c0)for w0 in waits for c0 in clears),{'waits':waits,'clears':clears,'direct':direct,'prearmed_fork':fork});row|={'waits':waits,'clears':clears}
     req.append(row)
 ck('all12 actual requests both directions, MQ306 none',len(req)==12 and {r['direction']for r in req}=={'incoming','outgoing'}and all('mq305'in r['resource']for r in req)and not custom,{'requests':len(req),'custom_new_family':custom,'typed_SMS_phone_actions':len(typed)})
 ck('current actual Hands initializer+cleanup integration',hc in n(init,73)['refs']and edge(init,25,'Out1',73,'In1')and edge(cl,462,'True',329,'In36')and find('mr_hands_cleanup.questphase')in n(cl,329)['refs'],'full native controller retained, not synthetic ACKs')
 studio=find('studio_support.questphase');ck('PH3 nested studio scope present',len([nn for gr in M[studio]['graphs'].values()for nn in gr['nodes'].values()if nn['prefabs']])>0,{'depot':studio,'phase_prefabs':[{'node':i,'prefabs':nn['prefabs']}for gr in M[studio]['graphs'].values()for i,nn in gr['nodes'].items()if nn['prefabs']]})
 # Scene socket/prefetch and presentation contracts from actual caller and scene definitions.
 sceneuses=[]
 for d,m in M.items():
  if not d.startswith('ep1\\quest\\minor_quests\\mq'):continue
  for gp,gr in m['graphs'].items():
   for i,nn in gr['nodes'].items():
    if nn['type']!='questSceneNodeDefinition':continue
    for target in [r for r in nn['refs']if r.endswith('.scene')]:
     for a,s,b,t in gr['edges']:
      if b!=i or t=='CutDestination':continue
      declared=t in M[target]['graphs']['scene']['entries'];control=t=='Prefetch'and{'name':'Prefetch','type':'Input'}in nn['sockets'];ck('scene actual socket '+d+gp+i+t,declared or control,{'scene':target,'socket':t,'kind':'DECLARED_ENTRY'if declared else'PREFETCH_CONTROL'});sceneuses.append((d,gp,i,t))
 ck('all50 caller scene sockets independently covered',len(sceneuses)==50,len(sceneuses))
 ck('native intro two root leases exact',M[intro]['root_prefabs']==['#mq306_pr_intro','#mq306_aaron_prefab'],M[intro]['root_prefabs'])
 ring=find('mq306_boxing_ring.questphase');ck('separate native ambient ring is not invented missing owner',n(ring,34)['reads'][0]['factName']=='mq306_active'and n(ring,36)['type']=='questLogicalAndNodeDefinition','ambient #cz communities != intro Aaron/boxer/spectators; dynamic owner remains conditional')
 jv=sources['PTFR_JohnnyVoiceJV1.reds'];ck('effective JV1 only visual actor policy','Character.Silverhand'in jv and 'visual.TemporaryHide(true)'in jv and 'SetFact'not in jv,'voice/timing retained; independent props/render remains opaque/live')
 # Omitted journal evidence is checked against raw guards/writers, not assumed harmless.
 conf=find('mq305_04_bunker_confrontation.questphase');ins=[e for e in g(conf)['edges']if e[2]=='55'];ck('unlisted confront objective only native Succeeded',bool(ins)and all(e[3]=='Succeeded'for e in ins),ins)
 scene=find('mq305_04_bunker.scene');ck('unlisted kill objective mapping exact Succeeded',[e for e in g(scene,'scene')['edges']if e[2]=='1318']==[['721','0:0','1318','0:3']]and n(scene,1318,'scene')['payload']['isockMappings'][3]['$value']=='Succeeded',n(scene,1318,'scene')['journal_paths'])
 gg=g(intro,'root/9');rr=copy.deepcopy(gg);rr['edges']=[e for e in gg['edges']if '8'not in[e[0],e[2]]];outs=[i for i,nn in gg['nodes'].items()if nn['type']=='questOutputNodeDefinition'];ck('intro native started writer dominates actual outputs',n(intro,8,'root/9')['writes'][0]['factName']=='mq306_started'and all(route(gg,0,i)and not route(rr,0,i)for i in outs),outs)
 ck('later Aaron message/reply native after started chain',route(g(ar,'root/25'),0,27)and route(g(ar,'root/25'),27,43)and '/mq306_meeting/'in n(ar,27,'root/25')['journal_paths'][0],{'source':ar,'graph':'root/25','message':27,'reply':43,'limit':'local source ordering cannot certify arbitrary saved/foreign journals'})
 # Explicit target record linkage from actual native reward nodes, bounded stock data only.
 for q,dd,ids in [('mq305_combat_zone_report',out,[128,188]),('mq306_dumpster',ar,[53,54])]:
  p=F/'shared/tdb_applicability_02'/str(q+'.json');t=read(p);pins.append({'path':str(p),'sha256':sha(p)});records={z['id']:z for z in t['targets']}
  for i in ids:
   nn=n(dd,i,'root/25'if q=='mq306_dumpster'else'root');rewards=[z['$value']for z in walk(canon(nn['payload']))if z.get('$type')=='TweakDBID'];ck('actual native reward definition '+q+str(i),all(z in records and records[z]['exists_in_stock']for z in rewards),{'resource':dd,'node':i,'records':rewards,'limits':t['limits']})
 # All20 authored conclusions must retain source-specific evidence and unresolved limitations.
 res=read(G/'results.json');expected={'entry':'APPROVED_DEVIATION','progression':'PASS','presentation':'OPAQUE'}
 for qr in res['quest_results']:
  p=Path(qr['contracts']);ck('frozen ten-contract hash '+qr['quest_id'],sha(p)==qr['contracts_sha256'],str(p));cc=read(p)['contracts'];ck('exact ten contract set '+qr['quest_id'],set(cc)=={'entry','eligibility','communications','ownership','progression','presentation','journal','completion_rewards_cleanup','persistence','shared_dependencies'},list(cc))
  for k,v in cc.items():
   ck('specific disposition/evidence '+qr['quest_id']+'/'+k,v['status']==expected.get(k,'CONDITIONAL')and bool(v['proven'])and bool(v['remaining'])and all(Path(z['path']).is_file()and sha(z['path'])==z['sha256']for z in v['evidence']),{'status':v['status'],'proven':v['proven'],'remaining':v['remaining']});reviewed.append({'quest':qr['quest_id'],'contract':k,'status':v['status'],'source_claims_reviewed':v['proven'],'remaining':v['remaining']})
 # Actual raw faults: mutate real native/resource data, use independently derived fixed expectations.
 def mutate_ack(raw):
  for z in walk(raw):
   if z.get('$type')=='questSetVar_NodeType'and z.get('factName')=='holo_v_calls_mr_hands_start_done'and z.get('value')==1:z['factName']='BROKEN_OUTGOING_ACK'
 def mutate_or(raw):
  r=Resource(raw);gr=r.d(r.root['graph']);nn=next(r.d(h)for h in gr['nodes']if r.d(h)['id']==27);r.d(nn['condition'])['operation']='AND'
 def mutate_pip(raw):raw['Data']['RootChunk']['phasePrefabs']=[z for z in raw['Data']['RootChunk']['phasePrefabs']if z['prefabNodeRef']['$value']!='#mq306_aaron_prefab']
 for name,d,fn,oracle in [('missing_outgoing_ACK',hs,mutate_ack,lambda m:any(w.get('factName')=='holo_v_calls_mr_hands_start_done'and w['value']==1 for nn in m['graphs']['scene']['nodes'].values()for w in nn['writes'])),('native_OR_changed_to_AND',parent,mutate_or,lambda m:m['graphs']['root']['nodes']['27']['payload']['condition']['operation']=='OR'),('missing_Aaron_root_lease',intro,mutate_pip,lambda m:m['root_prefabs']==['#mq306_pr_intro','#mq306_aaron_prefab'])]:
  raw=copy.deepcopy(R[d]);fn(raw);mm=Resource(raw).normalize();ck('independent actual raw fault '+name,oracle(M[d])and not oracle(mm),{'depot':d,'decode_errors':mm['errors']});p=O/'mutations'/str(name+'.json');write(p,raw);mut.append({'fault':name,'path':str(p),'sha256':sha(p),'detected':True})
 write(O/'tests.json',tests);write(O/'source_pins.json',pins);write(O/'contracts_reviewed.json',reviewed);write(O/'protocols.json',{'requests':req,'typed_phone_SMS':typed,'custom_requests':custom});write(O/'mutations.json',mut)
 result={'status':'PASS_INDEPENDENT_TWENTY_CONTRACT_SOURCE_REVIEW_WITH_SPECIFIC_LIMITS','quests':res['quest_ids'],'checks':len(tests),'mutations':len(mut),'contracts':20,'independent_fresh_exports':12,'frozen_graph_inputs':len(M),'phone_requests':len(req),'source_epoch':str(epoch),'source_epoch_sha256':sha(epoch),'tests':str(O/'tests.json'),'source_pins':str(O/'source_pins.json'),'code_sha256':sha(__file__),'findings':['Both fresh entry slices preserve exact native predicates/branch sockets and current saved receipts; no synthetic quest progress or ACK reset.','MQ305 incoming and outgoing Hands callers retain real listeners, native ACKs, caller wait/clear and current U9/PH3 scope. MQ306 uses native SMS/journal reply paths.','Current MQ306 S23 rootInactive-only agrees in serialized guards and effective package REDS; broader historical [1,4] contract is inactive evidence.','MQ306 narrow progressed reply slice preserves selected donor identities, original reward54/final native cleanup, and skips only prior setup/SMS prefix.','Succeeded-only omissions and later native SMS local ordering are source-proven; no blanket saved-journal or actor/lease completeness claim.'],'limitations':['Exact saved-owner transitions, delivery/reload/interrupt behavior and rewards need supported live fixtures.','World/prefab placement, scene acquisition, independent Johnny props/render timing remain opaque/live.','Stock direct target records are bounded captures; economic descendants/runtime overlays and foreign journal/device writers remain conditional.'],'confirmed_new_defects':[],'runtime_changes':[]};write(O/'review.json',result);print(json.dumps(result))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);run(Path(p.parse_args().output).resolve())
