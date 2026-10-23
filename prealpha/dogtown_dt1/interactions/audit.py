"""Read-only Dogtown service inventory. Does not write game state or build resources."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def scalar(value):
    return value.get('$value') if isinstance(value, dict) else value


def inspect(path):
    data = json.loads(path.read_text(encoding='utf-8-sig'))
    nodes = [v for v in walk(data) if str(v.get('$type', '')).endswith('NodeDefinition')]
    refs = sorted({scalar(v['DepotPath']) for v in walk(data) if 'DepotPath' in v
                   and scalar(v['DepotPath']) not in ('0', None)})
    writers = []
    for n in nodes:
        for v in walk({k: val for k, val in n.items() if k not in ('sockets', 'phaseGraph')}):
            if v.get('$type') == 'questSetVar_NodeType':
                writers.append({'node': n['id'], 'fact': v['factName'], 'value': v['value'],
                                'exact': v['setExactValue']})
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path),
            'node_count': len(nodes), 'node_types': dict(sorted(Counter(n['$type'] for n in nodes).items())),
            'references': refs, 'writers': writers,
            'facts': sorted({v['factName'] for v in walk(data) if 'factName' in v}),
            'scene_entries': [{'node': n['id'], 'scene': scalar(n.get('sceneFile', {}).get('DepotPath'))}
                              for n in nodes if n['$type'] == 'questSceneNodeDefinition']}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', required=True)
    args = p.parse_args()
    out = (ROOT / args.out).resolve()
    if not out.is_relative_to(ROOT / 'research/dogtown_dt1/interactions'):
        raise ValueError('Output outside audit evidence root')
    if out.exists():
        raise FileExistsError(out)
    native = ROOT / 'research/dogtown_dt1/interactions/native_01/json'
    sources = [ROOT / 'research/courier_c1/roots_01/json/ep1/openworld/ep1_open_world.questphase.json']
    sources += sorted(native.rglob('*.json'))
    sources += [ROOT / 'research/b0_mirror_investigation/additional/json/ep1/openworld/scene/mirrors/mirrors_ep1_interactions_control.questphase.json']
    records = [inspect(path) for path in sources]
    result = {'status': 'READ_ONLY_NATIVE_INVENTORY_NOT_LIVE_PROOF', 'native_writes': 0,
              'inspector_sha256': sha(Path(__file__)), 'sources': records,
              'note': 'Native writer lists describe source payloads; no payload is executed by this audit.'}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(out), 'sources': len(records),
                      'nodes': sum(r['node_count'] for r in records)}))


if __name__ == '__main__':
    main()
