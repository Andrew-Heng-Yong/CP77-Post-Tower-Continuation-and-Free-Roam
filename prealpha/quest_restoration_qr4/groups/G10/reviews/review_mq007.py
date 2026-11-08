"""Independent MQ007 follow-up consumer/owner review. No B verifier imported."""
from pathlib import Path
import sys,json,gzip,collections,argparse,re,hashlib
W=Path(__file__).resolve().parents[5];H=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value
from model import Resource,reachable
A=W/'diagnostics/vanilla_parity_20261029_01/analysis_02';IDX=read(A/'resource_inventory.json');MI=read(A/'model_inventory.json');Q3=W/'prealpha/quest_restoration_qr3/candidate_01';EPOCH=read(H.parents[2]/'source_epoch_00.json')
B=r'base\quest\bugfixing\minor_quests\mq007\mq007_quest_bugfixes.questphase';N=r'base\quest\minor_quests\mq007\mq007.questphase';P=r'towercontinued\sidejobs_s23\base_a\mq007_smartgun.questphase';R=r'towercontinued\sidejobs_s23\base_a_v2\mq007_resume_owner.questphase';PF='#mq007_pr_gun_return';DONE='mq007_skippy_re_acquiring_done';MSG='contacts/regina_jones/mq007_giving_back_skippy/'
def run(O):
 assert not O.exists();tests=[];pins=[];models={};refs={};hits=[];private_count=0;current_hash_checks=0
 def check(name,ok,e):tests.append(dict(name=name,status='PASS' if ok else 'FAIL',evidence=e));assert ok,name
 overlays={r'towercontinued\sidejobs_s23\base_b\mq037.questphase':Q3/'repair/after.json',r'towercontinued\sidejobs_s23\base_b\mq030.questphase':Q3/'repair_mq030/after.json'}
 refs={d:r.get('refs',[]) for d,r in IDX.items()};cache_hashes=0
 for d,row in MI.items():
  compressed=Path(row['normalized_model']).read_bytes();assert hashlib.sha256(compressed).hexdigest().upper()==row['normalized_sha256'],d;cache_hashes+=1
  blob=gzip.decompress(compressed);matched=any(t in blob for t in [PF.encode(),DONE.encode(),MSG.encode()]);m=None
  if d in overlays:m=Resource(read(overlays[d])).normalize();refs[d]=m['refs']
  elif matched or d in [B,N,P,R]:m=json.loads(blob)
  if d in EPOCH['source_resources']:
   raw=Q3/'archive_source'/d.replace('\\','/');check('current private model binary '+d,sha(raw)==EPOCH['source_resources'][d],str(raw));current_hash_checks+=1
   if d not in overlays:check('cached private JSON baseline matches current binary '+d,IDX[d]['sha256']==EPOCH['source_resources'][d],d)
  if d.startswith('towercontinued\\'):private_count+=1
  if m is None:continue
  models[d]=m;mh=[]
  for gp,g in m['graphs'].items():
   for i,n in g['nodes'].items():
    if PF in str(n['payload']) or DONE in str(n['payload']) or MSG in str(n['payload']):mh.append(dict(graph=gp,node=i,payload=n['payload'],prefabs=n['prefabs'],node_refs=n['node_refs'],journal_paths=n['journal_paths'],incoming=[e for e in g['edges'] if e[2]==i],outgoing=[e for e in g['edges'] if e[0]==i]))
  owner=PF in m.get('root_prefabs',[]) or any(PF in x.get('root_prefabs',[]) for x in m.get('embedded_files',[])) or any(PF in n['prefabs'] for g in m['graphs'].values() for n in g['nodes'].values())
  if mh or owner:hits.append(dict(depot=d,owner=owner,root_prefabs=m['root_prefabs'],hits=mh))
 check('all normalized cache hashes independently verified',cache_hashes==len(MI),dict(verified=cache_hashes,inventory_sha256=sha(A/'model_inventory.json'),resource_inventory_sha256=sha(A/'resource_inventory.json')))
 for d in [B,N,P,R]:
  p=IDX[d];j=Path(p['json']);raw=Q3/'archive_source'/d.replace('\\','/') if d.startswith('towercontinued\\') else j.with_suffix('')
  if not raw.is_file():raw=Path(str(j).replace('\\json\\','\\raw\\')).with_suffix('')
  check('relevant native/current binary '+d,sha(raw)==p['sha256'],str(raw));rawmodel=Resource(read(j)).normalize();rawmodel.setdefault('embedded_files',[]);models[d].setdefault('embedded_files',[]);check('relevant raw/cache equality '+d,rawmodel==models[d],str(j));pins.append(dict(depot=d,binary=str(raw),sha256=sha(raw),json=str(j),json_sha256=sha(j)))
 def g(d,gp='root'):return models[d]['graphs'][gp]
 def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
 def edge(d,e,gp='root'):return list(map(str,e)) in g(d,gp)['edges']
 for d in [N,R]:check('real native/restored return writer '+d,any(x.get('factName')=='mq007_done' and x.get('value')==1 for x in n(d,66,'root/5')['writes']) and edge(d,[66,'Out',62,'In'],'root/5'),dict(graph='root/5',node=66))
 check('fresh wrapper delegates actual native full body',N in models[P]['refs'],P)
 actuators=[row for row in hits if any(PF in h['node_refs'] or any(p.startswith(MSG) for p in h['journal_paths']) or any(x.get('$type')=='questSetVar_NodeType' and x.get('factName')==DONE for x in walk(h['payload'])) for h in row['hits'])]
 check('unique indexed message/variant/postreceipt actuator',len(actuators)==1 and actuators[0]['depot']==B,dict(actuators=actuators,guard_only_resources=[x['depot'] for x in hits if x not in actuators]))
 check('post-return done wait then exact five days',edge(B,[0,'Out',2,'In'],'root/14') and edge(B,[2,'Out',4,'In'],'root/14') and any(x.get('factName')=='mq007_done' and x.get('comparisonType')=='GreaterOrEqual' and x.get('value')==1 for x in n(B,2,'root/14')['reads']) and any(x.get('$type')=='questGameTimeDelay_ConditionType' and x.get('days')==5 for x in walk(n(B,4,'root/14')['payload'])),dict(graph='root/14',nodes=[2,4]))
 cond=n(B,3,'root/14/3')['payload']['condition'];check('outside reacquiring office AND actual content token',cond['operation']=='AND' and any(x.get('$type')=='questTriggerCondition' and x.get('type')=='IsOutside' and value(x['triggerAreaRef'])=='#mq007_tr_regina_jones_office_re_acquiring' for x in walk(cond)) and any(x.get('$type')=='questContentToken_ConditionType' and x.get('type')=='MinorQuestAndSts' for x in walk(cond)),cond)
 check('variant show then three actual messages then receipt',all(edge(B,e,'root/14/3') for e in [(3,'Out',4,'In'),(4,'Out',5,'Active'),(5,'Out',6,'Active'),(6,'Out',7,'Active'),(7,'Out',1,'In')]) and all(any(p.startswith(MSG) for p in n(B,i,'root/14/3')['journal_paths']) for i in [5,6,7]) and edge(B,[3,'Out1',5,'In'],'root/14') and any(x.get('factName')==DONE and x.get('value')==1 for x in n(B,5,'root/14')['writes']),dict(variant=n(B,4,'root/14/3')['payload'],messages=[n(B,i,'root/14/3')['journal_paths'] for i in [5,6,7]]))
 check('original follow-up phase terminates after messages',n(B,1,'root/14')['payload']['type']=='Terminating' and n(B,14)['prefabs']==[] and models[B]['root_prefabs']==[],dict(parent=n(B,14)['payload'],output=n(B,1,'root/14')['payload']))
 # Complete over-approximate native-reference closure from all private model roots.
 starts={d for d in MI if d.startswith('towercontinued\\')};seen=set(starts);todo=list(starts);parents={d:None for d in starts}
 while todo:
  a=todo.pop()
  for b in refs[a]:
   if b in refs and b not in seen:seen.add(b);parents[b]=a;todo.append(b)
 check('no transitive current-private native rehost reaches consumer',B not in seen,dict(starts=len(starts),reachable_resources=len(seen),target=B))
 check('no modeled phase lease for target prefab',not any(x['owner'] for x in hits),dict(prefab=PF,scope='All indexed root, embedded and nested PhaseInstancePrefabs; world-sector definitions outside normalized phase/scene scope remain unresolved'))
 # Independently inspect actual pinned main-tree retirement ancestry.
 paths=[('base\\quest\\cyberpunk2077.questphase',W/'prealpha/quest_restoration_qr2/provider_readback_01/basegame_4_gamedata/base/quest/cyberpunk2077.questphase.json','B3703A63166653CC78901EFE8A847D5E615C2E1CB6581CAA4CC796F825D82817'),('base\\quest\\bugfixing.questphase',W/'prealpha/quest_restoration_qr2/provider_readback_01/basegame_4_gamedata/base/quest/bugfixing.questphase.json','7EFD7CED7DEBAC337907D63F6494AD1276DBA87404FC80F06D483A0BBA0FFBB7'),('base\\quest\\bugfixing\\quest_bugfixing.questphase',W/'research/sidejobs_s29/discovery_01/basegame_4_gamedata/json/base/quest/bugfixing/quest_bugfixing.questphase.json','C459001B5305DCD37606E71E296D5DA9F3704958738B16338C9CE3EDB46286AE')]
 for d,j,h in paths:check('pinned native retirement JSON '+d,sha(j)==h,str(j));models[d]=Resource(read(j)).normalize();pins.append(dict(depot=d,json=str(j),json_sha256=sha(j)))
 root=paths[0][0];bug=paths[1][0];qb=paths[2][0]
 check('genuine ending crosses main-root Terminating',edge(root,[106,'Out',109,'In']) and edge(root,[109,'Out',107,'In']) and n(root,107)['payload']['type']=='Terminating',dict(nodes=[106,109,107],payloads=[n(root,i)['payload'] for i in [106,109,107]]))
 check('original bugfix consumer is below retired main root',bug in n(root,4,'root/82')['refs'] and qb in n(bug,9)['refs'] and B in n(qb,27,'root/3')['refs'],dict(main_root_graph='root/82',main_node=4,bugfix_node=9,quest_bugfix_graph='root/3',quest_bugfix_node=27))
 # Current packaged scripts are separately pinned/scanned for effectful follow-up writes.
 script_hits=[]
 for row in EPOCH['package_files']:
  if not row['path'].endswith('.reds'):continue
  p=Q3/'package'/row['path'];check('epoch script '+row['path'],sha(p)==row['sha256'],str(p));txt=p.read_text(encoding='utf8')
  current_function=None
  for line,text in enumerate(txt.splitlines(),1):
   match=re.search(r'\bfunc\s+(\w+)\(',text)
   if match:current_function=match.group(1)
   if DONE in text or MSG in text or PF in text:script_hits.append(dict(path=str(p),line=line,text=text,function=current_function))
 check('current REDscript token hits are read-only catalogues not follow-up actuators',all(x['function'] and x['function'].startswith(('Facts','FactNames','MetadataJSON')) and DONE in x['text'] and PF not in x['text'] and MSG not in x['text'] for x in script_hits),script_hits)
 report=dict(status='MISSING_POST_RETURN_CONSUMER_CONFIRMED_SAFE_REHOST_BLOCKED_BY_TARGET_OWNER_EVIDENCE',reviewer='qr4_worker_a',independent=True,checks=len(tests),tests=tests,source_pins=pins,global_scan=dict(models=len(MI),private_models=private_count,current_private_binary_hashes=current_hash_checks,qr3_overlay_json={d:str(p) for d,p in overlays.items()},hits=hits,transitive_private_reachable=len(seen),script_hits=script_hits),confirmed_route='Native/restored return root/5:66 mq007_done1 → missing native bugfix14/2 done>=1 →14/4 five game days →14/3 outside Regina reacquiring-office AND MinorQuestAndSts →show gun-return var_container →three native SMS →re_acquiring_done1 →Terminating.',adversarial_conclusion=['The missing consumer is source-confirmed in the indexed current successor: all real message/variant/postreceipt writers reside in one original bugfix owner under the genuinely terminating main tree. No current private direct OR transitive native-reference rehost reaches it.','This establishes a lost producer-consumer route, not proof every current save lacks an already-running instance or that an arbitrary new owner is safe.','No decoded root/embedded/nested phase lease owns #mq007_pr_gun_return. The original consumer itself carries no prefab and terminates after messages. World-sector/NodeRef ownership and persistent variant semantics are missing evidence, not proof the target does not exist.'],repair_disposition=dict(source_defect='Confirmed missing post-return consumer after restored mq007_done writer',automatic_patch='NOT_APPROVED_BY_THIS_REVIEW',precise_blockers=['Resolve original #mq007_pr_gun_return world/prefab placement, scope and ownership (including native world persistence/streaming), and #mq007_tr_regina_jones_office_re_acquiring target binding.','Prove target visibility/state and item pickup persist after native14 terminates; do not attach prefab solely to a terminating14 if doing so would unload it before pickup.','Define a conservative fresh-versus-existing post-return timer/owner seam. Rehosting after done1 must not restart an already-progressed five-day timer, repeat native SMS, reopen a completed reacquisition or duplicate returned-item contents; historical owner liveness cannot be replaced by synthetic facts.'],safe_scope_if_resolved='Small separately guarded post-return consumer only, preserving all original nodes/IDs/timer/outside-office/content gates/variant/messages/receipt and existing main completion. No full bugfix-root transplant, item/reward replay, AI/device commands or admission relaxation.',admission_gap_separate='Exact MQ007 native11/51/95 admission prerequisites are unchanged and are not resolved by this review.'),runtime_changes=[])
 write(O/'MQ007_followup.json',report);return dict(status=report['status'],checks=len(tests),models=len(MI))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();print(json.dumps(run(Path(a.output).resolve())))
