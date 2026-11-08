"""Pin separately approved bounded monitor recipes for candidate02 staging."""
from pathlib import Path
import sys
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;C=O/'candidate_02'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
assert not (C/'monitor_plans.json').exists()
plans=[]
cp=O/'groups/G12/cheetah_proposal_02/proposal.json';cr=O/'reviews/worker_a/CHEETAH/verification_03/review.json';c=read(cp);r=read(cr);assert r['status'].startswith('APPROVE')and r['proposal_sha256']==sha(cp)
pins=read(O/'groups/G12/cheetah_followup_01/source_pins.json');native=next(x for x in pins if 'nid_03_bugfixing' in x.get('depot',''))
tag='PTFRU9_sts_wat_nid_03_';claim=tag+'MonitorEntered'
facts={tag+'ParentEntered':1,tag+'Started':0,tag+'MainFinished':0,tag+'OwnerFinished':0,tag+'Fault':0,'PTFRU9_Support_Issued':1,'PTFRU9_Support_Fault':0,claim:0,'nid_03_start':0,'nid_03_finished':0,'sts_wat_nid_03_bugfixing':0,'sts_wat_nid_03_bugfixing_end':0,'sts_wat_nid_03_completed':0}
plans.append({'key':'cheetah','depot':c['only_proposed_resource'],'before':c['source_sha256'],'proposal':str(cp),'proposal_sha256':sha(cp),'review':str(cr),'review_sha256':sha(cr),'native':native,'parent_graph':'root','new_ids':[1200,1201,1202],'guard_facts':facts,'claim_fact':claim,'parent_removed_edges':[c['attachment']['replace']],'parent_added_edges':c['attachment']['new_edges'],'native_phase_id':3,'native_input_remove':[[0,'Out',8,'In']],'native_input_add':[[0,'Out',12,'In'],[0,'Out',13,'In']],'retained_arm_ids':[8,9],'expected_prefabs':['#sts_wat_nid_03_streetstory'],'required_join_types':{'17':'questLogicalXorNodeDefinition','24':'questLogicalAndNodeDefinition'},'native_arm_fact':'CYB-626818','normal_child':'2'})
np=O/'groups/G11/nid02_failure/proposal_01/proposal.json';nr=O/'reviews/worker_b/NID02/review.json';n=read(np);rr=read(nr);assert rr['status'].startswith(('APPROVE','PASS')),rr['status'];native=next(x for x in n['source_pins']if 'nid_02_bugfixing' in x.get('depot',''))
claim=next(k for k in n['initial_guard_facts']if k.endswith('FailureMonitorEntered'))
plans.append({'key':'nid02','depot':n['resource'],'before':n['before'],'proposal':str(np),'proposal_sha256':sha(np),'review':str(nr),'review_sha256':sha(nr),'native':native,'parent_graph':'root','new_ids':n['new_parent_local_ids'],'guard_facts':n['initial_guard_facts'],'claim_fact':claim,'parent_removed_edges':n['parent_removed_edges'],'parent_added_edges':n['parent_added_edges'],'native_phase_id':23,'native_input_remove':[n['native_template']['cloned_only_edge_replacement']['remove']],'native_input_add':[n['native_template']['cloned_only_edge_replacement']['add']],'retained_arm_ids':[12,13],'expected_prefabs':[],'required_join_types':{'41':'questLogicalXorNodeDefinition','9':'questLogicalAndNodeDefinition','48':'questLogicalXorNodeDefinition'},'native_arm_fact':'CYB-651268','normal_child':'2'})
for p in plans:
 assert sha(C/'archive_source'/p['depot'])==p['before'];pin=p['native'];assert sha(pin['binary'])==pin.get('sha256',pin.get('resource_sha256'))
 assert not any(p['claim_fact'].encode()in f.read_bytes()for f in (C/'archive_source').rglob('*')if f.is_file())
write(C/'monitor_plans.json',{'status':'INDEPENDENTLY_SOURCE_APPROVED_BOUNDED_STAGING_PLANS','plans':plans,'canonical_source_unchanged_until_aggregate_validation':str(O/'source_epoch_02.json'),'no_new_depots_or_XL_ids':True})
print({'source_approved_monitors':[p['key']for p in plans],'canonical_epoch':2,'runtime_changes_in_this_step':0})
