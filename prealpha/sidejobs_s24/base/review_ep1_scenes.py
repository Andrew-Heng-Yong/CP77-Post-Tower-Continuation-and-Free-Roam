"""Independent read-only scene journal writer inventory for S24 EP1 review.

Does not establish game-engine scheduling or replace native failure-edge review.
It resolves serialized handles, identifies actual root journal writer nodes, and
reports their incoming scene socket mappings (rather than counting Failed labels).
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / 'prealpha/sidejobs_s24/ep1/contract02.json'
OUT = ROOT / 'research/sidejobs_s24/base/ep1_scene_review_01.json'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def walk(v):
    if isinstance(v, dict):
        yield v
        for x in v.values():
            yield from walk(x)
    elif isinstance(v, list):
        for x in v:
            yield from walk(x)


def value(v):
    return v.get('$value') if isinstance(v, dict) else v


def main():
    contract = json.loads(CONTRACT.read_text(encoding='utf-8-sig'))
    result = {'contract_sha256': sha(CONTRACT), 'reviewer_sha256': sha(Path(__file__)),
              'scope': 'Scene root journal writers and actual incoming sockets only',
              'owners': []}
    for owner in contract['owners']:
        if owner['key'] not in {'MQ306_FRESH', 'Q304_FRESH'}:
            continue
        entry = {'owner': owner['key'], 'scenes': [], 'root_writers': []}
        rootpath = 'ep1/quests/minor_quest/' + owner['id']
        for depot in owner['native_dependencies']:
            if not depot.endswith('.scene'):
                continue
            matches = list((ROOT/'research/sidejobs_s24/ep1').glob('native_*/json/' + depot.replace('\\', '/') + '.json'))
            assert len(matches) == 1, (depot, matches)
            path = matches[0]
            obj = json.loads(path.read_text(encoding='utf-8-sig'))
            handles = {d['HandleId']: d['Data'] for d in walk(obj) if 'HandleId' in d and 'Data' in d}

            def resolve(v, trail=()):
                if isinstance(v, list):
                    return [resolve(x, trail) for x in v]
                if isinstance(v, dict):
                    if 'HandleRefId' in v or 'HandleId' in v:
                        hid = v.get('HandleRefId', v.get('HandleId'))
                        if hid == '-1':
                            return None
                        assert hid not in trail, (path, hid, trail)
                        return resolve(handles[hid], trail + (hid,))
                    return {k: resolve(x, trail) for k, x in v.items() if k != 'sockets'}
                return v

            nodes = [d for d in walk(obj) if d.get('$type') == 'scnQuestNode']
            scene = {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path),
                     'quest_nodes': len(nodes), 'root_path_refs': 0}
            # A non-quest scene event root ref is significant; do not silently omit it.
            rawroots = [d for d in walk(obj) if d.get('realPath') == rootpath]
            scene['root_path_refs'] = len(rawroots)
            roots_found = 0
            for node in nodes:
                payload = resolve(node['questNode'])
                refs = [d for d in walk(payload) if d.get('realPath') == rootpath]
                if not refs:
                    continue
                roots_found += len(refs)
                nodeid = node['nodeId']['id']
                mappings = [value(x) for x in node['isockMappings']]
                incoming = []
                for source in walk(obj):
                    if 'nodeId' not in source or 'outputSockets' not in source:
                        continue
                    for sock in source['outputSockets']:
                        for dest in sock.get('destinations', []):
                            if dest.get('nodeId', {}).get('id') != nodeid:
                                continue
                            ordinal = dest['isockStamp']['ordinal']
                            assert 0 <= ordinal < len(mappings), (path, nodeid, ordinal)
                            incoming.append({'source': source['nodeId']['id'],
                                             'source_stamp': sock['stamp'],
                                             'destination_stamp': dest['isockStamp'],
                                             'input': mappings[ordinal]})
                entry['root_writers'].append({'scene': scene['path'], 'node': nodeid,
                                             'type': payload.get('$type'), 'incoming': incoming})
            assert roots_found == len(rawroots), (path, 'unaccounted root refs', roots_found, len(rawroots))
            entry['scenes'].append(scene)
        result['owners'].append(entry)
    result['root_failed_inputs'] = sum(x['input'] == 'Failed' for o in result['owners']
                                      for n in o['root_writers'] for x in n['incoming'])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    assert not OUT.exists(), OUT
    OUT.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
