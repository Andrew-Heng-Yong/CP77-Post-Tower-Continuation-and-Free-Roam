"""Resolve only explicitly reviewed resource donors; no sort-based winners."""
from common import *
contract_path=HERE/'donor_review/selection_01.json'
contract=read(contract_path);review=read(HERE/'donor_review/review_01.json')
assert contract['status']=='APPROVED_30_RESOURCE_RECONCILIATION' and review['status']=='PASS'
assert review['contract_sha256']==sha(contract_path)
assert len(contract['rows'])==len({r['depot'] for r in contract['rows']})==30
base={r['depot']:r['sha256'] for r in read(CANDIDATE/'baseline_01.json')['resources']}
resources=[]
for r in contract['rows']:
    assert r['decision']=='RESTORE_REVIEWED_PRECONSOLIDATION_REPAIR' and r['rationale']
    donor=WS/r['source']
    assert donor.resolve().is_relative_to(HERE/'donor_review/selected_raw')
    assert sha(donor)==r['selected_sha256']
    assert base[r['depot']]==r['current_sha256']
    for pin in [r['archived_source']]+r['decoded_sources']+r['evidence']:
        p=Path(pin['path']);p=p if p.is_absolute() else WS/p
        assert sha(p)==pin['sha256'],p
    resources.append({'depot':r['depot'],'key':r['key'],'before':r['current_sha256'],'after':r['selected_sha256'],'donor_raw':str(donor),'repair':r['repair'],'rationale':r['rationale']})
write_new(CANDIDATE/'selected_resources_01.json',{'status':'EXPLICIT_DONOR_SELECTION_VERIFIED','contract_path':str(contract_path),'contract_sha256':sha(contract_path),'resources':resources})
print('30 explicit donors and original repair evidence verified.')
