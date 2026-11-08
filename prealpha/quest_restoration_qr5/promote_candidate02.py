"""Coordinator gate: publish only independently approved serialized successor bytes."""
from pathlib import Path
import sys,copy
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;C=O/'candidate_02'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
assert not (O/'source_epoch_03.json').exists()
plans=read(C/'monitor_plans.json')['plans'];actor=read(C/'actor_repair_plan.json')
items=[('steven',actor,O/'reviews/worker_a/STEVEN_serialized/verification_02/review.json',C/'repair_steven/verification_02/tests.json')]
items += [(p['key'],p,O/('reviews/worker_a/CHEETAH_serialized/verification_01/review.json'if p['key']=='cheetah'else'reviews/worker_b/NID02_serialized/verification_01/review.json'),C/'monitor_verification_01/tests.json')for p in plans]
a=read(O/'approved_changes_02.json');a.update(version=3,status='APPROVED_EXACT_SERIALIZED_SUCCESSOR_FOR_PACKAGE_VALIDATION',supersedes_allowlist=str(O/'approved_changes_02.json'),supersedes_allowlist_sha256=sha(O/'approved_changes_02.json'))
for key,p,rp,tp in items:
 r=read(rp);t=read(tp);patch=read(C/('repair_'+key)/'patch.json')
 assert r['status'].startswith(('PASS','APPROVE')),r['status'];assert t['status'].startswith('PASS')
 assert sha(C/'archive_source'/p['depot'])==patch['after'];assert sha(O/'candidate_01/archive_source'/p['depot'])==patch['before']
 assert sha(p['proposal'])==p['proposal_sha256']and sha(p['review'])==p['review_sha256']
 a['resources'].append({'depot':p['depot'],'before':patch['before'],'after':patch['after'],'intent':{'steven':'Future U9 Steven actor-only helper with ordered enrollment and late Ana choice/history fences; preserve native invitation timer/SMS and old S23 owner.','cheetah':'Future Cheetah fallback monitor, preserving native XOR/AND and exact shared prefab lease; bypass original arm prefix without resetting it.','nid02':'Future Many Ways van-failure monitor, preserving native health/water/listener/cleanup/journals; bypass original arm prefix without resetting it.'}[key],'evidence':[p['proposal'],p['review']],'tests':[str(tp),str(rp)],'independent_source_review':p['review'],'independent_source_review_sha256':p['review_sha256'],'independent_serialized_review':str(rp),'independent_serialized_review_sha256':sha(rp)})
a.update(new_unique_defects=4,new_affected_quests=['sts_std_arr_12','sts_ep1_08_steven_meeting_night_city','sts_wat_nid_03','sts_wat_nid_02'],scope='Four existing private resource repairs cumulative versus QR4; three new relative to QR5candidate01. Spy in the Jungle also depends on the Steven repair carrier and requires preservation review. No new depots, XL registrations, scripts, game or save changes.')
assert len(a['resources'])==4;write(O/'approved_changes_03.json',a)
e=read(O/'source_epoch_02.json');e.update(epoch=3,epoch_key='QR5:03',candidate=str(C),predecessor_epoch_path=str(O/'source_epoch_02.json'),predecessor_epoch_sha256=sha(O/'source_epoch_02.json'),package_state='CANONICAL_SERIALIZED_SOURCE_PACKAGE_STILL_CANDIDATE01_PREDECESSOR',archive_sha256_semantics='Predecessor packaged archive until next packaging epoch',approved_changes_sha256=sha(O/'approved_changes_03.json'),changes=a['resources'])
for r in a['resources']:e['source_resources'][r['depot']]=r['after']
assert len(e['source_resources'])==1574
write(O/'source_epoch_03.json',e)
# Fresh guarded builder derived from inspected predecessor; candidate02 begins with candidate01 package.
s=(O/'rebuild_candidate.ps1').read_text(encoding='utf-8-sig').replace("='candidate_01'","='candidate_02'").replace("'candidate_01'))","'candidate_02'))").replace('approved_changes_02.json','approved_changes_03.json')
start=s.index('foreach($r in $b.package_files)');end=s.index('$archive=Join-Path',start)
s=s[:start]+"$prior=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'source_epoch_02.json') -Raw|ConvertFrom-Json -Depth 100\nforeach($r in $prior.package_files){\n $p=Join-Path (Join-Path $C 'package') $r.path\n if((Get-FileHash -LiteralPath $p).Hash -cne $r.sha256){throw 'Package differs from pinned candidate01 before rebuild'}\n}\n"+s[end:]
assert "Join-Path $PSScriptRoot 'candidate_02'"in s
(O/'rebuild_candidate02.ps1').write_text(s,encoding='utf-8')
q=read(O/'queue.json');q.update(working_candidate=str(C),source_epoch=3,source_epoch_manifest=str(O/'source_epoch_03.json'),changed_resources=4,cumulative_changed_resources_vs_PH3=8,gameplay_repairs=7,package_verification='CANDIDATE02_SOURCE_APPROVED_PACKAGE_PENDING');write(O/'queue.json',q)
print({'canonical_epoch':3,'approved_changed_resources_vs_QR4':4,'new_vs_candidate01':3,'package':'PENDING'})
