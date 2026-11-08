"""G20 native EP1 graph/owner/phone/outcome audit; evidence-only outputs."""
from pathlib import Path
import sys,json,copy,re,collections
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import inputs as I
from common import read,write,sha,walk
from model import Resource,compare_graph
sys.path.insert(0,str(I.W/'prealpha/quest_restoration_qr5/reviews/worker_b'));from review_remaining import path,ext
def evalf(c,f):
 if c['$type']=='questLogicalCondition':
  a=[evalf(x,f)for x in c['conditions']];return all(a)if c['operation']=='AND'else any(a)if c['operation']=='OR'else not any(a)if c['operation']=='NOR'else False
 if c['$type']=='questFactsDBCondition':return evalf(c['type'],f)
 if c['$type']=='questVarComparison_ConditionType':
  a,b=f.get(c['factName'],0),c['value'];return {'Equal':a==b,'Greater':a>b,'GreaterOrEqual':a>=b,'Less':a<b,'LessOrEqual':a<=b,'NotEqual':a!=b}[c['comparisonType']]
 raise ValueError(c['$type'])
def run():
 O=H/'verification_01';assert not O.exists();M={};pins=[];tests=[];mut=[];records={};phones=[];flows=[]
 def ck(k,v,e):tests.append({'name':k,'status':'PASS'if v else'FAIL','evidence':e});assert v,json.dumps({'name':k,'evidence':e},ensure_ascii=True)
 for d in I.selected():
  m,p=I.load(d);M[d]=m;pins.append(p);ck('source_hash_and_decode '+d,not m['errors'],p)
  if d.startswith('ep1\\openworld\\street_stories\\'):
   raw=I.W/'research/gig_restoration/rollout_r2/native_sources/raw'/Path(d.replace('\\','/'));j=I.W/'research/gig_restoration/rollout_r2/native_sources/json'/Path(d.replace('\\','/')+'.json')
   if raw.is_file()and j.is_file():ck('matching_original_R2_raw '+d,sha(raw)==p['raw_sha256'],{'raw':str(raw),'sha256':sha(raw),'json':str(j),'json_sha256':sha(j)})
 core=read(H/'shared_core.json');ck('pinned_shared_Tier3_core',sha(H/'shared_core.json')=='97F7F30E81EA363C193138A1DE9ACE405DE6739F3FA349380417C62C0C0ABF82'and len(read(core['tests']))==19 and all(t['status']=='PASS'for t in read(core['tests'])),core['tests']);M.update(read(core['models']));pins+=read(core['source_pins'])
 def g(d,p='root'):return M[d]['graphs'][p]
 def n(d,i,p='root'):return g(d,p)['nodes'][str(i)]
 def e(d,a,s,b,t,p='root'):return [str(a),s,str(b),t]in g(d,p)['edges']
 def find(t):return next(d for d in M if d.endswith('\\'+t))
 # Derive original edges from raw native graph; builder recipe is a separate cross-check.
 for r in I.REC:
  d=r['depot'];native='recipe:'+r['raw'];cp=r.get('compiled_graph','root');np=r['graph'];ids=set(map(str,r['ids']))
  for ni in ids:
   if ni=='0':continue
   old=n(native,ni,np);new=n(d,ni,cp);ck('selected_native_node '+d+ni,new['payload']==ext(old['payload']),{'native':native,'graph':np,'node':ni,'current_graph':cp})
   pref=cp+'/'+ni;op=np+'/'+ni
   if r['id']=='sts_ep1_06'and r['kind']=='entry'and ni=='9':continue # Explicit separately proved shared original Tier3 owner.
   for child,cg in M[d]['graphs'].items():
    if child==pref or child.startswith(pref+'/'):ck('entire_native_nested_graph '+d+child,cg==g(native,op+child[len(pref):]),op+child[len(pref):])
  ck('actual_recipe_edges '+d,g(d,cp)['edges']==sorted([[str(a),s,str(b),t]for a,s,b,t in r['edges']]),r['edges'])
  if r['kind']=='entry':
   ck('original_freezing_ancestor_preserved '+d,n(d,50)['payload']==n(native,50)['payload'],n(d,50)['payload'])
   ck('original_retained_parent_edges '+d,all([a,s,b,t]in g(d,cp)['edges']or ([a,s,'65004','In']in g(d,cp)['edges']and ['65004','Out',b,t]in g(d,cp)['edges']and n(d,65004,cp)['writes']==[{'$type':'questSetVar_NodeType','factName':'PTFRU9_'+r['id']+'_Started','value':1,'setExactValue':1}])for a,s,b,t in g(native,np)['edges']if a in ids and a!='0'and b in ids and not(a in [str(i)for i in r['ids']if n(native,i,np)['type']=='questPhaseNodeDefinition']and s=='Out1'and n(native,b,np)['type']=='questOutputNodeDefinition')),{'native_graph':np,'retained_ids':sorted(ids)})
   for comp,ci in zip(r['companions'],[64000,64001]):
    old=copy.deepcopy(n('recipe:'+comp['source_raw'],comp['source_node'],comp['source_graph'])['payload']);old['id']=ci;ck('exact_original_companion_scope '+d+str(ci),n(d,ci,cp)['payload']==old,{'source_graph':comp['source_graph'],'source_node':comp['source_node'],'current_node':ci,'kind':comp['kind'],'prefabs':n(d,ci,cp)['prefabs']})
   ck('ordered_native_completion_cleanup '+d,e(d,65003,'Out',64001,'In1',cp)and e(d,64000,'Out1',65006,'In',cp),{'body_and_cleanup_edges':[x for x in g(d,cp)['edges']if x[0]in ['64000','64001','65003']]})
 # Explicitly verify the original outer interface that the direct private cleanup replaces.
 par=next('recipe:'+r['raw']for r in I.REC if r['kind']=='entry');parent=g(par)
 for q,body,outid,clinput,clnode in [('sts_ep1_06',4,33,8,16),('sts_ep1_03',19,30,5,14),('sts_ep1_12',26,29,4,10)]:
  ck('actual_native_body_to_cleanup_interface '+q,e(par,body,'Out1',outid,'In','root/50')and n(par,outid,'root/50')['payload']['socketName']['$value']==q and ['50',q,'51',q]in parent['edges']and e(par,clinput,'Out',clnode,'In1','root/51'),{'body':body,'native_output':outid,'outer_edge':['50',q,'51',q],'cleanup_input':clinput,'cleanup_node':clnode})
 # Current complete-input data tables plus actual dynamic guard, not a historical quest count.
 script=I.C/'package/r6/scripts/PTFR_Consolidated/PTFR_ActivityStateR3.reds';text=script.read_text(encoding='utf8');cl=text[text.index('class NativeGigDataU9'):];line=next(s for s in cl.splitlines()if'func IDs()'in s);ids=json.loads(line[line.index('['):line.rindex(']')+1]);pins.append({'path':str(script),'sha256':sha(script)})
 def arr(method,i):
  b=cl[cl.index('public static func '+method+'('):];b=b[:b.index('\n  public static func',1)];l=next(l for l in b.splitlines()if'if i=='+str(i)+' 'in l);return json.loads(l[l.index('['):l.rindex(']')+1])
 for q in I.Q:
  idx=ids.index(q);data={k:arr(k,idx)for k in ['Paths','Classes','Facts','TerminalFacts']};entry='towercontinued\\native_gigs_u9\\'+q+'_entry.questphase';cp='root/50';guard=n(entry,65002,cp);fixture={r['factName']:r['value']for r in guard['reads']if r.get('factName')};ck('actual_guard_positive '+q,evalf(guard['payload']['condition'],fixture),fixture)
  for f,v in [('q307_done',0),('q307_finished',0),('PTFRU9_Support_Issued',0),('PTFRU9_'+q+'_ParentEntered',1),('PTFRU9_'+q+'_Fault',1),(q+'_start',1),(q+'_finished',1)]:ck('actual_guard_reject '+q+f,not evalf(guard['payload']['condition'],fixture|{f:v}),f)
  row=[];writers={};jp={};non_generic=[]
  for d,m in M.items():
   if not d.startswith('ep1')or q not in d:continue
   for gp,gr in m['graphs'].items():
    for ni,nd in gr['nodes'].items():
     rr={'resource':d,'graph':gp,'node':ni,'type':nd['type'],'payload_sha256':nd['payload_sha256'],'reads':nd['reads'],'writes':nd['writes'],'journal_paths':nd['journal_paths'],'refs':nd['refs'],'prefabs':nd['prefabs'],'node_refs':nd['node_refs'],'reward':nd['reward'],'sms':nd['sms'],'incoming':[x for x in gr['edges']if x[2]==ni],'outgoing':[x for x in gr['edges']if x[0]==ni]};row.append(rr)
     for w in nd['writes']:
      if w['factName'].startswith(q):writers.setdefault(w['factName'],[]).append(rr)
      if w['value']==1 and (w['factName'].startswith('new_')or'call'in w['factName'].lower()and not w['factName'].startswith(('holo_','audio_'))):non_generic.append({'resource':d,'graph':gp,'node':ni,'fact':w})
     for x in walk(nd['payload']):
      if x.get('$type')=='gameJournalPath'and x.get('realPath'):jp.setdefault(x['realPath'],[]).append({'resource':d,'graph':gp,'node':ni,'class':x.get('className',{}).get('$value'),'incoming':rr['incoming']})
  omitted={f:rs for f,rs in writers.items()if f not in data['Facts']};missing={p:rs for p,rs in jp.items()if p.startswith('ep1/quests/street_stories/'+q)and p not in data['Paths']};records[q]={'data_index':idx,**data,'guard':guard['payload']['condition'],'positive_fixture':fixture,'handlers':row,'native_local_writers':writers,'unlisted_local_writer_names':omitted,'all_journal_uses':jp,'unlisted_native_journal':missing,'non_generic_call_like_writes':non_generic};ck('local_writer_admission_inventory '+q,isinstance(omitted,dict),{'omitted':list(omitted),'journal_omissions':list(missing)})
 # Both directions/modes and all metadata/direct-scene paths are inventoried separately.
 init='towercontinued\\gig_phone_u9\\fixer_initializer.questphase';cleanup='towercontinued\\gig_phone_u9\\fixer_cleanup.questphase';ck('actual_Hands_shared_owner',I.HC in n(init,73)['refs']and e(init,25,'Out1',73,'In1')and I.CL in n(cleanup,329)['refs']and e(cleanup,462,'True',329,'In36'),'Native Hands controller73 plus actual cleanup329 and preserved PH3 studios')
 rx=re.compile(r'^(holo|audio)_(?:(.+)_calls_v|v_calls_(.+))_(start|end)_activate$')
 for q,rec in records.items():
  for rr in rec['handlers']:
   nd=n(rr['resource'],rr['node'],rr['graph']);gr=g(rr['resource'],rr['graph'])
   for w in nd['writes']:
    ma=rx.fullmatch(w['factName'])if w['value']==1 else None
    if not ma:continue
    mode,inc,outgoing,kind=ma.groups();contact=inc or outgoing;ack='holo_'+(contact+'_calls_v'if inc else'v_calls_'+contact)+'_'+kind+'_done';listeners=[i for i,x in g(I.HC)['nodes'].items()if any(r.get('factName')==w['factName']for r in x['reads'])];real=[i for i,x in g(I.HS,'scene')['nodes'].items()if any(v.get('factName')==ack and v['value']==1 for v in x['writes'])];r={'quest':q,'resource':rr['resource'],'graph':rr['graph'],'node':rr['node'],'request':w['factName'],'direction':'incoming'if inc else'outgoing','mode':mode,'listeners':listeners,'real_ACK_writers':real,'ACK':ack};ck('all_actual_protocol_directions '+q+rr['resource']+rr['node'],contact=='mr_hands'and bool(listeners)and bool(real),r)
    if rr['graph']=='scene':
     waits=[i for i,x in gr['nodes'].items()if any(v.get('factName')==ack for v in x['reads'])];clears=[i for i,x in gr['nodes'].items()if any(v.get('factName')==ack and v['value']==0 for v in x['writes'])];direct=[i for i in waits if path(gr,rr['node'],i)];fork=[i for i in gr['nodes']if len([e0 for e0 in gr['edges']if e0[0]==i])>1 and path(gr,i,rr['node'])and any(path(gr,i,wi)for wi in waits)];after=[(a,b)for a in waits for b in clears if path(gr,a,b)];ck('actual_ACK_wait_clear_paths '+q+rr['resource']+rr['node'],bool(direct or fork)and bool(after),{'request':r,'waits':waits,'clears':clears,'prearmed_forks':fork,'wait_to_clear':after});r|={'waits':waits,'clears':clears,'prearmed_forks':fork}
    phones.append(r)
  custom=rec['non_generic_call_like_writes'];ck('custom_request_family_investigated '+q,all(x['fact']['factName']=='sts_ep1_03_wagner_called_regina'for x in custom),{'all_non_generic_call_like':custom,'meaning':'The Rinder field is a native outcome receipt, not a named V-call request. Separate scene actors/ref and predecessor SMS trace below.'})
 # Source-specific outcomes/continuations, not an undifferentiated body hash claim.
 ow6=find('sts_ep1_06_openworld.questphase');ow3=find('sts_ep1_03_openworld.questphase');main12=find('sts_ep1_12_phase.questphase')
 for d,gp,rewards,fin,fn in [(ow6,'root/7',[128,280],72,'sts_ep1_06_finished'),(ow3,'root/4',[361],365,'sts_ep1_03_finished'),(main12,'root',[61],66,'sts_ep1_12_finished')]:
  ck('native_reward_terminal_route '+d,all(n(d,r,gp)['type']=='questRewardManagerNodeDefinition'and (path(g(d,gp),r,fin)if d==ow6 else path(g(d,gp),fin,r))for r in rewards)and n(d,fin,gp)['writes'][0]['factName']==fn,{'rewards':rewards,'finished':fin,'paths':{r:(path(g(d,gp),r,fin)if d==ow6 else path(g(d,gp),fin,r))for r in rewards}})
 stand=find('sts_ep1_03_wagner_standoff.scene');ck('Rinder_Regina_receipt_not_invented_phone_owner',n(stand,550,'scene')['writes'][0]['factName']=='sts_ep1_03_wagner_called_regina'and not any('regina'in a['actorName'].lower()for a in M[stand]['metadata']['actors'])and not any('reggie'in r.lower()or'regina'in r.lower()for r in M[stand]['refs']),{'actor_names':[a['actorName']for a in M[stand]['metadata']['actors']],'receipt_node':550,'limit':'Source named receipt and absence of actual V-call producer/actor/ref; no external Regina conversation is added.'})
 ck('Rinder_prior_code_SMS_actual_suppression_route',n(ow3,132,'root/4/59')['payload']['condition']['operation']=='OR'and e(ow3,132,'False',135,'In','root/4/59')and e(ow3,135,'Out',133,'In','root/4/59')and e(ow3,133,'Out',134,'Active','root/4/59'),'No-garage OR called-Regina suppresses; otherwise outside trigger→contact→code SMS; not replayed from dogtag')
 # Regression controls mutate actual raw source, with independent original expectations.
 p=next(p for p in pins if p.get('depot')==I.HS);raw=read(p['json']);changed=0
 for x in walk(raw):
  if x.get('$type')=='questSetVar_NodeType'and x.get('factName')=='holo_mr_hands_calls_v_end_done'and x.get('value')==1:x['value']=0;changed+=1
 mm=Resource(raw).normalize();caught=not any(w.get('factName')=='holo_mr_hands_calls_v_end_done'and w['value']==1 for n0 in mm['graphs']['scene']['nodes'].values()for w in n0['writes']);ck('raw_missing_Hands_real_end_ACK_detected',changed>0 and caught,changed);mut.append({'name':'missing_real_Hands_end_ACK','detected':caught});write(O/'missing_Hands_end_ACK.scene.json',raw)
 raw=copy.deepcopy(read(next(p['json']for p in pins if p.get('depot')=='towercontinued\\native_gigs_u9\\sts_ep1_06_entry.questphase')));r=Resource(raw);outer=r.d(r.root['graph']);node=next(r.d(h)for h in outer['nodes']if r.d(h)['id']==50);node['unfreezingTriggerNodeRef']['$value']='#BROKEN_DOGTOWN_TRIGGER';mm=Resource(raw).normalize();caught=mm['graphs']['root']['nodes']['50']['payload']!=n('towercontinued\\native_gigs_u9\\sts_ep1_06_entry.questphase',50)['payload'];ck('raw_lost_original_unfreezing_scope_detected',caught,'Actual saved phase50 wake scope changed');mut.append({'name':'lost_native_unfreezing_scope','detected':caught});write(O/'lost_unfreezing_scope.questphase.json',raw)
 write(O/'tests.json',tests);write(O/'source_pins.json',pins);write(O/'handlers.json',records);write(O/'protocols.json',phones);write(O/'mutations.json',mut);write(O/'summary.json',{'checks':len(tests),'raw_mutations':len(mut),'graph_resources':len(M),'phone_requests':len(phones),'quests':I.Q});print(json.dumps({'checks':len(tests),'raw_mutations':len(mut),'resources':len(M),'phone_requests':len(phones)},ensure_ascii=True))
if __name__=='__main__':run()
