"""Deep MQ305/MQ306 source contracts, inventories and native-driven controls."""
from pathlib import Path
import sys,copy,json,re,collections
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import inputs as I
sys.path.insert(0,str(I.W/'prealpha/quest_restoration_qr5/reviews/worker_b'))
from review_remaining import path,ext
from common import read,write,sha,walk
from model import Resource,compare_graph
def ev(c,f,j):
 t=c['$type']
 if t=='questLogicalCondition':
  a=[ev(x,f,j)for x in c['conditions']];return all(a)if c['operation']=='AND'else any(a)if c['operation']=='OR'else not any(a)if c['operation']=='NOR'else False
 if t in ['questFactsDBCondition','questJournalCondition']:return ev(c['type'],f,j)
 if t=='questVarComparison_ConditionType':
  a,b=f.get(c['factName'],0),c['value'];return {'Equal':a==b,'NotEqual':a!=b,'Greater':a>b,'GreaterOrEqual':a>=b,'Less':a<b,'LessOrEqual':a<=b}[c['comparisonType']]
 if t=='questJournalEntryState_ConditionType':
  a=j.get(c['path']['realPath'],'MISSING')==c['state'];return not a if c.get('inverted')else a
 raise ValueError(t)
def run():
 O=H/'verification_01';assert not O.exists();M={};pins=[];tests=[];mut=[];rows={};protocols=[];admission={}
 def ck(k,v,e):tests.append({'name':k,'status':'PASS'if v else'FAIL','evidence':e});assert v,k
 for d in I.selected():
  m,p=I.load(d);M[d]=m;pins.append(p);ck('exact_effective_resource '+d,not m['errors'],p)
  if 'original'in p:
   ck('exact_native_raw_parity '+d,p['raw_sha256']==p['original']['raw_sha256'],p['original']);orig=Resource(read(p['original']['json'])).normalize();ck('native_full_graph_parity '+d,not compare_graph(orig,m),p['original'])
 def g(d,p='root'):return M[d]['graphs'][p]
 def n(d,i,p='root'):return g(d,p)['nodes'][str(i)]
 def e(d,a,s,b,t,p='root'):return [str(a),s,str(b),t]in g(d,p)['edges']
 def find(t):return next(d for d in M if d.endswith('\\'+t))
 parent=I.PARENT;mq305=find('mq305.questphase');mq306=find('mq306.questphase');out=find('mq305_outcome.questphase');hook=find('mq305_01_hook.questphase');net=find('mq305_netwatch_encounter.questphase');intro=find('mq306_01_intro.questphase');expo=find('mq306_02_tech_expo.questphase');aaron=find('mq306_04a_aaron_meeting.questphase');angie=find('mq306_04b_angie_meeting.questphase');boot23='towercontinued\\sidejobs_s23\\ep1\\mq306_boot.questphase';owner23='towercontinued\\sidejobs_s23\\ep1\\mq306_owner.questphase';aaron23='towercontinued\\sidejobs_s23\\ep1\\mq306_aaron.questphase'
 for o in I.OWN:
  d=o['depot'];s=o['parent_slice'];old=g(parent,s['graph']);cg=g(d,'root/100');ids=set(map(str,s['ids']));expected=sorted(x for x in old['edges']if x[0]in ids and x[2]in ids)
  for ni in ids:ck('complete_native_entry_node '+o['key']+ni,n(d,ni,'root/100')==n(parent,ni,s['graph']),{'source':parent,'native_graph':s['graph'],'current_graph':'root/100','node':ni})
  ck('exact_native_entry_edges '+o['key'],cg['edges']==sorted(expected+[['0','Out',str(s['entry']),s['socket']]]),cg['edges'])
  sample={}
  for ni in [2,3,90]:
   cn=n(d,ni);fs={x['factName']:x['value']for x in cn['reads']if x.get('factName')and x['comparisonType']=='Equal'};js={x['path']['realPath']:x['state']for x in cn['reads']if x.get('$type')=='questJournalEntryState_ConditionType'};fs.setdefault('mq306_active',0);ck('actual_admission_positive '+o['key']+str(ni),ev(cn['payload']['condition'],fs,js),{'facts':fs,'journals':js});sample[str(ni)]={'facts':fs,'journals':js,'condition':cn['payload']['condition']}
  cn=n(d,2);fs=sample['2']['facts'];js=sample['2']['journals']
  for fact,v in [('q307_done',0),('q307_finished',0),('PTFRU9_Support_Issued',0),(o['tag']+'_Issued',1),('mq305_started'if'MQ305'in o['key']else'mq306_started',1)]:ck('actual_admission_reject '+o['key']+fact,not ev(cn['payload']['condition'],fs|{fact:v},js),fact)
  if o['key']=='MQ306_FRESH':
   ck('MQ306_allows_only_passive_active0_or1',all(ev(cn['payload']['condition'],fs|{'mq306_active':v},js)for v in [0,1])and not ev(cn['payload']['condition'],fs|{'mq306_active':2},js),'Original main30 writes active1 before invitation/started; no progress widening beyond0..1')
   ck('MQ306_old_resume_Issued_excludes_fresh',not ev(cn['payload']['condition'],fs|{'PTFRS23_MQ306_Issued':1},js),'No existing S23 owner restarted')
  admission[o['id']]=sample
 ck('MQ305_native_entry_logical_semantics',n(parent,27)['payload']['condition']['operation']=='OR'and n(parent,12)['reads'][0]['factName']=='q301_failed'and e(parent,12,'True',14,'In1')and e(parent,12,'False',27,'In'),n(parent,27)['payload'])
 ck('MQ305_native_stage_chain',all(e(mq305,a,s,b,t)for a,s,b,t in [(0,'Out',3,'In'),(3,'Out',4,'In'),(4,'Out',5,'In'),(5,'Out',6,'In'),(6,'Out',7,'In'),(6,'out_failed',7,'In_failed'),(7,'out_bree_sold_data',19,'In')]),g(mq305)['edges'])
 ck('MQ305_native_terminal_writers',e(out,140,'Out',141,'In')and e(out,141,'Out',142,'In')and [n(out,i)['writes'][0]['factName']for i in [140,141,142]]==['mq305_done','mq305_finished','mq305_active'],'Outcome140done1→141finished1→142active0')
 ck('MQ305_native_reward_and_failure_not_forced',n(out,128)['type']=='questRewardManagerNodeDefinition'and n(out,188)['type']=='questRewardManagerNodeDefinition'and n(out,134)['writes'][0]['factName']=='mq305_failed',{'rewards':[n(out,i)['payload']for i in [128,188]],'failure':n(out,134)['payload']})
 ck('MQ306_native_outcome_and_cleanup_chain',n(mq306,10)['type']=='questLogicalXorNodeDefinition'and e(mq306,5,'mq306_aaron',7,'In1')and e(mq306,5,'mq306_angie',8,'In1')and e(mq306,10,'Out1',9,'In1')and e(mq306,32,'Out',31,'In')and e(mq306,31,'Out',33,'In'),'Distinct Aaron/Angie routes;32done1→31finished1→33active0')
 ck('MQ306_native_intro_refusal_cleanup',e(intro,50,'True',51,'Failed')and e(mq306,3,'Out2',35,'In1')and e(mq306,35,'Out1',39,'In1')and e(mq306,39,'Out1',32,'In'),'Native failed route ends in exact done/finished cleanup; fresh Issued stays durable even if private success watcher never fires')
 ck('MQ306_native_expo_failure_cleanup',e(expo,8,'Out',12,'Failed','root/58')and e(mq306,4,'failed',35,'In1'),'Abandonment remains native, no synthetic journal/failure rewrite')
 # Complete source-specific S23 resume slice, separate from fresh body enrollment.
 for gp,gr in M[owner23]['graphs'].items():
  if gp=='root/9':ck('MQ306_S23_native_full_cleanup',gr==g(mq306,'root/9'),'Exact native cleanup nested graph including reward/actions/delays')
  elif gp=='root':
   for ni,nn in gr['nodes'].items():
    if ni in ['0','7']:continue
    ck('MQ306_S23_owner_native_node '+ni,nn==n(mq306,ni),nn['payload_sha256'])
 for gp,gr in M[aaron23]['graphs'].items():
  og=g(aaron,gp)
  for ni,nn in gr['nodes'].items():ck('MQ306_S23_SMS_native_node '+gp+ni,nn==og['nodes'][ni],nn['payload_sha256'])
  ids=set(gr['nodes']);expected=[x for x in og['edges']if x[0]in ids and x[2]in ids]
  if gp=='root/25':expected=[x for x in expected if x[0]!='0']+[['0','Out','24','In']]
  ck('MQ306_S23_SMS_exact_selected_edges '+gp,gr['edges']==sorted(expected),gr['edges'])
 ck('MQ306_S23_original_reply_wait',e(aaron23,0,'Out',24,'In','root/25')and set(n(aaron23,24,'root/25')['journal_paths'])=={'ep1/contacts/aaron/mq306/02a_ch_dive_reply/ch_01','ep1/contacts/aaron/mq306/02a_ch_dive_reply/ch_02'},'Narrow resume begins original dive-reply wait24, not fresh setup/SMS replay')
 ck('MQ306_S23_fresh_progress_mutually_exclusive',any(x.get('factName')=='mq306_started'and x.get('value')==1 for x in n(boot23,2)['reads'])and all(any(x.get('factName')==f and x.get('value')==0 for x in n(boot23,2)['reads'])for f in ['mq306_done','mq306_finished']),{x.get('factName'):x.get('value')for x in n(boot23,2)['reads']if x.get('factName')})
 # Inventory every actual handler, not a handpicked holo-call subset.
 for q,prefix in zip(I.Q,['mq305','mq306']):
  selected=[];factwrites={};factreads={};calls=[];sms=[];assets=[];external=[]
  for d,m in M.items():
   if prefix not in d:continue
   for gp,gr in m['graphs'].items():
    for ni,nd in gr['nodes'].items():
     row={'resource':d,'graph':gp,'node':ni,'type':nd['type'],'payload_sha256':nd['payload_sha256'],'reads':nd['reads'],'writes':nd['writes'],'journals':nd['journal_paths'],'refs':nd['refs'],'prefabs':nd['prefabs'],'node_refs':nd['node_refs'],'incoming':[x for x in gr['edges']if x[2]==ni],'outgoing':[x for x in gr['edges']if x[0]==ni]};selected.append(row)
     for w in nd['writes']:factwrites.setdefault(w['factName'],[]).append(row)
     for r in nd['reads']:
      if r.get('factName'):factreads.setdefault(r['factName'],[]).append(row)
     if nd['sms']or nd['type']=='questPhoneManagerNodeDefinition':sms.append(row)
     if nd['refs']or nd['prefabs']or nd['node_refs']:assets.append(row)
     if nd['type']=='questSceneNodeDefinition':calls.append(row)
  guarded=set(I.OWN[0 if prefix=='mq305'else 1]['facts_equal'])|set(I.OWN[0 if prefix=='mq305'else 1]['fact_ranges']);omitted={f:[{'resource':x['resource'],'graph':x['graph'],'node':x['node']}for x in rs]for f,rs in factwrites.items()if f.startswith(prefix+'_')and f not in guarded}
  rows[q]={'handlers':selected,'fact_writers':factwrites,'fact_readers':factreads,'scene_calls':calls,'phone_and_SMS':sms,'asset_bindings':assets,'native_local_writers_not_in_fresh_guard':omitted,'read_facts_without_local_writers':{f:rs for f,rs in factreads.items()if f not in factwrites and f.startswith(prefix)},'test_resource_note':'mq305_chickentest and debug entry sockets are inventoried, not automatically executing gameplay owners'}
 # Exact native Hands protocol in both directions and every specialized name.
 hc='base\\quest\\holocalls\\mr_hands\\mr_hands_holocall.questphase';hs='base\\quest\\holocalls\\mr_hands\\mr_hands_holocall.scene';init='towercontinued\\gig_phone_u9\\fixer_initializer.questphase';cleanup='towercontinued\\gig_phone_u9\\fixer_cleanup.questphase';cl='base\\quest\\holocalls\\mr_hands\\mr_hands_cleanup.questphase';ck('effective_Hands_listener_and_cleanup',hc in n(init,73)['refs']and e(init,25,'Out1',73,'In1')and cl in n(cleanup,329)['refs']and e(cleanup,462,'True',329,'In36'),'Actual U9 Hands73, cleanup329, PH3 shared studios retained')
 rx=re.compile(r'^(holo|audio)_(?:(.+)_calls_v|v_calls_(.+))_(start|end)_activate$');custom=[]
 for d,m in M.items():
  if not d.startswith('ep1\\quest\\minor_quests\\mq'):continue
  for gp,gr in m['graphs'].items():
   for ni,nd in gr['nodes'].items():
    for w in nd['writes']:
     if w['value']!=1:continue
     ma=rx.fullmatch(w['factName'])
     if not ma:
      if w['factName'].startswith('new_')and any(x in w['factName'].lower()for x in ['call','brief','end']):custom.append({'resource':d,'graph':gp,'node':ni,'fact':w})
      continue
     mode,inc,outgoing,kind=ma.groups();contact=inc or outgoing;ack='holo_'+(contact+'_calls_v'if inc else'v_calls_'+contact)+'_'+kind+'_done';readers=[i for i,n0 in g(hc)['nodes'].items()if any(x.get('factName')==w['factName']for x in n0['reads'])];writers=[i for i,n0 in g(hs,'scene')['nodes'].items()if any(x.get('factName')==ack and x['value']==1 for x in n0['writes'])];p={'resource':d,'graph':gp,'node':ni,'request':w['factName'],'direction':'incoming'if inc else'outgoing','contact':contact,'real_ACK':ack,'controller_listeners':readers,'ACK_writers':writers};ck('all_request_direction_binding '+d+ni,contact=='mr_hands'and bool(readers)and bool(writers),p)
     if gp=='scene':
      waits=[i for i,x in gr['nodes'].items()if any(r.get('factName')==ack for r in x['reads'])];clears=[i for i,x in gr['nodes'].items()if any(r.get('factName')==ack and r['value']==0 for r in x['writes'])];ck('real_scene_wait_and_clear '+d+ni,bool(waits)and bool(clears),{'waits':waits,'clears':clears});p|={'waits':waits,'clears':clears}
     protocols.append(p)
 ck('explicit_custom_call_request_inventory',not custom,{'custom_new_request_family':custom,'other_named_phone/SMS and scene endpoints':{q:len(r['phone_and_SMS'])+len(r['scene_calls'])for q,r in rows.items()},'limit':'All request writers inventoried; arbitrary runtime engine scripts are separate evidence.'})
 for q in I.Q:
  p=I.W/'prealpha/quest_restoration_qr5/shared/tdb_applicability_02'/str(q+'.json');t=read(p);pins.append({'path':str(p),'sha256':sha(p)});ck('bounded_stock_definition_index '+q,bool(t['limits']),t['limits'])
 for name in ['PTFR_SideJobsS24.reds','PTFR_SideJobsS23.reds','PTFR_HistorySnapshotHS1.reds','PTFR_JohnnyVoiceJV1.reds']:
  p=I.C/'package/r6/scripts/PTFR_Consolidated'/name;pins.append({'path':str(p),'sha256':sha(p)})
 jv=(I.C/'package/r6/scripts/PTFR_Consolidated/PTFR_JohnnyVoiceJV1.reds').read_text(encoding='utf8');ck('R4_JV1_visual_only_scope','visual.TemporaryHide(true)'in jv and 'Character.Silverhand'in jv and 'SetFact'in jv==False if False else 'visual.TemporaryHide(true)'in jv and 'Character.Silverhand'in jv and 'SetFact'not in jv,{'scope':'Actor kept for voice/native timing; exact Silverhand visuals hidden after genuine Tower. Independent props, render and arbitrary actor records not proven.'})
 # Actual raw native controls, separate original evidence drives the checks.
 for name,depot,nodeid,field,val in [('lost_native_tier_gate',I.PARENT,8,'factName','BROKEN_NATIVE_TIER'),('missing_outgoing_real_ACK',hs,None,'factName','BROKEN_REAL_ACK')]:
  pin=next(p for p in pins if p.get('depot')==depot);raw=copy.deepcopy(read(pin['json']));changed=0
  for x in walk(raw):
   if name=='lost_native_tier_gate'and x.get('$type')=='questVarComparison_ConditionType'and x.get('factName')=='sts_ep1_tier_1':x['factName']=val;changed+=1
   if name=='missing_outgoing_real_ACK'and x.get('$type')=='questSetVar_NodeType'and x.get('factName')=='holo_v_calls_mr_hands_start_done'and x.get('value')==1:x['factName']=val;changed+=1
  mm=Resource(raw).normalize();caught=(mm['graphs']['root']['nodes']['8']['payload']!=n(I.PARENT,8)['payload'])if name=='lost_native_tier_gate'else not any(w.get('factName')=='holo_v_calls_mr_hands_start_done'and w['value']==1 for n0 in mm['graphs']['scene']['nodes'].values()for w in n0['writes']);ck('raw_mutation '+name,changed>0 and caught,name);mut.append({'name':name,'source':pin['json'],'changed':changed,'detected':caught});write(O/(name+'.json'),raw)
 write(O/'tests.json',tests);write(O/'source_pins.json',pins);write(O/'admission.json',admission);write(O/'handlers.json',rows);write(O/'protocols.json',protocols);write(O/'mutations.json',mut);write(O/'summary.json',{'quests':I.Q,'checks':len(tests),'raw_mutations':len(mut),'resources':len(M),'phone_requests':len(protocols),'custom_new_call_requests':custom});print(json.dumps({'checks':len(tests),'raw_mutations':len(mut),'resources':len(M),'phone_requests':len(protocols)},ensure_ascii=True))
if __name__=='__main__':run()
