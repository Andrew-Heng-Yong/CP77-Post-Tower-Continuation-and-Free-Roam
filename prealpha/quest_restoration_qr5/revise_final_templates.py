"""Align unexecuted final report templates with the fifth reviewed repair."""
from pathlib import Path
O=Path(__file__).resolve().parent
p=O/'write_reports.py';s=p.read_text(encoding='utf-8')
pairs={
 'approved_changes_03.json':'approved_changes_04.json',
 'The four packaged QR5 changes restore native ARR12 failure monitoring, Steven’s future U9 actor consumer, Cheetah’s fallback monitor and NID02’s van-failure monitor. They preserve native callbacks, joins, journal/reward/cleanup payloads and saved identities. They enroll only future supported events; they do not retrofit already-entered saved owners.':'The five packaged QR5 changes restore native ARR12 failure monitoring, Steven’s future U9 actor consumer, Cheetah’s fallback monitor, NID02’s van-failure monitor and MovingHeat’s dedicated accepted-body prefab lease. They preserve native callbacks, joins, journal/reward/cleanup payloads and saved identities. Only future attachment edges gain support; already executing child descendants are unchanged. A claimed MovingHeat owner still pending before9.True can use the new wrapper if its late guards pass.',
 '275 assertion events and 12 mutations':'324 assertion events and 17 mutations',
 '454 assertion events and 25 raw-document mutations':'513 assertion events and 30 raw-document mutations',
 'Current candidate package review adds 280 checks; the metadata-only epoch05 scope correction has a separate 14-check attestation.':'The independent final package review checks all packed keys, bytes, ZIP members, unchanged files, prior repairs, compile-input equality and canonical epoch08 linkage. Metadata-only scope corrections are explicit and do not change package bytes.',
 'groups/G11/reviews/QR5candidate02/verification_01/REPORT.json':'groups/G11/reviews/QR5candidate03/verification_01/REPORT.json',
 'compile_reuse_02.json':'compile_reuse_03.json',
 'and the four QR5 repairs.':'and the five QR5 repairs.',
 '- `source_epoch_05.json` is a metadata-only correction of epoch04 inherited ARR12-only prose. Same1574source/51package bytes. Package manifest\'s `new_unique_defects=4` describes packaged repairs; full confirmed/blocked counts are in the current ledger.':'- `source_epoch_08.json` is a metadata-only correction of epoch07 inherited source-stage package-pending prose. Same1574source/51package bytes. Package manifest\'s `new_unique_defects=5` describes packaged repairs; full ledger has6 new confirmed defects including blocked CVI02. Epoch05 is the preserved earlier candidate02 metadata correction.',
 'Dynami' : 'Dynami'
}
for a,b in pairs.items():
 assert a in s,a;s=s.replace(a,b)
s=s.replace("and [repair adjudication](adjudications/repairs_01.json)","[primary repair adjudication](adjudications/repairs_01.json) and [MovingHeat adjudication](adjudications/moving_heat_01.json)")
s=s.replace('The stock TDB capture is bounded:','The main stock TDB capture is bounded:').replace('These are source definitions, not runtime merged winners or executed rewards.','A separate one-record depth0 supplement resolves the exact native MovingHeat vehicle alias; its child references remain open. These are source definitions, not runtime merged winners or executed rewards.')
s=s.replace('and inherited source-epoch prose.','the flattened-fact false tier-cohort restriction, and inherited source-epoch prose.')
s=s.replace('No gameplay certification.','No gameplay certification.')
# Third focused recheck, with actual existing CLI and expected result.
needle='& C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B prealpha/quest_restoration_qr5/check_steven_actor.py --output diagnostics/qr6_recheck_NEW/steven'
assert needle in s;s=s.replace(needle,needle+'\n& C:/Users/Ayong/.local/bin/python3.14.exe -X utf8 -B prealpha/quest_restoration_qr5/check_moving_heat.py --output diagnostics/qr6_recheck_NEW/moving_heat')
s=s.replace('Expected:126checks/6raw mutations and91checks/2raw mutations, respectively','Expected:126checks/6raw mutations,91checks/2raw mutations and49checks/5raw mutations, respectively')
p.write_text(s,encoding='utf-8')
p=O/'finalize_qr5.py';s=p.read_text(encoding='utf-8');needle="O/'groups/G16/timer_arithmetic_correction_01.json']";assert needle in s
s=s.replace(needle,"O/'groups/G16/timer_arithmetic_correction_01.json',O/'adjudications/moving_heat_01.json',O/'metadata_corrections_02.json',O/'groups/G18/moving_heat_prefab_03/proposal_scope_addendum_01.json',O/'shared/tier3_condition_readback_01/disjunction_tests.json']")
p.write_text(s,encoding='utf-8')
print({'updated_unexecuted_final_templates':2,'runtime_changes':0})
