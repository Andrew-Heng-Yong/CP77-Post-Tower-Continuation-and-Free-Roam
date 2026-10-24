from pathlib import Path
import json,re
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01';O=C/'diagnosis_01'
for p in (C/'native_inspect_01/0000_TowerContinued_SideJobs_S23').rglob('*.json'):
 d=json.loads(p.read_text(encoding='utf-8-sig'));nodes=d['Data']['RootChunk']['graph']['Data']['nodes'];print(p.name)
 for n in nodes:
  n=n['Data'];t={k:v for k,v in n.items() if k not in ['sockets','phaseGraph']};print(json.dumps(t))
# Small H10 sector preserves the ordinary door controller node and placement.
for p in (W/'research/b0_missing_content/h10_sectors/ep1_1_nightcity/json').rglob('*.streamingsector.json'):
 d=json.loads(p.read_text(encoding='utf-8-sig'));r=d['Data']['RootChunk']
 for i,n in enumerate(r.get('nodes',[])):
  ns=json.dumps(n)
  if 'DoorControllerPS' in ns:
   print(p.name,i,ns[:12000]);(O/'h10_door_sector_fragment.json').write_text(json.dumps({'source':str(p),'node_index':i,'node':n},indent=2))
s=(W/'prealpha/loading_cover_lc3/candidate_01/compile_01/compiled.script').read_text(encoding='utf-8-sig')
for term in ['  public func GetTweakDBChoiceRecord()', '  public func GetTweakDBChoiceID()']:
 i=s.index(term);print(s[i:i+550])
