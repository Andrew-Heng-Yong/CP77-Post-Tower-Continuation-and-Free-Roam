"""Restore the two verified pre-ending q307 autosaves; preserve current slots."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path

W=Path(__file__).resolve().parents[2]
S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
SOURCE=W/'recovery/pre_ending_autosaves_20261024_01'
OUT=W/'recovery/autosave_restore_20261026_01'
SLOTS=('AutoSave-6','AutoSave-7')
NAMES=('metadata.9.json','sav.dat','screenshot.png')

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1<<20),b''):h.update(block)
 return h.hexdigest().upper()

def closed():
 r=subprocess.run(['powershell','-NoProfile','-Command','Get-Process -Name Cyberpunk2077,REDprelauncher -ErrorAction SilentlyContinue | Select-Object -First 1 Id'],capture_output=True,text=True)
 assert r.returncode in (0,1) and not r.stdout.strip() and not r.stderr.strip(),'Close Cyberpunk 2077 before save restoration'

def source_rows():
 receipt=json.loads((SOURCE/'receipt.json').read_text(encoding='utf-8'))
 assert receipt['status']=='LATEST_TWO_PRE_COMPLETION_AUTOSAVES_BACKED_UP_HASH_VERIFIED'
 rows={r['slot']:r for r in receipt['saves']}
 assert set(rows)==set(SLOTS)
 for slot in SLOTS:
  assert set(rows[slot]['files'])==set(NAMES)
  for name in NAMES:assert sha(SOURCE/slot/name)==rows[slot]['files'][name]['sha256'],(slot,name)
 return rows

def prepare():
 closed();rows=source_rows();assert not OUT.exists(),'Prior restoration backup exists'
 for slot in SLOTS:
  current=S/slot
  assert current.is_dir() and {p.name for p in current.iterdir()}==set(NAMES),slot
  backup=OUT/'current'/slot;backup.mkdir(parents=True,exist_ok=True)
  for name in NAMES:shutil.copy2(current/name,backup/name)
 manifest={'status':'PREPARED_NOT_RESTORED','source_receipt_sha256':sha(SOURCE/'receipt.json'),'slots':{slot:{'current':{n:sha(OUT/'current'/slot/n) for n in NAMES},'restore':{n:rows[slot]['files'][n]['sha256'] for n in NAMES}} for slot in SLOTS}}
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'status':manifest['status'],'slots':list(SLOTS),'current_backup':str(OUT/'current')}))

def restore():
 closed();rows=source_rows();m=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
 assert m['status']=='PREPARED_NOT_RESTORED'
 assert sha(SOURCE/'receipt.json')==m['source_receipt_sha256']
 for slot in SLOTS:
  for name in NAMES:
   assert sha(S/slot/name)==m['slots'][slot]['current'][name],('current slot changed',slot,name)
   assert sha(OUT/'current'/slot/name)==m['slots'][slot]['current'][name],('preserved backup changed',slot,name)
 try:
  for slot in SLOTS:
   for name in NAMES:
    shutil.copy2(SOURCE/slot/name,S/slot/name)
    assert sha(S/slot/name)==m['slots'][slot]['restore'][name],('restore readback',slot,name)
 except Exception:
  for slot in SLOTS:
   for name in NAMES:shutil.copy2(OUT/'current'/slot/name,S/slot/name)
  raise
 m['status']='RESTORED_PRE_ENDING_Q307'
 (OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8')
 verify()

def verify():
 m=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
 assert m['status']=='RESTORED_PRE_ENDING_Q307'
 for slot in SLOTS:
  for name in NAMES:
   assert sha(S/slot/name)==m['slots'][slot]['restore'][name],(slot,name)
 print(json.dumps({'status':'VERIFIED_PRE_ENDING_Q307','slots':list(SLOTS),'current_versions_preserved':str(OUT/'current')}))

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('action',choices=('prepare','restore','verify'));action=a.parse_args().action
 {'prepare':prepare,'restore':restore,'verify':verify}[action]()
