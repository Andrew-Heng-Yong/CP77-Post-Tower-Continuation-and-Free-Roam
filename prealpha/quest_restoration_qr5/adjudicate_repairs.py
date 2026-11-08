"""Central matrix update after independent final packaged-byte verification."""
from pathlib import Path
import sys,argparse,copy
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
ap=argparse.ArgumentParser();ap.add_argument('--package-review',required=True);args=ap.parse_args()
out=O/'adjudications/repairs_01.json';assert not out.exists()
rp=Path(args.package_review).resolve();pr=read(rp);assert pr['status'].startswith(('PASS','APPROVE')),pr['status']
allow=read(O/'approved_changes_03.json');q=read(O/'queue.json');rows=read(O/'contract_status_matrix.json');changes=[]
details={
 'sts_std_arr_12':('G04','QR5-G04-ARR12-MISSING-FUTURE-FAILURE-MONITOR','towercontinued\\native_gigs_u9\\sts_std_arr_12_entry.questphase','Future65003 entry guard1200→private claim1201 forks exact native failure/abandonment monitor1202 and original8. Native prearmed arm0/1 are accepted without a reset; native32/36 monitors retain failed1 dominance and authored failure/reward exclusion.'),
 'sts_wat_nid_03':('G12','QR5-CHEETAH-FUTURE-FALLBACK-MONITOR','towercontinued\\native_gigs_u9\\sts_wat_nid_03_entry.questphase','Future65003→1200 thirteen-clause immediate guard→private1201 claim forks original main2 plus native3 helper1202; False retains original2. Only native prefix0→8 becomes0→12/13; original17XOR/24AND, end18 and exact #sts_wat_nid_03_streetstory shared PIP/recursive10 remain. Normal273 completion still works; this repairs the missing fallback only.'),
 'sts_wat_nid_02':('G11','QR5-NID02-FUTURE-VAN-FAILURE-MONITOR','towercontinued\\native_gigs_u9\\sts_wat_nid_02_entry.questphase','Future65003→1300 eleven-clause immediate guard→private1301 claim forks original main2 plus exact native23 helper1302; False retains original2. Native prefix0→12 becomes0→33; health2/water49→XOR41, AND9 personal-link barrier, XOR48 phone/SMS and all real callbacks/journals/device/token/achievement/cleanup remain unchanged.')}
newdefs=[]
for ident,(gid,did,depot,text)in details.items():
 item=next(x for x in q['quests']if x['id']==ident);original=read(O/'groups'/gid/'quests'/ident/'contracts.json');a=next(r for r in allow['resources']if r['depot']==depot)
 for stage,old in original['contracts'].items():
  if old['status']!='FAIL':continue
  v=item['contracts'][stage];v.setdefault('pre_repair_status',old['status']);v.setdefault('pre_repair_proven',copy.deepcopy(old['proven']));v.setdefault('pre_repair_remaining',copy.deepcopy(old.get('remaining',[])))
  v.update(status='CONDITIONAL',proven=[text,'Actual serialized native-oracle, refusal/identity/join/cleanup checks and independent full packaged-byte comparison pass; source correctness is not gameplay certification.'],remaining=['LIVE_ONLY: Native callback admission, pulse scheduling, interrupt/reload, actor/vehicle streaming and completion/reward observations remain untested.','SAVED_SCOPE: Only future supported entry events enroll. Previously-Entered/Started/progressed saved owners are not adopted or reset.']+(['OPAQUE: Exact native Cheetah shared prefab reference/ownership is retained; engine placement/lease semantics are not decoded or live-certified.']if ident=='sts_wat_nid_03'else[]),repair=did,effective_source_epoch='QR5:05',verified_candidate_resource_sha256=a['after'])
  v['approved_differences']=v.get('approved_differences',[])+[a['intent']];v['evidence']+=a['evidence']+a['tests']+[str(rp)]
  changes.append({'quest_id':ident,'stage':stage,'before':'FAIL','after':'CONDITIONAL','repair':did})
 item['defects']=[did];item['repairs']=[a]
 newdefs.append({'id':did,'affected':[ident],'status':'REPAIRED_FUTURE_ONLY_SERIALIZED_AND_PACKAGE_STATIC_VERIFIED_LIVE_PENDING','resources':[a],'evidence':a['evidence'],'tests':a['tests'],'independent_package_review':str(rp),'limitation':'No retroactive saved-owner enrollment, reset, fake callback or live success claim.'})
# Author and independent reviewer supplied a source-specific staged contract set.
ident='sts_ep1_08_steven_meeting_night_city';item=next(x for x in q['quests']if x['id']==ident);sp=O/'groups/G15/quests'/ident/'staged_contracts.json';sd=read(sp);a=next(r for r in allow['resources']if r['depot'].endswith('sts_ep1_08_entry.questphase'));old=item['contracts'];cs=copy.deepcopy(sd['contracts'])
for stage,v in cs.items():
 if old[stage]['status']=='FAIL':v['pre_repair_status']='FAIL';v['pre_repair_proven']=copy.deepcopy(old[stage]['proven']);changes.append({'quest_id':ident,'stage':stage,'before':'FAIL','after':v['status'],'repair':'QR5-STEVEN-U9-FUTURE-DEFAULT-OWNER'})
 v['effective_source_epoch']='QR5:05';v['evidence']+=a['tests']+[str(rp)];v['verified_future_carrier_sha256']=a['after'];v['final_package_gate']='PASS_INDEPENDENT_PACKAGED_BYTES'
item['contracts']=cs;item['repairs']=[a];item['defects']=['QR5-STEVEN-U9-FUTURE-DEFAULT-OWNER'];item['explicit_staged_contracts']={'path':str(sp),'sha256':sha(sp)}
newdefs.append({'id':'QR5-STEVEN-U9-FUTURE-DEFAULT-OWNER','affected':[ident],'carrier_preservation_quest':'sts_ep1_08','status':'REPAIRED_FUTURE_ONLY_SERIALIZED_AND_PACKAGE_STATIC_VERIFIED_LIVE_PENDING','resources':[a],'evidence':a['evidence'],'tests':a['tests'],'independent_package_review':str(rp),'limitation':'Only ordered future U9 enrollment; no second native SMS/timer/reward or old saved-owner adoption. Late Ana choice fence excludes stadium route.'})
cp=O/'groups/G11/reviews/CVI02_EP1/verification_03/review.json'
newdefs.append({'id':'QR5-CVI02-EP1-ALTERNATE-HANDS-CONTROLLER','affected':['sts_pac_cvi_02'],'status':'CONFIRMED_REPAIR_BLOCKED_EXACT_MARKER_LEASE_AND_OWNER_EVIDENCE','resources':[],'evidence':[str(O/'reviews/worker_b/G03_EP1/evidence.json'),str(cp)],'adjudication':str(O/'adjudications/G03_01.json'),'blocker':'Native alternate EP1 request listener/real ACK owner is retired. Selected scene inputs are holo-only, but exact physical-default marker lease comes from conditional FO1/native default owner not implied by CVI02 entry. Safe independent support acquisition and future/saved-owner handling lack proof. No unfiltered default/PIP clone or fake ACK approved.'})
prior=read(W/'prealpha/quest_restoration_qr4/defects_and_repairs.json')
write(O/'defects_and_repairs.json',{'new_confirmed_unique_defects':len(newdefs),'new_repaired_unique_defects':4,'new_blocked_unique_defects':1,'new_affected_quest_count':len({i for d in newdefs for i in d['affected']}),'new_changed_resources':4,'cumulative_confirmed_unique_defects':len(prior['defects'])+len(newdefs),'cumulative_staged_repairs':7,'cumulative_changed_resources_vs_PH3':8,'defects':prior['defects']+newdefs,'scope':'Independent static source/serialized/package proof; no installed or live certification.'})
q.update(new_unique_defects=5,new_affected_quest_count=5,new_repaired_unique_defects=4,new_blocked_unique_defects=1,gameplay_repairs=7,changed_resources=4,cumulative_changed_resources_vs_PH3=8,source_epoch=5,source_epoch_manifest=str(O/'source_epoch_05.json'),package_verification='PASS_INDEPENDENT_FULL_CANDIDATE02_PACKAGE_DIFF',independent_package_review={'path':str(rp),'sha256':sha(rp)})
for item in q['quests']:
 if item['id']not in {d['affected'][0]for d in newdefs}:continue
 for row in rows:
  if row['quest_id']==item['id']:row.update(copy.deepcopy(item['contracts'][row['stage']]))
write(out,{'status':'FINAL_PACKAGED_REPAIR_ADJUDICATION','changes':changes,'package_review':str(rp),'package_review_sha256':sha(rp),'new_confirmed':5,'implemented':4,'blocked':1,'original_findings_preserved':True})
write(O/'queue.json',q);write(O/'contract_status_matrix.json',rows)
p=read(O/'progress.json');p['new_defects']=newdefs;p['final_package_review']=q['independent_package_review'];p['repair_epochs'].append(str(O/'source_epoch_05.json'));write(O/'progress.json',p)
write(O/'repair_queue.json',{'items':newdefs,'source_epoch':5,'candidate':q['working_candidate'],'installed':'PH3_UNCHANGED','remaining_blocked':1})
print({'new_confirmed':5,'implemented':4,'blocked':1,'repaired_contract_dispositions':len(changes)})
