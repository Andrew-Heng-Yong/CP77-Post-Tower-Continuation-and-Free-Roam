"""Add an optional, explicit user-operated master-backup plan; never copy a save."""
from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
p=HERE/'core_manifest_01.json';m=read(p);masterfile=HERE.parent/'selected_master.json';master=read(masterfile)
assert master['status']=='USER_SELECTED_GENUINE_TOWER_MASTER_KEEP_UNTOUCHED' and Path(master['path']).name=='ManualSave-23'
m['master_backup']={'slot':'ManualSave-23','files':master['files'],'policy':'Only on explicit user Install -BackupMaster; verified copy to recovery/master_before/ManualSave-23. No Saved Games writes; never automatically restored.'}
m['proofs'].append({'path':str(masterfile),'sha256':sha(masterfile)})
out=HERE/'core_manifest_02.json';assert not out.exists();out.write_text(json.dumps(m,indent=2)+'\n',encoding='utf8');(HERE/'core_manifest_02.json.sha256').write_text(sha(out)+'\n',encoding='ascii');print(sha(out))
