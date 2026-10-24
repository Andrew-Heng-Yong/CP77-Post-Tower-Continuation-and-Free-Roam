from pathlib import Path
import json
H=Path(__file__).resolve().parent;W=H.parent.parent;O=H/'candidate_01/diagnosis_01'
p=W/'research/sidejobs_s28/vehicles/world_03/json/ep1_1_nightcity_always_loaded_1.streamingsector.json'
d=json.loads(p.read_text(encoding='utf-8-sig'));r=d['Data']['RootChunk'];print('root',list(r))
rows=[]
def walk(x,path):
 if isinstance(x,dict):
  typ=x.get('$type','')
  if typ.startswith('world') and 'debugName' in x and any(t in x['debugName'].get('$value','') for t in ['q001_door_v','v_room_stash']):
   rows.append({'path':path,'value':x})
  for k,v in x.items():walk(v,path+'/'+k)
 elif isinstance(x,list):
  for i,v in enumerate(x):walk(v,path+'/'+str(i))
walk(r,'root')
(O/'world_doors_01.json').write_text(json.dumps(rows,indent=2))
for row in rows:print(row['path'],json.dumps(row['value'])[:600])
print('matches',len(rows))
