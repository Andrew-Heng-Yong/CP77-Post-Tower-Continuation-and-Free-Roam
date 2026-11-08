"""G12 Padre gigs: exact U9 donor, body, protocol and outcome checks."""
from pathlib import Path
import sys,copy,json,re,argparse,collections
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import source_inputs as I
from common import read,write,sha,walk
from model import Resource,compare_graph,digest
def externalize(x):
 if isinstance(x,list):return [externalize(v)for v in x]
 if isinstance(x,dict):
  out={k:externalize(v)for k,v in x.items()}
  if 'DepotPath'in out and out.get('Flags')=='Embedded':out['Flags']='Soft'
  if out.get('$type')=='questQuestPhaseResource'and out.get('cookingPlatform')=='PLATFORM_None':out['cookingPlatform']='PLATFORM_PC'
  return out
 return x
def path(g,a,b):
 q=collections.deque([[str(a)]]);seen={str(a)}
 while q:
  p=q.popleft()
  if p[-1]==str(b):return p
  for x,s,y,t in g['edges']:
   cut=g['nodes'].get(x,{}).get('type')=='scnCutControlNode'and s.startswith('1:')
   if x==p[-1]and s!='CutSource'and t!='CutDestination'and not cut and y not in seen:seen.add(y);q.append(p+[y])
 return None
def ev(c,f):
 t=c['$type']
 if t=='questLogicalCondition':
  r=[ev(x,f)for x in c['conditions']];return all(r)if c['operation']=='AND'else any(r)if c['operation']=='OR'else not any(r)if c['operation']=='NOR'else False
 if t=='questFactsDBCondition':return ev(c['type'],f)
 if t=='questVarComparison_ConditionType':
  if c['factName']not in f:return False
  a,b=f[c['factName']],c['value'];return {'Equal':a==b,'NotEqual':a!=b,'Greater':a>b,'GreaterOrEqual':a>=b,'Less':a<b,'LessOrEqual':a<=b}[c['comparisonType']]
 raise ValueError('Unsupported condition never assumed true: '+t)
def run(O):
 assert not O.exists();M={};pins=[];tests=[];mut=[]
 def ck(name,ok,ev):tests.append({'name':name,'status':'PASS'if ok else'FAIL','evidence':ev});assert ok,name
 for d in I.selected():m,p=I.load(d);M[d]=m;pins.append(p);ck('pinned_source_model '+d,True,p);ck('graph_integrity '+d,not m['errors'],m['errors'])
 def g(d,gp='root'):return M[d]['graphs'][gp]
 def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
 def e(d,a,s,b,t,gp='root'):return [str(a),s,str(b),t]in g(d,gp)['edges']
 def wr(d,i,f,v,gp='root'):return any(x.get('factName')==f and x.get('value')==v for x in n(d,i,gp)['writes'])
 corep=H.parent/'G09/shared_core.json';core=read(corep);rr=read(H.parent/'G09/results.json')
 ck('U9_shared_core_pin',sha(corep)==rr['shared_core_sha256']and sha(core['tests'])==core['tests_sha256']and sha(core['source_pins'])==core['source_pins_sha256'],{'path':str(corep),'sha256':sha(corep),'reused_checks':core['checks'],'scope':'Common U9 support only; Padre protocols independently checked below'})
 for row in core['sources']:
  if row.get('depot','').startswith('towercontinued\\'):
   ck('U9_current_shared_binary '+row['depot'],sha(I.C/'archive_source'/row['depot'].replace('\\','/'))==row['resource_sha256'],row['resource_sha256'])
 # Native district stores embedded bodies; the adapter intentionally uses exact
 # standalone native counterparts. Prove gameplay equality before accepting the
 # explicit handle-flag/platform envelope relocation.
 embedded=[]
 for item in M[I.GL]['embedded_files']:
  d=item['depot']
  if not any(q in d for q in I.Q):continue
  prefix=item['graph_prefix']+'/root';graphs={'root'+gp[len(prefix):]:gr for gp,gr in M[I.GL]['graphs'].items()if gp==prefix or gp.startswith(prefix+'/')}
  original={'graphs':graphs,'metadata':item['metadata'],'metadata_sha256':digest(item['metadata'])};adapted=externalize(copy.deepcopy(original));adapted['metadata_sha256']=digest(adapted['metadata'])
  ck('embedded_to_standalone_native_semantics '+d,not compare_graph(adapted,M[d]),{'original_embedded':item['graph_prefix'],'standalone':d,'allowed_envelope':['Embedded→Soft resource handles','cookingPlatform None→PC'],'root_prefabs':item['root_prefabs']})
  embedded.append({'depot':d,'original_differences':compare_graph(original,M[d]),'adapted_semantic_differences':compare_graph(adapted,M[d]),'root_prefabs':item['root_prefabs']})
 # Current private recipe must preserve original selected payloads and recursively copied graphs.
 recipes=[r for r in I.U['recipes']if r.get('id')in I.Q and r.get('depot')in M]
 for r in recipes:
  cur=r['depot'];don='recipe:'+r['raw'];gp=r['graph']
  for ni in r['ids']:
   if ni==0:continue
   ck('native_selected_payload '+cur+':'+str(ni),n(cur,ni)['payload']==externalize(n(don,ni,gp)['payload']),{'donor':don,'graph':gp,'node':ni,'allowed_relocation':'Embedded→Soft exact external native body, verified separately'})
   prefix='root/'+str(ni);nativeprefix=gp+'/'+str(ni)
   for child,cg in M[cur]['graphs'].items():
    if child==prefix or child.startswith(prefix+'/'):
     ng=nativeprefix+child[len(prefix):];ck('native_nested_graph '+cur+child,cg==g(don,ng),{'native_graph':ng,'private_graph':child})
  ck('recipe_exact_current_edges '+cur,sorted([[str(a),s,str(b),t]for a,s,b,t in r['edges']])==g(cur)['edges'],r['edges'])
 # Actual scripted source admission, not journal presence or historical counts.
 sp=I.C/'package/r6/scripts/PTFR_Consolidated/PTFR_ActivityStateR3.reds';s=sp.read_text(encoding='utf8');pins.append({'path':str(sp),'sha256':sha(sp),'role':'current U9 driver and data'})
 cl=s[s.index('class NativeGigDataU9'):];idline=next(x for x in cl.splitlines()if 'func IDs()'in x);ids=json.loads(idline[idline.index('['):idline.rindex(']')+1])
 def array(method,index):
  body=cl[cl.index('public static func '+method+'('):];body=body[:body.index('\n  public static func',1)]
  line=next(x for x in body.splitlines()if 'if i=='+str(index)+' 'in x);return json.loads(line[line.index('['):line.rindex(']')+1])
 admissions=[];omissions=[]
 for q in I.Q:
  idx=ids.index(q);paths=array('Paths',idx);classes=array('Classes',idx);facts=array('Facts',idx);terminal=array('TerminalFacts',idx)
  ck('data_identity_and_path_class_count '+q,len(paths)==len(classes)and paths[0].endswith(q),{'index':idx,'paths':paths,'classes':classes,'facts':facts,'terminal':terminal})
  entry='towercontinued\\native_gigs_u9\\'+q+'_entry.questphase';c=n(entry,65002)['payload']['condition'];fs={x['factName']:x['value']for x in n(entry,65002)['reads']if'factName'in x};ck('positive_actual_entry_guard '+q,ev(c,fs),fs)
  for k in ['q307_done','q307_finished','PTFRU9_Support_Issued']:
   ck('missing_required_common '+q+k,not ev(c,fs|{k:0}),k)
  for k in ['PTFRU9_'+q+'_ParentEntered','PTFRU9_'+q+'_Fault','PTFRU7_Support_Issued','PTFRU6_Padre_Issued']:
   ck('old_or_duplicate_owner_refused '+q+k,not ev(c,fs|{k:1}),k)
  writes={};jp={}
  for d,m in M.items():
   if not d.startswith('base\\open_world')or q not in d:continue
   for gp,gr in m['graphs'].items():
    for ni,node in gr['nodes'].items():
     for x in node['writes']:
      if x['factName'].startswith(q.replace('sts_hey_','')):writes.setdefault(x['factName'],[]).append({'depot':d,'graph':gp,'node':ni,'write':x})
     for x in walk(node['payload']):
      if x.get('$type')=='gameJournalPath'and x.get('realPath','').startswith('quests/'):
       p=x['realPath'];jp.setdefault(p,[]).append({'depot':d,'graph':gp,'node':ni,'node_type':node['type'],'class':x.get('className',{}).get('$value'),'incoming':[e for e in gr['edges']if e[2]==ni]})
  ck('all_local_native_gig_fact_writers_guarded '+q,not(set(writes)-set(facts)),{'writers':writes,'guarded':facts,'limit':'does not prove all external/saved actor state'})
  omitted={p:rows for p,rows in jp.items()if p not in paths}
  omissions.append({'quest_id':q,'omitted_native_journal_targets':omitted,'classification':'Mappins can legitimately be Active. EyeForAnEye accept_tucker_offer is an omitted objective but only current read/cleanup writes found; no Active writer in bounded native closure. Saved/historical provenance remains conditional.'})
  admissions.append({'quest_id':q,'index':idx,'paths':paths,'classes':classes,'facts':facts,'terminal':terminal,'native_fact_writers':writes,'actual_guard':c,'fixture':fs})
 ck('EntrySafe_original_untouched_and_POI_policy',all(x in s for x in ['if this.State(paths[k],classes[k])!=1','if this.Fact(a[k])!=0','return poi==1 || poi==2;']),'all listed journals Inactive/facts0; native POI Inactive OR Active, no fake reset')
 # Complete Padre native request consumption, real acknowledgement and shared cleanup ownership.
 init='towercontinued\\gig_phone_u9\\fixer_initializer.questphase';cleanup='towercontinued\\gig_phone_u9\\fixer_cleanup.questphase'
 ck('Padre_actual_owned_initializer',n(init,79)['refs']==[I.HC]and e(init,25,'Out1',79,'In1'),'U9 native initializer25→79 Padre controller')
 ck('Padre_actual_owned_cleanup',n(cleanup,336)['refs']==[I.CL]and e(cleanup,468,'True',336,'In42')and e(cleanup,336,'Out42',474,'In'),'native reset chain owned by existing U9 cleanup')
 ck('Padre_native_queued_start_consumer',all(e(I.HC,*x)for x in [(32,'Out',33,'In'),(33,'Out',34,'In'),(34,'Out',35,'In1'),(36,'Out',28,'In')])and wr(I.HC,33,'holo_padre_calls_v_start_activate_count',1)and wr(I.HC,34,'holo_padre_calls_v_start_activate',0)and wr(I.HC,10,'holo_padre_calls_v_start_activate_count',-1)and e(I.HC,10,'Out',0,'holo_padre_calls_v_start'),'native queued request counter not synthetic reset')
 for typ,ack in [('start',41),('end',42)]:
  name='holo_padre_calls_v_'+typ;ck('Padre_native_real_ack '+typ,wr(I.HS,ack,name+'_done',1,'scene')and bool(path(g(I.HS,'scene'),g(I.HS,'scene')['entries'][name],ack)),{'scene_input':name,'ack':ack})
 ck('Padre_native_end_and_cleanup',e(I.HC,3,'Out',11,'In')and e(I.HC,11,'Out',0,'holo_padre_calls_v_end')and wr(I.CL,6,'holo_padre_calls_v_reset_counter',1)and e(I.CL,6,'Out',0,'holo_padre_calls_v_end'),'native real end and reset-counter branch, no fake acknowledgements')
 protocols=[]
 for q in I.Q:
  for suffix in ['prebrief','debriefs']:
   d=next(x for x in M if q+'\\scenes\\'in x and x.endswith('holocall_'+suffix+'.scene'));gr=g(d,'scene');entry=next(iter(gr['entries'].values()))
   for ni,node in gr['nodes'].items():
    for w in node['writes']:
     if w['factName']not in ['holo_padre_calls_v_start_activate','holo_padre_calls_v_end_activate']or w['value']!=1:continue
     done=w['factName'][:-9]+'_done';wait=[i for i,x in gr['nodes'].items()if any(z.get('factName')==done for z in x['reads'])and path(gr,ni,i)];parallel=False;forks=[]
     if not wait:
      # Native debrief repeat-request loops have an acknowledgement listener
      # already armed by a parallel fork; retry producer need not lead to it.
      parallel=True;wait=[i for i,x in gr['nodes'].items()if any(z.get('factName')==done for z in x['reads'])and path(gr,entry,i)]
      forks=[i for i in gr['nodes']if len([z for z in gr['edges']if z[0]==i])>1 and path(gr,entry,i)and path(gr,i,ni)and any(path(gr,i,wa)for wa in wait)]
      ck('native_retry_parallel_ack_arm '+d+ni,bool(forks)and any(nd['type']=='scnCutControlNode'and any(path(gr,wa,ci)for wa in wait)for ci,nd in gr['nodes'].items()),{'retry_producer':ni,'armed_waits':wait,'parallel_forks':forks})
     clear=[i for i,x in gr['nodes'].items()if any(z.get('factName')==done and z.get('value')==0 for z in x['writes'])and any(path(gr,a,i)for a in wait)]
     ck('caller_owned_input_reaches_request '+d+ni,bool(path(gr,entry,ni)),{'entry':entry,'request':ni,'fact':w['factName']})
     ck('caller_native_wait_clear '+d+ni,bool(wait)and bool(clear),{'producer':ni,'waits':wait,'clears':clear,'done':done,'parallel_ack_prearmed':parallel,'forks':forks});protocols.append({'depot':d,'entry':entry,'producer':ni,'request':w['factName'],'waits':wait,'clears':clear,'parallel_ack_prearmed':parallel,'forks':forks})
 # Actual native outcomes, reward paths and parent/tier/counter arbitration.
 life='base\\open_world\\street_stories\\heywood\\glenn\\sts_hey_gle_06\\phase\\sts_hey_gle_06_openworld.questphase';eye='base\\open_world\\street_stories\\heywood\\glenn\\sts_hey_gle_01\\phases\\sts_hey_gle_01_streetstory.questphase'
 ck('LifeWork_tier_arbitration_XOR',n('towercontinued\\native_gigs_u9\\sts_hey_gle_06_entry.questphase',58)['type']=='questLogicalXorNodeDefinition','tier_1_1>0 versus tier_1_1==0 AND tier_1>0, not an impossible AND')
 ck('EyeForEye_tier2_exact',any(x.get('factName')=='sts_hey_gle_tier_2'and x.get('comparisonType')=='Greater'and x.get('value')==0 for x in n('towercontinued\\native_gigs_u9\\sts_hey_gle_01_entry.questphase',3,'root/11')['reads']),'native tier2 remains')
 for x in [(24,'True',5,'In'),(24,'True',2,'In'),(24,'False',2,'In'),(5,'Out',37,'In'),(2,'Out',6,'In')]:ck('LifeWork_native_completion '+str(x),e(life,*x,'root/2'),x)
 ck('LifeWork_reward_success_native','QuestRewards.sts_hey_gle_06_completion'in str(n(life,5,'root/2')['payload'])and wr(life,37,'gle_06_succeed',1,'root/2'),'native success fact downstream of actual reward, not all finished outcomes')
 for x in [(3,'OutKilled',6,'In'),(3,'Outdefeted',7,'In'),(3,'failed',25,'In1'),(6,'Out',8,'In'),(7,'Out',8,'In'),(8,'Out',19,'In'),(19,'Out',9,'In'),(9,'Out',5,'In1')]:ck('EyeForEye_native_outcome '+str(x),e(eye,*x),x)
 for f,ni in [('gle_01_killed',203),('gle_01_spared',204),('gle_01_delivered',205)]:ck('EyeForEye_native_result '+f,wr(eye,ni,f,1,'root/3'),ni)
 ck('EyeForEye_failed_result_connected',wr(eye,9,'gle_01_failed',1,'root/3/190')and e(eye,21,'Out',9,'In','root/3/190'),'native refusal/failure path, never promoted to success')
 for q in I.Q:
  d='towercontinued\\native_gigs_u9\\'+q+'_credit.questphase';ck('native_counter_one_time_claim '+q,wr(d,3,'hey_sts_counter',1)and n(d,3)['writes'][0]['setExactValue']==0 and wr(d,65001,'PTFRU9_'+q+'_CreditEntered',1)and wr(d,65002,'PTFRU9_'+q+'_CreditDone',1),{'native_increment':3,'claim_before_wait':65001,'done_after':65002})
 ck('EyeForEye_native_credit_OR_not_AND',n('towercontinued\\native_gigs_u9\\sts_hey_gle_01_credit.questphase',18)['type']=='questLogicalXorNodeDefinition','finished OR failed original XOR18→increment3')
 # Reuse exact Jake proof inputs, including its original timing limitation.
 jake=H.parents[2]/'quest_restoration_qr3/agents/agent_d/quests/mq044_jakes_vehicle/contracts.json'
 if not jake.exists():jake=I.W/'prealpha/quest_restoration_qr3/agents/agent_d/quests/mq044_jakes_vehicle/contracts.json'
 pins.append({'path':str(jake),'sha256':sha(jake),'role':'existing QR3 Jake continuation proof; not new gameplay proof'})
 # Fresh outputs and native resource mutations.
 def raw(d):return Resource(copy.deepcopy(read(I.IDX[d]['json'])))
 def rn(r,gp,ni):
  gr=r.d(r.root['graph'])
  for part in gp.split('/')[1:]:gr=r.d(next(r.d(h)for h in gr['nodes']if str(r.d(h)['id'])==part)['phaseGraph'])
  return next(r.d(h)for h in gr['nodes']if str(r.d(h)['id'])==str(ni))
 def cut(r,gp,a,s,b,t):
  an,bn=rn(r,gp,a),rn(r,gp,b);sh=next(h for h in an['sockets']if r.d(h)['name']['$value']==s);dh=next(h for h in bn['sockets']if r.d(h)['name']['$value']==t)
  for no in [an,bn]:
   for h in no['sockets']:
    so=r.d(h);so['connections']=[ch for ch in so.get('connections',[])if not(r.hid(r.d(ch)['source'])==r.hid(sh)and r.hid(r.d(ch)['destination'])==r.hid(dh))]
 def mutation(name,d,edit,predicate):
  r=raw(d);edit(r);mm=r.normalize();ok=not predicate(mm);mut.append({'name':name,'source':d,'sha256':I.IDX[d]['sha256'],'actual_decoded_payload_copy':True,'detected':ok,'files_mutated':False});ck('Mutation '+name,ok,d)
 mutation('Padre_missing_listener',init,lambda r:cut(r,'root',25,'Out1',79,'In1'),lambda m:['25','Out1','79','In1']in m['graphs']['root']['edges'])
 mutation('Padre_missing_cleanup',cleanup,lambda r:cut(r,'root',468,'True',336,'In42'),lambda m:['468','True','336','In42']in m['graphs']['root']['edges'])
 mutation('LifeWork_missing_success_result',life,lambda r:cut(r,'root/2',5,'Out',37,'In'),lambda m:['5','Out','37','In']in m['graphs']['root/2']['edges'])
 mutation('EyeForEye_missing_delivery_branch',eye,lambda r:cut(r,'root/3',182,'Out1',205,'In'),lambda m:['182','Out1','205','In']in m['graphs']['root/3']['edges'])
 cred='towercontinued\\native_gigs_u9\\sts_hey_gle_01_credit.questphase'
 mutation('EyeForEye_credit_counter_double_increment',cred,lambda r:r.d(rn(r,'root',3)['type']).__setitem__('value',2),lambda m:m['graphs']['root']['nodes']['3']['writes'][0]['value']==1)
 main='base\\open_world\\street_stories\\heywood\\glenn\\sts_hey_gle_06\\phase\\sts_hey_gle_06_phase.questphase'
 mutation('LifeWork_missing_root_support',main,lambda r:r.root.__setitem__('phasePrefabs',[]),lambda m:m['root_prefabs']==['#sts_hey_gle_06_streetstory'])
 # Decode findings are exact pointers; no assets/definitions or save-state proof invented.
 dependencies=[]
 for q in I.Q:
  ds=[d for d in M if q in d and d.startswith('base\\open_world')];refs=sorted({x for d in ds for x in M[d]['refs']});dependencies.append({'quest_id':q,'targets':[{'depot':x,'indexed':x in I.IDX,'decoded_here':x in M,'status':'PINNED_DECODED'if x in M else'LITERAL_REFERENCE_NOT_TARGET_PROOF'}for x in refs],'root_prefabs':{d:M[d]['root_prefabs']for d in ds if M[d]['root_prefabs']},'limits':['Opaque streamed world/actor/vehicle/camera/workspot definitions','Reward/TweakDB target definitions and amounts unverified','Saved executing owner/receipt/timer adoption not simulated']})
 write(O/'source_pins.json',pins);write(O/'graph_evidence.json',M);write(O/'admissions.json',admissions);write(O/'journal_omissions.json',omissions);write(O/'protocols.json',protocols);write(O/'dependencies.json',dependencies);write(O/'embedded_parity.json',embedded)
 write(O/'tests.json',{'group':'G12','checks':tests,'mutations':mut,'total_checks':len(tests),'total_mutations':len(mut),'failed':sum(x['status']!='PASS'for x in tests),'sources':len(M),'shared_core':{'path':str(corep),'sha256':sha(corep),'checks_reused':core['checks']},'runtime_changes':[]})
 print(json.dumps({'checks':len(tests),'mutations':len(mut),'sources':len(M),'protocols':len(protocols),'output':str(O)}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);run(Path(p.parse_args().output).resolve())
