"""Read-only native graph inspection; writes only new FO1 research artifacts."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten
from catalog_gig_rollout_r2 import read, sha, walk

OUT = ROOT / 'research/fixer_offices_fo1'

def main():
    paths = list((ROOT / 'research/gig_restoration/family_b7/fixers/json').rglob('*.questphase.json'))
    paths += list((OUT / 'scenes/json').rglob('*.questphase.json'))
    reports = []
    for path in paths:
        r = SafeResource(read(path))
        graphs = flatten(r, r.obj['Data']['RootChunk'])
        row = {'source': str(path.relative_to(ROOT)), 'sha256': sha(path), 'graphs': graphs}
        reports.append(row)
        print('\nRESOURCE', path.name)
        for g in graphs:
            if any(n['$type'] == 'questSceneNodeDefinition' for n in g['nodes']) and g['path'] != 'root':
                print('SCENE BRANCH', g['path'])
                for n in g['nodes']:
                    print(n['id'], json.dumps(n, separators=(',', ':')))
                print('EDGES', g['edges'])
    dest = OUT / 'native_graphs.json'
    data = json.dumps(reports, indent=2) + '\n'
    if dest.exists():
        assert dest.read_text() == data, 'Existing audit differs; use a revision'
    else:
        dest.write_text(data)

if __name__ == '__main__':
    main()
