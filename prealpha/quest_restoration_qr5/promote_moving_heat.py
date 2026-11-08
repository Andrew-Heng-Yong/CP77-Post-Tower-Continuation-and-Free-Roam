"""Publish independently verified fifth repair and prepare one changed rebuild."""
from pathlib import Path
import sys,argparse,json
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;C=O/'candidate_03'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
ap=argparse.ArgumentParser();ap.add_argument('--serialized-review',required=True);args=ap.parse_args()
assert not (O/'source_epoch_06.json').exists()
rp=Path(args.serialized_review).resolve();r=read(rp);assert r['status'].startswith(('PASS','APPROVE')),r['status']
plan=read(C/'moving_heat_plan.json');patch=read(C/'repair_moving_heat/patch.json');tp=C/'repair_moving_heat/verification_03/tests.json';assert read(tp)['status'].startswith('PASS')
assert patch['after']in json.dumps(r),'Independent review must pin exact serialized bytes'
assert sha(C/'archive_source'/patch['depot'])==patch['after']
a=read(O/'approved_changes_03.json');a.update(version=4,supersedes_allowlist=str(O/'approved_changes_03.json'),supersedes_allowlist_sha256=sha(O/'approved_changes_03.json'))
resource={'depot':patch['depot'],'before':patch['before'],'after':patch['after'],'intent':'Restore exact native dedicated MovingHeat prefab lease around future accepted-stage resume child, with existing native guards plus S24FreshIssued0. Preserve already executing root10 descendants and completion edge. Claimed/pending before future9.True may enter new wrapper if rechecks pass; no retrospective lease assignment or new owner polling. Outside-trigger availability before lease remains unproved.','evidence':[plan['proposal'],plan['review'],str(O/'groups/G18/moving_heat_prefab_03/evidence.json'),str(O/'groups/G18/moving_heat_prefab_03/proposal_scope_addendum_01.json')],'tests':[str(tp),str(rp)],'independent_source_review':plan['review'],'independent_source_review_sha256':plan['review_sha256'],'independent_serialized_review':str(rp),'independent_serialized_review_sha256':sha(rp)}
assert all(Path(x).is_file()for x in resource['evidence'])
a['resources'].append(resource);a.update(new_unique_defects=5,new_affected_quests=a['new_affected_quests']+['q304_car_retrieval'],scope='Five existing private resources repaired cumulatively versus QR4; one new versus QR5candidate02. No new depot, XL registration, script or original-body rebuild.')
write(O/'approved_changes_04.json',a)
e=read(O/'source_epoch_05.json');e.update(epoch=6,epoch_key='QR5:06',candidate=str(C),predecessor_epoch_path=str(O/'source_epoch_05.json'),predecessor_epoch_sha256=sha(O/'source_epoch_05.json'),approved_changes_sha256=sha(O/'approved_changes_04.json'),changes=a['resources'],package_state='CANONICAL_SERIALIZED_SOURCE_PACKAGE_STILL_CANDIDATE02_PREDECESSOR',archive_sha256_semantics='Predecessor packaged bytes until next package epoch',scope='Canonical QR5 candidate03 source: five independently source/serialized reviewed repairs versus QR4, adding exact future MovingHeat accepted-body prefab lease to four candidate02 repairs. Package still predecessor until epoch07.',metadata_only=False)
e.pop('metadata_correction',None);e['source_resources'][patch['depot']]=patch['after'];write(O/'source_epoch_06.json',e)
s=(O/'rebuild_candidate02.ps1').read_text(encoding='utf-8-sig').replace('candidate_02','candidate_03').replace('approved_changes_03.json','approved_changes_04.json').replace('source_epoch_02.json','source_epoch_05.json').replace('pinned candidate01','pinned candidate02')
(O/'rebuild_candidate03.ps1').write_text(s,encoding='utf-8')
s=(O/'package_candidate02.py').read_text(encoding='utf-8-sig').replace("C=O/'candidate_02'","C=O/'candidate_03'").replace('approved_changes_03.json','approved_changes_04.json').replace('compile_reuse_02.json','compile_reuse_03.json').replace('source_epoch_03.json','source_epoch_06.json').replace('source_epoch_04.json','source_epoch_07.json').replace("e1['epoch']=4","e1['epoch']=7").replace("e1['epoch_key']='QR5:04'","e1['epoch_key']='QR5:07'").replace("q['source_epoch']=4","q['source_epoch']=7").replace("'new_unique_defects':4","'new_unique_defects':5").replace("'cumulative_repairs':7","'cumulative_repairs':8").replace('Four existing private CR2W','Five existing private CR2W').replace('Fresh-event monitor repair only','Future-entry monitors and accepted-body support-lease repair only')
assert "write(O/'source_epoch_07.json'"in s and "e1['epoch']=7"in s
(O/'package_candidate03.py').write_text(s,encoding='utf-8')
q=read(O/'queue.json');q.update(working_candidate=str(C),source_epoch=6,source_epoch_manifest=str(O/'source_epoch_06.json'),new_unique_defects=6,new_affected_quest_count=6,new_repaired_unique_defects=5,new_blocked_unique_defects=1,changed_resources=5,cumulative_changed_resources_vs_PH3=9,gameplay_repairs=8,package_verification='CANDIDATE03_PACKAGE_PENDING')
write(O/'queue.json',q)
write(C/'source_promotion.json',{'status':'INDEPENDENT_SERIALIZED_APPROVED_SOURCE_EPOCH06_PACKAGE_PENDING','resource':resource,'saved_boundary':resource['intent'],'canonical_epoch':6})
print({'canonical_epoch':6,'changed_resources_vs_QR4':5,'package':'PENDING'})
