from pathlib import Path
import hashlib,json,shutil
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01';O=C/'diagnosis_01';G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077');S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077');B=W/'recovery/h10_h3_diagnosis_01'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def copy(p,d):
 h=sha(p);d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,d);assert sha(p)==sha(d)==h;return h
O.mkdir(parents=True,exist_ok=False);B.mkdir(parents=True,exist_ok=False);receipt={};inputs={}
for p in (S/'AutoSave-13').iterdir():
 if p.is_file():receipt[str(p)]={'backup':str(B/'AutoSave-13'/p.name),'sha256':copy(p,B/'AutoSave-13'/p.name)}
(B/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
for rel in ['red4ext/logs/red4ext-2026-10-24-18-17-21.log','r6/logs/redscript_rCURRENT.log','bin/x64/plugins/cyber_engine_tweaks/gamelog.log','bin/x64/plugins/cyber_engine_tweaks/cyber_engine_tweaks.log']:
 inputs[rel]=copy(G/rel,O/'logs'/Path(rel).name)
for p in (G/'r6/scripts/TowerContinued_Housing_H1').glob('*.reds'):inputs[str(p.relative_to(G))]=copy(p,O/'context'/p.name)
(O/'inputs.json').write_text(json.dumps({'copied':inputs,'saves':{str(p):sha(p) for p in S.rglob('*') if p.is_file()}},indent=2)+'\n')
for src in ['read_saves_01.ps1','read_systems_01.ps1']:
 s=(W/'prealpha/h10_h2'/src).read_text(encoding='utf-8-sig').replace("@('AutoSave-11','AutoSave-12')","@('AutoSave-13')").replace('recovery/h10_h2_diagnosis_01/','recovery/h10_h3_diagnosis_01/')
 (H/src).write_text(s,encoding='utf-8')
s=(W/'diagnostics/deployment_test_20261024_01/read_doors.ps1').read_text(encoding='utf-8-sig')
s=s.replace("$out=Join-Path $PSScriptRoot 'doors_01'","$out=Join-Path $PSScriptRoot 'candidate_01/diagnosis_01/doors_01'")
s=s.replace("@('AutoSave-8','AutoSave-9')","@('AutoSave-13')").replace('recovery/deployment_test_20261024_01/','recovery/h10_h3_diagnosis_01/')
s=s.replace("$doors=@($ps.Entries|Where-Object Id -in @([uint64]750000000011001,[uint64]750000000011002))","$doors=@($ps.Entries|Where-Object {$_.Data.GetType().Name -eq 'DoorControllerPS' -or ($_.Data -is [WolvenKit.RED4.Types.IDynamicClass] -and $_.Data.ClassName.ToString() -eq 'DoorControllerPS')})")
(H/'read_doors_01.ps1').write_text(s,encoding='utf-8')
print(json.dumps({'backup_files':len(receipt),'saves':len(list(S.rglob('sav.dat')))}))
