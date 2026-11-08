"""Final packaged-state metadata; preserve source-stage wording as epoch07."""
from pathlib import Path
import sys
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
assert not (O/'source_epoch_08.json').exists()
e=read(O/'source_epoch_07.json');old=e['scope'];assert 'Package still predecessor' in old
e.update(epoch=8,epoch_key='QR5:08',metadata_only=True,predecessor_epoch_path=str(O/'source_epoch_07.json'),predecessor_epoch_sha256=sha(O/'source_epoch_07.json'),scope='Canonical QR5 candidate03: five independently source/serialized reviewed private-resource repairs versus QR4, all1574payloads rebuilt/read back in the current51path staged package. Original primary four repairs plus exact future MovingHeat accepted-body prefab lease. Installed PH3 unchanged; no gameplay certification.',metadata_correction={'old_scope':old,'reason':'Epoch07 inherited epoch06 source-stage package-pending prose; hashes/package_state/manifest correctly identify current rebuilt package. Scope only corrected; all source/package bytes unchanged.'})
write(O/'source_epoch_08.json',e)
q=read(O/'queue.json');q.update(source_epoch=8,source_epoch_manifest=str(O/'source_epoch_08.json'));write(O/'queue.json',q)
write(O/'metadata_corrections_02.json',{'status':'EXPLICIT_METADATA_ONLY_FINAL_SCOPE_SUPERSESSION','original_epoch07_preserved':sha(O/'source_epoch_07.json'),'canonical_epoch08':sha(O/'source_epoch_08.json'),'source_and_package_bytes_changed':False,'old_scope':old,'new_scope':e['scope'],'manifest_count_note':'candidate03.package_manifest.new_unique_defects=5 counts packaged repairs; full confirmed ledger has6 including blockedCVI02. Prior metadata_corrections.json is the preserved candidate02/epoch05 correction, not current candidate metadata.'})
print({'canonical_epoch':8,'metadata_only':True})
