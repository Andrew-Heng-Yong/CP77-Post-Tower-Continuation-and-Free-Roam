"""Inventory extracted interaction owners without starting them in game."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/b0_world_interactions'

def walk(value):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk(item)

def value(obj):
    return obj.get('$value') if isinstance(obj, dict) else obj

def summarize(path, base=None):
    base = base or OUT / 'extracted/json'
    root = json.loads(path.read_text(encoding='utf-8-sig'))['Data']['RootChunk']
    objects = list(walk(root))
    return {
        'resource': str(path.relative_to(base)).removesuffix('.json').replace('/', '\\'),
        'root_type': root['$type'],
        'prefabs': [value(p['prefabNodeRef']) for p in root.get('phasePrefabs', [])],
        'phases': sorted({value(o['phaseResource']['DepotPath']) for o in objects if 'phaseResource' in o} - {'0'}),
        'scenes': sorted({value(o['sceneFile']['DepotPath']) for o in objects if 'sceneFile' in o} - {'0'}),
        'node_refs': sorted({value(o) for o in objects if o.get('$type') == 'NodeRef'} - {'0', None}),
        'facts': sorted({o['factName'] for o in objects if 'factName' in o}),
        'writers': [o for o in objects if o.get('$type') == 'questSetVar_NodeType'],
        'node_types': sorted({o['$type'] for o in objects if o.get('$type', '').endswith('NodeDefinition')}),
        'root_nodes': [{'id': n['Data']['id'], 'type': n['Data']['$type']} for n in root.get('graph', {}).get('Data', {}).get('nodes', [])],
    }

if __name__ == '__main__':
    rows = [summarize(p) for p in sorted((OUT / 'extracted/json').rglob('*.json'))]
    (OUT / 'inventory.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
    for row in rows:
        print(json.dumps({k: row[k] for k in ['resource', 'prefabs', 'phases', 'scenes', 'facts', 'writers']}))
