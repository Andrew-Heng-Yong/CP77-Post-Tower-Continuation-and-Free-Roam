"""Explicit source-review supersession; original investigation bytes stay frozen."""
from pathlib import Path
import sys,copy
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
out=O/'adjudications/G03_01.json';assert not out.exists()
bp=O/'reviews/worker_b/G03.json';ep=O/'reviews/worker_b/G03_EP1/evidence.json';cp=O/'groups/G11/reviews/CVI02_EP1/verification_03/review.json'
b,e,c=map(read,[bp,ep,cp]);assert c['status']=='CONFIRMED_SOURCE_DEFECT_REPAIR_BLOCKED_BY_EXACT_CONTEXT_AND_OWNER_EVIDENCE'
q=read(O/'queue.json');rows=read(O/'contract_status_matrix.json');updated={}
for ident in ['sts_pac_cvi_02','sts_pac_wwd_05']:
 item=next(x for x in q['quests']if x['id']==ident);cs=copy.deepcopy(item['contracts'])
 if ident=='sts_pac_cvi_02':
  details={
   'communications':'EP1installed1 route205.True→208 emits new_sts_pac_cvi_02_holocall_prebrief then221 waits genuine new_q110 result. Failed/perfect debrief213/214→215/217 likewise require separate activator9 real callbacks; generic holo_mr_hands ACKs cannot satisfy them.',
   'ownership':'Exact native EP1 openworld28/activator9 consumers16/17/18 and callbacks6/10/11 were retired by genuine Tower EP1 root cut. No equivalent private listener/ACK owner exists in pinned5136-model/script census. Existing generic Hands owner remains valid for legacy ep1_installed0.',
   'progression':'The supported fresh EP1installed1/zero-outcome counterexample reaches208→221 without a restored specialized request consumer. Native body progression and existing owned van-failure XOR257 are intact; adding a second failure monitor would not repair this call gap.',
   'completion_rewards_cleanup':'Native failure/perfect debrief requests215/217 wait for the same absent specialized real call outcome producer. Authored rewards/cleanup are preserved but their post-call route lacks a complete executing dependency; no fake acknowledgement or payout is accepted.',
   'shared_dependencies':'Three selected scene-input closures are holo-only dialogue by mr_hands_holo; physicalHands/Johnny metadata alone does not establish visible Johnny or physical actor demand. Scene marker #mr_sm_hands_combat_zone_default depends on exact default prefab whose FO1 provider has earned default_on/default_ep1/lifecycle fences not implied by CVI02 admission.'}
  for stage,text in details.items():
   v=cs[stage];v['pre_review_status']=v['status'];v['original_proven']=copy.deepcopy(v['proven']);v['status']='FAIL'
   v['proven']=['SUPERSESSION: Original generic phone evidence applies to ep1_installed0; exact unchanged native body evidence remains valid.',text]
   v['remaining']=v.get('remaining',[])+['CONFIRMED_BLOCKED_REPAIR: Establish source-confirmed independent marker lease/scene startup acquisition and safe future/saved-owner context before cloning a bounded activator. Existing conditional FO1 provider is neither absent nor guaranteed. No unfiltered default/PIP/global owner, synthetic ACK or main-story/Johnny revival approved.']
   v['evidence'] += [str(bp),str(ep),str(cp)];v['defect']='QR5-CVI02-EP1-ALTERNATE-HANDS-CONTROLLER';v['repair_status']='BLOCKED_EXACT_MARKER_LEASE_AND_OWNER_EVIDENCE'
 else:
  replacements={'Original already-Soft body references stay Soft.':'Native selected Rancho parent12 is Embedded. Three main/phase/combat embedded bodies independently match effective originals after only reviewed Embedded→Soft/cooking envelope.','already-Soft native body':'independently compared native Embedded main/phase/combat bodies under the private Soft binding'}
  for v in cs.values():
   changed=False
   for key in ['proven','approved_differences']:
    old=copy.deepcopy(v.get(key,[]));new=[]
    for text in old:
     for a,z in replacements.items():text=text.replace(a,z)
     new.append(text)
    if old!=new:v['original_'+key]=old;v[key]=new;changed=True
   if changed:v['evidence'] += [str(bp)];v['documentation_correction']='WWD05 Embedded parent12/three embedded bodies; CVI02 parent3 Soft. Native parity passes; no runtime defect.'
 item.update(contracts=cs,explicit_review_supersession=str(out),explicit_review_supersession_sha256='RECORDED_BY_FINAL_COVERAGE_INDEX',independent_additional_review=str(cp));updated[ident]=cs
 for row in rows:
  if row['quest_id']==ident:row.update(copy.deepcopy(cs[row['stage']]))
write(out,{'status':'COORDINATOR_ACCEPTS_INDEPENDENT_SOURCE_ADJUDICATION','originals_preserved':True,'updated_contracts':updated,'reviews':{str(x):sha(x)for x in [bp,ep,cp]},'runtime_changes':0,'source_confirmed_unique_defects_added':1,'repair':'BLOCKED_EXACT_CONTEXT_AND_OWNER_EVIDENCE','separate_documentation_correction':'WWD05 Embedded/Soft body envelope; native three-body parity proved, no runtime repair.'})
write(O/'queue.json',q);write(O/'contract_status_matrix.json',rows)
p=read(O/'progress.json');p['groups']['G03']['review_addendum']={'path':str(out),'sha256':sha(out),'independent_review':str(cp),'independent_review_sha256':sha(cp)};write(O/'progress.json',p)
print({'primary_deep_reviewed':q['deep_reviewed_count'],'new_blocked_defects':1,'affected_contracts':5})
