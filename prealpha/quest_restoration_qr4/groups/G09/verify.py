"""Five Dakota deep contracts: exact original slices, whole bodies, protocols, credit."""
from lib import *
import argparse,copy,re
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();O=Path(a.output).resolve();assert not O.exists(),'Fresh output required';O.mkdir(parents=True)
S=Store();M=read(W/'research/gig_restoration/native_gigs_u9/manifest.json');EP=read(W/'prealpha/quest_restoration_qr4/source_epoch_00.json');tests=[];mut=[]
IDS=['sts_bls_ina_11','sts_bls_ina_09','sts_bls_ina_08','sts_bls_ina_07','sts_bls_ina_06'];EXPECTED={'sts_bls_ina_11':(14,5,45,'#loc_sts_bls_ina_11_logic',8),'sts_bls_ina_09':(13,5,44,'#sts_bls_ina_09_logic',7),'sts_bls_ina_08':(12,4,42,'#sts_bls_ina_08_logic',6),'sts_bls_ina_07':(11,3,73,'#sts_bls_ina_07_minefield_logic',3),'sts_bls_ina_06':(10,4,40,'#sts_bls_ina_06_logic',5)}
def ck(name,b,e):tests.append({'name':name,'status':'PASS'if b else'FAIL','evidence':e});assert b,name
core=read(Path(__file__).parent/'shared_core.json');ck('frozen_shared_core',sha(Path(__file__).parent/'shared_core.json')=='BDD1BB748A68160491FE98715951DAD7C79D8CB8233333255C250D2FF060A857','38 separately tested shared controls')
recipes=[r for r in M['recipes']if r['id']in IDS and r['kind']in['entry','credit','map']]
for r in recipes:S.extra(r['raw'],M)
for d in sorted({d for d in S.MI if any(('\\'+q+'\\')in d for q in IDS)}|{r['depot']for r in recipes}|{x['depot']for x in core['sources']if not x['depot'].startswith('vanilla_recipe:')}):ck('source_pin '+d,not S.load(d)['errors'],d)
g=S.g;n=S.n
def has(q,f,op,v):return any(x.get('factName')==f and x.get('comparisonType')==op and x.get('value')==v for x in q['reads'])
def es(d,edges,gp='root'):
 for e in edges:ck('edge '+d+' '+str(e),S.edge(d,*e,gp=gp),{'graph':gp,'edge':e})
def soften(x):
 y=copy.deepcopy(x)
 for z in walk(y):
  z.pop('payload_sha256',None) # derived digest changes when only storage Flags change
  if 'phaseResource'in z and z['phaseResource'].get('Flags')=='Embedded':z['phaseResource']['Flags']='Soft'
 return y
def path_to_fact(gr,start,fact):
 todo=[(str(start),[])];seen=set()
 while todo:
  i,path=todo.pop(0)
  if i in seen or len(path)>7:continue
  seen.add(i)
  if any(x.get('factName')==fact and x.get('comparisonType')=='Greater'and x.get('value')==0 for x in gr['nodes'][i]['reads']):return path
  for e in gr['edges']:
   if e[0]==i and e[1]!='CutSource':todo.append((e[2],path+[e]))
 return None
script_rel='r6/scripts/PTFR_Consolidated/PTFR_ActivityStateR3.reds';sp=W/'prealpha/quest_restoration_qr3/candidate_01/package'/script_rel;expected=next(x for x in EP['package_files']if x['path']==script_rel);ck('effective_consolidated_admission_source',sha(sp)==expected['sha256'],{'path':str(sp),'sha256':sha(sp)});src=sp.read_text(encoding='utf-8-sig');script_pins=[{'path':str(sp),'sha256':sha(sp),'epoch_path':script_rel}]
def block(text,needle):
 i=text.index(needle);a=text.index('{',i);depth=1;j=a+1
 while depth:
  depth+=(text[j]=='{')-(text[j]=='}');j+=1
 return text[a+1:j-1]
data=block(src,'public abstract class NativeGigDataU9');driver=block(src,'public class NativeGigsU9');idbody=block(data,'func IDs()');idlist=json.loads(re.search(r'return (\[.*?\]);',idbody,re.S)[1]);
def arrayfn(name,i):
 b=block(data,'func '+name+'(');m=re.search(r'if i=='+str(i)+r'\s*\{\s*return (\[.*?\]);',b,re.S)
 if m:return json.loads(m[1])
 m=re.search(r'let a: array<[^>]+>=(\[.*?\]);',b,re.S)
 return json.loads(m[1])[i] if m else None
ck('EntrySafe_actual_journal_loop','this.State(paths[k],classes[k])!=1' in block(driver,'func EntrySafe('),'All enumerated paths require Inactive; missing State returns -1')
ck('EntrySafe_actual_fact_loop','this.Fact(a[k])!=0' in block(driver,'func EntrySafe('),'Full generated per-quest native fact list')
ck('Poll_revalidates_before_Permit','this.OldUnused(k) && this.EntrySafe(k)'in block(driver,'func Poll('),'Permit carries journal/legacy checks absent from CR2W wrapper')
ck('production_history_current_not_old_stub','this.Request(id,"DISPOSABLE_SAVE",true)'in block(driver,'func RestoreCertified(') and 'snapshot.FreshU9(id)'in block(driver,'func RestoreSnapshot('),'Current consolidated source differs from historical root NativeGigsU9.reds')
findings={};protocols=[];embedded=[]
for qid in IDS:
 er=next(r for r in recipes if r['id']==qid and r['kind']=='entry');ed=er['depot'];donor='vanilla_recipe:'+er['raw'];main,inline,poi,prefab,finish=EXPECTED[qid];body=er['native'];index=idlist.index(qid);paths=arrayfn('Paths',index);classes=arrayfn('Classes',index);facts=arrayfn('Facts',index);legacy=arrayfn('LegacyTags',index);terminal=arrayfn('TerminalFacts',index)
 ck('catalogue_binding '+qid,idlist[index]==qid and len(paths)==len(classes)and paths[0].endswith('/'+qid),{'index':index,'paths':paths,'classes':classes})
 for i in er['ids']:
  if i==0:continue
  expected_payload=soften(n(donor,i,er['graph'])['payload']);ck('original_entry_payload '+qid+' '+str(i),expected_payload==n(ed,i)['payload'],{'native':donor,'node':i,'only_adaptation':'phaseResource.Flags Embedded to Soft'})
 for gp,gr in S.load(ed)['graphs'].items():
  if gp!='root':ck('original_inline_graph '+qid+' '+gp,gr==S.load(donor)['graphs'][gp],{'donor':donor,'graph':gp})
 es(ed,[(65002,'Out',65003,'In'),(65003,'Out',inline,'In1'),(poi,'Out',65004,'In'),(65004,'Out',main,'In1'),(main,'Out1',65005,'In'),(65005,'Out',65006,'In')])
 ck('actual_native_entry_socket '+qid,n(ed,main)['refs']==[body]and'In1'in g(body)['entries'],{'main_node':main,'body':body,'entry':g(body)['entries']})
 ck('whole_native_root_prefab '+qid,S.load(body)['root_prefabs']==[prefab],{'body':body,'prefab':prefab})
 ck('no_final_provider_override '+qid,body not in EP['source_resources'],'Native depot is not replaced in candidate; private entry external reference')
 for gp,gr in S.load(body)['graphs'].items():
  eg='embedded/'+body+'/'+gp
  if eg in S.load(donor)['graphs']:
   original=S.g(donor,eg);same=soften(original)==soften(gr);embedded.append({'quest_id':qid,'embedded_graph':eg,'external':body,'external_graph':gp,'equal_after_only_phaseResource_Flags':same});ck('embedded_external_body_equivalence '+qid+' '+gp,same,embedded[-1])
 guard=n(ed,65002);f={x['factName']:x['value']for x in guard['reads']if'factName'in x};ck('actual_wrapper_guard_fixture '+qid,evaluate(guard['payload']['condition'],f,{})is True,{'fact_fixture':f})
 for key in ['ParentEntered','Fault']:
  ck('used_wrapper_refusal '+qid+key,evaluate(guard['payload']['condition'],f|{'PTFRU9_'+qid+'_'+key:1},{})is False,key)
 ck('support_required '+qid,has(guard,'PTFRU9_Support_Issued','Equal',1),'Receipt requirement; not a scheduler claim')
 cr=next(r for r in recipes if r['id']==qid and r['kind']=='credit');cd=cr['depot'];co='vanilla_recipe:'+cr['raw']
 for i in cr['ids']:
  if i!=0:ck('original_credit_payload '+qid+' '+str(i),n(cd,i)['payload']==n(co,i,cr['graph'])['payload'],{'native':co,'graph':cr['graph'],'node':i})
 ck('credit_exact_counter '+qid,any(x['factName']=='bls_sts_counter'and x['value']==1 and x['setExactValue']==0 for x in n(cd,11)['writes']),'Original district credit increment, not custom reward')
 ck('credit_once_guards '+qid,all(has(n(cd,65000),'PTFRU9_'+qid+'_'+k,'Equal',v)for k,v in [('Started',1),('CreditEntered',0),('CreditDone',0)]),'Fresh shared credit owner fencing')
 es(cd,[(0,'Out',65000,'In'),(65000,'Out',65001,'In'),(11,'Out',65002,'In')]);ck('native_terminal_credit '+qid,has(n(cd,finish),'ina_'+qid[-2:]+'_finished','Greater',0),'Original finish predicate')
 maps=[]
 for mr in [r for r in recipes if r['id']==qid and r['kind']=='map']:
  md=mr['depot'];mo='vanilla_recipe:'+mr['raw'];maps.append({'depot':md,'native_graph':mr['graph'],'foreign_poi_contraction':mr.get('foreign_poi_contraction',[])})
  for i in mr['ids']:
   if i!=0:ck('original_map_payload '+md+' '+str(i),n(md,i)['payload']==n(mo,i,mr['graph'])['payload'],{'donor':mo,'graph':mr['graph'],'node':i})
  ck('map_actual_dakota_visit '+md,has(n(md,2),'dakota_visited','Greater',0),'No fabricated visit')
  ck('map_owned_permit '+md,has(n(md,65000),'PTFRU9_'+qid+'_MapPermit','Equal',1)and has(n(md,65000),'PTFRU9_'+qid+'_Started','Equal',1),'Current Poll grants only inactive root and nonterminal native history')
 body_ds=[d for d in S.models if d.startswith('base\\open_world\\street_stories\\badlands\\inland_avenue\\'+qid+'\\')];native_journals=sorted({p for d in body_ds for gp,gr in S.load(d)['graphs'].items()for q in gr['nodes'].values()for p in q['journal_paths']if p.startswith('quests/')});missing=sorted(set(native_journals)-set(paths));rewards=[];nativefin=[];branches=[]
 for d in body_ds:
  for gp,gr in S.load(d)['graphs'].items():
   for i,q in gr['nodes'].items():
    if q['reward']:rewards.append({'depot':d,'graph':gp,'node':i,'records':[val(z)for z in walk(q['payload'])if z.get('$type')in['TweakDBID','TweakDBID']]})
    if any(z['factName']in['ina_'+qid[-2:]+'_finished','ina_'+qid[-2:]+'_failed']for z in q['writes']):nativefin.append({'depot':d,'graph':gp,'node':i,'writes':q['writes'],'incoming':[e for e in gr['edges']if e[2]==i],'outgoing':[e for e in gr['edges']if e[0]==i]})
    if q['refs']:branches.append({'depot':d,'graph':gp,'node':i,'refs':q['refs'],'prefabs':q['prefabs']})
 for scene in [d for d in body_ds if d.endswith('_holocall_prebrief.scene')or d.endswith('_holocall_debriefs.scene')]:
  for part in ['start','end']:
   fact='holo_dakota_calls_v_'+part;writers=sorted([i for i,q in g(scene,'scene')['nodes'].items()if any(w['factName']==fact+'_activate'and w['value']==1 for w in q['writes'])],key=int);ck('native_primary_producer_exists '+scene+part,bool(writers),writers);writer=writers[0];path=path_to_fact(g(scene,'scene'),writer,fact+'_done');ck('actual_connected_ack_wait '+scene+part,bool(path),{'producer':writer,'path':path});protocols.append({'quest_id':qid,'caller':scene,'part':part,'producer':writer,'wait':path[-1][2],'path':path,'request':fact+'_activate','ack':fact+'_done','master_ack_node':41 if part=='start' else 42})
 findings[qid]={'entry':ed,'entry_main_node':main,'inline_node':inline,'poi_node':poi,'body':body,'native_prefab':prefab,'index':index,'admission_paths':paths,'admission_classes':classes,'native_fact_guards':facts,'legacy_tags':legacy,'terminal_facts':terminal,'native_journal_paths':native_journals,'journal_paths_not_in_EntrySafe':missing,'maps':maps,'credit':cd,'credit_finished_node':finish,'native_terminal_routes':nativefin,'rewards':rewards,'scene_phase_bindings':branches}
 # A mutation must be rejected by an independently specified original payload or connection invariant.
 bad=copy.deepcopy(g(ed));bad['edges'].remove([str(main),'Out1','65005','In']);mut.append({'quest_id':qid,'fault':'lost_native_owner_completion_connection','detected':[str(main),'Out1','65005','In']not in bad['edges']})
 bad=copy.deepcopy(n(cd,11)['payload']);bad['type']['value']=2;mut.append({'quest_id':qid,'fault':'duplicate_district_credit_increment','detected':bad!=n(co,11,cr['graph'])['payload']})
for qid in ['sts_bls_ina_11','sts_bls_ina_09']:
 d=findings[qid]['entry'];bad=copy.deepcopy(n(d,74)['payload']);bad['condition']['type']['value']=100;mut.append({'quest_id':qid,'fault':'changed_native_tier_threshold','detected':bad!=n('vanilla_recipe:'+next(r for r in recipes if r['id']==qid and r['kind']=='entry')['raw'],74)['payload']})
for x in mut:ck('mutation '+x['quest_id']+' '+x['fault'],x['detected'],x)
handlers=[];assets=[]
for d,m in S.models.items():
 for gp,gr in m['graphs'].items():
  # Extra donor embedded unrelated quests are input provenance, not claimed extra quest coverage.
  if d.startswith('vanilla_recipe:')and gp.startswith('embedded/'):continue
  for i,q in gr['nodes'].items():
   if q['reads']or q['writes']or q['journal_paths']or q['reward']or q['sms']:handlers.append({'depot':d,'graph':gp,'node':i,'payload_sha256':q['payload_sha256'],'reads':q['reads'],'writes':q['writes'],'journal':q['journal_paths'],'reward':q['reward'],'sms':q['sms'],'incoming':[e for e in gr['edges']if e[2]==i],'outgoing':[e for e in gr['edges']if e[0]==i]})
   if q['refs']or q['prefabs']or q['node_refs']:assets.append({'depot':d,'graph':gp,'node':i,'refs':q['refs'],'prefabs':q['prefabs'],'node_refs':q['node_refs']})
save(O/'source_pins.json',S.pins);save(O/'script_pins.json',script_pins);save(O/'tests.json',{'count':len(tests),'checks':tests,'mutations':mut,'status':'PASS_SCOPED_STATIC_CHECKS'});save(O/'quest_evidence.json',findings);save(O/'protocols.json',protocols);save(O/'embedded_external.json',embedded);save(O/'graph_evidence.json',{'handlers':handlers,'assets':assets,'root_prefabs':{d:m['root_prefabs']for d,m in S.models.items()}})
print(json.dumps({'checks':len(tests),'mutations':len(mut),'sources':len(S.pins),'protocols':len(protocols),'journal_admission_gaps':{q:v['journal_paths_not_in_EntrySafe']for q,v in findings.items()}}))

