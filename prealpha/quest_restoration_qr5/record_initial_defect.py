"""Record a source-confirmed discrepancy without authorizing a runtime change."""
from pathlib import Path
import sys
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
ep=O/'groups/G04/arr12_failure_01/evidence.json';e=read(ep)
assert not (O/'repair_queue.json').exists()
item={'id':e['id'],'quest_id':e['quest_id'],'status':'SOURCE_CONFIRMED_PENDING_INDEPENDENT_REPAIR_REVIEW','evidence':str(ep),'evidence_sha256':sha(ep),'source_checks':e['checks'],'affected_contracts':e['affected_contracts'],'runtime_changes':[],'implementation_authorized_after':'Independent source/ownership/adapter review plus coordinator acceptance; no reset/wholebugfix replay'}
write(O/'repair_queue.json',{'items':[item],'source_epoch':0,'candidate_unchanged':True})
p=read(O/'progress.json');p['new_defects']=[item];write(O/'progress.json',p)
write(O/'approved_changes_00.json',{'version':0,'source_epoch':0,'status':'NO_APPROVED_RUNTIME_CHANGES_YET','resources':[],'working_candidate':read(O/'source_epoch_00.json')['candidate']})
write(O/'source_epoch_identity.json',{'current':'QR5:00','current_manifest':str(O/'source_epoch_00.json'),'current_manifest_sha256':sha(O/'source_epoch_00.json'),'predecessor':'QR4:03','predecessor_manifest':str(W/'prealpha/quest_restoration_qr4/source_epoch_03.json'),'predecessor_manifest_sha256':sha(W/'prealpha/quest_restoration_qr4/source_epoch_03.json'),'rule':'Epoch numbers are local to their QR workspace. Retained QR4 findings keep original provenance; new QR5groups use this frozen epoch00.'})
print({'id':e['id'],'status':item['status'],'source_changes':0})
