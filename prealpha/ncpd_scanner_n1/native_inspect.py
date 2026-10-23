"""Read-only native graph inspection; no runtime or save changes."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from test_gig_pilot_r1 import Resource
from audit_activity_batches_b1 import flatten


class SafeResource(Resource):
    def d(self, v):
        return None if isinstance(v, dict) and v.get('HandleRefId') == '-1' else super().d(v)


def main():
    args = sys.argv[1:]
    brief = '--brief' in args
    root_only = '--root' in args
    for pattern in [a for a in args if not a.startswith('--')]:
        for path in ROOT.glob(pattern):
            r = SafeResource(json.loads(path.read_text(encoding='utf-8-sig')))
            print('\nFILE', path.relative_to(ROOT))
            roots = [('root', r.obj['Data']['RootChunk'])]
            roots += [(f'embedded/{i}', e['Content']) for i, e in enumerate(r.obj['Data'].get('EmbeddedFiles', [])) if 'graph' in e.get('Content', {})]
            for name, root in roots:
                for g in flatten(r, root):
                    if root_only and (name != 'root' or g['path'] != 'root'):
                        continue
                    print('GRAPH', name + g['path'][4:])
                    for n in g['nodes']:
                        text = json.dumps(n, ensure_ascii=False, separators=(',', ':'))
                        if brief:
                            extras = []
                            from catalog_gig_rollout_r2 import walk
                            for v in walk(n):
                                if 'factName' in v: extras.append(v)
                                if 'realPath' in v: extras.append(v['realPath'])
                                if 'phaseResource' in v: extras.append(v['phaseResource']['DepotPath'])
                            text = f"{n['id']} {n['$type']} " + json.dumps(extras, separators=(',', ':'))
                        print(text)
                    print('EDGES', json.dumps(g['edges'], separators=(',', ':')))


if __name__ == '__main__':
    main()
