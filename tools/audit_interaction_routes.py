"""Bounded scene-route evidence for the world-interaction batch (read only)."""
import argparse
import json
from pathlib import Path
from audit_world_interactions import walk

def reachable(root, entry):
    nodes = {n['Data']['nodeId']['id']: n['Data'] for n in root['sceneGraph']['Data']['graph']}
    seen, queue = set(), [entry]
    while queue:
        i = queue.pop()
        if i in seen:
            continue
        seen.add(i)
        queue.extend(d['nodeId']['id'] for s in nodes[i].get('outputSockets', []) for d in s.get('destinations', []))
    return nodes, seen

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('scene', type=Path)
    ap.add_argument('entry', type=int)
    args = ap.parse_args()
    r = json.loads(args.scene.read_text(encoding='utf-8-sig'))['Data']['RootChunk']
    nodes, seen = reachable(r, args.entry)
    print('reachable', sorted(seen))
    for i in sorted(seen):
        n = nodes[i]
        print(i, n['$type'], 'actors', sorted({o['id'] for o in walk(n) if o.get('$type') == 'scnActorId'}),
              'performers', sorted({o['id'] for o in walk(n) if o.get('$type') == 'scnPerformerId'}),
              'events', [(e['Data']['$type'], sorted({o['id'] for o in walk(e) if o.get('$type') == 'scnActorId'})) for e in n.get('events', [])],
              'writers', [o for o in walk(n) if o.get('$type') == 'questSetVar_NodeType'])
    for key in ('referencePoints', 'notablePoints', 'interruptionScenarios', 'workspotInstances'):
        print(key, [(x.get('id'), [(o['$type'], o['id']) for o in walk(x) if o.get('$type') in ('scnActorId','scnPerformerId')]) for x in r[key]])
