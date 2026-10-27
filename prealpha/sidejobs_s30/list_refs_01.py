import json
from pathlib import Path
from inspect_native_01 import ROOT,SOURCES,walk
SOURCES['coaster_ride']=ROOT/'research/b0_world_interactions/dependencies/json/base/quest/minor_quests/mq006/phases/mq006_rollercoaster_ride_controller.questphase.json'
for label,path in SOURCES.items():
 d=json.loads(path.read_text(encoding='utf-8'))
 deps=sorted({v['DepotPath'].get('$value') for v in walk(d) if isinstance(v.get('DepotPath'),dict) and v['DepotPath'].get('$value')})
 print('\n'+label+' '+str(len(deps)))
 for x in deps:print(x)
