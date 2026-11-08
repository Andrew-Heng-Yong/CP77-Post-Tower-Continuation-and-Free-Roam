"""Steven's actual followup contracts; preserves root research and consumes pinned fresh readbacks."""
from pathlib import Path
import sys,json,copy,gzip,zlib,argparse,re,collections
H=Path(__file__).resolve().parent;W=H.parents[3];F=H.parents[1]
# Existing coordinator inspect.py has top-level writes; never let it shadow stdlib inspect.
sys.path=[p for p in sys.path if Path(p or '.').resolve()!=H]
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value
from model import Resource,reachable

def run(O):
 assert not O.exists();tests=[];pins=[];R={};M={}
 def ck(k,v,e):
  tests.append({'name':k,'status':'PASS'if v else'FAIL','evidence':e})
  if not v:write(O/'failed_tests.json',tests);raise AssertionError(k)
 def canon(x):
  x=json.loads(json.dumps(x))
  for z in walk(x):
   z.pop('payload_sha256',None);z.pop('metadata_sha256',None)
   if z.get('$type')=='TweakDBID':
    s=z['$value'];v=(len(s.encode())<<32)|zlib.crc32(s.encode())if z['$storage']=='string'else int(s);z['$storage']='uint64';z['$value']=str(v)
  return x
 for p in read(F/'reviews/worker_a/STEVEN_serialized/readback_01/manifest.json'):
  ck('actual raw source pin '+p['name'],sha(p['binary'])==p['sha256']and sha(p['json'])==p['json_sha256'],p);pins.append(p);R[p['name']]=read(p['json']);M[p['name']]=Resource(R[p['name']]).normalize()
  ck('actual decoded graph '+p['name'],not M[p['name']]['errors'],M[p['name']]['errors'])
 b=M['native_7'];c=M['native_1'];a=M['native_3'];s=M['native_4'];before=M['before'];after=M['after'];gp='root/3';bp='root/100/501';ap='root/28'
 def n(m,k,g='root'):return m['graphs'][g]['nodes'][str(k)]
 def edge(m,a,s,b,t,g='root'):return [str(a),s,str(b),t]in m['graphs'][g]['edges']
 def readf(m,k,f,g='root'):return [x for x in n(m,k,g)['reads']if x.get('factName')==f]
 def writef(m,k,f,v,g='root'):return any(x.get('factName')==f and x.get('value')==v for x in n(m,k,g)['writes'])
 # Exact S23 resume seam; original U9 exclusion is deliberate and retained.
 for ni in [2,3,90]:
  for fact in ['sts_ep1_08_biomonitor_ana','steven_santos_default_on','PTFRU9_sts_ep1_08_ParentEntered','PTFRU9_sts_ep1_08_Started']:
   ck('S23 native/history exclusion '+str(ni)+'/'+fact,readf(b,ni,fact)==[{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':fact,'value':0}],n(b,ni)['payload_sha256'])
  ck('S23 exact finished range '+str(ni),{(x['comparisonType'],x['value'])for x in readf(b,ni,'sts_ep1_08_finished')}=={('GreaterOrEqual',1),('LessOrEqual',2147483647)},'not a fabricated pre-Tower completion')
  js=[x for x in n(b,ni)['reads']if x['$type']=='questJournalEntryState_ConditionType'];ck('S23 seven followup Inactive histories '+str(ni),len(js)==7 and all(x['state']=='Inactive'for x in js),js)
 ck('S23 stable claim then two ticks recheck',edge(b,3,'True',4,'In')and edge(b,4,'Out',89,'In')and edge(b,89,'Out',90,'In')and edge(b,90,'True',92,'In')and edge(b,92,'Out',100,'In1')and writef(b,4,'PTFRS23_STEVEN_Issued',1),'native owner100 starts only after issued/recheck/entered; missing scalar0 not proof of provenance')
 ck('S23 finish observes genuine root journal',edge(b,92,'Out',102,'In')and edge(b,102,'Out',101,'In')and n(b,102)['reads'][0]['state']=='Succeeded'and writef(b,101,'PTFRS23_STEVEN_Finished',1),'no fake root completion')
 # Native message slice is actual retained node/edge subset, preserving timings and independent replies.
 for i,nd in b['graphs'][bp]['nodes'].items():ck('retained native message node '+i,nd==n(c,i,gp),nd['payload_sha256'])
 ck('retained native message edges',b['graphs'][bp]['edges']==[e for e in c['graphs'][gp]['edges']if e[0]in b['graphs'][bp]['nodes']and e[2]in b['graphs'][bp]['nodes']],b['graphs'][bp]['edges'])
 for e in [(3,'False',5,'In'),(5,'Out',91,'In'),(91,'True',92,'In'),(91,'False',93,'In'),(92,'Out',94,'In1'),(93,'Out',94,'In2'),(94,'Out1',95,'In'),(95,'Out',56,'In'),(56,'Out',8,'In'),(8,'Out',39,'Active'),(8,'Out',58,'Active'),(58,'Out',96,'Active'),(96,'Out',17,'In'),(17,'Out',59,'Succeeded'),(59,'Out',9,'Active'),(9,'Out',2,'In'),(39,'Out',37,'In'),(39,'Out',64,'In'),(37,'Out',38,'In'),(64,'Out',65,'In')]:ck('native followup route '+str(e),edge(c,*e,gp),e)
 ck('real66gamehour wait',n(c,5,gp)['payload']['condition']['type']=={'$type':'questGameTimeDelay_ConditionType','days':0,'hours':66,'minutes':0,'seconds':0},n(c,5,gp)['payload'])
 ck('native standalone content token alternatives',n(c,91,gp)['reads'][0]['factName']=='ep1_standalone'and n(c,92,gp)['payload']['condition']['type']['type']=='EP1_Minor'and n(c,93,gp)['payload']['condition']['type']['type']=='MinorQuestAndSts','native token selection not collapsed')
 ck('native wait outside Wellsprings then add contact', '#wellsprings_content_tr'in n(c,95,gp)['node_refs']and n(c,56,gp)['payload']['type']['params'][0]['addContact']==1,n(c,56,gp)['payload'])
 ck('invitation genuine SendMessage and visited acknowledgement',n(c,8,gp)['sms']and n(c,17,gp)['payload']['condition']['type']['$type']=='questJournalEntryVisited_ConditionType'and n(c,17,gp)['payload']['condition']['type']['visited']==1,'native journal phone delivery/visited contract, no synthetic holo ACK')
 ck('default signal only after visited/meeting state',writef(c,2,'steven_santos_default_on',1,gp),n(c,2,gp)['payload'])
 ck('both native response messages',all(n(c,i,gp)['sms']for i in [38,65]),[n(c,i,gp)['journal_paths']for i in [38,65]])
 # Actual actor loop, branch, journal/reward and cleanup; exact external native source is unchanged.
 for i in [17,19]:ck('S23 exact native actor gate '+str(i),n(b,i,'root/100')==n(after,i,'root/50/1302'),n(b,i,'root/100')['payload_sha256'])
 for e in [(2,'False',5,'In'),(2,'False',26,'In'),(26,'Out',28,'In1'),(28,'Out1',26,'In'),(30,'Out',32,'In'),(32,'False',31,'In'),(31,'Out',1,'In')]:ck('native actor loop/shutdown '+str(e),edge(a,*e),e)
 ck('NightCity native community exact','#steven_default_night_city_com'in n(a,5)['node_refs']and value(n(a,5)['payload']['actions'][0]['type']['communityEntryPhaseName'])=='night_city',n(a,5)['payload'])
 for e in [(3,'End 2',13,'In'),(13,'Out',15,'Succeeded'),(15,'Out',16,'Succeeded'),(16,'Out',33,'In'),(33,'Out',30,'In'),(30,'Out',12,'In'),(12,'Out',7,'In'),(7,'Out',14,'In'),(14,'Out',23,'In'),(23,'Out',27,'In')]:ck('native conversation lifecycle '+str(e),edge(a,*e,ap),e)
 ck('root succeeded and default0/contact removal authored',n(a,16,ap)['journal_paths']==['ep1/quests/minor_quest/sts_ep1_08_steven_meeting_night_city']and writef(a,14,'steven_santos_default_on',0,ap)and n(a,23,ap)['payload']['type']['params'][0]['addContact']==0,'never reset to permit replay')
 ck('native prevention+vehicle cleanup',n(a,27,ap)['payload']['event']['enable']==0 and n(a,30,ap)['payload']['type']['activate']==0 and '#steve_default_night_city_vehicle_forbidden_area'in n(a,30,ap)['node_refs'],'source placement remains opaque, actions not removed')
 ck('scene191 real reward retained',n(s,191,'scene')['reward']and n(s,191,'scene')['payload']['questNode']['type']['rewards'][0]['$value']=='177079350664'and['238','0:0','191','0:1']in s['graphs']['scene']['edges'],'actual native QuestRewards.sts_ep1_08_steven_nc_meeting, not private grant')
 stock=F/'shared/tdb_applicability_02/sts_ep1_08_steven_meeting_night_city.json';st=read(stock);rw=[x for x in st['targets']if x['id']=='177079350664'];ck('native scene reward stock definition',len(rw)==1 and rw[0]['exists_in_stock']and rw[0]['requested_aliases']==['QuestRewards.sts_ep1_08_steven_nc_meeting'],rw);pins.append({'path':str(stock),'sha256':sha(stock)})
 ck('native actor and current helper no implicit holo requests',not any(x.get('factName','').startswith(('holo_','audio_'))for mm in [a,s]for g in mm['graphs'].values()for nd in g['nodes'].values()for x in nd['writes']),'followup direct SMS/contact/visited contract; not certified by generic fixer holocall listener')
 # Current package S23/ArchiveXL applicability with exact source epoch hashes.
 E=read(F/'source_epoch_00.json');C=Path(E['candidate']);package=[]
 for rel in ['r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds','archive/pc/mod/zzzz_PTFR_Combined.archive.xl']:
  q=next(x for x in E['package_files']if x['path']==rel);f=C/'package'/rel;ck('effective package source pin '+rel,sha(f)==q['sha256'],q);package.append({'path':str(f),'sha256':sha(f)});pins.append(package[-1])
 red=Path(package[0]['path']).read_text();xl=Path(package[1]['path']).read_text();ck('ArchiveXL true EP1 root attachment',re.search(r'path: towercontinued\\sidejobs_s23\\ep1\\steven_boot.questphase\s+parent: ep1\\quest\\ep1.quest\s+input:\s+node: \[1\]\s+socket: Out',xl)is not None,'scope lives off EP1root1, not inside killed additional defaults')
 ck('current script seven-path data and native guard ranges',all(t in red for t in ['FactNames21()','"PTFRU9_sts_ep1_08_ParentEntered"','"PTFRU9_sts_ep1_08_Started"','FactMax21() -> array<Int32> { return [0, 0, 0, 0, 2147483647]; }','StatesA21() -> array<Int32> { return [1, 1, 1, 1, 1, 1, 1]; }','EnumInt(jm.GetEntryState(entry)) : -1','if jm.HasAnyDelayedStateChanges()','if !a.valid || !b.valid']),'settled journal existence/two matching samples before Permit; no unknown history fabrication')
 # Keep source proof, proposal and actual serialized repair as separate evidence gates.
 approvals=[(H/'steven_gap_01/evidence.json',None),(F/'groups/G11/reviews/STEVEN/source_verification_02/review.json','F2EFBFFDFF70C320503D8CFC26065D9F330CF9036815718BFEAABF5D9E45B563'),(F/'groups/G11/reviews/STEVEN/proposal02_verification_01/review.json','23CE232D1D3DE41174249A2AE1522A407369957BE5DB32793BC6370B190A6F48'),(F/'reviews/worker_a/STEVEN_serialized/verification_02/review.json','6F0442571AC1F922DBCAC22457BAD4226B8EC43AB29D281B403AC56CDE73BF15')]
 for f,h in approvals:ck('frozen independent source/repair evidence '+f.parent.name,h is None or sha(f)==h,str(f));pins.append({'path':str(f),'sha256':sha(f)})
 ck('baseline future owner gap is explicit',not any('steven_default.questphase'in str(x['refs'])for g in before['graphs'].values()for x in g['nodes'].values()),'future U9 Parent/Started/default1 refuses sole old S23; native default owner retires at genuineTower per143-source proof')
 ck('staged helper is actor-only future successor',set(after['graphs']['root/50/1302']['nodes'])=={'0','17','19','1303'}and'root/50/1302/501'not in after['graphs'],'not a baseline PASS, no old-save adoption or SMS/timer restart')
 # Fresh readback resolves cache representation mismatch, preserving two original diagnostics.
 pp=read(H/'contracts_readback_01/manifest.json');p=pp[0]if isinstance(pp,list)else pp;ck('fresh gameplay binary/json pin',sha(p['binary'])==p['sha256']and sha(p['json'])==p['json_sha256'],p);pins.append(p);gm=Resource(read(p['json'])).normalize();MI=read(W/'diagnostics/vanilla_parity_20261029_01/analysis_02/model_inventory.json');mc=MI[p['depot']];cache=json.loads(gzip.decompress(Path(mc['normalized_model']).read_bytes()));cache.setdefault('embedded_files',[])
 ck('gameplay cache hash matches pinned inventory',sha(mc['normalized_model'])==mc['normalized_sha256'],mc);ck('gameplay exact after storage-only normalization',canon(gm)==canon(cache),'TDBID CRC32+UTF8-length numeric identity, derived digests, tuple→JSON list only; no graph/node/edge/condition omitted')
 ck('two native dangling diagnostics retained',len(gm['errors'])==2 and all(x['kind']=='DANGLING_EDGE'and x['graph']=='root'for x in gm['errors']),gm['errors']);write(O/'gameplay_cache_clarification.json',{'status':'CACHE_REPRESENTATION_DISAGREEMENT_RESOLVED_NATIVE_DIAGNOSTICS_RETAINED','source':p,'model_pin':mc,'diagnostics':gm['errors'],'scope':'Native Spy gameplay whole-parity remains G19; no statement of playable branches from these dangling original endpoints. Steven followup body/cleanup/scenes use separate exact resources.'})
 # Raw faults test actual native66h/visited/reward outcomes, independent of the staged actor checker.
 muts=[]
 for name,key,change,oracle in [('changed_66h','native_1',lambda r:[x.update(hours=1)for x in walk(r)if x.get('$type')=='questGameTimeDelay_ConditionType'and x.get('hours')==66],lambda m:n(m,5,gp)['payload']['condition']['type']['hours']==66),('missing_visited_ACK','native_1',lambda r:[x.update(visited=0)for x in walk(r)if x.get('$type')=='questJournalEntryVisited_ConditionType'],lambda m:n(m,17,gp)['payload']['condition']['type']['visited']==1),('wrong_scene_reward','native_4',lambda r:[x.update({'$value':'0'})for x in walk(r)if x.get('$type')=='TweakDBID'and x.get('$value')=='177079350664'],lambda m:n(m,191,'scene')['payload']['questNode']['type']['rewards'][0]['$value']=='177079350664')]:
  r=copy.deepcopy(R[key]);change(r);mm=Resource(r).normalize();ck('actual raw contract mutation '+name,oracle(M[key])and not oracle(mm),name);fp=O/'mutations'/str(name+'.json');write(fp,r);muts.append({'fault':name,'path':str(fp),'sha256':sha(fp),'detected':True})
 write(O/'tests.json',tests);write(O/'source_pins.json',pins);write(O/'mutations.json',muts);write(O/'native_bindings.json',{'root_prefabs':a['root_prefabs'],'actors':s['metadata'].get('actors',[]),'scene_workspots':s['metadata'].get('workspots',[]),'scenes':s['refs'],'relative_NodeRefs':sorted({x for mm in [a,s,c]for g in mm['graphs'].values()for nd in g['nodes'].values()for x in nd['node_refs']}),'limits':'Original world/community/notifier/vehicle/workspot placement and live acquisition remain OPAQUE despite exact source bindings.'})
 result={'status':'PASS_SPECIFIC_CONTRACT_EVIDENCE_WITH_BASELINE_FUTURE_OWNER_DEFECT','checks':len(tests),'mutations':len(muts),'source_count':len(pins),'tests':str(O/'tests.json'),'source_pins':str(O/'source_pins.json'),'staged_serialized_review':str(F/'reviews/worker_a/STEVEN_serialized/verification_02/review.json'),'fully_static_verified':False,'runtime_changes':[],'code':str(Path(__file__).resolve()),'code_sha256':sha(__file__)};write(O/'summary.json',result);print(json.dumps(result))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);run(Path(ap.parse_args().output).resolve())
