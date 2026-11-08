"""Independent G18 two-quest native/effective review; preserves precise UNKNOWNs and baseline FAILs."""
from pathlib import Path
import sys,json,copy,re,zlib,argparse
H=Path(__file__).resolve().parent;W=H.parents[4];F=W/'prealpha/quest_restoration_qr5';G=F/'groups/G18';sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value
from model import Resource
def run(O):
 assert not O.exists();tests=[];pins=[];M={};R={};mut=[]
 def ck(k,v,e):
  tests.append({'name':k,'status':'PASS'if v else'FAIL','evidence':e})
  if not v:write(O/'failed_tests.json',tests);raise AssertionError(k)
 def canon(x):
  x=json.loads(json.dumps(x))
  for z in walk(x):
   z.pop('payload_sha256',None);z.pop('metadata_sha256',None)
   if z.get('$type')=='TweakDBID':
    t=z['$value'];z['$value']=str((len(t.encode())<<32)|zlib.crc32(t.encode()))if z['$storage']=='string'else str(int(t));z['$storage']='uint64'
  return x
 for p in read(G/'raw_exports_01/manifest.json'):
  ck('frozen raw/sourceJSON pin '+p['depot'],sha(p['raw'])==p['raw_sha256']and sha(p['json'])==p['json_sha256'],p);pins.append(p);R[p['depot']]=read(p['json']);M[p['depot']]=Resource(R[p['depot']]).normalize();ck('actual decode '+p['depot'],not M[p['depot']]['errors'],M[p['depot']]['errors'])
 for p in read(H/'readback_01/manifest.json'):
  ck('independent fresh raw/json '+p['name'],sha(p['binary'])==p['sha256']and sha(p['json'])==p['json_sha256'],p);fresh=read(p['json']);ck('independent fresh semantics '+p['depot'],canon(Resource(fresh).normalize())==canon(M[p['depot']]),'Only TDBID storage/derived digests/tuple-list normalization');R[p['depot']]=fresh;M[p['depot']]=Resource(fresh).normalize();pins.append(p)
 ST=r'ep1\quest\main_quests\q304\phases\q304_slider_stash.questphase';V=r'towercontinued\sidejobs_s23\ep1\voodoo_boot.questphase';CAR=r'ep1\quest\main_quests\q304\phases\q304_car_retrieval.questphase';MSG=r'ep1\quest\main_quests\q304\phases\subphases\q304_car_retrieval_messages.questphase';B=r'towercontinued\sidejobs_s22\moving_heat_boot.questphase';RR=r'towercontinued\sidejobs_s22\moving_heat_resume.questphase';FF=r'towercontinued\sidejobs_s24\ep1\q304_fresh_boot.questphase';PP=r'ep1\quest\ep1_persistent_content.questphase'
 def n(d,k,g='root'):return M[d]['graphs'][g]['nodes'][str(k)]
 def e(d,a,s,b,t,g='root'):return[str(a),s,str(b),t]in M[d]['graphs'][g]['edges']
 # Voodoo direct object/loot quest, genuine original prefab from external full resource.
 ck('Voodoo external original body and PIP retained',n(V,4,'root/100')['refs']==[ST]and M[ST]['root_prefabs']==['#q304_pr_slider_stash_quest'],'unlike accepted car copy, full external stash resource acquires original root scope')
 for ee in [(0,'Out',2,'In'),(2,'Out',3,'In'),(3,'Out',10,'In'),(10,'True',11,'Succeeded'),(11,'Out',12,'In1'),(10,'False',12,'In2'),(12,'Out1',22,'In'),(22,'Out',5,'In'),(5,'Out',13,'In'),(13,'Out',6,'In'),(6,'Out',1,'In'),(0,'Out',14,'In'),(14,'Out',15,'Active'),(15,'Out',17,'Active')]:ck('native stash authored route '+str(ee),e(ST,*ee),ee)
 ck('Voodoo real object/loading and info gates',n(ST,2)['payload']['condition']['$type']=='questNodeLoadingCondition'and n(ST,3)['payload']['condition']['type']['deviceConditionFunction']['$value']=='IsOpen'and n(ST,14)['reads'][0]['factName']=='q304_05_slider_stash_info_downloaded','no forced door/code/info fact')
 ck('Voodoo actual generic hub, no invented dispatch proof',n(ST,12)['type']=='questLogicalHubNodeDefinition'and n(ST,12)['payload']['inputSocketCount']==2,'native type and paths established; exact engine dispatch not inferred as XOR/AND')
 inject=[x for x in walk(canon(n(ST,22)['payload']))if 'itemTDBID'in x and'quantity'in x];ck('Voodoo exact native Inject quantities',{(x['itemTDBID']['$value'],x['quantity'])for x in inject}=={('51369838828',8000),('127255451537',1),('118124605694',1)}and all(x['operationType']=='Inject'for x in inject),inject)
 ck('Voodoo original empty-container completion',n(ST,6)['payload']['condition']['type']['quantity']==0 and n(ST,1)['payload']['type']=='Terminating','not an entitlement/Inject-idempotence proof')
 ck('Voodoo no phone/scene request obligation',not any(x['sms']or x['type']in ['questPhoneManagerNodeDefinition','questSceneNodeDefinition']for g in M[ST]['graphs'].values()for x in g['nodes'].values()),'native authored non-applicability, distinct from q304 main phone')
 ck('original persistent stash caller has no output receipt',n(PP,4,'root/30')['refs']==[ST]and not any(ed[0]=='4'for ed in M[PP]['graphs']['root/30']['edges']),'four journal states alone cannot reconstruct every prior claimed object history')
 # Actual accepted S22 slice and fresh S24 native path, without broad excluded q304 parent replay.
 rroot=M[RR]['graphs']['root'];native=M[CAR]['graphs']['root'];ck('S22 exact retained49 native root identities',len(rroot['nodes'])==49 and all(canon(z)==canon(native['nodes'][i])for i,z in rroot['nodes'].items()),list(rroot['nodes']))
 for gp,gr in M[RR]['graphs'].items():
  if gp!='root':ck('S22 complete retained native descendant '+gp,canon(gr)==canon(M[CAR]['graphs'][gp]),len(gr['nodes']))
 ck('S22 accepted prefix only removed',set(native['nodes'])-set(rroot['nodes'])=={'2','252','253'}and e(RR,0,'Out',115,'In1'),'already accepted message/started/active prefix not replayed')
 ck('S22 exact support omission baseline',M[CAR]['root_prefabs']==['#q304_pr_car_retrieval']and not M[RR]['root_prefabs']and not any(z['prefabs']for m in[M[B],M[RR]]for g in m['graphs'].values()for z in g['nodes'].values()),'baseline missing dedicated native car lease: three FAIL dispositions justified, independent after review separate')
 for gp,g in M[FF]['graphs'].items():
  if gp.startswith('root/100/6'):ck('fresh S24 exact native persistent snippet '+gp,canon(g)==canon(M[PP]['graphs']['root/30/6'+gp[len('root/100/6'):]]),'native q305/q306/tokens unchanged')
 ck('fresh genuine native q305 OR q306 prerequisite',any(z.get('operation')=='OR'and {x.get('type',{}).get('factName')for x in z.get('conditions',[])}=={'q305_done','q306_done'}for gr in M[FF]['graphs'].values()for nd in gr['nodes'].values()for z in walk(nd['payload'])),'no forced excluded main-story completion')
 ck('actual Ashley contact DanTaylor',n(FF,93)['payload']['type']['params'][0]['contact']['realPath']=='ep1/contacts/dan_taylor'and n(FF,93)['payload']['type']['params'][0]['addContact']==1,'display name is not internal ownership ID')
 for ee in [(1,'Out',2,'In'),(1,'Out',3,'In'),(11,'Out',12,'In'),(11,'Out',13,'In'),(19,'Out',20,'In'),(19,'Out',21,'In'),(56,'Out',66,'In'),(63,'Out',66,'In'),(66,'Out',42,'In'),(42,'Out',10,'In')]:ck('actual native Ashley response path '+str(ee),e(MSG,*ee),ee)
 ck('actual accepted fact not forged',n(MSG,66)['writes']==[{'$type':'questSetVar_NodeType','factName':'q304_car_retrieval_accepted','setExactValue':1,'value':1}]and all(n(MSG,i)['reads'][0]['state']=='Succeeded'for i in[2,3,12,13,20,21]),'native choice acknowledgements precede accepted seam')
 ck('no alternate custom holocall producer hidden in car closure',not any(w['factName'].startswith(('holo_','audio_','new_sts','new_q110'))for d,m in M.items()if'car_retrieval'in d and not d.startswith('towercontinued')for g in m['graphs'].values()for z in g['nodes'].values()for w in z['writes']),'native direct SMS/contact/choice protocol, no generic listener substitute')
 for ee in[(357,'False',352,'In'),(357,'True',358,'In'),(352,'Out',256,'In'),(358,'Out',256,'In'),(356,'Out',255,'In1'),(255,'Out1',268,'In'),(268,'Out',249,'In'),(249,'Out',267,'In'),(267,'Out',157,'In'),(157,'Out',1,'In')]:ck('native car reward/cleanup '+str(ee),e(CAR,*ee),ee)
 ck('native vehicle exact earned entitlement',n(CAR,291)['payload']['type']['vehicle']=='Vehicle.v_sport1_quadra_sport_r7_netrunner'and n(CAR,291)['payload']['type']['enable']==1,'not a new grant route')
 ck('native spotted/undetected reward separation',n(CAR,357)['reads'][0]['factName']=='q304_car_retrieval_got_spotted'and n(CAR,352)['payload']['type']['rewards'][0]['$value']=='197050762775'and n(CAR,358)['payload']['type']['rewards'][0]['$value']=='148894229735','do not collapse reward outcomes')
 # Exact current code tables / settled-history semantics, all pinned current05.
 epoch=read(F/'source_epoch_05.json');C=Path(epoch['candidate']);sources={}
 for name in ['PTFR_SideJobsS22.reds','PTFR_SideJobsS23.reds','PTFR_SideJobsS24.reds','PTFR_HistorySnapshotHS1.reds','PTFR_JohnnyVoiceJV1.reds']:
  f=C/'package/r6/scripts/PTFR_Consolidated'/name;rel=f.relative_to(C/'package').as_posix();h=next(x['sha256']for x in epoch['package_files']if x['path']==rel);ck('current source code pin '+name,sha(f)==h,str(f));pins.append({'path':str(f),'sha256':h});sources[name]=f.read_text()
 def arr(file,name):return json.loads(re.search(r'func '+name+r'\(\).*?return (\[.*?\]);',sources[file]).group(1))
 ck('Voodoo four inactive histories and empty native fact list',arr('PTFR_SideJobsS23.reds','StatesA17')==[1]*4 and arr('PTFR_SideJobsS23.reds','FactNames17')==[],'no tracked container receipt invented')
 ck('fresh91Inactive histories exact graph/script',len([x for x in n(FF,3)['reads']if x['$type']=='questJournalEntryState_ConditionType'])==len(arr('PTFR_SideJobsS24.reds','Paths5'))==91 and arr('PTFR_SideJobsS24.reds','StatesA5')==[1]*91,'unknown journal !=Inactive')
 ck('settled matching samples and missing journal sentinel',all('EnumInt(jm.GetEntryState(entry)) : -1'in sources[f]and'if !a.valid || !b.valid'in sources[f]for f in ['PTFR_SideJobsS22.reds','PTFR_SideJobsS23.reds','PTFR_SideJobsS24.reds']),'scalar missing0 and missing journal-1 are separate')
 # Inspect all20 substantive dispositions, preserving baseline/source versions and uncertainty.
 res=read(G/'results.json');reviewed=[]
 for q in res['quest_results']:
  f=Path(q['contracts']);ck('frozen quest contract hash '+q['quest_id'],sha(f)==q['contracts_sha256'],q);cc=read(f)['contracts'];ck('ten actual contract keys '+q['quest_id'],len(cc)==10 and all(v['proven']and v['evidence']for v in cc.values()),list(cc))
  for k,v in cc.items():ck('specific findings/evidence '+q['quest_id']+'/'+k,all(Path(p).is_file()for p in v['evidence'])and(v['status']not in ['UNKNOWN','FAIL','CONDITIONAL','OPAQUE']or bool(v['remaining'])),{'status':v['status'],'proven':v['proven'],'remaining':v['remaining']});reviewed.append({'quest_id':q['quest_id'],'contract':k,'status':v['status']})
  if q['quest_id']=='q304_splinter_stash':ck('three precise native-history unknowns retained',{k for k,v in cc.items()if v['status']=='UNKNOWN'}=={'eligibility','completion_rewards_cleanup','persistence'},'untracked container/Inject idempotence/hub semantics, no duplicate reward proven or speculative fix')
  else:ck('three baseline support failures retained',{k for k,v in cc.items()if v['status']=='FAIL'}=={'ownership','presentation','shared_dependencies'},'baseline05 is separate from newly serialized candidate03')
 sr=F/'reviews/worker_a/MOVING_HEAT_serialized/verification_01/review.json';ck('separate serialized successor review applies',sha(sr)=='0F2BF560F1CFF7D4E4F3A69B788A3F2F8177558A39CECC701608B69C5A6CD90E'and read(sr)['after_sha256']=='37E4B4076D7506A9D1A62BAFDCD8FD66576E3C8A27A07736FCD738F4E94AA5D1',str(sr));pins.append({'path':str(sr),'sha256':sha(sr)})
 # Actual native raw controls independent of the source author's verifier.
 for label,d,change,oracle in [('stash_wrong_native_loot',ST,lambda r:[x.update(quantity=0)for x in walk(r)if x.get('quantity')==8000],lambda m:any(x.get('quantity')==8000 for x in walk(m['graphs']['root']['nodes']['22']['payload']))),('Ashley_missing_native_accept',MSG,lambda r:[x.update(value=0)for x in walk(r)if x.get('$type')=='questSetVar_NodeType'and x.get('factName')=='q304_car_retrieval_accepted'],lambda m:any(x.get('factName')=='q304_car_retrieval_accepted'and x['value']==1 for x in m['graphs']['root']['nodes']['66']['writes']))]:
  r=copy.deepcopy(R[d]);change(r);mm=Resource(r).normalize();ck('actual raw mutation '+label,oracle(M[d])and not oracle(mm),d);fp=O/'mutations'/str(label+'.json');write(fp,r);mut.append({'fault':label,'path':str(fp),'sha256':sha(fp),'detected':True})
 write(O/'tests.json',tests);write(O/'source_pins.json',pins);write(O/'contracts_reviewed.json',reviewed);write(O/'mutations.json',mut);result={'status':'PASS_INDEPENDENT_TWENTY_CONTRACT_SOURCE_REVIEW_WITH_BASELINE_FAILS_AND_EXACT_UNKNOWNS','checks':len(tests),'mutations':len(mut),'contracts':20,'independent_fresh_exports':5,'frozen_native_resource_inputs':20,'reused_serialized_review':str(sr),'source_version':'Frozenbaseline00=current05 for G18 four private inputs; candidate03 MovingHeat wrapper is separately scoped, not silently baseline-adjudicated.','tests':str(O/'tests.json'),'source_pins':str(O/'source_pins.json'),'code_sha256':sha(__file__),'findings':['Three source-confirmed accepted MovingHeat support failures are preserved; current native/phone/reward parity cannot substitute for missing lease.','Three Voodoo history/entitlement/Inject/hub unknowns are specific, supported and not converted to a duplicate-grant defect.','Current serialized wrapper59/5 reviewed independently; old executing10 unchanged versus oldclaimedpending9 future wrapper boundary preserved.'],'limits':['World/prefab/container/actor placement and rendered JV1 independent props remain opaque/live-only.','Unknown old container claims, Inject semantics and generic hub dispatch remain unresolved; no live duplicate reward proved.','Pre-wrapper outside-trigger availability and arbitrary saved/external owner state remain outside source approval.'],'runtime_changes':[]};write(O/'review.json',result);print(json.dumps(result))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);run(Path(ap.parse_args().output).resolve())
