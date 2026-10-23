"""Read extracted vanilla graph and sector data for Phase 2B-P4 staging research."""
import json
from pathlib import Path
from analyze_q307 import walk

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/phase2b_p4'
SOURCE = ROOT / 'research/q307_extracted/json/ep1/quest/main_quests/q307'

def scalar(v):
    return v.get('$value') if isinstance(v, dict) else v

def main():
    variants, teleports, spawns = [], [], []
    for path in sorted(SOURCE.rglob('*.json')):
        doc = json.loads(path.read_text(encoding='utf-8-sig'))
        for obj, loc, parents in walk(doc):
            chain = [{'type': p['$type'], 'id': p.get('id')} for p in parents if '$type' in p and 'Node' in p['$type'] and 'id' in p]
            context = {'resource': str(path.relative_to(SOURCE)), 'json_path': '.'.join(map(str,loc)), 'nodes': chain}
            if obj.get('$type') == 'questTogglePrefabVariant_NodeTypeParams':
                ref = scalar(obj.get('prefabNodeRef'))
                if any(s in str(ref).lower() for s in ('misty', 'mystic', 'wlc_02_b', 'q307')):
                    variants.append(context | {'prefab': ref, 'states': [{k:scalar(v) for k,v in s.items() if k in ('name','show')} for s in obj.get('variantStates',[])]})
            if obj.get('$type') == 'questTeleportPuppetNodeDefinition':
                params = obj.get('params',{}).get('Data',{})
                ref = scalar(params.get('destinationRef',{}).get('Data',{}).get('entityReference',{}).get('reference'))
                if ref == '#fb_sm_victor':
                    teleports.append(context | {'node_id':obj.get('id'), 'destination':ref, 'offset':params.get('destinationOffset'), 'doNavTest':params.get('doNavTest'), 'healAtTeleport':params.get('healAtTeleport'), 'useFastTravelMechanism':params.get('useFastTravelMechanism')})
            if obj.get('$type') == 'questCommunityTemplate_NodeType':
                entry = scalar(obj.get('communityEntryName'))
                if any(s in str(entry).lower() for s in ('thug','zetatech','alley')):
                    spawns.append(context | {'action':obj.get('action'), 'entry':entry, 'phase':scalar(obj.get('communityEntryPhaseName')), 'spawner':scalar(obj.get('spawnerReference'))})
    OUT.mkdir(exist_ok=True,parents=True)
    result={'variants':variants,'teleports':teleports,'staged_spawns':spawns}
    (OUT/'staging_graph_evidence.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    for row in variants:
        if row['resource'].endswith(('q307_cleanup.questphase.json','q307_03_hospital.questphase.json')):
            print(row['resource'],row['nodes'],row['prefab'],row['states'])
    print('TELEPORT',teleports)
    print('Staged community actions',len(spawns))

if __name__=='__main__':main()
