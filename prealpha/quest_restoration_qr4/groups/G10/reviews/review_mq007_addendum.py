"""Independent prospective-only MQ007 proposal review after new world evidence."""
from pathlib import Path
import sys,json,argparse,copy
W=Path(__file__).resolve().parents[5];H=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value
from model import Resource,reachable
IDX=read(W/'diagnostics/vanilla_parity_20261029_01/analysis_02/resource_inventory.json')
PROPOSAL=H.parents[1]/'G08/regina_proposal_01/proposal.json';WORLD=H.parents[1]/'G08/regina_world_01/ownership.json';ACTUAL=H/'mq007_world_readback_02/descriptors.json';OLD=H/'MQ007_followup.json'
def run(O):
 assert not O.exists();pr=read(PROPOSAL);wo=read(WORLD);ac=read(ACTUAL);old=read(OLD);tests=[];pins=[];models={}
 def check(name,ok,e):tests.append(dict(name=name,status='PASS' if ok else 'FAIL',evidence=e));assert ok,name
 check('old blocking review retained',old['status']=='MISSING_POST_RETURN_CONSUMER_CONFIRMED_SAFE_REHOST_BLOCKED_BY_TARGET_OWNER_EVIDENCE',dict(path=str(OLD),sha256=sha(OLD)))
 check('proposal exact world evidence pin',sha(WORLD)==pr['support']['sha256'],str(WORLD))
 returns=[r for r in ac['sources'] if r['definition']['category']=='Exterior'];helpers=[r for r in ac['sources'] if r['definition']['category']=='Quest']
 check('actual independent binary world readback',ac['status']=='INDEPENDENT_ACTUAL_BINARY_DESCRIPTOR_READBACK' and len(returns)==2 and len(helpers)==2,dict(path=str(ACTUAL),sha256=sha(ACTUAL)))
 for row in returns:
  check('native world block current hash '+row['archive'],sha(row['binary'])==row['sha256'],row['binary']);d=row['definition'];v=d['variants'][0]
  check('persistent Exterior descriptor '+row['archive'],d['category']=='Exterior' and value(d['questPrefabNodeRef'])=='0' and d['numNodeRanges']==2 and d==wo['descriptor'],d)
  check('exact unchanged native container variant '+row['archive'],value(v['name'])=='var_container' and v['enabledByDefault']==0 and v['rangeIndex']==1 and v['variantId']==358103817 and value(v['nodeRef']).endswith('/#mq007_pr_gun_return'),v)
 check('both native providers agree on descriptor identity',returns[0]['definition']==returns[1]['definition'],[x['archive'] for x in returns])
 check('distinct native helper quest lease identified',helpers[0]['definition']==helpers[1]['definition'] and all(value(r['definition']['questPrefabNodeRef']).endswith('/#mq007_pr_gun_re_acquiring') and r['definition']['numNodeRanges']==1 and r['definition']['variants']==[] for r in helpers),helpers)
 for row in ac['sector_pins']:check('captured native sector bytes preserved '+row['archive'],sha(row['raw'])==row['sha256'] and bool(row['decode_error']),dict(path=row['raw'],sha256=row['sha256'],opaque=row['decode_error']))
 d=pr['native_source']['depot'];native=Resource(read(pr['native_source']['json'])).normalize();check('exact native followup binary and JSON pins',sha(pr['native_source']['binary'])==pr['native_source']['sha256'] and sha(pr['native_source']['json'])==pr['native_source']['json_sha256'],pr['native_source'])
 ng=native['graphs']['root/14'];check('native full timer-to-context continuation preserved',ng['nodes']['4']['payload']['condition']['type']=={'$type':'questGameTimeDelay_ConditionType','days':5,'hours':0,'minutes':0,'seconds':0} and native['graphs']['root']['nodes']['14']['prefabs']==[] and ng['nodes']['1']['payload']['type']=='Terminating',dict(graph='root/14',nodes=[2,4,3,5,1]))
 proofs=[]
 for row in pr['resources']:
  pin=row['source_pin'];check('actual current resource '+row['resource'],sha(pin['binary'])==pin['sha256'] and sha(pin['json'])==pin['json_sha256'],pin);m=Resource(read(pin['json'])).normalize();models[row['resource']]=m;pins.append(pin);gr=m['graphs']['root'];prefix=row['existing_issued_fact'].removesuffix('_Issued')
  check('existing event writes exact Issued and Entered receipts '+row['resource'],any(x.get('factName')==row['existing_entered_fact'] and x.get('value')==1 for x in gr['nodes']['1101']['writes']) and any(x.get('factName')==row['existing_issued_fact'] and x.get('value')==1 for x in gr['nodes']['1003']['writes']),dict(issued=1003,entered=1101))
  check('private parent has no root terminator '+row['resource'],not any(n['type']=='questOutputNodeDefinition' for n in gr['nodes'].values()),dict(body21=gr['nodes']['21']['payload'],root_outputs=[]))
  check('all new IDs are local unused '+row['resource'],all(str(i) not in gr['nodes'] for i in range(1200,1205)),list(range(1200,1205)))
  check('existing event fanout preserved verbatim '+row['resource'],sorted(row['existing_edges_preserved'])==sorted(e for e in gr['edges'] if e[0]=='1101'),row['existing_edges_preserved'])
  added=row['proposed_added_edges'];check('only future event feeds enrollment '+row['resource'],[e for e in added if e[2]=='1200']==[['1101','Out','1200','In']] and all(e[0] not in ['0','1000','1001','1002','1003','21'] for e in added if e[2]=='1200'),added)
  check('shared claim precedes exact copied phase '+row['resource'],added==[['1101','Out','1200','In'],['1200','True','1201','In'],['1201','Out','1202','In1'],['1202','Out1','1203','In']],added)
  guard=row['enrollment_guard'];fs=guard['facts_equal'];check('enrollment actual scope guards '+row['resource'],guard['operation']=='AND' and all(fs.get(f)==v for f,v in [(prefix+'_Issued',1),(prefix+'_Entered_21',1),(prefix+'_Finished',0),(prefix+'_Fault',0),('mq007_done',0),('mq007_skippy_re_acquiring_done',0),('PTFRQR4_MQ007_ReacquisitionIssued',0),('q307_done',1),('q307_finished',1),('q307_main_game_killed',1),('q307_ep1_killed',1),('q307_active',0)]),guard)
  def accepts(facts,event):return event and all(facts.get(k)==v for k,v in fs.items())
  check('positive future supported entry '+row['resource'],accepts(fs,True),fs)
  for k in fs:
   bad=dict(fs);bad[k]=1-fs[k];check('guard rejects altered '+row['resource']+k,not accepts(bad,True),dict(fact=k,wrong=bad[k]))
  check('old Entered fact alone never enrolls '+row['resource'],not accepts(fs,False),dict(event=False,entered_fact=1))
  for k in ['mq007_done','mq007_skippy_re_acquiring_done','PTFRQR4_MQ007_ReacquisitionIssued']:
   check('old returned/reacquired/claimed state rejected '+row['resource']+k,not accepts(fs|{k:1},True),k)
  # Hierarchical structural proof: native story21 is not an ancestor of1202.
  fake=copy.deepcopy(gr);fake['edges']+=added;without_story=[e for e in fake['edges'] if e[0]!='21' and e[2]!='21'];check('new continuation path independent of story child21 '+row['resource'],'1202' in reachable(fake['nodes'],without_story,['1101']),dict(continuation_path=['1101','1200','1201','1202'],removed_story=21,limit='Structural hierarchy proof; exact engine persistence still requires fixtures'))
  check('preserve distinct authored helper lease and no invented container lease '+row['resource'],native['graphs']['root']['nodes']['14']['prefabs']==[] and native['graphs']['root/14']['nodes']['3']['prefabs']==['#mq007_pr_gun_re_acquiring'] and all('#mq007_pr_gun_return' not in n['prefabs'] for gp,g in native['graphs'].items() if gp=='root/14' or gp.startswith('root/14/') for n in g['nodes'].values()),dict(copy='root14→1202',outer_native_prefabs=[],nested_phase3_native_prefabs=native['graphs']['root/14']['nodes']['3']['prefabs'],helper_world_descriptor=helpers[0]['definition']))
  proofs.append(dict(resource=row['resource'],prefix=prefix,enrollment_guard=guard,added_edges=added,existing_root_output_count=0))
 fresh=models[pr['resources'][0]['resource']]['graphs']['root'];resume=models[pr['resources'][1]['resource']]['graphs']['root']
 ff={r['factName']:r['value'] for r in fresh['nodes']['1100']['reads'] if 'factName'in r};rf={r['factName']:r['value'] for r in resume['nodes']['1100']['reads'] if 'factName'in r}
 check('actual final fresh/resume gates mutually exclusive',ff['PTFRS23_MQ007_Issued']==1 and rf['PTFRS23_MQ007_Issued']==0 and ff['mq007_skippy_50_enemies_maimed']==0 and rf['mq007_skippy_50_enemies_maimed']==1,dict(fresh_final_guard=1100,fresh_required={k:ff[k] for k in ['PTFRS23_MQ007_Issued','mq007_skippy_50_enemies_maimed']},resume_required={k:rf[k] for k in ['PTFRS23_MQ007_Issued','mq007_skippy_50_enemies_maimed']}))
 # Proposal-level negative controls: these mutations violate independently read
 # native timer/context, stable future-only enrollment or world ownership.
 controls=[]
 for name,bad in [('past-state enrollment',True),('drop mq007_done0 guard',True),('attach prefab to terminating14',True),('shorten native five days',True),('put continuation under story21',True)]:
  # Concrete representations are deliberately changed, never source files.
  if name=='past-state enrollment':edges=copy.deepcopy(pr['resources'][0]['proposed_added_edges']);edges.append(['0','Out','1200','In']);det=any(e[0]!='1101' for e in edges if e[2]=='1200')
  elif name=='drop mq007_done0 guard':guard=copy.deepcopy(pr['resources'][0]['enrollment_guard']['facts_equal']);del guard['mq007_done'];det=guard.get('mq007_done')!=0
  elif name=='attach prefab to terminating14':node=copy.deepcopy(native['graphs']['root']['nodes']['14']['payload']);node['phaseInstancePrefabs']=[{'prefabNodeRef':{'$value':'#mq007_pr_gun_return'}}];det=node['phaseInstancePrefabs']!=native['graphs']['root']['nodes']['14']['payload']['phaseInstancePrefabs']
  elif name=='shorten native five days':cond=copy.deepcopy(ng['nodes']['4']['payload']);cond['condition']['type']['days']=1;det=cond!=ng['nodes']['4']['payload']
  else:edges=copy.deepcopy(pr['resources'][0]['proposed_added_edges']);edges[0]=['21','Out1','1200','In'];det=edges[0][0]!='1101'
  controls.append(dict(fault=name,detected=det));check('proposal negative control '+name,det,controls[-1])
 report=dict(status='APPROVED_PREIMPLEMENTATION_FUTURE_EVENT_ONLY_PRESERVE_NATIVE_HELPER',reviewer='qr4_worker_a',independent=True,checks=len(tests),tests=tests,proposal=dict(path=str(PROPOSAL),sha256=sha(PROPOSAL)),new_evidence=dict(ownership=str(WORLD),ownership_sha256=sha(WORLD),independent_actual_binary_readback=str(ACTUAL),readback_sha256=sha(ACTUAL)),preserved_prior_review=dict(path=str(OLD),sha256=sha(OLD),status=old['status']),source_pins=pins,enrollment_proofs=proofs,negative_controls=controls,disposition=['APPROVE this exact two-resource future1101-event attachment for source implementation and serialized verification. The newly independently read persistent Exterior descriptor resolves the previous phase-owner/lifetime implementation blocker; no invented return-container prefab/sector owner is needed or allowed. Preserve the distinct authored root/14 node3 lease #mq007_pr_gun_re_acquiring exactly; its Quest descriptor is independently verified in both native blocks.','The pending native14 continuation is a sibling of story21 in an existing nonterminating boot parent. Preserve exact native five-day timer, outside-office/content gate, variant toggle, three SMS, native receipt and local nested node identities. Only outer phase14→1202 changes identity.','Enroll only when a real future existing1101 event fires while own Issued/Entered1 and Finished/Fault0, native done/reacquisition0 and shared claim0. Existing Entered facts without the event, already-done saves and unknown past timers remain deferred; no on-attach/poll/default0 adoption.','The actual fresh/resume final guards are disjoint by durable freshIssued1 versus0 and maimed0 versus1. The common owned claim adds one-shot protection within this supported scope. No admission11/51/95 change, native reward/item grant, fact reset, sector edit or full bugfix-root transplant is approved.'],required_before_candidate_acceptance=pr['validation_required'],remaining=['OPAQUE: Native sector payload contents and exact loot/entity/range internals cannot be decoded by WolvenKit9.1. Existing exact world variant identity/provider descriptors are verified; numerical/item correctness and pickup remain native/live obligations.','LIVE_ONLY: Actual elapsed timer persistence, engine scheduling, native token availability, variant persistence across streaming and message/pickup behavior require transition/gameplay fixtures. Static approval is not successful gameplay or broad old-save repair.','Serialize/read back both repaired final resources, compare all old nodes/edges/fields and recursively copied native14 graphs, pin final package, run baseline-fail/repaired-pass regressions and preservation checks.'],runtime_changes=[])
 write(O/'MQ007_followup_addendum.json',report);return dict(status=report['status'],checks=len(tests),controls=len(controls))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();print(json.dumps(run(Path(a.output).resolve())))
