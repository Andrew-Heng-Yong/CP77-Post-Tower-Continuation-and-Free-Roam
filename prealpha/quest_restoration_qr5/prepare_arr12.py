"""Stage only after exact independent source/proposal approval; never install."""
from pathlib import Path
import sys,shutil
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
C=O/'candidate_01';assert not C.exists(),'Fresh successor required'
rp=O/'groups/G07/reviews/ARR12/verification_03/review.json';r=read(rp)
assert r['status']=='APPROVE_SOURCE_CONFIRMED_DEFECT_AND_TIGHTENED_FUTURE_EVENT_REPAIR_SCOPE'
proposal=Path(r['proposal']);assert sha(proposal)==r['proposal_sha256'];p=read(proposal);e=read(O/'source_epoch_00.json');src=Path(e['candidate'])
delta=r['approved_delta'];depot=delta['resource'];assert e['source_resources'][depot]==p['current_binary_sha256']
fact='PTFRU9_sts_std_arr_12_MonitorEntered';hits=[]
for f in (src/'archive_source').rglob('*'):
 if f.is_file() and fact.encode() in f.read_bytes():hits.append(str(f))
for f in (src/'package/r6/scripts').rglob('*.reds'):
 if fact in f.read_text(encoding='utf-8-sig'):hits.append(str(f))
assert not hits,('New receipt already exists in current mod',hits)
for sub in ['archive_source','package']:
 for f in (src/sub).rglob('*'):assert not (f.stat().st_file_attributes&0x400),'Reparse input refused'
 shutil.copytree(src/sub,C/sub)
native=next(x for x in p['source_pins'] if 'arr_12_bugfixing' in x['depot']);assert sha(native['binary'])==native['sha256']
plan={'status':'APPROVED_EXACT_FUTURE_EVENT_ONLY_ARR12_MONITOR','depot':depot,'before':e['source_resources'][depot],'graph':'root/10','native':native,'proposal':str(proposal),'proposal_sha256':sha(proposal),'review':str(rp),'review_sha256':sha(rp),'guard_facts':delta['private_guard_required_values'],'claim_fact':fact,'new_ids':delta['new_local_ids'],'replace_edge':delta['replace_only'],'native_phase_id':3,'native_input_remove':[0,'Out',15,'In'],'native_input_add':[0,'Out',13,'In'],'scope':'Future65003 event only; arm0/1 unchanged, no reset or retroactive owner adoption; preserve full native failure/reward guards.'}
write(C/'repair_plan.json',plan)
write(O/'baseline.json',{'candidate':str(src),'game':read(O/'prepared.json')['game'],'private_resources':e['source_resources'],'package_files':[{'path':x['path'],'after':x['sha256']}for x in e['package_files']],'scope':'QR4 staged source successor, including all four prior corrected resources'})
write(C/'before_regression.json',{'status':'EXPECTED_FAIL_MISSING_FUTURE_FAILURE_MONITOR','resource':depot,'sha256':plan['before'],'test':'Supported new65003 entry has no owned ARR12 fail-loop-end producer; exact live consumers and retired sole producer pinned by independent raw review','expected_native':'Native root3 waitstart13/Convoy/abandonment branches eventually emit native end1 on genuine failure','source_evidence':str(O/'groups/G04/arr12_failure_01/evidence.json'),'independent_raw_review':str(rp),'independent_checks':r['checks'],'game_writes':0,'save_writes':0})
print({'status':'STAGED_APPROVED_QR4_SUCCESSOR','new_receipt_collisions':hits,'changed_runtime_resources':0})
