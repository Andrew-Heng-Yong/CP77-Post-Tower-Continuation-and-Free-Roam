from pathlib import Path
import hashlib,json,shutil,sys
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01';O=C/'diagnosis_01';O.mkdir(parents=True,exist_ok=False)
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
R=Path(r'C:\Users\Ayong\AppData\Local\REDEngine\ReportQueue\Cyberpunk2077-20261024-170729-6616-17612')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
copied={}
def copy(src,dest):
 before=sha(src);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest);assert sha(src)==sha(dest)==before;copied[str(src)]=before
for p in R.rglob('*'):
 if p.is_file():copy(p,O/'report'/p.relative_to(R))
for name in ['red4ext/logs/red4ext-2026-10-24-17-02-13.log','bin/x64/plugins/cyber_engine_tweaks/gamelog.log','bin/x64/plugins/cyber_engine_tweaks/scripting.log','r6/logs/redscript_rCURRENT.log']:
 copy(G/name,O/'logs'/Path(name).name)
for p in (G/'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1').glob('snapshot*.json'):copy(p,O/'snapshots'/p.name)
copy(Path(r'C:\Users\Ayong\AppData\Local\Temp\codex-clipboard-b811c18a-ca90-4eee-ac69-496d828d92e6.png'),O/'user_screenshot.png')
saves={str(p):sha(p) for p in S.rglob('*') if p.is_file()}
current={str(p.relative_to(G)):sha(p) for root in [G/'r6/scripts',G/'archive/pc/mod',G/'r6/cache',G/'red4ext/plugins'] for p in root.rglob('*') if p.is_file() and p.suffix not in ['.log']}
(O/'inputs.json').write_text(json.dumps({'copied':copied,'saves':saves,'game':current},indent=2)+'\n')
sys.path.insert(0,str(W/'tools'));from inspect_native_crash import Dump
d=Dump(O/'report/Cyberpunk2077.dmp');report=d.report();(O/'exception.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'copies':len(copied),'saves':len(saves),'dump_bytes':(R/'Cyberpunk2077.dmp').stat().st_size,'exception':report},indent=2))
