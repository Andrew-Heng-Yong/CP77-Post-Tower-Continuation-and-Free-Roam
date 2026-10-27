import json
from pathlib import Path

W = Path(__file__).resolve().parent / 'candidate_04/world_coaster_review'

def walk(x):
    if isinstance(x, dict):
        yield x
        for v in x.values(): yield from walk(v)
    elif isinstance(x, list):
        for v in x: yield from walk(v)

for name in ('coaster.scene', 'coaster_ride.questphase', 'coaster_owner.questphase', 'coaster_gate.questphase'):
    root = json.loads((W / (name+'.json')).read_text())['Data']['RootChunk']
    print('\n', name, 'root type', root.get('$type'))
    print('depot refs', sorted({str(v.get('$value')) for x in walk(root) for k,v in x.items() if isinstance(v,dict) and k in ('sceneFile','phaseResource','sceneResource') and ('$value' in v or 'DepotPath' in v)}))
    print('paths', sorted({str(x.get('DepotPath',{}).get('$value')) for x in walk(root) if 'DepotPath' in x and isinstance(x['DepotPath'],dict) and any(t in str(x['DepotPath']).lower() for t in ('scene','questphase'))}))
    if name.endswith('.scene'):
        print('actors', [(x.get('actorName'),x.get('actorId')) for x in root.get('actors',[])])
        lines = {x['itemId']['id']: x['speaker']['id'] for x in walk(root.get('screenplayStore',{})) if x.get('$type')=='scnscreenplayDialogLine'}
        dialogs = [x for x in walk(root.get('sceneGraph',{})) if x.get('$type')=='scnDialogLineEvent']
        print('dialog count',len(dialogs),'speakers', {k:sum(lines.get(x.get('screenplayLineId',{}).get('id'))==k for x in dialogs) for k in sorted(set(lines.values()))})
        print('johnny lines', [(x.get('screenplayLineId',{}).get('id'),x.get('id',{}).get('id')) for x in dialogs if lines.get(x.get('screenplayLineId',{}).get('id'))==5])
    else:
        print('scene refs', sorted({str(x.get('DepotPath',{}).get('$value')) for x in walk(root) if 'DepotPath' in x and 'scene' in str(x.get('DepotPath')).lower()}))
