from pathlib import Path
import json,hashlib,shutil
H=Path(__file__).resolve().parent; W=H.parent.parent
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
C=H/'candidate_01'; O=C/'diagnosis_01';O.mkdir(parents=True,exist_ok=False)
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
logs=['red4ext/logs/red4ext-2026-10-24-16-30-20.log','r6/logs/redscript_rCURRENT.log','bin/x64/plugins/cyber_engine_tweaks/gamelog.log','bin/x64/plugins/cyber_engine_tweaks/scripting.log']
for name in logs:shutil.copyfile(G/name,O/Path(name).name)
receipt={'logs':{name:sha(G/name) for name in logs},'saves':{str(p):sha(p) for p in S.rglob('*') if p.is_file()},'installed':{str(p.relative_to(G)):sha(p) for root in [G/'r6/scripts',G/'archive/pc/mod',G/'red4ext/plugins',G/'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1'] for p in root.rglob('*') if p.is_file() and p.suffix.lower() not in ['.log']}}
(O/'inputs.json').write_text(json.dumps(receipt,indent=2)+'\n')
phase=json.loads((W/'prealpha/loading_cover_lc1/candidate_02/native_phase.json').read_text())
nodes=phase['Data']['RootChunk']['graph']['Data']['nodes']
for n in nodes:
 d=n['Data'];id=d.get('id')
 if isinstance(id,dict):id=id.get('value')
 if str(id) in [str(i) for i in range(140,147)]+['110','111','112','113','114','159','161','176','177','178','179','180','181']:
  print(json.dumps({k:v for k,v in d.items() if k not in ['sockets']},ensure_ascii=False))
print('Captured',len(receipt['saves']),'save hashes and',len(receipt['installed']),'installed hashes')
