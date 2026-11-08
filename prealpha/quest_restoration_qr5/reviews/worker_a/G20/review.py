"""Independent final G20 source peer. No author or coordinator checkers imported."""
from pathlib import Path
import sys,json,copy,re,zlib,argparse,collections
H=Path(__file__).resolve().parent;W=H.parents[4];F=W/'prealpha/quest_restoration_qr5';G=F/'groups/G20'
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
def soft(x):
 x=copy.deepcopy(x)
 for z in walk(x):
  if'phaseResource'in z and z['phaseResource'].get('Flags')=='Embedded':z['phaseResource']['Flags']='Soft'
 return x
def route(g,a,b):
 todo=[str(a)];seen=set()
 while todo:
  u=todo.pop(0)
  if u==str(b):return True
  if u in seen:continue
  seen.add(u);todo.extend(e[2]for e in g['edges']if e[0]==u and e[1]!='CutSource'and e[3]!='CutDestination'and not(g['nodes'][u]['type']=='scnCutControlNode'and e[1].startswith('1:')))
 return False
def ev(c,f,j=None):
 j=j or{};t=c['$type']
 if t=='questLogicalCondition':
  a=[ev(x,f,j)for x in c['conditions']];return all(a)if c['operation']=='AND'else any(a)if c['operation']=='OR'else not any(a)if c['operation']=='NOR'else False
 if t in ['questFactsDBCondition','questJournalCondition']:return ev(c['type'],f,j)
 if t=='questVarComparison_ConditionType':
  a,b=f.get(c['factName'],0),c['value'];return{'Equal':a==b,'NotEqual':a!=b,'Greater':a>b,'GreaterOrEqual':a>=b,'Less':a<b,'LessOrEqual':a<=b}[c['comparisonType']]
 if t=='questJournalEntryState_ConditionType':return j.get(c['path']['realPath'],'MISSING')==c['state']
 raise ValueError(t)
def run(O):
 assert not O.exists();tests=[];pins=[];M={};R={};mut=[];reviewed=[]
 def ck(k,v,e):
  tests.append({'name':k,'status':'PASS'if v else'FAIL','evidence':e})
  if not v:write(O/'failed_tests.json',tests);raise AssertionError(k)
 res=read(G/'results.json');ck('frozen final three-quest results',sha(G/'results.json')=='E90250BC7D1CA0582FE43CA296C7C542081AE7302F9D08E288F8E20B9FAE1F2A',res['quest_ids'])
 plist=[]
 for rel in ['verification_01/source_pins.json','deep_02/source_pins.json','lifecycle_01/source_pins.json']:
  for p in read(G/rel):
   if p.get('depot')and p['depot']not in {z.get('depot')for z in plist}:plist.append(p)
 for p in plist:
  d=p['depot'];ck('exact actual binary/JSON '+d,sha(p['raw'])==p['raw_sha256']and sha(p['json'])==p['json_sha256'],p);R[d]=read(p['json']);M[d]=Resource(R[d]).normalize();ck('actual model decode '+d,not M[d]['errors'],M[d]['errors']);pins.append(p)
 for p in read(H/'readback_01/manifest.json'):
  ck('independent fresh export pin '+p['name'],sha(p['binary'])==p['sha256']and sha(p['json'])==p['json_sha256'],p);mm=Resource(read(p['json'])).normalize();ck('independent binary semantics '+p['depot'],canon(mm)==canon(M[p['depot']]),'Only TDB numeric identity/derived digests/tuple-list normalization');M[p['depot']]=mm;R[p['depot']]=read(p['json']);pins.append(p)
 def find(t):return next(d for d in M if d.endswith('\\'+t))
 def g(d,p='root'):return M[d]['graphs'][p]
 def n(d,i,p='root'):return g(d,p)['nodes'][str(i)]
 def edge(d,a,s,b,t,p='root'):return[str(a),s,str(b),t]in g(d,p)['edges']
 ep=F/'source_epoch_08.json';E=read(ep);C=Path(E['candidate']);pins.append({'path':str(ep),'sha256':sha(ep)})
 for d,m in M.items():
  if d in E['source_resources']:
   pp=C/'archive_source'/Path(d.replace('\\','/'));ck('current C3 unchanged investigated resource '+d,sha(pp)==E['source_resources'][d]==next(p['raw_sha256']for p in plist if p['depot']==d),str(pp))
 for name in ['PTFR_ActivityStateR3.reds','PTFR_JohnnyVoiceJV1.reds']:
  p=C/'package/r6/scripts/PTFR_Consolidated'/name;want=next(z['sha256']for z in E['package_files']if z['path']==p.relative_to(C/'package').as_posix());ck('effective packaged source '+name,sha(p)==want,str(p));pins.append({'path':str(p),'sha256':want})
 U=read(W/'research/gig_restoration/native_gigs_u9/manifest.json');recipes=[r for r in U['recipes']if r['id']in res['quest_ids']];par=next('recipe:'+r['raw']for r in recipes if r['kind']=='entry')
 # Selected nodes derive from original donor, while private wrappers/companion routes are explicit deviations.
 for r in recipes:
  d=r['depot'];native='recipe:'+r['raw'];cp=r.get('compiled_graph','root');np=r['graph']
  for i in map(str,r['ids']):
   if i=='0':continue
   ck('actual selected native payload '+d+i,canon(n(d,i,cp)['payload'])==canon(soft(n(native,i,np)['payload'])),{'source':native,'native_graph':np,'current_graph':cp,'node':i})
   if r['id']=='sts_ep1_06'and r['kind']=='entry'and i=='9':continue
   pref=cp+'/'+i;op=np+'/'+i
   for gp,gr in M[d]['graphs'].items():
    if gp==pref or gp.startswith(pref+'/'):ck('full selected native descendant '+d+gp,canon(gr)==canon(g(native,op+gp[len(pref):])),{'source':native,'native_graph':op+gp[len(pref):]})
  ck('explicit recipe/socket adaptation '+d,g(d,cp)['edges']==sorted([[str(a),s,str(b),t]for a,s,b,t in r['edges']]),g(d,cp)['edges'])
  if r['kind']=='entry':
   ck('saved phase50 wake metadata native '+d,canon(n(d,50)['payload'])==canon(n(native,50)['payload']),n(d,50)['payload']['unfreezingTriggerNodeRef'])
   for co,newid in zip(r['companions'],[64000,64001]):
    old=copy.deepcopy(n('recipe:'+co['source_raw'],co['source_node'],co['source_graph'])['payload']);old['id']=newid;ck('native full companion binding '+d+str(newid),canon(n(d,newid,cp)['payload'])==canon(old),{'kind':co['kind'],'native_graph':co['source_graph'],'native_node':co['source_node'],'new_node':newid})
   ck('real body completion owns cleanup '+d,edge(d,65003,'Out',64001,'In1',cp)and edge(d,64000,'Out1',65006,'In',cp),'native parallel bugfix + body-completion cleanup, not detached receipts')
 for q,body,outid,inp,cl in [('sts_ep1_06',4,33,8,16),('sts_ep1_03',19,30,5,14),('sts_ep1_12',26,29,4,10)]:ck('native outer cleanup interface '+q,edge(par,body,'Out1',outid,'In','root/50')and edge(par,50,q,51,q)and edge(par,inp,'Out',cl,'In1','root/51'),{'body':body,'outer_output':outid,'cleanup_node':cl})
 # Exact genuine-history guard fixtures; ordinary absent scalar0 is not rejection/history proof.
 for q in res['quest_ids']:
  d=find(q+'_entry.questphase');nn=n(d,65002,'root/50');f={r['factName']:r['value']for r in nn['reads']if r.get('factName')};ck('current admission positive '+q,ev(nn['payload']['condition'],f),f)
  for fact,v in [('q307_done',0),('q307_finished',0),('PTFRU9_Support_Issued',0),('PTFRU9_'+q+'_ParentEntered',1),('PTFRU9_'+q+'_Fault',1),(q+'_start',1),(q+'_finished',1)]:ck('actual native/history refusal '+q+fact,not ev(nn['payload']['condition'],f|{fact:v}),fact)
  zero=next(k for k,v in f.items()if v==0);missing=dict(f);missing.pop(zero);ck('absent scalar0 modeled normally '+q,ev(nn['payload']['condition'],missing),zero)
 # Full native Tier3 mechanism, and distinct tier2 OR/debug/Hands and introduction wait.
 core=read(G/'shared_core.json');ck('frozen Tier3 applicability',sha(G/'shared_core.json')=='97F7F30E81EA363C193138A1DE9ACE405DE6739F3FA349380417C62C0C0ABF82'and core['applies_to']==['sts_ep1_06','sts_ep1_07'],core)
 gate=core['resource'];ck('whole native Tier3 descendant retained',canon(g(gate,'root/50/9'))==canon(g(par,'root/50/9')),'native tier3 versus q304_done routes, SMS and reply graph unchanged')
 d6=find('sts_ep1_06_entry.questphase');ck('perjob Tier3 uses shared readiness',n(d6,2,'root/50/9')['reads'][0]['factName']=='PTFRU9_EP1Tier3_Ready'and set(g(d6,'root/50/9')['nodes'])=={'0','1','2'},'one shared global notification rather than per-job replay')
 guard=n(gate,65000,'root/50')['payload']['condition'];base={r['factName']:r['value']for r in n(gate,65000,'root/50')['reads']if r.get('factName')};base.update({'PTFRU9_sts_ep1_06_Request':0,'PTFRU9_sts_ep1_06_Permit':0,'PTFRU9_sts_ep1_07_Request':0,'PTFRU9_sts_ep1_07_Permit':0})
 for q in ['sts_ep1_06','sts_ep1_07']:ck('shared request AND permit OR cohorts '+q,ev(guard,base|{'PTFRU9_'+q+'_Request':1,'PTFRU9_'+q+'_Permit':1})and not ev(guard,base|{'PTFRU9_'+q+'_Request':1}),q)
 d3=find('sts_ep1_03_entry.questphase');d12=find('sts_ep1_12_entry.questphase');ck('tier2 debug Hands independent native alternatives',all(edge(d3,0,'Out',i,'In','root/50/10')for i in[3,4,7]),'original alternatives not invented AND')
 ck('TreatingSymptoms actual Hands intro wait',n(d12,25,'root/50/8')['reads'][0]['factName']=='mr_hands_dogtown_introduced'and edge(d12,0,'Out',25,'In','root/50/8'),'positive earned introduction not manufactured')
 # Every actual generic producer, both directions/modes and call-like/custom writer inventory.
 hc=find('mr_hands_holocall.questphase');hs=find('mr_hands_holocall.scene');req=[];custom=[];typed=[];sceneuses=[];rx=re.compile(r'^(holo|audio)_(?:(.+)_calls_v|v_calls_(.+))_(start|end)_activate$')
 for d,m in M.items():
  if not d.startswith('ep1')or not any(q in d for q in res['quest_ids']):continue
  for gp,gr in m['graphs'].items():
   for i,nn in gr['nodes'].items():
    if nn['sms']or nn['type']=='questPhoneManagerNodeDefinition':typed.append({'resource':d,'graph':gp,'node':i,'journals':nn['journal_paths']})
    for w in nn['writes']:
     if w['value']!=1:continue
     ma=rx.fullmatch(w['factName'])
     if not ma:
      if w['factName'].startswith('new_')or('call'in w['factName'].lower()and not w['factName'].startswith(('holo_','audio_'))):custom.append({'resource':d,'graph':gp,'node':i,'fact':w['factName']})
      continue
     mode,inc,outing,kind=ma.groups();contact=inc or outing;ack='holo_'+(contact+'_calls_v'if inc else'v_calls_'+contact)+'_'+kind+'_done';ls=[j for j,x in g(hc)['nodes'].items()if any(r.get('factName')==w['factName']for r in x['reads'])];acks=[j for j,x in g(hs,'scene')['nodes'].items()if any(z.get('factName')==ack and z['value']==1 for z in x['writes'])];row={'resource':d,'graph':gp,'node':i,'request':w['factName'],'direction':'incoming'if inc else'outgoing','ACK':ack,'listeners':ls,'real_ACK_writers':acks}
     ck('real Hands producer/listener/ACK '+d+gp+i,contact=='mr_hands'and bool(ls)and bool(acks),row)
     if gp=='scene':
      waits=[j for j,x in gr['nodes'].items()if any(r.get('factName')==ack for r in x['reads'])];clears=[j for j,x in gr['nodes'].items()if any(z.get('factName')==ack and z['value']==0 for z in x['writes'])];direct=any(route(gr,i,j)for j in waits);fork=any(route(gr,j,i)and any(route(gr,j,k)for k in waits)for j in gr['nodes']if len([e for e in gr['edges']if e[0]==j])>1);ck('native caller wait/clear '+d+i,(direct or fork)and any(route(gr,a,b)for a in waits for b in clears),{'waits':waits,'clears':clears,'direct':direct,'prearmed':fork})
     req.append(row)
    if nn['type']=='questSceneNodeDefinition':
     for target in[r for r in nn['refs']if r.endswith('.scene')]:
      for a,s,b,t in gr['edges']:
       if b!=i or t=='CutDestination':continue
       declared=target in M and t in M[target]['graphs']['scene']['entries'];prefetch=t=='Prefetch'and{'name':'Prefetch','type':'Input'}in nn['sockets'];ck('actual scene input '+d+gp+i+t,declared or prefetch,{'scene':target,'input':t,'kind':'DECLARED'if declared else'PREFETCH_CONTROL'});sceneuses.append((d,gp,i,t))
 ck('all28 native Hands producer sites',len(req)==28 and all(x['direction']=='incoming'for x in req),{'count':len(req),'custom':custom,'typed_SMS_phone':len(typed)})
 ck('all non-generic calllike writes are native outcome receipt',all(x['fact']=='sts_ep1_03_wagner_called_regina'for x in custom),'no V-Regina request or synthetic listener inferred from receipt name')
 ck('all77 actual scene sockets covered',len(sceneuses)==77,len(sceneuses))
 init=find('fixer_initializer.questphase');cl=find('fixer_cleanup.questphase');ck('actual generic listener and cleanup registered in U9',hc in n(init,73)['refs']and edge(init,25,'Out1',73,'In1')and edge(cl,462,'True',329,'In36')and find('mr_hands_cleanup.questphase')in n(cl,329)['refs'],'separate from missing Ronald news')
 # Actual outcomes, journals, earned rewards and final cleanup branches.
 ow6=find('sts_ep1_06_openworld.questphase');ow3=find('sts_ep1_03_openworld.questphase');main12=find('sts_ep1_12_phase.questphase');cl6=find('sts_ep1_06_cleanup.questphase');cl3=find('sts_ep1_03_cleanup.questphase');cl12=find('sts_ep1_12_cleanup.questphase')
 ck('Heaviest combat OR selects distinct native rewards',n(ow6,279,'root/7')['payload']['condition']['operation']=='OR'and edge(ow6,279,'True',128,'In','root/7')and edge(ow6,279,'False',280,'In','root/7')and all(edge(ow6,i,'Out',72,'In','root/7')for i in[128,280]),'normal/optional outcome preserved')
 ck('Heaviest muted/rejected SMS fallback exact',edge(ow6,224,'True',271,'In','root/7')and edge(ow6,81,'rejected_out',271,'In','root/7')and n(ow6,272,'root/7')['payload']['condition']['operation']=='OR','real authored SMS, not fake ACK')
 ck('Heaviest MQ304 cleanup16hours and scene handshake',edge(cl6,74,'Out',176,'In1')and edge(cl6,74,'Out',5,'In')and n(cl6,5)['payload']['condition']['type']['hours']==16 and edge(cl6,176,'Out1',214,'In')and edge(cl6,214,'Out',175,'lean_in'),'source body complete required; external owner/saved stage remains conditional')
 ck('Rinder spared code suppression OR exact',n(ow3,132,'root/4/59')['payload']['condition']['operation']=='OR'and edge(ow3,132,'False',135,'In','root/4/59')and edge(ow3,135,'Out',133,'In','root/4/59')and edge(ow3,133,'Out',134,'Active','root/4/59'),'native code SMS not replayed from dogtag')
 ck('Rinder real debrief or fallback earns reward',edge(ow3,353,'End 0',361,'In','root/4')and edge(ow3,353,'rejected_out',357,'Active','root/4')and edge(ow3,357,'Out',557,'In','root/4')and edge(ow3,557,'Out',361,'In','root/4'),'Regina safe/dead message branches are in unchanged local cleanup')
 ck('TreatingSymptoms distinct alive dead exit paths',edge(main12,143,'Out',152,'In')and edge(main12,152,'Out',144,'In')and edge(main12,308,'Out',153,'In')and edge(main12,153,'Out',139,'In'),'no forced kill/outcome rewrite')
 ck('TreatingSymptoms terminal before reward and incrementcleanup',all(edge(main12,*e)for e in[(51,'Out',165,'Succeeded'),(165,'Out',66,'In'),(66,'Out',256,'In'),(256,'Out',257,'In'),(257,'Out',61,'In')])and n(cl12,43,'root/36')['writes'][0]['setExactValue']==0,'native cleanup increment remains increment')
 ck('Rinder complete native main/cleanup leases',M[find('sts_ep1_03_phase.questphase')]['root_prefabs']==['#sts_ep1_03_streetstory','#sts_ep1_03_gunfight_streetstory','#loc_sts_ep1_03_combat']and M[cl3]['root_prefabs']==['#sts_ep1_03_streetstory','#loc_sts_ep1_03_combat'],'source identity is not streamed acquisition proof')
 ck('TreatingSymptoms prefab-bearing scopes native',M[main12]['root_prefabs']==['#sts_ep1_12_streetstory_quest_prefab']and '#sts_ep1_12_streetstory_quest_prefab'in n(find('sts_ep1_12_bugfixing.questphase'),17)['prefabs'],'not just bare initializer support')
 pick=find('sts_ep1_12_pickup.questphase');ck('S29 aftermath distinct guarded WST02 owner',n(pick,26)['reads'][0]['factName']=='wst_ep1_02_active'and edge(pick,65005,'Out',26,'In')and edge(pick,26,'Out',65006,'In')and edge(pick,65006,'Out',2,'In1')and all(any(r.get('factName')==f and r['value']==0 for r in n(pick,65003)['reads'])for f in['wst_ep1_02_start','wst_ep1_02_finished','PTFRS29_sts_ep1_12_pickup_Issued']),pick)
 omissions=read(G/'lifecycle_01/journal_omissions.json');ck('complete native journal omissions retained',all(len(omissions[q]['all_unlisted_journal_uses'])==v for q,v in[('sts_ep1_06',54),('sts_ep1_03',48),('sts_ep1_12',28)]),'phone/foreign/Internet paths retained by class; not all harmless map pins')
 for q in res['quest_ids']:
  sp=F/'shared/tdb_applicability_02'/str(q+'.json');sx=read(sp);pins.append({'path':str(sp),'sha256':sha(sp)});ids={z['id']:z for z in sx['targets']};uses=[]
  for d,m in M.items():
   if not d.startswith('ep1')or q not in d:continue
   for gp,gr in m['graphs'].items():
    for i,nn in gr['nodes'].items():
     if nn['reward']:
      for z in walk(canon(nn['payload'])):
       if z.get('$type')=='TweakDBID':uses.append({'resource':d,'graph':gp,'node':i,'id':z['$value']});ck('actual native reward stock record '+q+d+gp+i+z['$value'],z['$value']in ids and ids[z['$value']]['exists_in_stock'],uses[-1])
  ck('bounded target definition limits retained '+q,bool(sx['limits'])and bool(uses),sx['limits'])
 # Ronald: independently validate exact applicability of already independently reviewed full family context.
 ctx=F/'groups/G21/reviews/RONALD/verification_05';cr=read(ctx/'review.json');pins.append({'path':str(ctx/'review.json'),'sha256':sha(ctx/'review.json')});fam=read(ctx/'family_map.json');pins.append({'path':str(ctx/'family_map.json'),'sha256':sha(ctx/'family_map.json')});ck('independent family review frozen context',cr['checks']==163 and cr['mutations']==3 and not cr['proposal_approved']and cr['source_epoch_sha256']==sha(ep),cr)
 selected=[x for x in fam if x.get('selected_quest_id')];ck('one native family four selected jobs',len(fam)==8 and {x['selected_quest_id']for x in selected}=={'sts_ep1_01','sts_ep1_03','sts_ep1_08','sts_ep1_12'},'four affected selected dependencies, one unique family, no new deep quest count')
 rt=find('q302_ronald_tree.questphase');br=find('ronald.questphase');ck('native host bar lease exact, child11 none',M[rt]['root_prefabs']==['#q302_pr_bar']and not n(rt,11)['prefabs'],'scope belongs to native root; not a physical actor requirement in SMS children')
 ck('current B0 lacks native news owner and bar lease',not M[br]['root_prefabs']and not any(nn['prefabs']for gr in M[br]['graphs'].values()for nn in gr['nodes'].values())and {'11','12'}.isdisjoint(g(br,'root/5')['nodes'])and not any('q302_msg_ronald_'in ref for ref in M[br]['refs']),'source missing lease does not prove world markers absent; safe host arbitration unresolved')
 ck('real native earned Ronald enrollment',n(rt,12)['reads'][0]['factName']=='q302_ronald_messages_enabled'and edge(rt,2,'Out',12,'In')and edge(rt,12,'Out',11,'In1'),'historical service-only scope cannot approve omitting selected-gig news')
 for row in selected:
  q=row['selected_quest_id'];wait=row['done_wait'];sent=row['native_sent_writer'];delay=row['delivery_game_delay'];phase=row['phase_node'];ng=g(rt,'root/11');ck('native optional news route applicable '+q,n(rt,wait,'root/11')['reads'][0]['factName']==q+'_done'and n(rt,sent,'root/11')['writes'][0]['factName']=='q302_msg_ronald_'+q and n(rt,sent,'root/11')['writes'][0]['value']==1 and row['phase_resource']in n(rt,phase,'root/11')['refs']and route(ng,wait,sent)and route(ng,sent,delay)and route(ng,delay,phase),row)
  ck('native two game days after sent '+q,any(z.get('days')==2 for z in walk(n(rt,delay,'root/11')['payload'])),'sent1 distinguishes claimed, not delivered; preclaim112/113/114 are separate realtime delays')
  nn=n(rt,row['normal_token_area_wait'],'root/11');ck('native outside markers exact '+q,nn['node_refs']==['#q302_tr_ronald_area_02']and nn['payload']['condition']['operation']=='AND'and any(z.get('type')=='MinorQuestAndSts'for z in walk(nn['payload'])),'normal MinorQuestAndSts token AND IsOutside #q302_tr_ronald_area_02; standalone outside branch separately retained')
  if q in ['sts_ep1_03','sts_ep1_12']:
   dd=row['phase_resource'];ck('news SMS child no actor scene or root PIP '+q,not M[dd]['root_prefabs']and not any(nn['type']=='questSceneNodeDefinition'or nn['prefabs']for gr in M[dd]['graphs'].values()for nn in gr['nodes'].values()),dd)
 pc=find('ep1_persistent_content.questphase');ad=find('ep1_additional_game_elements.questphase');ep1=find('ep1.questphase');ck('actual news additional/persistent ancestor Tower cut',pc in n(ad,2)['refs']and rt in n(pc,26,'root/30')['refs']and edge(ep1,9,'CutSource',4,'CutDestination','root/10'),'no invented Ronald death/cut; saved external owner not inferred from killed fact alone')
 ce=G/'ronald_verification_02/evidence.json';ck('author whole-cache census evidence unchanged',sha(ce)=='28234973623EE917C537FBD2A7B11BB8348C95F5E8B6EA49A1605C89955EF879'and read(ce)['models_pinned']==5136 and read(ce)['old_B0_scope_is_not_quest_exception'],'reuse pinned exact named consumer census; no duplicate full scan');pins.append({'path':str(ce),'sha256':sha(ce)})
 # Review all30 substantive dispositions against actual findings above, preserving baseline FAILs.
 for qr in res['quest_results']:
  p=Path(qr['contracts']);ck('exact frozen ten-contract pin '+qr['quest_id'],sha(p)==qr['contracts_sha256'],qr);cc=read(p)['contracts'];ck('ten exact contract keys '+qr['quest_id'],set(cc)=={'entry','eligibility','communications','ownership','progression','presentation','journal','completion_rewards_cleanup','persistence','shared_dependencies'},list(cc))
  for k,v in cc.items():
   expected='APPROVED_DEVIATION'if k=='entry'else'PASS'if k=='progression'else'OPAQUE'if k=='presentation'else'FAIL'if qr['quest_id']in['sts_ep1_03','sts_ep1_12']and k in['communications','shared_dependencies']else'CONDITIONAL'
   def vp(z):return Path(z).is_file()if isinstance(z,str)else Path(z['path']).is_file()and(not z.get('sha256')or sha(z['path'])==z['sha256'])
   ck('source-specific contract disposition '+qr['quest_id']+'/'+k,v['status']==expected and bool(v['proven'])and bool(v['remaining'])and all(vp(z)for z in v['evidence']),{'status':v['status'],'proven':v['proven'],'remaining':v['remaining']});reviewed.append({'quest_id':qr['quest_id'],'contract':k,'status':v['status'],'findings':v['proven'],'remaining':v['remaining']})
 # Three independent actual raw fixture controls; pinned native source drives each expectation.
 def ma(raw):
  for z in walk(raw):
   if z.get('$type')=='questSetVar_NodeType'and z.get('factName')=='holo_mr_hands_calls_v_end_done'and z.get('value')==1:z['value']=0
 def mb(raw):
  for z in walk(raw):
   if z.get('$type')=='questSetVar_NodeType'and z.get('factName')=='q302_msg_ronald_sts_ep1_03'and z.get('value')==1:z['value']=0
 def mc(raw):raw['Data']['RootChunk']['phasePrefabs']=[]
 for label,d,fn,oracle in [('missing_real_Hands_end_ACK',hs,ma,lambda m:any(w.get('factName')=='holo_mr_hands_calls_v_end_done'and w['value']==1 for nn in m['graphs']['scene']['nodes'].values()for w in nn['writes'])),('wrong_Ronald_native_sent_receipt',rt,mb,lambda m:m['graphs']['root/11']['nodes']['55']['writes'][0]['value']==1),('missing_Ronald_native_host_lease',rt,mc,lambda m:m['root_prefabs']==['#q302_pr_bar'])]:
  raw=copy.deepcopy(R[d]);fn(raw);mm=Resource(raw).normalize();ck('independent actual raw mutation '+label,oracle(M[d])and not oracle(mm),{'resource':d,'model_errors':mm['errors']});p=O/'mutations'/str(label+'.json');write(p,raw);mut.append({'fault':label,'path':str(p),'sha256':sha(p),'detected':True})
 write(O/'tests.json',tests);write(O/'source_pins.json',pins);write(O/'contracts_reviewed.json',reviewed);write(O/'protocols.json',{'requests':req,'custom_calllike':custom,'typed_SMS':typed});write(O/'mutations.json',mut)
 result={'status':'PASS_INDEPENDENT_THIRTY_CONTRACT_REVIEW_WITH_ONE_CONFIRMED_SHARED_FAMILY_BLOCKER','quests':res['quest_ids'],'checks':len(tests),'mutations':len(mut),'contracts':30,'independent_fresh_exports':12,'actual_graph_inputs':len(M),'phone_request_sites':len(req),'source_epoch':str(ep),'source_epoch_sha256':sha(ep),'tests':str(O/'tests.json'),'source_pins':str(O/'source_pins.json'),'code_sha256':sha(__file__),'contract_counts':dict(collections.Counter(x['status']for x in reviewed)),'confirmed_new_defect_families':1,'Ronald_selected_affected':['sts_ep1_01','sts_ep1_03','sts_ep1_08','sts_ep1_12'],'Ronald_blocker':'Exact native host #q302_pr_bar marker lease absent from B0 source scope; child SMS has no physical scene/PIP. Safe isolated future dispatch still needs token/shared pause/2-day timer/saved sent1 pending-vs-delivered arbitration. No concrete safe proposal approved.','findings':['Exact selected original entry predicates, phase50 wake scope, nested bodies, companion bugfix/cleanup and credit nodes retained. Tier3 shared message ordering and distinct tier2/debug/Hands alternatives remain native.','All28 actual main generic Hands requests, real listener/ACK/wait/clear/cleanup and77 scene socket uses are independently checked. Regina/Rinder/Briana/Maldonado local SMS remain distinct from missing Ronald optional news.','Native Rinder outcomes, Heaviest testimony/combat rewards and16h MQ304 cleanup, TreatingSymptoms alive/dead routes/reward/cleanup and S29 aftermath fences remain intact.','All30 findings retain source-specific omissions and static/live limits. Four G20 FAIL contracts are supported; full family adds two other selected dependencies without adding new unique family or claiming full quest parity.'],'limits':['Native raw equality/reachability does not establish saved-owner adoption, live phone delivery/reload, timer scheduling, world placement or engine reward behavior.','Stock capture direct records do not certify economic descendants or runtime merged overrides.','Pinned5136-model family census and C163/3 context proof reused with independently verified applicability; no new full census, world decode or runtime patch.'],'runtime_changes':[]};write(O/'review.json',result);print(json.dumps(result))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);run(Path(p.parse_args().output).resolve())
