"""Narrow source-confirmed future ARR12 failure-monitor dependency."""
import sys,json,gzip,copy,argparse
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import source_inputs as I
from common import read,write,sha,walk
from model import Resource
from verify_core import path
FACTS=['arr_12_fail_loop_end','dlc_sts_std_arr_12_convoy_destroyed','dlc_sts_std_arr_12_failed_spawn_additional_car','arr_12_fail_loop_start']
def run(O):
 assert not O.exists();tests=[];pins=[];M={}
 def ck(name,ok,evidence):tests.append({'name':name,'status':'PASS'if ok else'FAIL','evidence':evidence});assert ok,name
 for tail in ['sts_std_arr_12_bugfixing.questphase','sts_std_arr_12_ow.questphase','sts_std_arr_12_gpl.questphase','sts_std_arr_12_entry.questphase']:
  d=next(x for x in I.selected()if x.endswith('\\'+tail));M[d],p=I.load(d);pins.append(p)
 for d in ['base\\quest\\bugfixing\\open_world_bugfixing.questphase','base\\open_world\\bugfixing\\sts\\sts_arroyo_bugfixing.questphase']:
  M[d],p=I.load(d);pins.append(p)
 ancestor=I.W/'prealpha/quest_restoration_qr2/ancestor_review.json';a=read(ancestor);pins.append({'path':str(ancestor),'sha256':sha(ancestor),'scope':'existing exact native provider/retirement evidence, rechecked below'})
 for row in a['inputs'][:2]:
  ck('native_ancestor_export_pin '+row['depot'],sha(row['source_json'])==row['json_sha256'],row);M[row['depot']]=Resource(read(row['source_json'])).normalize();pins.append(row)
 def suffix(t):return next(d for d in M if d.endswith('\\'+t))
 def g(d,p='root'):return M[d]['graphs'][p]
 def n(d,i,p='root'):return g(d,p)['nodes'][str(i)]
 def e(d,a,s,b,t,p='root'):return [str(a),s,str(b),t]in g(d,p)['edges']
 bug=suffix('sts_std_arr_12_bugfixing.questphase');ow=suffix('sts_std_arr_12_ow.questphase');entry=suffix('sts_std_arr_12_entry.questphase');main='base\\quest\\cyberpunk2077.questphase';bparent='base\\quest\\bugfixing.questphase';op='base\\quest\\bugfixing\\open_world_bugfixing.questphase';ap='base\\open_world\\bugfixing\\sts\\sts_arroyo_bugfixing.questphase'
 ck('genuine_Tower_terminates_original_parent',e(main,106,'Out',109,'In')and e(main,109,'Out',107,'In')and n(main,107)['payload']['type']=='Terminating'and bparent in n(main,4,'root/82')['refs'],{'route':'root106→109→Terminating107; nestedroot/82:4 holds bugfix tree'})
 ck('native_open_world_bugfix_owner',op in n(bparent,11)['refs']and ap in n(op,43,'root/1')['refs']and bug in n(ap,15)['refs'],{'ancestry':['cyberpunk root/82:4','bugfixing root11','openworld root/1:43','arroyo root15','ARR12 root3']})
 for edge in [(0,'Out',15,'In'),(15,'False',14,'In'),(14,'Out',13,'In'),(13,'Out',4,'In'),(4,'Out',10,'In'),(10,'Out',34,'In2'),(34,'Out1',5,'In'),(5,'Out',8,'In'),(8,'Out',7,'Failed'),(7,'Out',6,'Failed'),(6,'Out',12,'In'),(12,'Out',11,'after_fail_start'),(11,'after_fail_end',9,'In'),(9,'Out',16,'In'),(16,'Out',22,'In')]:ck('native_future_monitor_route '+str(edge),e(bug,*edge,'root/3'),edge)
 ck('native_receipt_is_armed_before_quest_start',n(bug,15,'root/3')['reads'][0]['factName']=='arr_12_fail_loop_start'and n(bug,14,'root/3')['writes'][0]['factName']=='arr_12_fail_loop_start'and n(bug,13,'root/3')['reads'][0]['factName']=='arr_12_start',{'reason':'receipt14 is issued before13 waits for a future actual start; a never-started pre-Tower save can legitimately retain start-receipt1'})
 ck('obsolete_main_health_listener_unreachable',not any(x[2]=='223'for x in g(ow,'root/4')['edges'])and e(ow,223,'Out',352,'In','root/4')and e(ow,352,'Out',351,'In','root/4'),{'node223':n(ow,223,'root/4')['payload'],'node351':n(ow,351,'root/4')['payload'],'incoming223':[]})
 # Independently scan the complete pinned cache, not this worker's selected closure.
 hits=[];modelpins=[]
 for d,row in I.MI.items():
  p=Path(row['normalized_model']);data=gzip.decompress(p.read_bytes())
  if not any(f.encode()in data for f in FACTS):continue
  m=json.loads(data);modelpins.append({'depot':d,'path':str(p),'sha256':sha(p)})
  for gp,gr in m['graphs'].items():
   for ni,nd in gr['nodes'].items():
    reads=[x for x in nd['reads']if x.get('factName')in FACTS];writes=[x for x in nd['writes']if x.get('factName')in FACTS]
    if reads or writes:hits.append({'depot':d,'graph':gp,'node':ni,'reads':reads,'writes':writes,'refs':nd['refs'],'prefabs':nd['prefabs']})
 private=[x for x in hits if x['depot'].startswith('towercontinued\\')];ck('no_private_alternative_failure_writer',not any(x['writes']for x in private),private)
 only=[x for x in hits if any(w.get('factName')=='arr_12_fail_loop_end'and w.get('value')==1 for w in x['writes'])];ck('sole_native_end_writer',len(only)==1 and only[0]['depot']==bug and only[0]['graph']=='root/3'and only[0]['node']=='22',only)
 scripts=[]
 for p in (I.C/'package').rglob('*'):
  if p.is_file()and p.suffix in ['.reds','.lua','.yaml','.yml']:
   txt=p.read_text(encoding='utf8',errors='replace');matches=[f for f in FACTS if f in txt]
   if matches:scripts.append({'path':str(p),'sha256':sha(p),'facts':matches,'lines':[{'line':i,'text':li}for i,li in enumerate(txt.splitlines(),1)if any(f in li for f in FACTS)]})
 # The bounded scan records script mention semantics rather than presuming every mention writes.
 ck('current_private_entry_has_no_original_monitor',all(bug not in nd['refs']for gr in M[entry]['graphs'].values()for nd in gr['nodes'].values())and not any(nd['writes']for gr in M[entry]['graphs'].values()for nd in gr['nodes'].values()if any(w.get('factName')in FACTS for w in nd['writes'])),'current adapter only launches native ARR12 main; no equivalent monitor producer in private adapter')
 rootprefabs={d:{'root':m['root_prefabs'],'nested':[{'graph':gp,'node':ni,'prefabs':nd['prefabs']}for gp,gr in m['graphs'].items()for ni,nd in gr['nodes'].items()if nd['prefabs']]}for d,m in M.items()if d in [bug,op,ap,bparent]}
 write(O/'tests.json',tests);write(O/'source_pins.json',pins);write(O/'global_model_matches.json',hits);write(O/'global_model_pins.json',modelpins);write(O/'script_mentions.json',scripts);write(O/'prefab_scopes.json',rootprefabs)
 evidence={'id':'QR5-G04-ARR12-MISSING-FUTURE-FAILURE-MONITOR','status':'SOURCE_CONFIRMED_DEFECT_PENDING_INDEPENDENT_REPAIR_REVIEW','severity':'HIGH','quest_id':'sts_std_arr_12','defective_candidate':str(I.C),'defect':'Native future convoy-destruction/abandonment monitor retired by genuine Tower; current restored body still relies on its unique failure/end producers. Main alternative health listener223 has no incoming edges.','native_expectation':'Original bugfix root/3 observes future arr_12_start, spawned Convoy and destruction/abandonment, fails objective/root, releases native token, runs native fail scene and writes end1 for GPL/OW cleanup.','specific_counterexample':'Supported fresh restored job starts arr_12_start1, convoy spawns then reaches health0; live main listener223 is never armed and original bugfix monitor was retired. Required unique arr_12_fail_loop_end writer22 is absent from current private ownership. This proves a structural missing route, not an in-game symptom.','repair_constraints':['Do not rehost unfiltered original bugfix resource or reset arr_12_fail_loop_start. It is legitimately set before a never-started quest.','Any repair must enroll only a new verified fresh private owner and preserve exact native monitor branches, native actors, acknowledgements, token source and cleanup.','Root must independently review source and parent lifetime before implementation; old progressed owners/unknown saved receipts defer.'],'tests':str(O/'tests.json'),'tests_sha256':sha(O/'tests.json'),'checks':len(tests),'global_scan_models':len(I.MI),'global_scan_matches':len(hits),'global_scan_limit':'Original audit cached models, with QR5 epoch pin proving only named unrelated four repair-resource changes; no new game provider scan. Current package scripts separately scanned.','affected_contracts':['ownership','progression','completion_rewards_cleanup','shared_dependencies'],'runtime_changes_by_worker':[]}
 write(O/'evidence.json',evidence);print({'checks':len(tests),'models':len(I.MI),'matches':len(hits),'evidence':str(O/'evidence.json')})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);run(Path(p.parse_args().out))
