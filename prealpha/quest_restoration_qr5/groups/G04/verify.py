"""QR5 Muamar Arroyo source contracts; writes evidence only below --out."""
import sys,copy,json,argparse
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import source_inputs as I
from verify_core import path
from common import read,write,sha,walk
from model import Resource,compare_graph,digest
def ext(x):
 if isinstance(x,list):return [ext(v)for v in x]
 if isinstance(x,dict):
  o={k:ext(v)for k,v in x.items()}
  if 'DepotPath'in o and o.get('Flags')=='Embedded':o['Flags']='Soft'
  if o.get('$type')=='questQuestPhaseResource'and o.get('cookingPlatform')=='PLATFORM_None':o['cookingPlatform']='PLATFORM_PC'
  return o
 return x
def ev(c,f):
 t=c['$type']
 if t=='questLogicalCondition':
  r=[ev(x,f)for x in c['conditions']];return all(r)if c['operation']=='AND'else any(r)if c['operation']=='OR'else not any(r)if c['operation']=='NOR'else False
 if t=='questFactsDBCondition':return ev(c['type'],f)
 if t=='questVarComparison_ConditionType':
  if c['factName']not in f:return False
  a,b=f[c['factName']],c['value'];return {'Equal':a==b,'NotEqual':a!=b,'Greater':a>b,'GreaterOrEqual':a>=b,'Less':a<b,'LessOrEqual':a<=b}[c['comparisonType']]
 raise ValueError(t)
def run(O):
 assert not O.exists();M={};pins=[];tests=[];mut=[]
 def ck(name,ok,evidence):tests.append({'name':name,'status':'PASS'if ok else'FAIL','evidence':evidence});assert ok,name
 for d in I.selected():
  m,p=I.load(d);M[d]=m;pins.append(p);ck('source_pin '+d,True,p);ck('graph_integrity '+d,not m['errors'],m['errors'])
 def g(d,gp='root'):return M[d]['graphs'][gp]
 def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
 def e(d,a,s,b,t,gp='root'):return [str(a),s,str(b),t]in g(d,gp)['edges']
 def wr(d,i,f,v,gp='root'):return any(x.get('factName')==f and x.get('value')==v for x in n(d,i,gp)['writes'])
 def find(tail):return next(d for d in M if d.endswith('\\'+tail))
 cp=H/'shared_core.json';core=read(cp);ck('Muamar_core_frozen',sha(cp)=='E18670F1292E0AB60C325EFCA7151F46107E79B58769E9C6B4DAE7BA985142AC'and sha(core['tests'])==core['tests_sha256']and sha(core['source_pins'])==core['source_pins_sha256'],{'path':str(cp),'sha256':sha(cp),'checks':core['checks']})
 bodies=[]
 for d in [d for d in M if d.startswith('recipe:')]:
  for item in M[d]['embedded_files']:
   nd=item['depot']
   if nd not in M or not any(q in nd for q in I.Q):continue
   pre=item['graph_prefix']+'/root';graphs={'root'+gp[len(pre):]:gr for gp,gr in M[d]['graphs'].items()if gp==pre or gp.startswith(pre+'/')};orig={'graphs':graphs,'metadata':item['metadata'],'metadata_sha256':digest(item['metadata'])};adapt=ext(copy.deepcopy(orig));adapt['metadata_sha256']=digest(adapt['metadata'])
   ck('embedded_body_native_semantics '+nd,not compare_graph(adapt,M[nd]),{'original':d,'prefix':pre,'allowed_envelope':['Embedded→Soft handles','cookingPlatform None→PC'],'root_prefabs':item['root_prefabs']});bodies.append({'depot':nd,'donor':d,'prefix':pre,'allowed_envelope':['Embedded→Soft','None→PC'],'differences_before_envelope':compare_graph(orig,M[nd]),'differences_after_envelope':compare_graph(adapt,M[nd]),'root_prefabs':item['root_prefabs']})
 for r in I.RECIPES:
  cur=r['depot'];don='recipe:'+r['raw'];gp=r['graph'];cg='root/10'if r['id']=='sts_std_arr_12'else'root'
  for ni in r['ids']:
   if ni==0:continue
   ck('recipe_payload '+cur+':'+str(ni),n(cur,ni,cg)['payload']==ext(n(don,ni,gp)['payload']),{'donor':don,'graph':gp,'node':ni})
   pre=cg+'/'+str(ni);np=gp+'/'+str(ni)
   for child,gr in M[cur]['graphs'].items():
    if child==pre or child.startswith(pre+'/'):ck('recipe_nested '+cur+child,gr==g(don,np+child[len(pre):]),{'native':np+child[len(pre):]})
  ck('recipe_exact_edges '+cur,g(cur,cg)['edges']==sorted([[str(a),s,str(b),t]for a,s,b,t in r['edges']]),r['edges'])
 script=I.C/'package/r6/scripts/PTFR_Consolidated/PTFR_ActivityStateR3.reds';s=script.read_text(encoding='utf8');pins.append({'path':str(script),'sha256':sha(script)});cl=s[s.index('class NativeGigDataU9'):];line=next(x for x in cl.splitlines()if'func IDs()'in x);ids=json.loads(line[line.index('['):line.rindex(']')+1])
 def array(method,i):
  b=cl[cl.index('public static func '+method+'('):];b=b[:b.index('\n  public static func',1)];l=next(x for x in b.splitlines()if'if i=='+str(i)+' 'in x);return json.loads(l[l.index('['):l.rindex(']')+1])
 admission=[];inventory={};protocol=[]
 for q in I.Q:
  i=ids.index(q);data={k:array(k,i)for k in ['Paths','Classes','Facts','TerminalFacts']};entry='towercontinued\\native_gigs_u9\\'+q+'_entry.questphase';gp='root/10'if q.endswith('_12')else'root';node=n(entry,65002,gp);cond=node['payload']['condition'];fs={x['factName']:x['value']for x in node['reads']if'factName'in x};ck('actual_guard_positive '+q,ev(cond,fs),fs)
  for fact,value in [('q307_done',0),('q307_finished',0),('PTFRU9_Support_Issued',0),('PTFRU9_'+q+'_ParentEntered',1),('PTFRU9_'+q+'_Fault',1),('PTFRU7_Support_Issued',1),('PTFRU6_Padre_Issued',1)]:ck('actual_guard_reject '+q+fact,not ev(cond,fs|{fact:value}),{'fact':fact,'value':value})
  factrows={};jp={};rows=[];prefix=q.replace('sts_std_','')
  for d,m in M.items():
   if not d.startswith('base\\open_world')or q not in d:continue
   for ng,gr in m['graphs'].items():
    for ni,nd in gr['nodes'].items():
     row={'depot':d,'graph':ng,'node':ni,'type':nd['type'],'payload_sha256':nd['payload_sha256'],'reads':nd['reads'],'writes':nd['writes'],'journal_paths':nd['journal_paths'],'refs':nd['refs'],'prefabs':nd['prefabs'],'node_refs':nd['node_refs'],'incoming':[x for x in gr['edges']if x[2]==ni],'outgoing':[x for x in gr['edges']if x[0]==ni]};rows.append(row)
     for w in nd['writes']:
      if prefix in w['factName']:factrows.setdefault(w['factName'],[]).append(row)
     for x in walk(nd['payload']):
      if x.get('$type')=='gameJournalPath'and x.get('realPath','').startswith('quests/'):
       p=x['realPath'];jp.setdefault(p,[]).append({'depot':d,'graph':ng,'node':ni,'class':x.get('className',{}).get('$value'),'type':nd['type'],'incoming':row['incoming']})
  omittedfacts={f:r for f,r in factrows.items()if f not in data['Facts']};omittedpaths={p:r for p,r in jp.items()if p not in data['Paths']};admission.append({'quest_id':q,'index':i,**data,'guard':cond,'positive_fixture':fs,'all_local_writers':factrows,'omitted_native_facts':omittedfacts,'omitted_native_journal':omittedpaths});inventory[q]=rows
  missing={f for f in factrows if f.startswith(prefix+'_')and f not in data['Facts']};expected={'arr_12_fail_loop_start'}if q=='sts_std_arr_12'else set();ck('exact_local_fact_guard_coverage '+q,missing==expected,{'missing_local_progress_facts':sorted(missing),'omitted_other_namespace':list(omittedfacts),'paths_omitted':list(omittedpaths),'limit':'Coverage assertion does not approve omitted facts. arr12_fail_loop_start is an original retired bugfix writer; ownership and saved provenance remain conditional. Local # and DLC facts separately retained in admission evidence.'})
  for d,m in M.items():
   if q not in d or not d.endswith('.scene'):continue
   gr=g(d,'scene')
   for ni,nd in gr['nodes'].items():
    for w in nd['writes']:
     if not(w['factName'].startswith(('holo_muamar_','audio_pedro_aimar_'))and w['factName'].endswith('_activate')and w['value']==1):continue
     done=w['factName'][:-9].replace('audio_','holo_')+'_done';entries=list(gr['entries'].values());waits=[a for a,x in gr['nodes'].items()if any(z.get('factName')==done for z in x['reads'])and(any(path(gr,en,a)for en in entries))];clear=[a for a,x in gr['nodes'].items()if any(z.get('factName')==done and z.get('value')==0 for z in x['writes'])and any(path(gr,wa,a)for wa in waits)];direct=[a for a in waits if path(gr,ni,a)];forks=[a for a in gr['nodes']if len([z for z in gr['edges']if z[0]==a])>1 and path(gr,a,ni)and any(path(gr,a,wa)for wa in waits)]
     ck('caller_real_wait_clear '+d+ni,bool(waits)and bool(clear)and(bool(direct)or bool(forks)),{'request':ni,'fact':w['factName'],'waits':waits,'clears':clear,'direct_waits':direct,'parallel_forks':forks});protocol.append({'depot':d,'producer':ni,'fact':w['factName'],'waits':waits,'clears':clear,'direct_waits':direct,'parallel_forks':forks})
 ck('EntrySafe_policy',all(x in s for x in ['if this.State(paths[k],classes[k])!=1','if this.Fact(a[k])!=0','return poi==1 || poi==2;']),'Inactive listed journals, zero progress; native POI may already be Active')
 # Source-specific progression, outcomes and one-time accounting.
 a10=find('sts_std_arr_10_open_world.questphase');a11=find('sts_std_arr_11_openworld.questphase');a12=find('sts_std_arr_12_ow.questphase')
 cases=[(a10,'root/4',[(124,'Out',185,'In'),(199,'Out',171,'In'),(171,'Out',125,'In1'),(188,'Out',125,'In2')]),(a10,'root/17',[(59,'End 0',39,'In'),(59,'rejected_out',91,'Active'),(91,'Out',39,'In'),(39,'Out',40,'In'),(40,'Out',60,'In'),(60,'Out',41,'In')]),(a11,'root/2',[(73,'Out',5,'Succeeded'),(5,'Out',55,'In'),(74,'Out',70,'Active'),(74,'CutSource',73,'CutDestination'),(89,'Out',91,'Succeeded'),(91,'Out',92,'In'),(92,'Out',95,'In'),(128,'Out',191,'In'),(191,'Out',129,'Succeeded')]),(a12,'root/5',[(14,'success',18,'In'),(14,'fail',23,'In2'),(45,'False',43,'Active'),(45,'True',46,'In'),(46,'True',47,'Active'),(46,'False',48,'Active'),(47,'Out',18,'In'),(48,'Out',18,'In'),(43,'Out',23,'In3'),(18,'Out',23,'In1'),(23,'Out1',40,'In1'),(40,'Out1',19,'In'),(69,'Out',13,'In'),(13,'Out',36,'In'),(36,'Out',1,'In')])]
 for d,gp,edges in cases:
  for edge in edges:ck('native_outcome_edge '+d+gp+str(edge),e(d,*edge,gp),edge)
 for d,gp,ni,q in [(a10,'root/17',39,'sts_std_arr_10'),(a11,'root/2',55,'sts_std_arr_11'),(a11,'root/2',92,'sts_std_arr_11'),(a12,'root/5',18,'sts_std_arr_12')]:ck('exact_native_reward '+q+str(ni),'QuestRewards.'+q+'_completion'in str(n(d,ni,gp)['payload']),{'depot':d,'graph':gp,'node':ni})
 ck('arr10_native_send_receipt',wr(a10,171,'arr_10_data_sended',1,'root/4')and n(a10,125,'root/4')['type']=='questLogicalAndNodeDefinition','download/send and leave are joined, no fabricated send completion')
 ck('arr11_branch_exclusion',n(a11,74,'root/2')['type']=='questCutControlNodeDefinition'and n(a11,73,'root/2')['type']=='questPauseConditionNodeDefinition',n(a11,73,'root/2')['payload'])
 ck('arr12_native_success_fail_predicates',n(a12,45,'root/5')['reads'][0]['factName']=='dlc_sts_std_arr_12_failed'and n(a12,46,'root/5')['reads'][0]['factName']=='arr_12_2nd_enemy','failed cannot traverse SMS reward branch; delay selects native SMS variant')
 for q in ['sts_std_arr_10','sts_std_arr_11']:
  cr='towercontinued\\native_gigs_u9\\'+q+'_credit.questphase';ck('counter_once_guard '+q,any(x.get('factName')=='PTFRU9_'+q+'_CreditEntered'and x.get('value')==0 for x in n(cr,65000)['reads'])and wr(cr,13,'std_sts_counter',1),n(cr,65000)['payload'])
 ck('arr12_no_invented_credit_recipe',not any(r['id']=='sts_std_arr_12'and r['kind']!='entry'for r in I.RECIPES),'DLC native ownership, no copied district counter/map owner added')
 # Exact Pedro listener and PH1 enrollment barrier, kept separate from Muamar.
 ph=I.EXTRA[3];pc=I.EXTRA[1];ps=I.EXTRA[2];cln='towercontinued\\gig_phone_u9\\fixer_cleanup.questphase'
 ck('Pedro_PH1_issued_before_native_body',wr(ph,4,'PTFRPH1_pedro_aimar_Issued',1)and any(I.EXTRA[1]in nd['refs']for nd in g(ph)['nodes'].values())and any(x.get('factName')=='PTFRPH1_pedro_aimar_Issued'and x.get('value')==1 for x in n('towercontinued\\native_gigs_u9\\sts_std_arr_12_entry.questphase',64999)['reads']),'outer native body wait64999 observes PH1 live listener receipt; no fake call ACK')
 ck('Pedro_native_start_end_audio_consumers',e(pc,12,'Out',33,'audio_pedro_aimar_calls_v_start')and e(pc,13,'Out',33,'audio_pedro_aimar_calls_v_end')and wr(ps,36,'holo_pedro_aimar_calls_v_start_done',1,'scene')and wr(ps,38,'holo_pedro_aimar_calls_v_end_done',1,'scene'),'audio producers use original holo-named ACK fields')
 ck('Pedro_owned_cleanup',n(cln,1411)['refs']==[I.EXTRA[0]],'current U9 cleanup owns native Pedro cleanup1411')
 # Save raw-copy faults, then normalize independently and require source oracle to fail.
 for label,d,gp,ni,fact in [('entry_prerequisite', 'towercontinued\\native_gigs_u9\\sts_std_arr_10_entry.questphase','root',65002,'q307_done'),('native_reward',a11,'root/2',92,'QuestRewards.sts_std_arr_11_completion'),('delayed_success',a12,'root/5',46,'arr_12_2nd_enemy')]:
  raw=copy.deepcopy(read(next(p['json']for p in pins if p.get('depot')==d)));r=Resource(raw);changed=0
  for x in walk(raw):
   if label=='native_reward'and x.get('$type')=='TweakDBID'and x.get('$value')==fact:x['$value']='QuestRewards.deliberately_missing_QR5';changed+=1
   elif label!='native_reward'and x.get('factName')==fact:x['value']=987654;changed+=1
  mm=r.normalize();caught=mm['graphs'][gp]['nodes'][str(ni)]['payload']!=n(d,ni,gp)['payload'];ck('mutation_raw '+label,changed>0 and caught,{'changed_fields':changed,'depot':d,'graph':gp,'node':ni});p=O/'mutations'/str(label+'.json');write(p,raw);mut.append({'fault':label,'path':str(p),'caught':caught,'sha256':sha(p)})
 write(O/'tests.json',tests);write(O/'source_pins.json',pins);write(O/'admission.json',admission);write(O/'handler_inventory.json',inventory);write(O/'protocols.json',protocol);write(O/'embedded_bodies.json',bodies);write(O/'mutations.json',mut);write(O/'summary.json',{'status':'PASS_BOUNDED_SOURCE_CHECKS_WITH_EXPLICIT_LIMITS','checks':len(tests),'resources':len(M),'mutations':len(mut),'quests':I.Q,'shared_core_sha256':sha(cp)})
 print({'checks':len(tests),'resources':len(M),'mutations':len(mut),'out':str(O)})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);run(Path(p.parse_args().out))
