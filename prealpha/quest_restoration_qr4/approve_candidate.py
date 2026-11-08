"""Pin reviewed QR4 source epoch and prepare the bounded consolidated rebuild."""
from pathlib import Path
import sys,datetime
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
assert not (O/'approved_changes_01.json').exists(),'Preserve completed approval'
C=O/'candidate_01';P=C/'repair_mq007';p=read(P/'patch.json');t=P/'verification_01/tests.json'
assert read(t)['status']=='PASS_FOCUSED_STATIC_REPAIR_AND_PRESERVATION'
review=O/'groups/G10/reviews/MQ007_serialized/verification_01/review.json'
assert read(review)['status'].startswith('APPROVED_SERIALIZED')
resources=[]
for r in p['resources']:
 resources.append(r|{'intent':'Future supported MQ007 entry enrolls exact native bugfix14 continuation with recursive helper lease, original done wait/five days/context/variant/Regina messages/receipt. No retroactive adoption or altered admission.','evidence':[str(P/'patch.json'),str(O/'groups/G08/regina_followup_01/evidence.json'),str(O/'groups/G08/regina_world_01/ownership.json')],'tests':[str(t),str(review)],'independent_review_sha256':sha(review)})
write(O/'approved_changes_01.json',{'version':1,'relative_to':'QR3 staged candidate_01','status':'APPROVED_SERIALIZED_FUTURE_EVENT_ONLY','resources':resources,'new_unique_defects':1,'new_affected_quests':['mq007_smartgun'],'new_depots':0,'new_ArchiveXL_IDs':0,'limits':read(t)['limits']})
epoch=read(O/'source_epoch_00.json');epoch['epoch']=1;epoch['candidate']=str(C);epoch['predecessor_epoch_sha256']=sha(O/'source_epoch_00.json');epoch['approved_changes_sha256']=sha(O/'approved_changes_01.json')
epoch['source_resources'].update({r['depot']:r['after'] for r in resources});epoch['package_state']='NOT_YET_REBUILT; package_files still pins predecessor51paths';epoch['changes']=resources
write(O/'source_epoch_01.json',epoch)
progress=read(O/'progress.json');progress['new_defects']=[{'id':'QR4-MQ007-POSTRETURN','affected':['mq007_smartgun'],'status':'SERIALIZED_VALIDATED_PACKAGE_PENDING','resources':[r['depot'] for r in resources]}];progress['repair_epochs'].append(str(O/'source_epoch_01.json'));progress['events'].append({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'event':'EPOCH01_REVIEWED_MQ007_TWO_RESOURCE_REPAIR'})
write(O/'progress.json',progress)
write(O/'WORKING_CHECKPOINT.json',{'state':'ALL48_SOURCE_INVESTIGATIONS_COMPLETE_FINAL_REVIEWS_AND_PACKAGE_PENDING','working_candidate':str(C),'source_epoch':1,'source_changes':2,'new_unique_defects':1,'root_tests':str(t),'next_action':'Run fresh QR4 bounded packer, read every1574payload and independently compare final package toQR3; finish G09/G10/G12 reviews and final queue adjudication.','restrictions':'No deployment/game/save/fact/release writes'})
prior=W/'prealpha/quest_restoration_qr3/rebuild_candidate.ps1'
script=prior.read_text(encoding='utf-8-sig').replace('approved_changes_02.json','approved_changes_01.json')
(O/'rebuild_candidate.ps1').write_text(script,encoding='utf-8')
print({'status':'APPROVED_EPOCH01','resources':len(resources),'new_defects':1})
