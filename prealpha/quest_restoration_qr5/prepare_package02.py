"""Prepare guarded packaging entrypoint; does not build or mutate candidates."""
from pathlib import Path
O=Path(__file__).resolve().parent
target=O/'package_candidate02.py';assert not target.exists()
s=(O/'package_candidate.py').read_text(encoding='utf-8-sig')
s=s.replace("C=O/'candidate_01'","C=O/'candidate_02'").replace('approved_changes_02.json','approved_changes_03.json').replace("O/'compile_reuse.json'","O/'compile_reuse_02.json'").replace('One private CR2W changed','Four existing private CR2W resources changed cumulatively versus QR4')
s=s.replace("'new_unique_defects':1,'new_affected_quests':['sts_std_arr_12'],'cumulative_repairs':4","'new_unique_defects':4,'new_affected_quests':a['new_affected_quests'],'cumulative_repairs':7")
s=s.replace("e1=read(O/'source_epoch_01.json');e1['epoch']=2;e1['epoch_key']='QR5:02'","e1=read(O/'source_epoch_03.json');e1['epoch']=4;e1['epoch_key']='QR5:04'")
s=s.replace("str(O/'source_epoch_01.json')","str(O/'source_epoch_03.json')").replace("sha(O/'source_epoch_01.json')","sha(O/'source_epoch_03.json')").replace("write(O/'source_epoch_02.json',e1)","write(O/'source_epoch_04.json',e1)")
s=s.replace("q['source_epoch']=2;q['source_epoch_manifest']=str(O/'source_epoch_02.json')","q['source_epoch']=4;q['source_epoch_manifest']=str(O/'source_epoch_04.json')")
s=s.replace("p['repair_epochs'].append(str(O/'source_epoch_02.json'));p['new_defects'][0]['status']='INDEPENDENT_SERIALIZED_VERIFIED_PACKAGED_FINAL_PACKAGE_REVIEW_PENDING'","p['repair_epochs'].extend([str(O/'source_epoch_03.json'),str(O/'source_epoch_04.json')]);p['final_package_review']='PENDING_INDEPENDENT_DIFF'")
assert "write(O/'source_epoch_02.json'"not in s and "e1['epoch']=4"in s
target.write_text(s,encoding='utf-8')
print({'prepared':str(target),'runtime_writes':0})
