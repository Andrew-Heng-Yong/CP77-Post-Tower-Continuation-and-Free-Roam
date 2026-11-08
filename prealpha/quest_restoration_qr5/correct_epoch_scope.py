"""Metadata-only supersession of inherited ARR12-only prose, caught by peer."""
from pathlib import Path
import sys
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
assert not (O/'source_epoch_05.json').exists()
e=read(O/'source_epoch_04.json');old=e['scope'];assert 'after one 'in old
e.update(epoch=5,epoch_key='QR5:05',scope='Canonical QR5 candidate02: four independently reviewed private-resource repairs versus QR4 (ARR12, Steven future actor, Cheetah fallback, NID02 van failure); all1574 payloads rebuilt/read back. Other investigations use frozen QR5:00 with exact unchanged-resource or affected-source applicability evidence. PH3 remains installed unchanged.',metadata_only=True,predecessor_epoch_path=str(O/'source_epoch_04.json'),predecessor_epoch_sha256=sha(O/'source_epoch_04.json'),metadata_correction={'previous_scope':old,'reason':'Independent package reviewer C detected inherited ARR12-only prose while all source hashes/allowlist/package correctly contained four repairs. No resource/package/manifest bytes changed.'})
write(O/'source_epoch_05.json',e)
q=read(O/'queue.json');q.update(source_epoch=5,source_epoch_manifest=str(O/'source_epoch_05.json'));write(O/'queue.json',q)
write(O/'metadata_corrections.json',{'status':'EXPLICIT_METADATA_ONLY_SCOPE_SUPERSESSION','original_epoch04_preserved':sha(O/'source_epoch_04.json'),'canonical_epoch05':sha(O/'source_epoch_05.json'),'runtime_resource_and_package_changes':False,'old_scope':old,'new_scope':e['scope'],'package_manifest_count_note':'Manifest new_unique_defects=4 counts repaired defects packaged here. The defect ledger separately counts the additional confirmed blocked CVI02 defect.'})
print({'canonical_epoch':5,'metadata_only':True,'resources_changed':0})
