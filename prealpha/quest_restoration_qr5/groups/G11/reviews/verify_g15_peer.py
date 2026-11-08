"""Independent bounded G15 peer review; no import of the reviewed verifier."""
from pathlib import Path
import argparse,sys,json,copy,re,zlib,gzip
H=Path(__file__).resolve().parent;W=H.parents[4];F=W/'prealpha/quest_restoration_qr5'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value
from model import Resource

def run(O):
 assert not O.exists();O.mkdir(parents=True);T=[];P=[];M={};R={}
 def ck(k,v,e):
  T.append({'name':k,'status':'PASS'if v else'FAIL','evidence':e})
  if not v:write(O/'failed.json',T);raise AssertionError(k)
 def node(m,i,g='root'):return m['graphs'][g]['nodes'][str(i)]
 def edge(m,a,s,b,t,g='root'):return [str(a),s,str(b),t]in m['graphs'][g]['edges']
 def fact(m,i,f,v,g='root',kind='reads'):return any(x.get('factName')==f and x.get('value')==v for x in node(m,i,g)[kind])
 result=F/'groups/G15/results.json';d=read(result);ck('frozen reviewed results',sha(result)=='CCA93EEE4F647D4070337652A8CEDF281F790D9C7416AA05E26A0DA2501A4DA5',str(result));P.append({'path':str(result),'sha256':sha(result)})
 q=d['quest_results'][0];C=read(q['contracts']);ck('frozen ten-contract source',sha(q['contracts'])==q['contracts_sha256']=='8297A10B6341BF99E01154CAF6760999301D31C566C1ED67C34244700632AA1F',q);P.append({'path':q['contracts'],'sha256':sha(q['contracts'])})
 ck('all ten exact contract keys',set(C['contracts'])=={'entry','eligibility','communications','ownership','progression','presentation','journal','completion_rewards_cleanup','persistence','shared_dependencies'},list(C['contracts']))
 ck('epoch00 four owner-contract failures retained',{k for k,v in C['contracts'].items()if v['status']=='FAIL'}=={'ownership','progression','completion_rewards_cleanup','shared_dependencies'},C['contracts'])
 for name,row in C['contracts'].items():ck('specific evidence links '+name,bool(row['proven'])and all(Path(x).is_file()for x in row['evidence']),row['evidence'])
 for p in read(F/'reviews/worker_a/STEVEN_serialized/readback_01/manifest.json'):
  ck('actual raw/readback pin '+p['name'],sha(p['binary'])==p['sha256']and sha(p['json'])==p['json_sha256'],p);P.append(p);R[p['name']]=read(p['json']);M[p['name']]=Resource(R[p['name']]).normalize();ck('decode '+p['name'],not M[p['name']]['errors'],M[p['name']]['errors'])
 s=M['native_7'];cl=M['native_1'];a=M['native_3'];sc=M['native_4'];b=M['before'];af=M['after'];gp='root/3'
 # Actual guard semantics and exact current script registry rather than finding fact occurrences only.
 for ni in [2,3,90]:
  for f in ['sts_ep1_08_biomonitor_ana','steven_santos_default_on','PTFRU9_sts_ep1_08_ParentEntered','PTFRU9_sts_ep1_08_Started']:
   ck('historical S23 refuses new U9 '+str(ni)+'/'+f,fact(s,ni,f,0),node(s,ni)['payload_sha256'])
  js=[x for x in node(s,ni)['reads']if x['$type']=='questJournalEntryState_ConditionType'];ck('all seven histories inactive '+str(ni),len(js)==7 and all(x['state']=='Inactive'for x in js),js)
  ck('native positive finished range '+str(ni),{(x['comparisonType'],x['value'])for x in node(s,ni)['reads']if x.get('factName')=='sts_ep1_08_finished'}=={('GreaterOrEqual',1),('LessOrEqual',2147483647)},'positive genuine history; absent ordinary scalar reads0')
 E=read(F/'source_epoch_00.json');candidate=Path(E['candidate']);red=candidate/'package/r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds';xl=candidate/'package/archive/pc/mod/zzzz_PTFR_Combined.archive.xl'
 for f in [red,xl]:
  rel=f.relative_to(candidate/'package').as_posix();pin=next(x['sha256']for x in E['package_files']if x['path']==rel);ck('effective current package '+rel,sha(f)==pin,pin);P.append({'path':str(f),'sha256':pin})
 text=red.read_text(encoding='utf-8-sig')
 def arr(name):return json.loads(re.search(r'func '+name+r'\(\).*?return (\[.*?\]);',text).group(1))
 expected=[x for x in node(s,3)['reads']if x['$type']=='questJournalEntryState_ConditionType']
 ck('script exact journal path/class registry',list(zip(arr('Paths21'),arr('Classes21')))==[(x['path']['realPath'],value(x['path']['className']))for x in expected],expected)
 ck('script known inactive values',arr('StatesA21')==arr('StatesB21')==[1]*7,'missing JournalManager entry returns-1 and validity checks refuse')
 ck('script exact range registry',list(zip(arr('FactNames21'),arr('FactMin21'),arr('FactMax21')))==[('sts_ep1_08_biomonitor_ana',0,0),('steven_santos_default_on',0,0),('PTFRU9_sts_ep1_08_ParentEntered',0,0),('PTFRU9_sts_ep1_08_Started',0,0),('sts_ep1_08_finished',1,2147483647)],'not synthetic pre-Tower evidence')
 ck('settled journal samples refuse unknown',all(x in text for x in ['EnumInt(jm.GetEntryState(entry)) : -1','if jm.HasAnyDelayedStateChanges()','if !a.valid || !b.valid']),str(red))
 ck('true root registration outside retired subtree',re.search(r'path: towercontinued\\sidejobs_s23\\ep1\\steven_boot.questphase\s+parent: ep1\\quest\\ep1.quest\s+input:\s+node: \[1\]\s+socket: Out',xl.read_text())is not None,str(xl))
 for e in [(3,'True',4,'In'),(4,'Out',89,'In'),(89,'Out',90,'In'),(90,'True',92,'In'),(92,'Out',100,'In1'),(92,'Out',102,'In'),(102,'Out',101,'In')]:ck('saved receipt/finish route '+str(e),edge(s,*e),e)
 ck('finish observes genuine journal',node(s,102)['reads'][0]['state']=='Succeeded'and fact(s,101,'PTFRS23_STEVEN_Finished',1,kind='writes'),'private receipt only after real native root success')
 # This is the native SMS+visited protocol, distinct from phone calls and distinct from the new actor helper.
 for i,nd in s['graphs']['root/100/501']['nodes'].items():ck('exact retained native message payload '+i,nd==node(cl,i,gp),nd['payload_sha256'])
 for e in [(3,'False',5,'In'),(5,'Out',91,'In'),(91,'True',92,'In'),(91,'False',93,'In'),(92,'Out',94,'In1'),(93,'Out',94,'In2'),(94,'Out1',95,'In'),(95,'Out',56,'In'),(56,'Out',8,'In'),(8,'Out',39,'Active'),(8,'Out',58,'Active'),(58,'Out',96,'Active'),(96,'Out',17,'In'),(17,'Out',59,'Succeeded'),(59,'Out',9,'Active'),(9,'Out',2,'In'),(39,'Out',37,'In'),(37,'Out',38,'In'),(39,'Out',64,'In'),(64,'Out',65,'In')]:ck('native message/journal route '+str(e),edge(cl,*e,gp),e)
 ck('66 game hours retained',node(cl,5,gp)['payload']['condition']['type']['hours']==66,node(cl,5,gp)['payload'])
 ck('genuine invitation and both responses',all(node(cl,i,gp)['sms']for i in [8,38,65]),[node(cl,i,gp)['journal_paths']for i in [8,38,65]])
 ck('actual visited acknowledgement',node(cl,17,gp)['payload']['condition']['type']['visited']==1,'not fabricated phone ACK')
 ck('default signal after native visited path',fact(cl,2,'steven_santos_default_on',1,gp,'writes'),'same native downstream default signal')
 # Actual actor route and terminal resource lifetime, not source-presence inference.
 ck('Ana0 selects Night City',edge(a,2,'False',5,'In')and edge(a,2,'False',26,'In')and node(a,2)['reads']==[{'$type':'questVarComparison_ConditionType','comparisonType':'Greater','factName':'sts_ep1_08_biomonitor_ana','value':0}],node(a,2)['payload'])
 for e in [(3,'End 2',13,'In'),(13,'Out',15,'Succeeded'),(15,'Out',16,'Succeeded'),(16,'Out',33,'In'),(33,'Out',30,'In'),(30,'Out',12,'In'),(12,'Out',7,'In'),(7,'Out',14,'In'),(14,'Out',23,'In'),(23,'Out',27,'In')]:ck('native completion/cleanup route '+str(e),edge(a,*e,'root/28'),e)
 ck('real default-off and contact cleanup',fact(a,14,'steven_santos_default_on',0,'root/28','writes')and node(a,23,'root/28')['payload']['type']['params'][0]['addContact']==0,'authored cleanup preserved')
 ck('native escape OR default-off terminates actor',node(a,30)['payload']['condition']['operation']=='OR'and edge(a,30,'Out',32,'In')and edge(a,32,'False',31,'In')and edge(a,31,'Out',1,'In'),'scene/controller engine lifetime remains live-only')
 ck('real scene reward payload/edge',node(sc,191,'scene')['payload']['questNode']['type']['rewards'][0]['$value']=='177079350664'and edge(sc,238,'0:0',191,'0:1','scene'),'QuestRewards.sts_ep1_08_steven_nc_meeting')
 stock=F/'shared/tdb_applicability_02/sts_ep1_08_steven_meeting_night_city.json';rw=next(x for x in read(stock)['targets']if x['id']=='177079350664');ck('stock reward definition independently applicable',rw['exists_in_stock']and rw['requested_aliases']==['QuestRewards.sts_ep1_08_steven_nc_meeting'],rw);P.append({'path':str(stock),'sha256':sha(stock)})
 ck('actual communities and world obligations', '#steven_default_night_city_com'in node(a,5)['node_refs']and '#steve_default_night_city_vehicle_forbidden_area'in node(a,30,'root/28')['node_refs'],'opaque external placements remain; empty prefabs not world success')
 # Frozen baseline and staged actual serialized source are separate authorities.
 ck('baseline carrier lacks actor consumer',not any('steven_default.questphase'in str(n['refs'])for g in b['graphs'].values()for n in g['nodes'].values()),'baseline four FAILs source-confirmed by earlier independent143 controls')
 ck('actual staged actor-only node set',set(af['graphs']['root/50/1302']['nodes'])=={'0','17','19','1303'}and'root/50/1302/501'not in af['graphs'],'no message/timer/reward clone')
 ck('actual ordered fresh initial guard',edge(af,65003,'Out',1300,'In','root/50')and not any(e[0]=='65003'and e[2]in['10','64001']for e in af['graphs']['root/50']['edges']),'native progress cannot beat Started0 enrollment')
 ck('actual every-dispatch late fence',edge(af,19,'Out',1303,'In','root/50/1302')and edge(af,1303,'Out',17,'In1','root/50/1302')and fact(af,1303,'sts_ep1_08_biomonitor_ana',0,'root/50/1302'),'late choice Ana0 can become1; not merely initial guard')
 for path,h in [(H/'STEVEN/source_verification_02/review.json','F2EFBFFDFF70C320503D8CFC26065D9F330CF9036815718BFEAABF5D9E45B563'),(H/'STEVEN/proposal02_verification_01/review.json','23CE232D1D3DE41174249A2AE1522A407369957BE5DB32793BC6370B190A6F48'),(F/'reviews/worker_a/STEVEN_serialized/verification_02/review.json','6F0442571AC1F922DBCAC22457BAD4226B8EC43AB29D281B403AC56CDE73BF15')]:ck('reuse exact prior scope '+path.parent.name,sha(path)==h,str(path));P.append({'path':str(path),'sha256':h})
 staged=read(d['staged_adjudication']['path']);ck('staged adjudication pinned separately',sha(d['staged_adjudication']['path'])==d['staged_adjudication']['sha256']and all(x['status']!='FAIL'for x in staged['contracts'].values())and d['staged_adjudication']['package_status']=='PENDING_ROOT_FINAL_PACKAGE_GATE',d['staged_adjudication'])
 # Independently verify clarification, not discard a source mismatch by assertion.
 pp=read(F/'groups/G15/contracts_readback_01/manifest.json');p=pp[0]if isinstance(pp,list)else pp;ck('fresh gameplay input pins',sha(p['binary'])==p['sha256']and sha(p['json'])==p['json_sha256'],p);P.append(p);fresh=Resource(read(p['json'])).normalize();mi=read(W/'diagnostics/vanilla_parity_20261029_01/analysis_02/model_inventory.json')[p['depot']];cached=json.loads(gzip.decompress(Path(mi['normalized_model']).read_bytes()));cached.setdefault('embedded_files',[])
 def canon(x):
  x=json.loads(json.dumps(x))
  for z in walk(x):
   z.pop('payload_sha256',None);z.pop('metadata_sha256',None)
   if z.get('$type')=='TweakDBID':
    v=z['$value'];z['$value']=str((len(v.encode('utf-8'))<<32)|zlib.crc32(v.encode('utf-8')))if z['$storage']=='string'else str(int(v));z['$storage']='uint64'
  return x
 ck('gameplay cache exact storage-only equality',sha(mi['normalized_model'])==mi['normalized_sha256']and canon(fresh)==canon(cached),'No NodeRef, graph, condition or edge omitted; only ID numeric identity, derived hashes, tuple/list representation')
 ck('two original gameplay diagnostics retained',len(fresh['errors'])==2 and all(x['kind']=='DANGLING_EDGE'for x in fresh['errors']),fresh['errors'])
 # Fault injection in real decoded source, not generated expected fixtures.
 mutations=[]
 for name,key,predicate,change,oracle in [('lost_default_cleanup','native_3',lambda x:x.get('$type')=='questSetVar_NodeType'and x.get('factName')=='steven_santos_default_on'and x.get('value')==0,lambda x:x.update(value=1),lambda m:fact(m,14,'steven_santos_default_on',0,'root/28','writes')),('visited_false','native_1',lambda x:x.get('$type')=='questJournalEntryVisited_ConditionType',lambda x:x.update(visited=0),lambda m:node(m,17,gp)['payload']['condition']['type']['visited']==1)]:
  raw=copy.deepcopy(R[key]);changed=0
  for x in walk(raw):
   if predicate(x):change(x);changed+=1
  mm=Resource(raw).normalize();ck('actual raw mutation '+name,changed>0 and oracle(M[key])and not oracle(mm),'independent source contract rejects mutation');f=O/'mutations'/str(name+'.json');write(f,raw);mutations.append({'name':name,'path':str(f),'sha256':sha(f),'detected':True})
 write(O/'tests.json',T);write(O/'source_pins.json',P);write(O/'mutations.json',mutations)
 review={'status':'PASS_INDEPENDENT_TEN_CONTRACT_REVIEW_WITH_BASELINE_DEFECT_AND_SEPARATE_STAGING','quest_id':C['quest_id'],'checks':len(T),'mutations':len(mutations),'input_pins':len(P),'baseline_fail_contracts':['ownership','progression','completion_rewards_cleanup','shared_dependencies'],'staged_status':'SOURCE_SERIALIZED_ADJUDICATION_SUPPORTED_PACKAGE_PENDING','reviewed_results_sha256':sha(result),'reviewed_contracts_sha256':sha(q['contracts']),'reused_controls':{'independent_source':143,'ordered_proposal':99,'independent_serialized':140},'limits':['No structural or gameplay blanket PASS.','Native world placement, saved leases, phone UI/read callback, token arbitration, reward child/runtime modifiers and reload stay explicit.','Gameplay representation clarification verified; two native dangling diagnostics remain G19 scope.','No runtime edit, deployment or game/save/fact changes.'],'tests':str(O/'tests.json'),'source_pins':str(O/'source_pins.json')};write(O/'review.json',review);print(json.dumps({'checks':len(T),'mutations':len(mutations),'review_sha256':sha(O/'review.json')}))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();run(Path(a.output).resolve())
