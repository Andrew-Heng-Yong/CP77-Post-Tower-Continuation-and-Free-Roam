"""Explicit metadata-only successor after independent linkage review."""
from pathlib import Path
import sys,copy
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,csvwrite
assert not (O/'source_epoch_03.json').exists(),'Preserve metadata correction'
e=read(O/'source_epoch_02.json');m=read(O/'candidate_01/package_manifest.json');old=e['archive_sha256']
assert old!=m['archive_sha256']
assert next(r['sha256'] for r in e['package_files'] if r['path']=='archive/pc/mod/zzzz_PTFR_Combined.archive')==m['archive_sha256']
e['epoch']=3;e['archive_sha256']=m['archive_sha256'];e['xl_sha256']=m['xl_sha256'];e['supersedes_metadata_of']={'path':str(O/'source_epoch_02.json'),'sha256':sha(O/'source_epoch_02.json'),'stale_top_level_archive_sha256':old,'correct_archive_sha256':m['archive_sha256']};e['metadata_only']=True;e['resource_hashes_changed_since_epoch02']=False
write(O/'source_epoch_03.json',e)
q=read(O/'queue.json');q['source_epoch']=3;q['source_epoch_manifest']=str(O/'source_epoch_03.json')
for x in q['quests']:
 if x.get('source_epoch')==2:x['source_epoch']=3
 for v in x['contracts'].values():
  if v.get('effective_source_epoch')==2:v['effective_source_epoch']=3
rows=read(O/'contract_status_matrix.json')
for r in rows:
 if r.get('effective_source_epoch')==2:r['effective_source_epoch']=3
write(O/'queue.json',q);write(O/'quest_status_matrix.json',q['quests']);write(O/'contract_status_matrix.json',rows)
for name,data in [('quest_status_matrix.csv',q['quests']),('contract_status_matrix.csv',rows)]:
 fields=list(dict.fromkeys(k for r in data for k in r));csvwrite(O/name,[{k:r.get(k) for k in fields} for r in data])
cp=read(O/'checkpoint.json');cp['source_epoch']=3;cp['source_epoch_manifest']=str(O/'source_epoch_03.json');cp['queue_sha256']=sha(O/'queue.json');write(O/'checkpoint.json',cp)
p=read(O/'progress.json');p['repair_epochs'].append(str(O/'source_epoch_03.json'));p['metadata_correction']='epoch03corrects inherited predecessor top-level archive hash; source/package bytes unchanged';write(O/'progress.json',p)
write(O/'metadata_corrections.json',{'status':'EXPLICIT_METADATA_ONLY_SUPERSESSION','source_epoch_02_preserved':sha(O/'source_epoch_02.json'),'current_source_epoch':3,'current_manifest':str(O/'source_epoch_03.json'),'reason':'Epoch02package_files and actual build/manifest/ZIP used new archive hash; its top-level archive_sha256 was inherited from QR3. Independent reviewer caught stale duplicate metadata.','before':old,'after':m['archive_sha256'],'runtime_resource_or_package_changes':False})
print({'status':'CORRECTED_EPOCH03_METADATA_ONLY','archive_sha256':m['archive_sha256']})
