"""Refresh current-session metadata without changing investigated conclusions."""
from pathlib import Path
import sys
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
p=read(O/'progress.json');q=read(O/'queue.json');rq=read(O/'repair_queue.json')
q['source_epoch_namespace']='QR5';q['retained_deep_provenance']={'queue':str(W/'prealpha/quest_restoration_qr4/queue.json'),'sha256':sha(W/'prealpha/quest_restoration_qr4/queue.json'),'epoch':'QR4:03'}
q['new_unique_defects']=0;q['new_affected_quest_count']=0;q['source_confirmed_defects_pending_review']=len(rq['items']);q['changed_resources']=0
write(O/'queue.json',q)
cp=read(O/'WORKING_CHECKPOINT.json');cp['state']='CONTINUOUS_PRIMARY_INVESTIGATIONS_WITH_ARR12_REVIEW_PENDING';cp['new_completed']=p['completed_quests'];cp['active_groups']={k:v['ids']for k,v in p['groups'].items()if v['status']=='CLAIMED'};cp['repair_queue']=str(O/'repair_queue.json');cp['candidate_runtime_changes']=0;cp['next_action']='C reviews ARR12 and proceeds G08; A finishes G01 then G02; B freezes G04 and proposal then G05 plus independent G07 review. Root alone integrates approved repairs; continue primary queue.'
write(O/'WORKING_CHECKPOINT.json',cp)
print({'new_completed':len(p['completed_quests']),'candidate_changes':0,'review_pending':len(rq['items'])})
