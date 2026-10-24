from pathlib import Path
import hashlib,json,shutil
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01';O=C/'diagnosis_01'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077');S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077');B=W/'recovery/h10_h2_diagnosis_01'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def copy(p,d):
 h=sha(p);d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,d);assert h==sha(p)==sha(d);return h
O.mkdir(parents=True,exist_ok=False);B.mkdir(parents=True,exist_ok=False)
receipt={}
for slot in ['AutoSave-11','AutoSave-12']:
 for p in (S/slot).iterdir():
  if p.is_file():receipt[str(p)]={'backup':str(B/slot/p.name),'sha256':copy(p,B/slot/p.name)}
(B/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
inputs={}
for r in ['red4ext/logs/red4ext-2026-10-24-17-42-28.log','bin/x64/plugins/cyber_engine_tweaks/gamelog.log','r6/logs/redscript_rCURRENT.log']:
 inputs[r]=copy(G/r,O/'logs'/Path(r).name)
for p in (G/'r6/scripts/TowerContinued_Housing_H1').glob('*.reds'):inputs[str(p.relative_to(G))]=copy(p,O/'context'/p.name)
p=G/'r6/scripts/PTFR_PreAlpha/PTFR_RestorationBaseline/RestorationBaseline.reds';inputs[str(p.relative_to(G))]=copy(p,O/'context'/p.name)
(O/'inputs.json').write_text(json.dumps({'copied':inputs,'saves':{str(p):sha(p) for p in S.rglob('*') if p.is_file()}},indent=2)+'\n')
for name in ['read_saves','read_systems']:
 s=(W/f'diagnostics/deployment_test_20261024_01/{name}.ps1').read_text(encoding='utf-8-sig')
 s=s.replace('$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent',"$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent\n$outRoot=Join-Path $PSScriptRoot 'candidate_01/diagnosis_01'")
 s=s.replace("@('AutoSave-8','AutoSave-9')","@('AutoSave-11','AutoSave-12')").replace('recovery/deployment_test_20261024_01/','recovery/h10_h2_diagnosis_01/').replace('Join-Path $PSScriptRoot','Join-Path $outRoot')
 s=s.replace("$outRoot=Join-Path $outRoot", "$outRoot=Join-Path $PSScriptRoot")
 if name=='read_saves':
  s=s.replace('$hashMethod=',"foreach($name in @('wat_lch_gunsmith_01_default_on','q001_spawn_wilson_attention','q101_spawn_wilson_attention','mq011_active','wat_lch_gunsmith_01_disabled','q001_wilson_talked','q101_done')){[void]$names.Add($name)}\n$hashMethod=",1)
 (H/f'{name}_01.ps1').write_text(s,encoding='utf-8')
print(json.dumps({'backup_files':len(receipt),'context_files':len(inputs),'save_files':len(list(S.rglob('sav.dat')))}))
